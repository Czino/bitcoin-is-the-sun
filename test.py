from PIL import Image
import os
import cv2
import imageUtils
import videoUtils
files = os.listdir('test')
files = set(files).difference(set(['.gitkeep', '.DS_Store', 'test/processed']))

for fileName in files:
    print('Processing', fileName)
    if fileName.lower().find('jpg') != -1 or fileName.lower().find('png') != -1:
        originalImage = cv2.imread(f'test/{fileName}')
        newImage = imageUtils.processImage(originalImage)
        if newImage is not None:
            cv2.imwrite(f'test/processed/{fileName}', newImage)
        else:
            print(f'No highlights detected for {fileName}')
    elif fileName.lower().find('gif') != -1 or fileName.lower().find('mp4') != -1:
        videoUtils.processVideo(f'test/{fileName}', fileName, 'test/processed')
