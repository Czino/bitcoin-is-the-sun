# Requirements
Python 3
`pip3 install -r requirements.txt`

ffmpeg
`sudo apt install ffmpeg`

# Twitter API connection
Copy `config.dist.py` and rename to `config.py`. Replace placeholders with your API credentials.

## To support video uploads install this fork
`pip3 install --upgrade git+https://github.com/tweepy/tweepy@video-upload#egg=tweepy`

# Usage

`python3 index.py`

# Test

run `python3 test.py` to process media in the `test` folder

# TODOs
- Reduce video compression
- Find out why some videos are 'invalid' and fix it
- Process all images in a tweet instead of only the first one
- Notify when bot gets blocked by Twitter API (supposedly because of spam)