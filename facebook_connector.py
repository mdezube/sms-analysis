from fbchat_archive_parser.parser import MessageHtmlParser
import fnmatch
import os
import pandas as pd


def initialize(dump_location='.'):
    global messages_file
    fb_message_filename = 'messages.htm'
    messages_file = os.path.join(dump_location, fb_message_filename)
    if not os.path.isfile(messages_file):
        print("Please place the message.htm file at {}".format(
            os.path.abspath(messages_file)))
        return


def get_cleaned_fully_merged_messages():
    chats = MessageHtmlParser(path=messages_file).parse()
    me = chats.user
    addresses = set()
    messages = []
    for thread in chats.threads.itervalues():
        for participant in thread.participants:
            if participant is not None and not participant.isspace():
                addresses.add(participant)
        for message in thread.messages:
            if (message.content is not None
                and message.content
                and not message.content.isspace()):
                from_me = True if message.sender == me else False
                messages.append([message.content,
                                 message.timestamp,
                                 from_me,
                                 message.sender])
    address_book = pd.DataFrame(columns=["full_name"],
                                data=[[address_entry]
                                      for address_entry in addresses])
    chat_messages = pd.DataFrame(
        columns=["text", "date", "is_from_me", "full_name"], data=messages)
    return chat_messages, address_book
