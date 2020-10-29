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

bitcoinLogo = cv2.imread('assets/bitcoin.png', -1)

# originalImage = cv2.imread('input/1320092324593008640.jpg')
# newImage = imageUtils.processImage(originalImage)
# cv2.imwrite('processed/image.jpg', newImage)
# exit()


def checkMentions(api, keywords, sinceId):
    logger.info(f'Retrieving mentions since {sinceId}')
    newSinceId = sinceId
    
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=sinceId).items():
        newSinceId = max(tweet.id, newSinceId)

        if tweet.in_reply_to_status_id is not None:
            if any(keyword in tweet.text.lower() for keyword in keywords):
                logger.info(f'Answering to {tweet.user.name} {tweet.id_str}')
                originalTweet = api.get_status(tweet.in_reply_to_status_id, include_entities=True, tweet_mode='extended')
                if hasattr(originalTweet, 'quoted_status_id_str'):
                    originalTweet = api.get_status(originalTweet.quoted_status_id_str, include_entities=True, tweet_mode='extended')

                if 'media' in originalTweet.extended_entities:
                    for media in  originalTweet.extended_entities['media']:
                        fileName = media['id_str']

                        if 'video_info' in media:
                            videoUrl = media['video_info']['variants'][0]['url']

                            video = cv2.VideoCapture(videoUrl)
                            frames = videoUtils.extractFrames(video)
                            FPS = videoUtils.getFPS(video)
                            newVideoFrames = []
                            for frame in frames:
                                newImage = imageUtils.processImage(frame)
                                if newImage is not None:
                                    newVideoFrames.append(newImage)
                                else:
                                    newVideoFrames.append(frame)

                            videoHeight = newVideoFrames[0].shape[0]
                            videoWidth = newVideoFrames[0].shape[1]
                            size = (videoWidth, videoHeight)

                            video = cv2.VideoWriter(f'processed/{fileName}.mp4',
                                cv2.VideoWriter_fourcc(*'mp4v'),
                                FPS,
                                size
                            )

                            for frame in newVideoFrames:
                                video.write(frame)

                            video.release()
                            os.system(f'ffmpeg -i processed/{fileName}.mp4 -vcodec libx264 processed/{fileName}-final.mp4')
                            os.remove(f'processed/{fileName}.mp4')
                            media_ids = []
                            res = api.media_upload(filename=f'processed/{fileName}-final.mp4')
                            media_ids.append(res.media_id)

                            try:
                                api.update_status(
                                    status='I have seen the light! @' + tweet.user.screen_name,
                                    in_reply_to_status_id=tweet.id,
                                    media_ids=media_ids
                                )
                            except:
                                e = sys.exc_info()[1]
                                print(e)
                                logger.error(e)
                            return newSinceId

                if 'media' in originalTweet.entities:
                    for image in  originalTweet.entities['media']:
                        fileName = image['id_str']
                        mediaUrl = image['media_url_https']

                        response =  requests.get(mediaUrl).content
                        nparr = numpy.frombuffer(response, numpy.uint8)
                        image = cv2.imdecode(nparr,cv2.IMREAD_UNCHANGED)

                        if mediaUrl.lower().find('jpg') != -1 or mediaUrl.lower().find('png') != -1:
                            newImage = imageUtils.processImage(image)
                            if newImage is not None:
                                cv2.imwrite('processed/' + fileName + '.jpg', newImage)
                                logger.info(f'Success, reply to {tweet.id_str}')
                                media_ids = []
                                res = api.media_upload(filename='processed/' + fileName + '.jpg',)
                                media_ids.append(res.media_id)

                                # try:
                                    # api.update_status(
                                    #     status='I have seen the light! @' + tweet.user.screen_name,
                                    #     in_reply_to_status_id=tweet.id,
                                    #     media_ids=media_ids
                                    # )
                                # except:
                                #     e = sys.exc_info()[0]
                                #     logger.error(e)

                                # cv2.imshow('Detection', image)
                                # cv2.waitKey()
                                # cv2.destroyAllWindows()
                            else:
                                logger.info(f'No highlights detected {tweet.id_str}')
                                # try:
                                    # api.update_status(
                                    #     status='I cannot see the light in this picture. @' + tweet.user.screen_name,
                                    #     in_reply_to_status_id=tweet.id
                                    # )
                                # except:
                                #     e = sys.exc_info()[0]
                                #     logger.error(e)
                        else:
                            logger.info(f'Not supported format for {mediaUrl}')
    return newSinceId

# sinceId = int(args['since'])
auth = tweepy.OAuthHandler(cf.credentials['consumer_key'], cf.credentials['consumer_secret'])
auth.set_access_token(cf.credentials['access_token'], cf.credentials['access_token_secret'])

api = tweepy.API(auth)

if not os.path.isfile('sinceId.txt'):
    with open('sinceId.txt', 'w') as saveFile:
        saveFile.write('1')

while True:
    with open('sinceId.txt', 'r') as readFile:
        sinceId = readFile.read()
        sinceId = int(sinceId)

    sinceId = checkMentions(api, ['light'], sinceId)
    with open('sinceId.txt', 'w') as saveFile:
        saveFile.write(str(sinceId))
    logger.info('Waiting...')
    time.sleep(60)