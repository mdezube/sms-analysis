"""

Author: Nigel Schuster <nigel schusters at gmail dot com>

This module provides a simple abstraction for accessing Facebook messages data
from a downloaded archive from facebook.com

"""

from __future__ import print_function

from bs4 import BeautifulSoup
from fbchat_archive_parser.parser import parse
import logging
import os
import io
import pandas as pd
import re
import requests
import warnings

_messages_file = None

_FB_ID_PATTERN = re.compile(r"(\d+)@facebook\.com")
_mapped_fb_ids = {}


def initialize(dump_directory="."):
    """
    Asserts the messages.htm file in the Facebook dump can be found and
    saves its location for later usage in this module

    Args:
        dump_directory: path to the directory that contains messages.htm file
    """
    global _messages_file
    fb_message_filename = "html/messages.htm"
    _messages_file = os.path.join(dump_directory, fb_message_filename)
    if not os.path.isfile(_messages_file):
        print("""
            The directory provided did not contain messages.htm,
            the directory should be within the archive
            downloaded from facebook.com
        """)
        _messages_file = None


def resolve_user_id(fb_provided_identifier):
    """
    Tries to map the provided identifier for facebook to the name of the user

    Args:
        fb_provided_identifier: identifier string that is provided
            in the messages file. This might be the user's name or
            his Facebook ID. Only if the input is a Facebook ID in the form
            of a number followed by @facebook.com, then it will be resolved.
            For example 100000125040120@facebook.com will resolve to
            "Nigel Schuster"

    Returns:
        The name of the user if it is able to find it, otherwise the input
    """
    fb_id_pattern_match = _FB_ID_PATTERN.match(fb_provided_identifier)
    if not fb_id_pattern_match:
        # fb_provided_identifier is not in the form
        # We are expecting (_FB_ID_PATTERN),
        # so it should not be mapped
        return fb_provided_identifier
    fb_numeric_id = fb_id_pattern_match.group(1)
    if fb_numeric_id in _mapped_fb_ids:
        # We have looked the id up before, so just return the result
        return _mapped_fb_ids[fb_numeric_id]
    try:
        # Try to find the user id
        fb_user_page = requests.get(
            "https://www.facebook.com/{}".format(fb_numeric_id))
        fb_page_title = BeautifulSoup(fb_user_page.content).title.string
        possible_username = fb_page_title.split("|")[0].strip()
        if ((possible_username.startswith('Security Check Required')
             or possible_username.startswith('Page Not Found'))):
            # Mapping not found for this user, this likely is not transient
            # since the HTTP request validly returned, therefore do not retry
            _mapped_fb_ids[fb_numeric_id] = fb_numeric_id
            logging.info(
                "Failed to lookup {0} via {1}, found result {2}".format(
                    fb_provided_identifier, fb_numeric_id, fb_page_title))
        else:
            # Here we know that possible_username is the user's name
            _mapped_fb_ids[fb_numeric_id] = possible_username
            logging.debug("Mapped identifier {0} to {1}".format(
                fb_provided_identifier, possible_username))
    except Exception as e:
        # Wasn't able to find the user - no harm done
        _mapped_fb_ids[fb_numeric_id] = fb_numeric_id
        logging.warning("Ran into error {0} for {1}".format(e, fb_numeric_id))
    return _mapped_fb_ids[fb_numeric_id]


def get_cleaned_fully_merged_messages(strip_html_content=True,
                                      resolve_fb_id=False):
    """
    Parses the messages file to create dataframes that contain the messages and
    their senders.

    Args:
        strip_html_content: The messages.htm file might contain some html tags
            in messages; this option will remove all html markup
        resolve_fb_id: The messages.htm file doesn't always print Facebook
            names, but sometimes ids instead; this will attempt
            to resolve them, but requires a web request per id and is not
            guaranteed to work. Note, that this method will not
            necessarily succeed, since facebook blocks the number requests
            above a certain volume threshold. Setting this to true can only
            improve the results, since it can always fall back to the numeric
            identifier, but it will increase the time it takes.

    Returns:
        a dataframe that contains all messages with info about their senders
    """
    if not _messages_file:
        print("Please initialize the facebook_connector module.")
        return
    chats = None
    with io.open(_messages_file, mode="rt", encoding="utf-8") as handle:
        chats = parse(handle=handle)
    me = chats.user
    addresses = set()
    messages = []
    # Suppressing warning that BS4 will display
    # when a message only contains a URL
    warnings.filterwarnings("ignore", category=UserWarning, module='bs4')
    try:
        threads = chats.threads.itervalues()
    except AttributeError:
        threads = chats.threads.values()
    for thread in threads:
        # This set holds the list of participants after their identifier
        # has been resolved to their name (see  resolve_user_id)
        resolved_participants = set()
        for participant in thread.participants:
            if participant is not None and not participant.isspace():
                resolved_participant = resolve_user_id(
                    participant) if resolve_fb_id else participant
                resolved_participants.add(resolved_participant)
        addresses.update(resolved_participants)
        for message in thread.messages:
            if not message.content or message.content.isspace():
                continue
            sender = resolve_user_id(
                message.sender) if resolve_fb_id else message.sender
            from_me = sender == me
            if strip_html_content:
                content = BeautifulSoup(message.content, "html.parser").text
            else:
                content = message.content
            # In the following we add a single message to our dataframe
            if from_me:
                # If the user is sending a message to a group,
                # then we need to add one message
                # per group participant to the dataframe
                for participant in resolved_participants:
                    messages.append({
                        'text': content,
                        'date': message.timestamp,
                        'is_from_me': from_me,
                        'full_name': participant
                    })
            else:
                messages.append({
                    'text': content,
                    'date': message.timestamp,
                    'is_from_me': from_me,
                    'full_name': sender
                })
    address_book_df = pd.DataFrame(data=list(addresses), columns=["full_name"])
    messages_df = pd.DataFrame.from_records(messages)
    return messages_df, address_book_df
