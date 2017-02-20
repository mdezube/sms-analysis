import os
import fnmatch
import pandas as pd
from fbchat_archive_parser.parser import MessageHtmlParser

def initialize(location = '.'):
    global _message_file
    fb_message_filename = 'messages.htm'
    _message_file = os.path.join(location, fb_message_filename)
    if os.path.isfile(_message_file):
        return
    count = 0
    fb_archive_path = 'html'
    for file in os.listdir(location):
        if os.path.isdir(os.path.join(location,file)) and fnmatch.fnmatch(file, 'facebook-*'):
            count = count + 1
            _message_file = os.path.join(file, fb_archive_path, fb_message_filename)
    if count == 0:
        print 'No Message file found.'
    if count > 1:
        print 'More than one Message file was found.'

def get_cleaned_fully_merged_messages():
    parser = MessageHtmlParser(path=_message_file)
    chats = parser.parse()
    me = chats.user
    addr = []
    msg = []
    for chat in chats.threads.itervalues():
        for participant in chat.participants:
            addr.append([participant])
        for message in chat.messages:
            from_me = True if message.sender == me else False
            msg.append([message.content, message.timestamp, from_me, message.sender])
    addressbook = pd.DataFrame(columns=("full_name",),data=addr)
    chatmessage = pd.DataFrame(columns=("text","date","is_from_me","full_name"),data=msg)
    return chatmessage, addressbook

if __name__ == "__main__":
    initialize()
    print(get_cleaned_fully_merged_messages())
