#!/usr/bin/env python

import praw, prawcore
from praw.models import Submission
from praw.models import Subreddit
import sys, getopt
import re, os, requests, getpass, logging
from shutil import copyfile
from videoparser import extract_mp4
from url_normalize import url_normalize
import configparser

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
    userdirectory = ""
    try:
        opts, args = getopt.getopt(argv, "hd:",["directory="])
    except getopt.GetoptError:
        print("run.py -d <directory>")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print("run.py -d <directory>")
            sys.exit()
        elif opt in ("-d", "--directory"):
            userdirectory = arg

    config = configparser.ConfigParser()
    try:
        file = open("config.ini")
    except FileNotFoundError:
        print("config.ini not found. Starting setup...")
        copyfile("sample_config.ini", "config.ini")
        config.read('config.ini')
        print(config.sections())
        print("Reddit username: ")
        config['rescuereddit']['USERNAME'] = input()
        config['rescuereddit']['PASSWORD'] = getpass.getpass(prompt='Reddit Password: ', stream=None)
        print("client_secret: ")
        config['rescuereddit']['CLIENT_SECRET'] = input()
        print("client_id: ")
        config['rescuereddit']['CLIENT_ID'] = input()
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    config.read('config.ini')
    # Define Reddit praw variables
    CLIENT_ID = config['rescuereddit']['CLIENT_ID']
    CLIENT_SECRET = config['rescuereddit']['CLIENT_SECRET']
    USERNAME = config['rescuereddit']['USERNAME']
    PASSWORD = config['rescuereddit']['PASSWORD']
    USER_AGENT = 'script:rescue-reddit:v0.1.4 (by /u/danishkaiju)'

    reddit = praw.Reddit(client_id=CLIENT_ID, password=PASSWORD, username=USERNAME, client_secret=CLIENT_SECRET, user_agent=USER_AGENT)
    user = str(reddit.user.me())

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
        if filename == '' :
            truncatedFilename = ('File_%s' % counter)
        else:
            truncatedFilename = (filename[:25] + '..') if len(filename) > 25 else filename

        # Remove crap after question mark in URl
        pattern = re.compile(r'\?(.*)', re.UNICODE)
        ext = pattern.sub('', ext)

        if((media == '2' or media == '1') and ('.png' in saves.url or '.jpg' in saves.url)):
            # Verify content type
            if is_downloadable(saves.url):
                makedir(userdirectory, saves)
                print('Title: '+ truncatedFilename +ext)
                print('URL: ' + saves.url)
                r = requests.get(saves.url, allow_redirects=True)
                open(truncatedFilename +ext, 'wb').write(r.content)
            else:
                print("\033[93m" + saves.url + '\x1b[0m')
                print("\033[93mUnable to retireive content..." + '\x1b[0m')

        if((media == '3' or media == '1') and ('.gif' in saves.url)):
            # Verify content type
            if ext == '.gifv':
                ext = '.mp4'
            if is_downloadable(saves.url):
                makedir(userdirectory, saves)
                print('Title: '+ truncatedFilename +ext)
                print('URL: ' + saves.url)
                r = requests.get(saves.url, allow_redirects=True)
                open(truncatedFilename +ext, 'wb').write(r.content)
            else:
                for x in extract_mp4(saves.url):
                # Verify content type
                    x = url_normalize(str(x))
                    if is_downloadable(x):
                        makedir(userdirectory, saves)
                        print('Title: '+ truncatedFilename +ext)
                        print('URL: ' + x)
                        r = requests.get(x, allow_redirects=True)
                        open(truncatedFilename +ext, 'wb').write(r.content)
                    else:
                        print("\033[93m" + x + '\x1b[0m')
                        print("\033[93mUnable to retireive content..." + '\x1b[0m')

        if((media == '4' or media == '1') and saves.is_self):
            makedir(userdirectory, saves)
            print('Title: ' + truncatedFilename + ext)
            print('URL: ' + saves.url)
            subtext = str(saves.selftext)
            open(truncatedFilename + '.md', 'w', encoding="utf-8").write(subtext)

def makedir(userdirectory, saves):
    # Crete Subreddit directory:
    sub = str(saves.subreddit)
    if userdirectory == "":
        if os.name == 'nt':
            path = os.path.expanduser('~') + "\\Documents\\RescueReddit\\" + sub
        else:
            path = os.path.expanduser('~') + "/RescueReddit/" + sub
    else:
        path = os.path.abspath(userdirectory) + "/RescueReddit/" + sub

    try:
        os.makedirs(os.path.expanduser(os.path.abspath(path)), exist_ok=False)
    except FileExistsError:
        print ("%s already exists. Skipping..." % path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created %s" % path)

    os.chdir(path)

while True:
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(0)
    except prawcore.exceptions.OAuthException:
        print("Failed to authenticate, please try different credentials.")
        sys.exit(0)
