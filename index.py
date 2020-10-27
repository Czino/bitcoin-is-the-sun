import logging
import cv2
import colorsys
import time
from colorThief import ColorThief
from PIL import Image
import numpy
import requests
import tweepy
import config as cf
from imutils import contours
from skimage import measure
import imutils
from blend_modes import grain_merge
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-s", "--since", required=True, help="id of when mentions should be listened to")
args = vars(ap.parse_args())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

bitcoinLogo = cv2.imread('assets/bitcoin.png', -1)

def getLuminosityInCircle(image, x, y, r):
    colorImage = image.copy()
    stencil = numpy.zeros(image.shape).astype(image.dtype)
    cv2.circle(stencil, (x, y), r, (255, 255, 255), -1)
    colorImage = cv2.bitwise_and(colorImage, stencil)

    colorImage = cv2.cvtColor(colorImage, cv2.COLOR_BGR2RGB)
    colorImage = Image.fromarray(colorImage)

    colorThief = ColorThief(colorImage, True)
    circlePalette = colorThief.get_palette(color_count=2, ignore_black=True, ignore_white=False)[0]

    c_h, c_l, c_s = colorsys.rgb_to_hls(
        circlePalette[0] / 255,
        circlePalette[1] / 255,
        circlePalette[2] / 255
    )
    return int(c_l * 100)

def processImage(image):
    h, w, c = image.shape

    image = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)
    grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grayImage, (7, 7), 0)
    thresh = cv2.threshold(blurred, 220, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.erode(thresh, None, iterations=4)
    thresh = cv2.dilate(thresh, None, iterations=4)

    labels = measure.label(thresh, connectivity=2, background=0)
    mask = numpy.zeros(thresh.shape, dtype="uint8")
    # loop over the unique components
    for label in numpy.unique(labels):
        # if this is the background label, ignore it
        if label == 0:
            continue
        # otherwise, construct the label mask and count the
        # number of pixels 
        labelMask = numpy.zeros(thresh.shape, dtype="uint8")
        labelMask[labels == label] = 255
        numPixels = cv2.countNonZero(labelMask)
        # if the number of pixels in the component is sufficiently
        # large, then add it to our mask of "large blobs"
        if numPixels > 300:
            mask = cv2.add(mask, labelMask)

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    if len(cnts) == 0:
        return None
    cnts = contours.sort_contours(cnts)[0]
    # loop over the contours
    for (_, c) in enumerate(cnts):
        ((x, y), r) = cv2.minEnclosingCircle(c)

        x = int(x)
        y = int(y)
        r = int(r)

        offsetX = x - r
        offsetY = y - r

        if offsetX < 0 or offsetY < 0 or offsetX + r * 2 >= w or offsetY + r * 2 >= h:
            continue

        if getLuminosityInCircle(image, x, y, r) < 69:
            continue

        smallBitcoinLogo = cv2.resize(
            bitcoinLogo,
            (r * 2, r * 2),
            interpolation = cv2.INTER_AREA
        )

        y2 = offsetY + smallBitcoinLogo.shape[0]
        x2 = offsetX + smallBitcoinLogo.shape[1]

        imageFloat = image.astype(float)
        smallBitcoinLogo = cv2.copyMakeBorder(smallBitcoinLogo,
            offsetY, image.shape[0] - y2, offsetX, image.shape[1]- x2,
            cv2.BORDER_CONSTANT
        )

        smallBitcoinLogoFloat = smallBitcoinLogo.astype(float)
        imageFloat = grain_merge(imageFloat, smallBitcoinLogoFloat, 1)
        image = numpy.uint8(imageFloat)

    return image


# originalImage = cv2.imread('input/1320092324593008640.jpg')
# newImage = processImage(originalImage)
# cv2.imwrite('processed/image.jpg', newImage)
# exit()


def check_mentions(api, keywords, since_id):
    logger.info("Retrieving mentions")
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id=since_id).items():
        new_since_id = max(tweet.id, new_since_id)
        if tweet.in_reply_to_status_id is not None:
            if any(keyword in tweet.text.lower() for keyword in keywords):
                logger.info(f"Answering to {tweet.user.name}")
                originalTweet = api.get_status(tweet.in_reply_to_status_id, include_entities=True, tweet_mode="extended")
                if hasattr(originalTweet, 'quoted_status_id_str'):
                    originalTweet = api.get_status(originalTweet.quoted_status_id_str, include_entities=True, tweet_mode="extended")

                if 'media' in originalTweet.entities:
                    for image in  originalTweet.entities['media']:
                        fileName = image['id_str']
                        mediaUrl = image['media_url_https']

                        response =  requests.get(mediaUrl).content
                        nparr = numpy.frombuffer(response, numpy.uint8)
                        image = cv2.imdecode(nparr,cv2.IMREAD_UNCHANGED)

                        if mediaUrl.lower().find('jpg') != -1:
                            newImage = processImage(image)
                            if newImage is not None:
                                cv2.imwrite('processed/' + fileName + '.jpg', newImage)
                                logger.info(f"Success, reply to " + tweet.id_str)
                                media_ids = []
                                res = api.media_upload(filename='processed/' + fileName + '.jpg',)
                                media_ids.append(res.media_id)

                                api.update_status(
                                    status='I have seen the light! @' + tweet.user.screen_name,
                                    in_reply_to_status_id=tweet.id,
                                    media_ids=media_ids
                                )

                                # cv2.imshow('Detection', image)
                                # cv2.waitKey()
                                # cv2.destroyAllWindows()
                            else:
                                logger.info(f"No highlights detected")
                                api.update_status(
                                    status='I cannot see the light in this picture. @' + tweet.user.screen_name,
                                    in_reply_to_status_id=tweet.id
                                )
                        # elif mediaUrl.lower().find('mp4') != -1:
                            # vidcap = cv2.VideoCapture(fileName)
                            # success, image = vidcap.read()
                            # count = 0
                            # path = "images/" + fileName.replace('source/', '').replace('.mp4', '')
                            # while success:
                            #     newImage = processImage(image)
                            #     if newImage is not None:
                            #         cv2.imwrite('processed/' + fileName, newImage)
                            #     success, image = vidcap.read()

    return new_since_id

since_id = int(args['since'])
auth = tweepy.OAuthHandler(cf.credentials["consumer_key"], cf.credentials["consumer_secret"])
auth.set_access_token(cf.credentials["access_token"], cf.credentials["access_token_secret"])

api = tweepy.API(auth)


while True:
    since_id = check_mentions(api, ["light"], since_id)
    logger.info("Waiting...")
    time.sleep(60)