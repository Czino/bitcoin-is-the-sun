# Requirements
Python 3

`pip3 install -r requirements.txt`

Copy `config.dist.py` and rename to `config.py`. Replace placeholders with your API credentials.

# Usage

`python3 index.py -t TWEET_ID`

# TODOs
- Handle case of 'Duration too short, minimum:500 (ms)'
- Reduce video compression
- Find out why some videos are 'invalid' and fix it
- Look first at original tweet for video/image
- Process all images in a tweet instead of only the first one
- Notify when bot gets blocked by Twitter API (supposedly because of spam)
