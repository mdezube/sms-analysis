"""

Author: Nigel Schuster <nigel schusters at gmail dot com>

This module provides a simple abstraction for accessing the Facebook chat data

"""

from __future__ import print_function

from bs4 import BeautifulSoup
from fbchat_archive_parser.parser import MessageHtmlParser
import os
import pandas as pd
import re
import warnings

_messages_file = None
_fb_id_pattern = re.compile(r"(\d+)@facebook\.com")


def initialize(dump_directory="."):
    """
        Initializes the access to the Facebook messages file by asserting its location

        Args:
            dump_directory: path to the directory that contains messages.htm file
    """
    global _messages_file
    fb_message_filename = "messages.htm"
    _messages_file = os.path.join(dump_directory, fb_message_filename)
    if not os.path.isfile(_messages_file):
        print("Please specify the location of the file in the function call")
        _messages_file = None


def resolve_user_id(user_id):
    """
    Tries to map the identifier facebook provides to the name of the user

    Args:
        user_id: identifier string that is provided in the messages file

    Returns:
        The name of the user if it is able to find it, otherwise the input
    """
    # TODO (neitsch): This method is not implemented yet
    #                 Use the user_id (format: 12345678@facebook.com) to get the
    #                 actual name of the user
    return user_id


def get_cleaned_fully_merged_messages(strip_html_content=True,
                                      resolve_fb_id=False):
    """
    Parses the messages file to create dataframes that contain the messages and their senders

    Args:
        strip_html_content: The messages.htm file might contain some html tags in messages; this option will remove all html markup
        resolve_fb_id: The messages.htm file doesn't always print Facebook names, but sometimes ids instead; this will atempt to resolve the issue,
		but requires a web request per id and is not guaranteed to work

    Returns:
        a dataframe that contains all messages with info about their senders
    """
    if _messages_file is None:
        print("Please initialize the module first.")
        return
    chats = MessageHtmlParser(path=_messages_file).parse()
    me = chats.user
    addresses = set()
    messages = []
    # Suppressing warning on BS4 that shows up when trying to parse non HTML content
    # Some messages might contain HTML tags others might not and we don't want to display
    # these warnings to the user
    warnings.filterwarnings("ignore", category=UserWarning, module='bs4')
    try:
        threads = chats.threads.itervalues()
    except AttributeError:
        threads = chats.threads.values()
    for thread in threads:
        resolved_participants = set()
        for participant in thread.participants:
            if participant is not None and not participant.isspace():
                resolved_participant = resolve_user_id(
                    participant) if resolve_fb_id else participant
                resolved_participants.add(resolved_participant)
        addresses.update(resolved_participants)
        for message in thread.messages:
            if (not message.content or message.content.isspace()):
                continue
            sender = resolve_user_id(
                message.sender) if resolve_fb_id else message.sender
            from_me = sender == me
            content = ""
            if strip_html_content:
                content = BeautifulSoup(message.content, "html.parser").text
            else:
                content = message.content
            # In the following we add a single message to our dataframe
            if from_me:
                # If the user is sending a message to a group, then we need to add
                # one message per group participant to the dataframe
                for participant in resolved_participants:
                    messages.append((content, message.timestamp, from_me, participant))
            else:
                messages.append((content, message.timestamp, from_me, sender))
    address_book_df = pd.DataFrame(data=list(addresses), columns=["full_name"])
    messages_df = pd.DataFrame(data=messages, columns=["text", "date", "is_from_me", "full_name"])
    return messages_df, address_book_df
