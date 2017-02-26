from fbchat_archive_parser.parser import MessageHtmlParser
import fnmatch
from lxml import html
import os
import pandas as pd
import re
from urllib2 import urlopen

_messages_file = None
_fb_id_pattern = re.compile("(\\d+)@facebook\\.com")
_html_tags_pattern = re.compile('<.*?>')
_mapped_fb_ids = {}


def initialize(dump_location='.'):
    global _messages_file
    fb_message_filename = 'messages.htm'
    _messages_file = os.path.join(dump_location, fb_message_filename)
    if not os.path.isfile(_messages_file):
        print("""
Please place the messages.htm file at {}
or specify the location of the file in the function call
""".format(os.path.abspath(_messages_file)))
        _messages_file = None


def resolve_user_id(user_id):
    pattern_match = fb_id_pattern.match(user_id)
    if pattern_match:
        fb_numeric_id = pattern_match.group(1)
        try:
            if fb_numeric_id not in mapped_fb_ids:
                fb_page_title = html.parse(urlopen(
                    "https://www.facebook.com/{}".format(fb_numeric_id)
                    )).find(".//title").text
                username = fb_page_title.split("|")[0].strip()
                if not username.startswith('Security Check Required'):
                    mapped_fb_ids[fb_numeric_id] = username
            else:
                return mapped_fb_ids[fb_numeric_id]
        except:
            # Probably deleted user
            mapped_fb_ids[fb_numeric_id] = fb_numeric_id
    return user_id


def get_cleaned_fully_merged_messages(
                                      resolve_fb_id=False,
                                      strip_html_content=True):
    if _messages_file is None:
        print("Please initialize the module first.")
        return
    chats = MessageHtmlParser(path=_messages_file).parse()
    me = chats.user
    addresses = set()
    messages = []
    for thread in chats.threads.itervalues():
        recipients = set()
        for participant in thread.participants:
            if participant is not None and not participant.isspace():
                recipient = resolve_user_id(
                    participant) if resolve_fb_id else participant
                recipients.add(recipient)
        addresses.update(recipients)
        for message in thread.messages:
            if (message.content and not message.content.isspace()):
                sender = resolve_user_id(
                    message.sender) if resolve_fb_id else message.sender
                from_me = sender == me
                content = ''
                if strip_html_content:
                    content = re.sub(_html_tags_pattern, '', message.content)
                else:
                    content = message.content
                if from_me:
                    for recipient in recipients:
                        messages.append([content,
                                         message.timestamp,
                                         from_me,
                                         recipient])
                else:
                    messages.append([content,
                                     message.timestamp,
                                     from_me,
                                     sender])
    address_book_df = pd.DataFrame(columns=["full_name"],
                                   data=list(addresses))
    messages_df = pd.DataFrame(
        columns=["text", "date", "is_from_me", "full_name"], data=messages)
    return messages_df, address_book_df
