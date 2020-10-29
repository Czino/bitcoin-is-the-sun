import os
import cv2
import imageUtils
import videoUtils
files = os.listdir('test')
files = set(files).difference(set(['.gitkeep', '.DS_Store', 'processed']))

for fileName in files:
    # print('Processing', fileName)
    if fileName.lower().find('jpg') != -1 or fileName.lower().find('png') != -1:
        originalImage = cv2.imread(f'test/{fileName}')
        newImage = imageUtils.processImage(originalImage)
        if newImage is not None:
            cv2.imwrite(f'test/processed/{fileName}', newImage)
        else:
            print(f'No highlights detected for {fileName}')
    elif fileName.lower().find('mp4') != -1:
        video = cv2.VideoCapture(f'test/{fileName}')

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

        video = cv2.VideoWriter(f'test/processed/{fileName}.mp4',
            cv2.VideoWriter_fourcc(*'mp4v'),
            FPS,
            size
        )

        for frame in newVideoFrames:
            video.write(frame)

        video.release()
        os.system(f'ffmpeg -i test/processed/{fileName}.mp4 -vcodec libx264 test/processed/{fileName}-final.mp4')
        os.remove(f'test/processed/{fileName}.mp4')
