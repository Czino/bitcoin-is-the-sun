import cv2
import os
from PIL import Image
import imageUtils

def getFPS(video):
    return video.get(cv2.CAP_PROP_FPS)

def processVideo(videoPath, fileName, path):
    video = cv2.VideoCapture(videoPath)

    success,image = video.read()

    FPS = getFPS(video)
    frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    videoLength = frames * (1 / FPS)

    videoHeight = image.shape[0]
    videoWidth = image.shape[1]
    size = (videoWidth, videoHeight)

    if videoLength > .5:
        fileType = 'mp4'

        os.system(f'ffmpeg -i {videoPath} -vn -acodec copy {path}/output-audio.aac')
        processedVideo = cv2.VideoWriter(f'{path}/{fileName}-pre.{fileType}',
            cv2.VideoWriter_fourcc(*'mp4v'),
            FPS,
            size
        )

        i = 0
        while success:
            progress = int(i / frames * 100)
            print(f'Processing Video: {str(progress)}% ({i}/{frames})', end="\r")

            image = imageUtils.processImage(image)
            processedVideo.write(image)

            i = i + 1
            success,image = video.read()

        processedVideo.release()

        if os.path.isfile(f'{path}/output-audio.aac'):
            os.system(f'ffmpeg -i {path}/{fileName}-pre.{fileType} -i {path}/output-audio.aac -vcodec libx264 -c:a aac -map 0:v:0 -map 1:a:0 {path}/{fileName}-final.{fileType} -y')
            os.remove(f'{path}/output-audio.aac')
        else:
            os.system(f'ffmpeg -i {path}/{fileName}-pre.{fileType} -vcodec libx264 -c:a aac -map 0:v:0 {path}/{fileName}-final.{fileType} -y')
        os.remove(videoPath)
        os.remove(f'{path}/{fileName}-pre.{fileType}')
    else:
        # create GIF
        fileType = 'gif'
        gifFrames = []

        i = 0
        while success:
            progress = int(i / frames * 100)
            print(f'Processing GIF: {str(progress)}% (frame {i}/{frames})', end="\r")
            image = imageUtils.processImage(image)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            gifFrames.append(Image.fromarray(image))

            i = i + 1
            success,image = video.read()

        gifFrames[0].save(f'{path}/{fileName}-final.{fileType}',
            save_all=True,
            append_images=gifFrames[1:],
            duration=FPS,
            loop=1
        )

    return f'{path}/{fileName}-final.{fileType}'
