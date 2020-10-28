import os
import cv2
import imageUtils

files = os.listdir('test')
files = set(files).difference(set(['.gitkeep', '.DS_Store', 'processed']))

for fileName in files:
    print('Processing', fileName)
    originalImage = cv2.imread(f'test/{fileName}')
    newImage = imageUtils.processImage(originalImage)
    if newImage is not None:
        cv2.imwrite(f'test/processed/{fileName}', newImage)
    else:
        print(f'No highlights detected for {fileName}')