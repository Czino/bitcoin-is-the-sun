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
from mastodon import Mastodon
import config_mastodon as cf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
dirname = os.path.dirname(__file__)

mastodon = Mastodon(
    client_id = cf.credentials['consumer_key'],
    client_secret = cf.credentials['consumer_secret'],
    access_token = cf.credentials['access_token'],
    api_base_url = cf.credentials['base_url']
)
mastodon.log_in(
    username = cf.credentials['login'],
    password = cf.credentials['password'],
    scopes = ['read', 'write']
)

def processToot(toot, username, replyTo, bold):
    hasMedia = False

    if hasattr(toot, 'media_attachments'):
        for media in toot.media_attachments:
            hasMedia = True
            fileName = str(media['id'])
            mediaType = media['type']
            mediaUrl = media['url']

            if mediaType == 'image':
                hasMedia = True

                response =  requests.get(mediaUrl).content
                nparr = numpy.frombuffer(response, numpy.uint8)
                image = cv2.imdecode(nparr,cv2.IMREAD_UNCHANGED)

                if mediaUrl.lower().find('jpg') != -1 or mediaUrl.lower().find('png') != -1:
                    newImage, hasSeenTheLightInImage = imageUtils.processImage(image, bold)
                    if hasSeenTheLightInImage:
                        cv2.imwrite(os.path.join(dirname, f'processed/' + fileName + '.jpg'), newImage)
                        logger.info(f'Success, reply to {toot.id}')
                        media_ids = []
                        res = mastodon.media_post(media_file=os.path.join(dirname, f'processed/{fileName}.jpg'),)
                        media_ids.append(res.id)

                        try:
                            mastodon.status_post(
                                status='I have seen the light! @' + username,
                                in_reply_to_id=replyTo,
                                media_ids=media_ids
                            )
                        except:
                            e = sys.exc_info()[0]
                            logger.error(e)
                    else:
                        logger.info(f'No highlights detected {toot.id}')
                        try:
                            mastodon.status_post(
                                status='I cannot see the light in this picture. @' + username,
                                in_reply_to_id=replyTo
                            )
                        except:
                            e = sys.exc_info()[0]
                            logger.error(e)
                else:
                    logger.info(f'Not supported format for {mediaUrl}')

            if mediaType == 'video' or mediaType == 'gifv':
                video = requests.get(mediaUrl, allow_redirects=True)
                open(os.path.join(dirname, f'processed/{fileName}.mp4'), 'wb').write(video.content)

                pathToVideo = videoUtils.processVideo(
                    os.path.join(dirname, f'processed/{fileName}.mp4'),
                    fileName,
                    os.path.join(dirname, f'processed'),
                    bold
                )

                media_ids = []
                res = mastodon.media_post(media_file=pathToVideo)
                media_ids.append(res.id)

                try:
                    mastodon.status_post(
                        status='I have seen the light! @' + username,
                        in_reply_to_id=replyTo,
                        media_ids=media_ids
                    )
                except:
                    e = sys.exc_info()[1]
                    print(e)
                    logger.error(e)
                return hasMedia

    return hasMedia

def checkMentions(mastodon, keywords, sinceId):
    logger.info(f'Retrieving mentions since {sinceId}')
    newSinceId = int(sinceId)
    try:
        notifications = mastodon.notifications(since_id=sinceId, mentions_only=True)
    except:
        e = sys.exc_info()[0]
        logger.error(e)
        return newSinceId

    for notification in notifications:
        if notification['type'] == 'mention':

            newSinceId = max(notification.id, newSinceId)
            username = notification.status.account.username
            replyTo = notification.status.id

            if any(keyword in notification.status.content.lower() for keyword in keywords):
                logger.info(f'Answering to {username} {replyTo}')
                bold = '/bold' in notification.status.content.lower()

                if bold:
                    print('Bold image requested')

                # check if actual toot has media
                try:
                    toot = mastodon.status(replyTo)
                    replyToot = None
                    hasMedia = processToot(toot, username, replyTo, bold)

                    # check if toot is in reply to
                    if hasMedia is False and hasattr(toot, 'in_reply_to_id'):
                        print('original toot has no media, proceed to check if replied toot exists')
                        replyToot = mastodon.status(toot.in_reply_to_id)

                    if replyToot is not None:
                        hasMedia = processToot(replyToot, username, replyTo, bold)
                except:
                    e = sys.exc_info()[0]
                    logger.error(e)

    return newSinceId

if not os.path.isfile(os.path.join(dirname, 'sinceId_mastodon.txt')):
    with open(os.path.join(dirname, 'sinceId_mastodon.txt'), 'w') as saveFile:
        saveFile.write('1')

while True:
    with open(os.path.join(dirname, 'sinceId_mastodon.txt'), 'r') as readFile:
        sinceId = readFile.read()
        sinceId = int(sinceId)

    sinceId = checkMentions(mastodon, ['light', 'sparkles'], sinceId)
    with open(os.path.join(dirname, 'sinceId_mastodon.txt'), 'w') as saveFile:
        saveFile.write(str(sinceId))
    logger.info('Waiting...')
    time.sleep(120)