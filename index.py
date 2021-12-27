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

def processTweet(tweet, username, replyTo, bold):
    logger.info('Process tweet')
    hasMedia = False

    if hasattr(tweet, 'extended_entities') and 'media' in tweet.extended_entities:
        logger.info('Tweet has video')
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

                pathToVideo, hasSeenTheLightInVideo = videoUtils.processVideo(
                    os.path.join(dirname, f'processed/{fileName}.mp4'),
                    fileName,
                    os.path.join(dirname, f'processed'),
                    bold
                )

                media_ids = []
                if hasSeenTheLightInVideo:
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
                else:
                    try:
                        api.update_status(
                            status='I cannot see the light in this video. @' + username,
                            in_reply_to_status_id=replyTo
                        )
                    except:
                        e = sys.exc_info()[0]
                        logger.error(e)
    logger.info(tweet.entities)
    if hasattr(tweet, 'entities') and 'media' in tweet.entities:
        hasMedia = True
        seenTheLight = False
        media_ids = []
        logger.info('has images')

        for image in tweet.entities['media']:
            fileName = image['id_str']
            mediaUrl = image['media_url_https']

            response =  requests.get(mediaUrl).content
            nparr = numpy.frombuffer(response, numpy.uint8)
            image = cv2.imdecode(nparr,cv2.IMREAD_UNCHANGED)

            if mediaUrl.lower().find('jpg') != -1 or mediaUrl.lower().find('png') != -1:
                newImage, hasSeenTheLightInImage = imageUtils.processImage(image, bold)
                if hasSeenTheLightInImage:
                    cv2.imwrite(os.path.join(dirname, f'processed/' + fileName + '.jpg'), newImage)
                    logger.info(f'Success, reply to {tweet.id_str}')
                    res = api.media_upload(filename=os.path.join(dirname, f'processed/{fileName}.jpg'),)
                    media_ids.append(res.media_id)
                    seenTheLight = True
                else:
                    logger.info(f'No highlights detected {tweet.id_str}')

            else:
                logger.info(f'Not supported format for {mediaUrl}')

        if seenTheLight:
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
            try:
                api.update_status(
                    status='I cannot see the light in this picture. @' + username,
                    in_reply_to_status_id=replyTo
                )
            except:
                e = sys.exc_info()[0]
                logger.error(e)
    return hasMedia

def checkMentions(api, keywords, sinceId):
    logger.info(f'Retrieving mentions since {sinceId}')
    newSinceId = sinceId

    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=sinceId).items():
        newSinceId = max(tweet.id, newSinceId)
        username = tweet.user.screen_name
        replyTo = tweet.id

        if any(keyword in tweet.text.lower() for keyword in keywords):
            try:
                logger.info(f'Answering to {tweet.user.name} {tweet.id_str}')
                bold = '/bold' in tweet.text.lower()

                if bold:
                    logger.info('Bold image requested')

                # check if actual tweet has media
                tweet = api.get_status(tweet.id, include_entities=True, tweet_mode='extended')
                replyTweet = None
                quotedTweet = None
                hasMedia = processTweet(tweet, username, replyTo, bold)

                # check if tweet is in reply to
                if hasMedia is False and hasattr(tweet, 'in_reply_to_status_id'):
                    logger.info('original tweet has no media, proceed to check if replied tweet exists', tweet.in_reply_to_status_id)
                    replyTweet = api.get_status(tweet.in_reply_to_status_id, include_entities=True, tweet_mode='extended')

                if replyTweet is not None:
                    logger.info('reply tweet exists')
                    hasMedia = processTweet(replyTweet, username, replyTo, bold)

                # check if tweet has quote
                if hasMedia is False and hasattr(tweet, 'quoted_status_id'):
                    logger.info('reply tweet has no media, proceed to check if quoted tweet exists', tweet.quoted_status_id)
                    quotedTweet = api.get_status(tweet.quoted_status_id, include_entities=True, tweet_mode='extended')

                if quotedTweet is not None:
                    logger.info('quotet tweet exists')
                    processTweet(quotedTweet, username, replyTo, bold)
            except:
                e = sys.exc_info()[0]
                logger.error(e)
                with open(os.path.join(dirname, 'errors.txt'), 'a') as saveFile:
                    saveFile.write(f'Failed answering to {tweet.user.name} {tweet.id_str} \n')
                    saveFile.write(e)

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

    sinceId = checkMentions(api, ['light', 'sparkles', 'luz', 'licht', 'illumin', 'show me the', 'do the thing'], sinceId)
    with open(os.path.join(dirname, 'sinceId.txt'), 'w') as saveFile:
        saveFile.write(str(sinceId))
    logger.info('Waiting...')
    time.sleep(60)
