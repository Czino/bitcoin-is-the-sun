import cv2
import colorsys
from colorThief import ColorThief
from PIL import Image
import numpy
import numpy as np
import requests
import tweepy
import config as cf
from imutils import contours
from skimage import measure
import imutils
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-t", "--tweet", required=True, help="id of tweet")
args = vars(ap.parse_args())

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

    grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grayImage, (3, 3), 0)
    thresh = cv2.threshold(blurred, 220, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.erode(thresh, None, iterations=4)
    thresh = cv2.dilate(thresh, None, iterations=4)

    labels = measure.label(thresh, connectivity=2, background=0)
    mask = np.zeros(thresh.shape, dtype="uint8")
    # loop over the unique components
    for label in np.unique(labels):
        # if this is the background label, ignore it
        if label == 0:
            continue
        # otherwise, construct the label mask and count the
        # number of pixels 
        labelMask = np.zeros(thresh.shape, dtype="uint8")
        labelMask[labels == label] = 255
        numPixels = cv2.countNonZero(labelMask)
        # if the number of pixels in the component is sufficiently
        # large, then add it to our mask of "large blobs"
        if numPixels > 300:
            mask = cv2.add(mask, labelMask)

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = contours.sort_contours(cnts)[0]
    # loop over the contours
    for (i, c) in enumerate(cnts):
        ((x, y), r) = cv2.minEnclosingCircle(c)

        x = int(x)
        y = int(y)
        r = int(r)

        offsetX = x - r
        offsetY = y - r

        if offsetX < 0 or offsetY < 0 or offsetX + r * 2 >= w or offsetY + r * 2 >= h:
            continue

        # cv2.circle(image, (x, y), r, (0, 250, 0), 1)
        if getLuminosityInCircle(image, x, y, r) < 70:
            continue

        smallBitcoinLogo = cv2.resize(
            bitcoinLogo,
            (r * 2, r * 2),
            interpolation = cv2.INTER_CUBIC
        )

        y1, y2 = offsetY, offsetY + smallBitcoinLogo.shape[0]
        x1, x2 = offsetX, offsetX + smallBitcoinLogo.shape[1]

        alphaBTC = smallBitcoinLogo[:, :, 3] / 255.0
        alphaOrig = 1.0 - alphaBTC

        for c in range(0, 3):
            image[y1:y2, x1:x2, c] = (alphaBTC * smallBitcoinLogo[:, :, c] + alphaOrig * image[y1:y2, x1:x2, c])


    return image


# originalImage = cv2.imread('input/1320092324593008640.jpg')
# newImage = processImage(originalImage)
# cv2.imwrite('processed/image.jpg', newImage)
# exit()


auth = tweepy.OAuthHandler(cf.credentials["consumer_key"], cf.credentials["consumer_secret"])
auth.set_access_token(cf.credentials["access_token"], cf.credentials["access_token_secret"])

api = tweepy.API(auth)

tweet = api.get_status(args["tweet"], include_entities=True, tweet_mode="extended")

if hasattr(tweet, 'quoted_status_id_str'):
    tweet = api.get_status(tweet.quoted_status_id_str, include_entities=True, tweet_mode="extended")

if 'media' in tweet.entities:
    for image in  tweet.entities['media']:
        fileName = image['id_str']
        mediaUrl = image['media_url_https']

        response =  requests.get(mediaUrl).content
        nparr = np.frombuffer(response, np.uint8)
        image = cv2.imdecode(nparr,cv2.IMREAD_UNCHANGED)

        if mediaUrl.lower().find('jpg') != -1:
            newImage = processImage(image)
            if newImage is not None:
                cv2.imwrite('processed/' + fileName + '.jpg', newImage)

                # cv2.imshow('Detection', image)
                # cv2.waitKey()
                # cv2.destroyAllWindows()
        elif mediaUrl.lower().find('mp4') != -1:
            vidcap = cv2.VideoCapture(fileName)
            success, image = vidcap.read()
            count = 0
            path = "images/" + fileName.replace('source/', '').replace('.mp4', '')
            while success:
                newImage = processImage(image)
                if newImage is not None:
                    cv2.imwrite('processed/' + fileName, newImage)
                success, image = vidcap.read()