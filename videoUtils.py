import cv2

def extractFrames(video):
    success,image = video.read()
    frames = []
    while success:
        frames.append(image)
        success,image = video.read()
    return frames


def getFPS(video):
    return video.get(cv2.CAP_PROP_FPS)