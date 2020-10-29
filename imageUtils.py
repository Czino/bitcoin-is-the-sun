import cv2
from PIL import Image
import numpy
from imutils import contours
from skimage import measure
import imutils
from blend_modes import hard_light

bitcoinLogo = cv2.imread('assets/bitcoin.png', -1)

def processImage(image):
    h, w, c = image.shape

    hasBeenEdited = False
    image = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)
    pixels = image.shape[0] * image.shape[1]

    lower = 255
    while lower > 200 and not hasBeenEdited:
        grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(grayImage, (21, 21), 0)
        thresh = cv2.threshold(blurred, lower, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.erode(thresh, None, iterations=4)
        thresh = cv2.dilate(thresh, None, iterations=4)

        labels = measure.label(thresh, connectivity=2, background=0)
        mask = numpy.zeros(thresh.shape, dtype='uint8')
        # loop over the unique components
        for label in numpy.unique(labels):
            # if this is the background label, ignore it
            if label == 0:
                continue
            # otherwise, construct the label mask and count the
            # number of pixels 
            labelMask = numpy.zeros(thresh.shape, dtype='uint8')
            labelMask[labels == label] = 255
            numPixels = cv2.countNonZero(labelMask)
            # if the number of pixels in the component is sufficiently
            # large, then add it to our mask of 'large blobs'
            if numPixels > pixels * 0.00005 and numPixels < pixels * 0.33:
                mask = cv2.add(mask, labelMask)

        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        lower = lower - 10
        if len(cnts) == 0:
            continue

        cnts = cnts[0:21]

        if len(cnts) == 0:
            continue

        # loop over the contours
        for (_, c) in enumerate(cnts):
            ((x, y), r) = cv2.minEnclosingCircle(c)
            x = int(x)
            y = int(y)
            r = int(r)

            offsetX = x - r
            offsetY = y - r

            if r < 10 or offsetX < 0 or offsetY < 0 or offsetX + r * 2 >= w or offsetY + r * 2 >= h:
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
            imageFloat = hard_light(imageFloat, smallBitcoinLogoFloat, 1)
            image = numpy.uint8(imageFloat)

            hasBeenEdited = True

    if hasBeenEdited:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

        return image
    else:
        return None
