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
        video = cv2.VideoCapture(f'test/{fileName}')

        frames = videoUtils.extractFrames(video)
        FPS = videoUtils.getFPS(video)
        videoLength = len(frames) * (1 / FPS)
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

        print(videoLength)
        if videoLength > .5:
            fileType = 'mp4'

            # get audio
            os.system(f'ffmpeg -i test/{fileName} -vn -acodec copy test/output-audio.aac')

            video = cv2.VideoWriter(f'test/processed/{fileName}.{fileType}',
                cv2.VideoWriter_fourcc(*'mp4v'),
                FPS,
                size
            )

            for frame in newVideoFrames:
                video.write(frame)

            video.release()
            if os.path.isfile('test/output-audio.aac'):
                os.system(f'ffmpeg -i test/processed/{fileName}.{fileType} -i test/output-audio.aac -vcodec libx264 -c:a aac -map 0:v:0 -map 1:a:0 test/processed/{fileName}-final.{fileType} -y')
                os.remove('test/output-audio.aac')
            else:
                os.system(f'ffmpeg -i test/processed/{fileName}.{fileType} -vcodec libx264 -c:a aac -map 0:v:0 test/processed/{fileName}-final.{fileType} -y')
            os.remove(f'test/processed/{fileName}.{fileType}')
        else:
            # create GIF
            fileType = 'gif'
            gifFrames = []
            for frame in newVideoFrames:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                gifFrames.append(Image.fromarray(frame))

            gifFrames[0].save(f'test/processed/{fileName}.{fileType}',
                save_all=True,
                append_images=gifFrames[1:],
                duration=1000/FPS,
                loop=1
            )
