# rescue-reddit
Save your Reddit saves! This python script will authenticate through Praw to your Reddit account and pull any desired saved content.

Differentiate between photos, text submission, GIFs/videos, or download them all! This script is intended for personal use, and requires an active app authentication in Reddit. If you are unsure of how to accomplish this, please check the [API docs](https://github.com/reddit-archive/reddit/wiki/OAuth2).

**Required python libraries:**
- url_normalize
- bs4
- praw

Usage ~ `python3 run.py -d <destination directory>`

If no destination directory is defined, saves will be downloaded the user's home directory: `~/RescueReddit/`

Please keep in mind that as per the [Reddit API docs](https://github.com/reddit-archive/reddit/wiki/API#rules), OAuth2 calls are limited to 60 requests every minute, which means that if you are downloading tons of your Reddit saves it will take some time. 

**TO-DO:**
- Proper logging
- Add more media types
- Increase efficiency
