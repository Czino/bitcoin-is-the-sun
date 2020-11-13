# Requirements
Python 3

`pip3 install -r requirements.txt`

## To support video uploads install this fork
`pip3 install --upgrade git+https://github.com/fitnr/tweepy@video-upload-3#egg=tweepy`

Copy `config.dist.py` and rename to `config.py`. Replace placeholders with your API credentials.

# Usage

`python3 index.py`

# Test

run `python3 test.py` to process media in the `test` folder

# TODOs
- Reduce video compression
- Find out why some videos are 'invalid' and fix it
- Process all images in a tweet instead of only the first one
- Notify when bot gets blocked by Twitter API (supposedly because of spam)