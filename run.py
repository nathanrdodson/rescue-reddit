import configparser
from shutil import copyfile
import os
import sys
import re
import getpass
import requests
import praw
import prawcore
from praw.models import Submission
from url_normalize import url_normalize
from videoparser import extract_mp4
# import logging
#
# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)
# logger = logging.getLogger('prawcore')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(handler)

CONFIG = configparser.ConfigParser()

def is_downloadable(url):
    h = requests.head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True

def main(argv):

    try:
        file = open("config.ini")
    except FileNotFoundError:
        # config not found
        print("config.ini not found. Starting setup...")

        # copy sample configuration template from root
        copyfile("sample_config.ini", "config.ini")

        # begin user input for new configuration
        CONFIG.read('config.ini')
        print("Reddit username: ")
        CONFIG['rescuereddit']['username'] = input()
        CONFIG['rescuereddit']['password'] = getpass.getpass(prompt='Reddit Password: ', stream=None)
        print("client_secret: ")
        CONFIG['rescuereddit']['client_secret'] = input()
        print("client_id: ")
        CONFIG['rescuereddit']['client_id'] = input()
        print("Define directory? (enter for default): ")
        dir = input()
        if dir == "":
            print("Using home directory...")
        elif dir != "":
            CONFIG['rescuereddit']['user_dir'] = dir
        with open('config.ini', 'w') as configfile:
            CONFIG.write(configfile)

    CONFIG.read('config.ini')
    # Define Reddit praw variables
    client_id = CONFIG['rescuereddit']['client_id']
    client_secret = CONFIG['rescuereddit']['client_secret']
    username = CONFIG['rescuereddit']['username']
    password = CONFIG['rescuereddit']['password']
    user_agent = 'script:rescue-reddit:v0.1.4 (by /u/danishkaiju)'
    userdirectory = CONFIG['rescuereddit']['user_dir']

    reddit = praw.Reddit(client_id=client_id, password=password, username=username, client_secret=client_secret, user_agent=user_agent)
    user = str(reddit.user.me())

    # saved_count = 0
    # for saves in reddit.user.me().saved(limit=None):
    #     saved_count += 1
    # print(saved_count)

    print("Successfully connected to user: \033[93m" + user + '\x1b[0m')
    print("==========")
    print("What saves would you like to pull from Reddit?:\n", "[1] All media types\n", "[2] Photos\n", "[3] GIFs\n", "[4] Text Submissions")
    print("==========")

    userchoice = input()

    counter = 1
    for saves in reddit.user.me().saved(limit=None):
        download(userdirectory, userchoice, saves, counter)
        counter += 1

    sys.exit(0)

def download(userdirectory, media, saves, counter):

    if isinstance(saves, Submission):

        # Convert Reddit title to string
        filename = str(saves.title)

        # Make filename alphanumeric
        pattern = re.compile(r'[\W_]+', re.UNICODE)
        filename = pattern.sub('', filename)

        # Get file extension from URL
        name, ext = os.path.splitext(saves.url)

        # Check for nameless files
        if filename == '':
            truncated_filename = ('File_%s' % counter)
        else:
            truncated_filename = (filename[:25] + '..') if len(filename) > 25 else filename

        # Remove crap after question mark in URl
        pattern = re.compile(r'\?(.*)', re.UNICODE)
        ext = pattern.sub('', ext)

        if((media == '2' or media == '1') and ('.png' in saves.url or '.jpg' in saves.url)):
            # Verify content type
            if is_downloadable(saves.url):
                makedir(userdirectory, saves)
                print("*", end='', flush=True)
                r = requests.get(saves.url, allow_redirects=True)
                open(truncated_filename +ext, 'wb').write(r.content)
            else:
                print("X", end='', flush=True)
        if((media == '3' or media == '1') and ('.gif' in saves.url)):
            # Verify content type
            if ext == '.gifv':
                ext = '.mp4'
            if is_downloadable(saves.url):
                makedir(userdirectory, saves)
                print("*", end='', flush=True)
                r = requests.get(saves.url, allow_redirects=True)
                open(truncated_filename +ext, 'wb').write(r.content)
            else:
                for x in extract_mp4(saves.url):
                # Verify content type
                    x = url_normalize(str(x))
                    if is_downloadable(x):
                        makedir(userdirectory, saves)
                        print("*", end='', flush=True)
                        r = requests.get(x, allow_redirects=True)
                        open(truncated_filename +ext, 'wb').write(r.content)
                    else:
                        print("X", end='', flush=True)

        if((media == '4' or media == '1') and saves.is_self):
            makedir(userdirectory, saves)
            print("*", end='', flush=True)
            subtext = str(saves.selftext)
            open(truncated_filename + '.md', 'w', encoding="utf-8").write(subtext)

def makedir(userdirectory, saves):
    # Crete Subreddit directory:
    sub = str(saves.subreddit)
    if userdirectory == "default":
        if os.name == 'nt':
            path = os.path.expanduser('~') + "\\Documents\\RescueReddit\\" + sub
        else:
            path = os.path.expanduser('~') + "/RescueReddit/" + sub
    else:
        path = os.path.abspath(userdirectory) + "/RescueReddit/" + sub

    try:
        os.makedirs(os.path.expanduser(os.path.abspath(path)), exist_ok=False)
    except FileExistsError:
        pass
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        pass

    os.chdir(path)

while True:
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        CONFIG.read('config.ini')
        if CONFIG['rescuereddit']['password'] == "<password>":
            os.remove("config.ini")
            print("\nRemoving unfinished configuration...")
        sys.exit(0)
    except prawcore.exceptions.OAuthException:
        print("Failed to authenticate, please try different credentials.")
        sys.exit(0)
