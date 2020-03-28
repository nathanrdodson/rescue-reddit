import configparser
from shutil import copyfile
import os
import datetime
import sys
import re
import getpass
import requests
import praw
import prawcore
from praw.models import Submission
from url_normalize import url_normalize
from videoparser import extract_mp4
import pdfkit
import logging

logging.basicConfig(filename="rescue.log",level=logging.DEBUG)
CONFIG = configparser.ConfigParser()
today = datetime.datetime.today()
__location__ = os.path.realpath(
os.path.join(os.getcwd(), os.path.dirname(__file__)))

def is_downloadable(url):
    try:
        h = requests.head(url, allow_redirects=True)
        header = h.headers
        content_type = header.get('content-type')
        if 'text' in content_type.lower():
            return False
        if 'html' in content_type.lower():
            return False
        return True
    except:
        return False

def main(argv):

    try:
        open(os.path.join(__location__, 'config.ini'));
    except FileNotFoundError:
        # config not found
        print("config.ini not found. Starting setup...")

        # copy sample configuration template from root
        copyfile("sample_config.ini", "config.ini")

        # begin user input for new configuration
        CONFIG.read('config.ini')
        print("Reddit username: ")
        CONFIG['rescuereddit']['username'] = input()
        CONFIG['rescuereddit']['password'] = getpass.getpass(prompt='Reddit Password: \n', stream=None)
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
    user_agent = 'script:rescue-reddit:v0.1.0 (by /u/danishkaiju)'

    reddit = praw.Reddit(client_id=client_id, password=password, username=username, client_secret=client_secret, user_agent=user_agent)

    print("\nSuccessfully connected to user: \033[93m" + str(reddit.user.me()) + '\x1b[0m')

    while True:
        print("\n==========")
        print("What would you like to do?:\n[1] /r/<subreddit> Scraper\n[2] Download Saves")
        print("==========")

        userchoice = input()

        if userchoice == '1':
            print("*No spaces, not case-sensitive*")
            print("For limit ~ Please consider max of 1 submission/second ")
            print("What subreddit to scrape?: ")
            sub = input()
            print("Sorting method?: \nTop\n---> [0] All time\n---> [1] 24 Hr\n---> [2] Week\n---> [3] Month\n---> [4] Year\n[5] Hot\n[6] Rising\n[7] New\n[8] Controverisal")
            sort = int(input())
            print("How many submissions to fetch?: ")
            limit = int(input())
            sub_scraper(reddit, sub, sort, limit)
        elif userchoice == '2':
            print("==========")
            print("What saves would you like to pull from Reddit?:\n", "[1] All media types\n", "[2] Photos\n", "[3] GIFs\n", "[4] Text Submissions")
            print("==========")
            userchoice = input()

            for saves in reddit.user.me().saved(limit=None):
                if isinstance(saves, Submission):
                    download(userchoice, saves, str(saves.subreddit))
        else:
            break

def sub_scraper(instance, sub, sort, limit):

    sort_list_map = {
        "hot": instance.subreddit(sub).hot(limit=limit),
        "new": instance.subreddit(sub).new(limit=limit),
        "rising": instance.subreddit(sub).rising(limit=limit),
        "controversial": instance.subreddit(sub).controversial(limit=limit),
        "top-all": instance.subreddit(sub).top('all', limit=limit),
        "top-day": instance.subreddit(sub).top('day', limit=limit),
        "top-week": instance.subreddit(sub).top('week', limit=limit),
        "top-month": instance.subreddit(sub).top('month', limit=limit),
        "top-year": instance.subreddit(sub).top('year', limit=limit)
    }
    sort_list = ["top-all", "top-day", "top-week", "top-month", "top-year", "hot", "rising", "new", "controversial"]
    for submission in sort_list_map[sort_list[sort]]:
        download('1', submission, instance.subreddit(sub).display_name)

def download(media, format, sub_name):

    # Convert Reddit title to string
    filename = str(format.title)

    # Make filename alphanumeric
    filename = re.compile(r'[\W_]+', re.UNICODE).sub('', filename)

    # Get file extension from URL
    name, ext = os.path.splitext(format.url)

    # Check for nameless files after truncation
    if filename == '':
        truncated_filename = ('File_%s')
    else:
        truncated_filename = (filename[:25] + '..') if len(filename) > 25 else filename

    # Remove values including and after question mark in URL
    ext = re.compile(r'\?(.*)', re.UNICODE).sub('', ext)

    if((media == '2' or media == '1') and ('.png' in format.url or '.jpg' in format.url)):
        # Verify content type
        if is_downloadable(format.url):
            makedir(sub_name)
            print("*", end='', flush=True)
            r = requests.get(format.url, allow_redirects=True)
            open(truncated_filename +ext, 'wb').write(r.content)
        else:
            print("X", end='', flush=True)
    if((media == '3' or media == '1') and ('.gif' in format.url)):
        # Verify content type
        if ext == '.gifv':
            ext = '.mp4'
        if is_downloadable(format.url):
            makedir(sub_name)
            print("*", end='', flush=True)
            r = requests.get(format.url, allow_redirects=True)
            open(truncated_filename +ext, 'wb').write(r.content)
        else:
            for x in extract_mp4(format.url):
            # Verify content type
                x = url_normalize(str(x))
                if is_downloadable(x):
                    makedir(sub_name)
                    print("*", end='', flush=True)
                    r = requests.get(x, allow_redirects=True)
                    open(truncated_filename +ext, 'wb').write(r.content)
                else:
                    print("X", end='', flush=True)

    if((media == '4' or media == '1') and format.is_self):
        try:
            makedir(sub_name)
            print("*", end='', flush=True)
            subtext = str(format.selftext)
            #Check for no body. If no body, body is title of post
            if subtext == "":
                subtext = str(format.title)
            open(truncated_filename + '.md', 'w', encoding="utf-8").write(subtext)
        except:
            print("X", end='', flush=True)

    if((media == '5' or media == '1')):
        try:
            makedir(sub_name)
            print("*", end='', flush=True)
            pdfkit.from_url(str(format.url), truncated_filename + ".pdf")
        except:
            print("X", end='', flush=True)

def makedir(sub_name):
    CONFIG.read('config.ini')
    userdirectory = CONFIG['rescuereddit']['user_dir']
    if str(CONFIG['rescuereddit']['subdirectory']) == "False":
        sub_name = ""

    # Crete Subreddit directory:
    if userdirectory == "default":
        if os.name == 'nt':
            path = os.path.expanduser('~') + "\\Documents\\RescueReddit\\" + "scrape_" + today.isoformat() + '\\' + sub_name
        else:
            path = os.path.expanduser('~') + "/RescueReddit/" + "scrape_" + today.isoformat() + '/' + sub_name
    else:
        path = os.path.abspath(userdirectory) + "/RescueReddit/" + "scrape_" + today.isoformat() + '/' + sub_name

    try:
        os.makedirs(os.path.expanduser(os.path.abspath(path)), exist_ok=False)
    except FileExistsError:
        pass
    except OSError:
        return 0
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
