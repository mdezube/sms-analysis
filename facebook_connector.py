"""

Author: Nigel Schuster <nigel schusters at gmail dot com>

This module provides a simple abstraction for accessing the Facebook chat data

"""

from __future__ import print_function

from bs4 import BeautifulSoup
from fbchat_archive_parser.parser import MessageHtmlParser
import fnmatch
import os
import pandas as pd
import re
import warnings

_messages_file = None
_fb_id_pattern = re.compile(r"(\d+)@facebook\.com")


def initialize(dump_location="."):
    """
        Initializes the access to the Facebook messages file by asserting its location

        Args:
            dump_location: path to the messages.htm file
    """
    global _messages_file
    fb_message_filename = "messages.htm"
    _messages_file = os.path.join(dump_location, fb_message_filename)
    if not os.path.isfile(_messages_file):
        print("Please specify the location of the file in the function call".format(
            os.path.abspath(_messages_file)))
        _messages_file = None


def resolve_user_id(user_id):
    """
    Tries to map the identifier facebook provides to the name of the user.

    Args:
        user_id: identifier string that is provided in the messages file

    Returns:
        The name of the user if it is able to find it, otherwise the input
    """
    return user_id


def get_cleaned_fully_merged_messages(strip_html_content=True,
                                      resolve_fb_id=False):
    """
    Parses the messages file to create dataframes that contain the messages and their senders respectively

    Args:
        strip_html_content: The messages.htm file might contain some html tags in messages. This option will remove all html markup.
        resolve_fb_id: The messages.htm file does always print Facebook names, but sometimes ids instead. This will atempt to resolve the issue.

    Returns:
        a dataframe that contained all messages with info about their senders
    """
    if _messages_file is None:
        print("Please initialize the module first.")
        return
    chats = MessageHtmlParser(path=_messages_file).parse()
    me = chats.user
    addresses = set()
    messages = []
    warnings.filterwarnings("ignore", category=UserWarning, module='bs4')
    for thread in chats.threads.itervalues():
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
                try:
                    content = BeautifulSoup(message.content, "html.parser").text
                except:
                    content = message.content
            else:
                content = message.content
            if from_me:
                for participant in resolved_participants:
                    messages.append([content, message.timestamp, from_me, participant])
            else:
                messages.append([content, message.timestamp, from_me, sender])
    address_book_df = pd.DataFrame(data=list(addresses), columns=["full_name"])
    messages_df = pd.DataFrame(data=messages, columns=["text", "date", "is_from_me", "full_name"])
    return messages_df, address_book_df
