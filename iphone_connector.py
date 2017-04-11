"""

Author: Mike Dezube <michael dezube at gmail dot com>

This module abstracts away a lot of the logic of dealing with the sqlite databases that contain text messages and
contacts on an iPhone.

For further exploring, I highly recommend using sqlitebrowser or DbVisualizer to connect to the databases directly. As
a convenience, you can find a visualization of both the address book DB and message DB adjacent to this file.

"""

from __future__ import print_function
from __future__ import division

import argparse
import os
import pandas as pd
import re
import sqlite3

from IPython.display import display

MESSAGE_DB = '3d0d7e5fb2ce288813306e4d4636395e047a3d28'
ADDRESS_DB = '31bb7ba8914766d4ba40d6dfb6113c8b614be442'

# Module variables
_latest_sync_dir = None
_message_con = None
_address_con = None

# START SIMPLE HELPER METHODS
# --------------


# Get's the most recently updated directory within the passed directory.
def __get_latest_dir_in_dir(directory):
    newest_path, newest_date = ('', -1)
    for relative_path in os.listdir(directory):
        full_path = os.path.join(directory, relative_path)
        if not os.path.isdir(full_path):  # Ignore non-directories.
            continue
        if os.path.getmtime(full_path) > newest_date:
            newest_path, newest_date = (full_path, os.path.getmtime(full_path))
    return newest_path


# Removes leading ones from phone numbers as well as any spaces or punctuation.
def __standardize_phone_numbers(row):
    phone_or_email = row.phone_or_email
    if '@' not in phone_or_email:
        # Change unbreakable space characters into regular spaces.
        phone_or_email = phone_or_email.replace(u'\xa0', u' ')
        phone_or_email = re.sub(r'[()\- ]+', '', phone_or_email)
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
    FROM handle, chat_handle_join, chat, chat_message_join, message
    WHERE
      handle.ROWID = chat_handle_join.handle_id
      AND chat_handle_join.chat_id = chat.ROWID
      AND chat.ROWID = chat_message_join.chat_id
      AND message.ROWID = chat_message_join.message_id
      AND ((chat_handle_join.handle_id = message.handle_id) OR message.is_from_me)''', _message_con)

    # Clean it up a bit.
    message_id_joined_to_phone_or_email['country'] = message_id_joined_to_phone_or_email['country'].str.lower()
    message_id_joined_to_phone_or_email['phone_or_email'] = message_id_joined_to_phone_or_email.apply(
        __standardize_phone_numbers, axis=1)
    return message_id_joined_to_phone_or_email


# Join the table that has message IDs and phones numbers/emails with the address book in order to get the full
# name and additional info.
def __get_address_joined_with_message_id(address_book):
    address_joined_with_message_id = (
        __get_message_id_joined_to_phone_or_email().merge(address_book, how='left', left_on='phone_or_email',
                                                          right_index=True, indicator='merge_chat_with_address')
    )
    address_joined_with_message_id = address_joined_with_message_id.drop(['ROWID'], axis=1)

    key_fields = ['message_id', 'chat_id', 'phone_or_email']
    duplicates = address_joined_with_message_id.duplicated(subset=key_fields,
                                                           keep=False)
    if not sum(duplicates) == 0:
        error_message = ('WARNING: tuple (message_id, chat_id, and phone_or_email) '
                         'do not form a composite key. There are %i duplicates. '
                         'Dropping the duplicates so later calculations are still valid.')
        print(error_message % sum(duplicates))
        address_joined_with_message_id.drop_duplicates(subset=key_fields, inplace=True)

    return address_joined_with_message_id


def initialize():
    """
        Initializes the connections to the address book and the messages sqlite databases.
    """
    global _latest_sync_dir, _message_con, _address_con

    if os.getenv('APPDATA'):  # Windows.
        base_dir = os.path.join(os.getenv('APPDATA'), 'Apple Computer')
    else:  # Mac.
        base_dir = os.path.join(os.getenv('HOME'), 'Library', 'Application Support')
    base_dir = os.path.join(base_dir, 'MobileSync', 'Backup')

    _latest_sync_dir = __get_latest_dir_in_dir(base_dir)
    print('Latest iPhone backup directory: {0}'.format(_latest_sync_dir))

    # Newer iPhone OS's shard the backup into subdirectories starting with the first two chars
    # of the files within them.
    has_subdirectory_structure = MESSAGE_DB[:2] in os.listdir(_latest_sync_dir)
    if has_subdirectory_structure:
        message_path = os.path.join(_latest_sync_dir, MESSAGE_DB[:2], MESSAGE_DB)
        address_path = os.path.join(_latest_sync_dir, ADDRESS_DB[:2], ADDRESS_DB)
    else:
        message_path = os.path.join(_latest_sync_dir, MESSAGE_DB)
        address_path = os.path.join(_latest_sync_dir, ADDRESS_DB)

    _message_con = sqlite3.connect(message_path)
    _address_con = sqlite3.connect(address_path)

    # Try to read from the DB files as a check to see if they are encrypted.
    # Checking if one of the tables is encrypted suffices because either all tables are encrypted or
    # all tables are unencrypted.
    try:
        _message_con.execute("SELECT name FROM SQLITE_MASTER where type='table'")
    except sqlite3.DatabaseError:
        raise sqlite3.DatabaseError(
            "A sqlite connection to the file at {0} failed, perhaps you've set iTunes to use encrypted backup?"
            .format(message_path)
        )

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
      FROM message''', _message_con)
    
    messages_df = messages_df.set_index('message_id')

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
    ''', _address_con)

    # Clean it up a bit.
    address_book = address_book[(address_book['property'] == 4) | (address_book['property'] == 3)]  # Of type phone or email
    address_book['phone_or_email'] = address_book.apply(__standardize_phone_numbers, axis=1)

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
        print('Messages Dataframe')
        display(messages_df.head(1))

        print('Address Book Dataframe')
        display(address_book.head(1))

        print('Phones/emails merged with message IDs via chats Dataframe')
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
        atoms_as_str = [atom.encode('utf8') if type(atom).__name__ == 'unicode' else str(atom) for atom in atoms]
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
    print('Loaded {0:,} messages.'.format(messages_df.shape[0]))

    # LOAD ADDRESS BOOK DATAFRAME
    address_book_df = get_address_book()
    # Drop a column that we don't use now, but may in the future.
    address_book_df = address_book_df.drop('property', axis=1)
    print('Loaded {0:,} contacts.'.format(address_book_df.shape[0]))

    # JOIN THE MESSAGE AND ADDRESS BOOK DATAFRAMES
    fully_merged_messages_df = get_merged_message_df(messages_df, address_book_df)
    # Drop a few columns we don't care about for now
    fully_merged_messages_df = fully_merged_messages_df.drop(['handle_id',
                                                              'country_messages_df',
                                                              'country_other_join_tbl',
                                                              'service_messages_df',
                                                              'service_other_join_tbl'],
                                                               axis=1)

    print('Messages with phone numbers not found in address book: {0:,}'.format(
        fully_merged_messages_df[fully_merged_messages_df.merge_chat_with_address != 'both'].shape[0]))

    print(('Messages loaded: {0:,} (this is larger than the length of the messages table due to group '
           'messages you sent)').format(fully_merged_messages_df.shape[0]))

    # Drop some columns that we're no longer going to need.
    fully_merged_messages_df = fully_merged_messages_df.drop(['merge_chat_with_address',
                                                              'merge_chat_with_address_and_messages'],
                                                               axis=1)

    # Merge the first name, last name and company column together to create a "full_name" column, runs in place.
    _collapse_first_last_company_columns(fully_merged_messages_df)
    _collapse_first_last_company_columns(address_book_df)

    fully_merged_messages_df.sort_values(by='date', inplace=True)
    fully_merged_messages_df.reset_index(inplace=True, drop=True)
    fully_merged_messages_df.index.name = 'row_index'  # Without this Excel will complain upon import.

    print('\nPrinting columns of merged messages dataframe:')
    print(', '.join(fully_merged_messages_df.columns.get_values()))
    print('\nPrinting columns of address book dataframe:')
    print(', '.join(address_book_df.columns.get_values()))
    return fully_merged_messages_df, address_book_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print out the text messages and contacts from '
                                                 'your iPhone\'s backup.')
    parser.add_argument('-f', '--full', action='store_true', dest='full',
                        help='If passed, message output includes more than just the text, date and '
                             'full_name columns, and the address book output includes more than '
                             'just the name and phone columns.')
    parser.add_argument('output_directory', nargs='?',
                        help='If passed, the messages and address book will be written to this '
                             'directory each as a CSV.  This directory must already exist.')
    args = parser.parse_args()

    # Set width to none so it auto-fills to the terminal window.
    pd.set_option('display.width', None)
    initialize()

    message_df, addresses_df = get_cleaned_fully_merged_messages()
    # Note we don't explicitly print phone_or_email since it's the index.
    addresses_to_print = addresses_df if args.full else addresses_df[['full_name']]
    messages_to_print = message_df if args.full else message_df[['full_name', 'date', 'text']]

    if args.output_directory:
        addresses_to_print.to_csv(os.path.join(args.output_directory, 'addresses.csv'), encoding='utf-8')
        messages_to_print.to_csv(os.path.join(args.output_directory, 'messages.csv'), encoding='utf-8')
    else:
        print('\nADDRESS BOOK (output to CSV for full data):')
        print(addresses_to_print)
        print('\n\n\nMESSAGES (output to CSV for full data):')
        print(messages_to_print)
