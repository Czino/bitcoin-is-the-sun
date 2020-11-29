#!/usr/bin/env python3

import logging
import sys
import cv2
import time
import os.path

from PIL import Image
import imageUtils
import videoUtils

import numpy
import requests
import tweepy
import config as cf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
dirname = os.path.dirname(__file__)

def processTweet(tweet, username, replyTo):
    hasMedia = False

    if hasattr(tweet, 'extended_entities') and 'media' in tweet.extended_entities:
        for media in tweet.extended_entities['media']:
            hasMedia = True
            fileName = media['id_str']

            if 'video_info' in media:
                for media in media['video_info']['variants']:
                    if media['content_type'] == 'video/mp4':
                        videoUrl = media['url']
                        break

                video = requests.get(videoUrl, allow_redirects=True)
                open(os.path.join(dirname, f'processed/{fileName}.mp4'), 'wb').write(video.content)

                pathToVideo = videoUtils.processVideo(
                    os.path.join(dirname, f'processed/{fileName}.mp4'),
                    fileName,
                    os.path.join(dirname, f'processed')
                )

                media_ids = []
                res = api.media_upload(filename=pathToVideo)
                media_ids.append(res.media_id)

                try:
                    api.update_status(
                        status='I have seen the light! @' + username,
                        in_reply_to_status_id=replyTo,
                        media_ids=media_ids
                    )
                except:
                    e = sys.exc_info()[1]
                    print(e)
                    logger.error(e)
                return hasMedia

    if hasattr(tweet, 'entities') and 'media' in tweet.entities:
        for image in tweet.entities['media']:
            hasMedia = True
            print('has images')

            fileName = image['id_str']
            mediaUrl = image['media_url_https']

            response =  requests.get(mediaUrl).content
            nparr = numpy.frombuffer(response, numpy.uint8)
            image = cv2.imdecode(nparr,cv2.IMREAD_UNCHANGED)

            if mediaUrl.lower().find('jpg') != -1 or mediaUrl.lower().find('png') != -1:
                newImage = imageUtils.processImage(image)
                if newImage is not None:
                    cv2.imwrite(os.path.join(dirname, f'processed/' + fileName + '.jpg'), newImage)
                    logger.info(f'Success, reply to {tweet.id_str}')
                    media_ids = []
                    res = api.media_upload(filename=os.path.join(dirname, f'processed/{fileName}.jpg'),)
                    media_ids.append(res.media_id)

                    try:
                        api.update_status(
                            status='I have seen the light! @' + username,
                            in_reply_to_status_id=replyTo,
                            media_ids=media_ids
                        )
                    except:
                        e = sys.exc_info()[0]
                        logger.error(e)
                else:
                    logger.info(f'No highlights detected {tweet.id_str}')
                    try:
                        api.update_status(
                            status='I cannot see the light in this picture. @' + username,
                            in_reply_to_status_id=replyTo
                        )
                    except:
                        e = sys.exc_info()[0]
                        logger.error(e)
            else:
                logger.info(f'Not supported format for {mediaUrl}')

    return hasMedia

def checkMentions(api, keywords, sinceId):
    logger.info(f'Retrieving mentions since {sinceId}')
    newSinceId = sinceId

    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=sinceId).items():
        newSinceId = max(tweet.id, newSinceId)
        username = tweet.user.screen_name
        replyTo = tweet.id

        if any(keyword in tweet.text.lower() for keyword in keywords):
            logger.info(f'Answering to {tweet.user.name} {tweet.id_str}')

            # check if actual tweet has media
            tweet = api.get_status(tweet.id, include_entities=True, tweet_mode='extended')
            replyTweet = None
            quotedTweet = None
            hasMedia = processTweet(tweet, username, replyTo)

            # check if tweet is in reply to
            if hasMedia is False and hasattr(tweet, 'in_reply_to_status_id'):
                print('original tweet has no media, proceed to check if replied tweet exists')
                replyTweet = api.get_status(tweet.in_reply_to_status_id, include_entities=True, tweet_mode='extended')

            if replyTweet is not None:
                hasMedia = processTweet(replyTweet, username, replyTo)

            # check if tweet has quote
            if hasMedia is False and hasattr(tweet, 'quoted_status_id'):
                print('original tweet has no media, proceed to check if quoted tweet exists')
                quotedTweet = api.get_status(tweet.quoted_status_id, include_entities=True, tweet_mode='extended')

            if quotedTweet is not None:
                processTweet(quotedTweet, username, replyTo)

    return newSinceId

auth = tweepy.OAuthHandler(cf.credentials['consumer_key'], cf.credentials['consumer_secret'])
auth.set_access_token(cf.credentials['access_token'], cf.credentials['access_token_secret'])

api = tweepy.API(auth)

if not os.path.isfile(os.path.join(dirname, 'sinceId.txt')):
    with open(os.path.join(dirname, 'sinceId.txt'), 'w') as saveFile:
        saveFile.write('1')

while True:
    with open(os.path.join(dirname, 'sinceId.txt'), 'r') as readFile:
        sinceId = readFile.read()
        sinceId = int(sinceId)

    sinceId = checkMentions(api, ['light', 'sparkles'], sinceId)
    with open(os.path.join(dirname, 'sinceId.txt'), 'w') as saveFile:
        saveFile.write(str(sinceId))
    logger.info('Waiting...')
    time.sleep(60)