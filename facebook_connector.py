import os
import fnmatch

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


if __name__ == "__main__":
    initialize()
