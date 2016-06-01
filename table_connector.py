"""

Author: Mike Dezube <michael dezube at gmail dot com>

This module abstracts away a lot of the logic of dealing with the sqlite databases that contain text messages and
contacts on an iPhone.

For further exploring, I highly recommend using sqlitebrowser or DbVisualizer to connect to the databases directly. As
a convenience, you can find a visualization of both the address book DB and message DB adjacent to this file.

"""

import os
import sys
import re
import sqlite3

import pandas as pd
from IPython.display import display

BASE_DIR = '~/Library/Application Support/MobileSync/Backup'
MESSAGE_DB = '3d0d7e5fb2ce288813306e4d4636395e047a3d28'
ADDRESS_DB = '31bb7ba8914766d4ba40d6dfb6113c8b614be442'

# START SIMPLE HELPER METHODS
# --------------


# Get's the most recently updated directory within the passed directory.
def __get_latest_dir_in_dir(directory):
    directory_path = os.path.expanduser(directory)
    newest_path, newest_date = ('', -1)
    for relative_path in os.listdir(directory_path):
        full_path = os.path.join(directory_path, relative_path)
        if not os.path.isdir(full_path):  # Ignore non-directories.
            continue
        if os.path.getmtime(full_path) > newest_date:
            newest_path, newest_date = (full_path, os.path.getmtime(full_path))
    return newest_path


latest_sync_dir = __get_latest_dir_in_dir(BASE_DIR)
print 'Latest directory: {0}'.format(latest_sync_dir)
message_con = sqlite3.connect('{0}/{1}'.format(latest_sync_dir, MESSAGE_DB))
address_con = sqlite3.connect('{0}/{1}'.format(latest_sync_dir, ADDRESS_DB))


# Removes a leading one if it exists.
def __strip_initial_1_in_phone(row):
    phone_or_email = row.phone_or_email
    return re.sub(r'(\+?1)(\d{10})', r'\2', phone_or_email)


# --------------
# END SIMPLE HELPER METHODS


# Joins messages with the phone numbers/emails that sent them.  This handles group messages as well where one
# message could be sent to multiple people.
def __get_message_id_joined_to_phone_or_email():
    message_id_joined_to_phone_or_email = pd.read_sql_query('''
    SELECT
      handle.id AS phone_or_email, handle.service, handle.country,
      chat_message_join.message_id, chat.ROWID AS chat_id
    FROM handle, chat_handle_join, chat, chat_message_join
    WHERE
      handle.ROWID = chat_handle_join.handle_id
      AND chat_handle_join.chat_id = chat.ROWID
      AND chat.ROWID = chat_message_join.chat_id''', message_con)

    # Clean it up a bit.
    message_id_joined_to_phone_or_email['country'] = message_id_joined_to_phone_or_email['country'].str.lower()
    message_id_joined_to_phone_or_email['phone_or_email'] = message_id_joined_to_phone_or_email.apply(
        __strip_initial_1_in_phone, axis=1)
    return message_id_joined_to_phone_or_email


# Join the table that has message IDs and phones numbers/emails with the address book in order to get the full
# name and additional info.
def __get_address_joined_with_message_id(address_book):
    address_joined_with_message_id = (
        __get_message_id_joined_to_phone_or_email().merge(address_book, how='left', left_on='phone_or_email',
                                                          right_index=True, indicator='merge_chat_with_address')
    )
    address_joined_with_message_id = address_joined_with_message_id.drop(['ROWID'], axis=1)

    # Confirm that message_id, chat_id and phone_or_email form a composite key
    assert sum(address_joined_with_message_id.duplicated(subset=['message_id', 'chat_id', 'phone_or_email'],
                                                         keep=False)) == 0

    return address_joined_with_message_id


def get_message_df():
    """
    Loads the message database from disk.

    Returns:
        a pandas dataframe representing all text messages
    """
    messages_df = pd.read_sql_query('''
    SELECT
      ROWID as message_id, text, handle_id, country, service, version,
      DATETIME(date, 'unixepoch', '31 years') AS date,
      DATETIME(date_read, 'unixepoch', '31 years') AS date_read,
      DATETIME(date_delivered, 'unixepoch', '31 years') AS date_delivered,
      is_emote, is_from_me, is_read, is_system_message, is_service_message, is_sent,
      has_dd_results
    FROM message''', message_con)

    messages_df = messages_df.set_index(keys='message_id')

    # Convert a few columns to dates.
    messages_df['date'] = pd.to_datetime(messages_df['date'])
    messages_df['date_read'] = pd.to_datetime(messages_df['date_read'])
    messages_df['date_delivered'] = pd.to_datetime(messages_df['date_delivered'])

    # Drop the rows that have no text, I think these are just iphone specific weird rows.
    messages_df = messages_df.dropna(subset=['text'], how='all')
    # There seem to be some true duplicates, <100 of them, so just drop them.
    messages_df = messages_df.drop_duplicates()
    return messages_df


def get_address_book():
    """
    Loads the address book database from disk.  Ignores entries that are neither phone numbers or emails.

    Note:
        This also normalizes phone numbers by removing ()- spaces and a leading 1.

    Returns:
        a pandas dataframe representing all entries in the address book
    """
    address_book = pd.read_sql_query('''
    SELECT
      ROWID, ABMultiValue.property, ABMultiValue.value AS phone_or_email,
      First AS first, Last AS last, Organization AS company,
      DATETIME(Birthday, 'unixepoch', '31 years') AS birthday,
      DATETIME(CreationDate, 'unixepoch', '31 years') AS creation_date,
      DATETIME(ModificationDate, 'unixepoch', '31 years') AS modification_date
     FROM ABPerson, ABMultiValue
     WHERE ABPerson.ROWID = ABMultiValue.record_id
    ''', address_con)

    # Clean it up a bit.
    address_book = address_book[(address_book['property'] == 4) | (address_book['property'] == 3)]  # Of type phone or email
    address_book['phone_or_email'] = address_book['phone_or_email'].str.replace(r'[()\- ]', '')
    address_book['phone_or_email'] = address_book.apply(__strip_initial_1_in_phone, axis=1)

    # Convert a few columns to dates.
    address_book['birthday'] = pd.to_datetime(address_book['birthday'], errors='coerce')
    address_book['creation_date'] = pd.to_datetime(address_book['creation_date'])
    address_book['modification_date'] = pd.to_datetime(address_book['modification_date'])

    address_book = address_book.set_index('phone_or_email')
    address_book = address_book.sort_values(by=['first', 'last'])

    return address_book


def get_merged_message_df(messages_df, address_book, print_debug=False):
    """
        Merges a message dataframe with the address book dataframe to return a single dataframe that contains all
        messages with detailed information (e.g. name, company, birthday) about the sender.

    Args:
        messages_df: a dataframe containing all transmitted messages
        address_book: a dataframe containing the address book as loaded via this module
        print_debug: true if we should print out the first row of each intermediary table as it's created

    Returns:
        a dataframe that contained all messages with info about their senders
    """
    phones_with_message_id_df = __get_address_joined_with_message_id(address_book)

    if print_debug:
        print 'Messages Dataframe'
        display(messages_df.head(1))

        print 'Address Book Dataframe'
        display(address_book.head(1))

        print 'Phones/emails merged with message IDs via chats Dataframe'
        display(phones_with_message_id_df.head(1))

    return messages_df.merge(phones_with_message_id_df,
                             how='left',
                             suffixes=['_messages_df', '_other_join_tbl'],
                             left_index=True, right_on='message_id',
                             indicator='merge_chat_with_address_and_messages')


def _collapse_first_last_company_columns(df):
    assert 'first' in df.columns, 'Column "first" did not exist in dataframe'
    assert 'last' in df.columns, 'Column "last" did not exist in dataframe'
    assert 'company' in df.columns, 'Column "company" did not exist in dataframe'

    def create_full_name(row):
        atoms = [atom for atom in [row['first'], row['last'], row['company']] if atom]
        atoms_as_str = [atom.encode('utf8') if isinstance(atom, unicode) else str(atom) for atom in atoms]
        return ' '.join(atoms_as_str)

    df['full_name'] = df.apply(create_full_name, axis=1)
    df.drop(['first', 'last', 'company'], inplace=True, axis=1)


def get_cleaned_fully_merged_messages():
    """
        Merges the message dataframe with the address book dataframe to return a single dataframe that contains all
        messages with detailed information (e.g. name, company, birthday) about the sender.

    Returns:
        a dataframe that contained all messages with info about their senders
    """
    # LOAD MESSAGE DATAFRAME
    messages_df = get_message_df()
    # Drop some columns that we don't use now, but may in the future.
    messages_df.drop(['version', 'is_emote', 'is_read', 'is_system_message',
                      'is_service_message', 'has_dd_results'],
                       inplace=True, axis=1)
    print 'Loaded {0:,} messages.  Printing first row:'.format(messages_df.shape[0])
    display(messages_df.head(1))

    # LOAD ADDRESS BOOK DATAFRAME
    address_book_df = get_address_book()
    # Drop a column that we don't use now, but may in the future.
    address_book_df = address_book_df.drop('property', axis=1)
    print 'Loaded {0:,} contacts.  Printing first row:'.format(address_book_df.shape[0])
    display(address_book_df.head(1))

    # JOIN THE MESSAGE AND ADDRESS BOOK DATAFRAMES
    fully_merged_messages_df = get_merged_message_df(messages_df, address_book_df)
    # Drop a few columns we don't care about for now
    fully_merged_messages_df = fully_merged_messages_df.drop(['handle_id',
                                                              'country_messages_df',
                                                              'country_other_join_tbl',
                                                              'service_messages_df',
                                                              'service_other_join_tbl'],
                                                               axis=1)

    print 'Messages with phone numbers not found in address book: {0:,}'.format(
        fully_merged_messages_df[fully_merged_messages_df.merge_chat_with_address != 'both'].shape[0])
    print ('Messages loaded: {0:,} (this is larger than the length of the messages table as certain '
           'message IDs were sent in group messages.)').format(fully_merged_messages_df.shape[0])

    # Drop some columns that we're no longer going to need.
    fully_merged_messages_df = fully_merged_messages_df.drop(['merge_chat_with_address',
                                                              'merge_chat_with_address_and_messages'],
                                                               axis=1)

    # Merge the first name, last name and company column together to create a "full_name" column, runs in place.
    _collapse_first_last_company_columns(fully_merged_messages_df)
    _collapse_first_last_company_columns(address_book_df)

    print 'Printing first row of merged message dataframe:'
    display(fully_merged_messages_df.head(1))
    print 'Printing first row of address book with full name column (merged first name/last name/company):'
    display(address_book_df.head(1))
    return fully_merged_messages_df, address_book_df

if __name__ == "__main__":
    messages, addresses = get_cleaned_fully_merged_messages()
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        messages.to_csv(file_path + "messages.csv", encoding='utf-8')
        addresses.to_csv(file_path + "addresses.csv", encoding='utf-8')
    else:
        print messages
        print addresses
        
