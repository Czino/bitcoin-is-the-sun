from PIL import Image 
import numpy as np
import glob
import re

imgs = []
images = []

print('Fetch images')
for filename in glob.glob('video/*.jpg'):
    img = Image.open(filename)

    imgs.append([
        img,
        filename.replace('.jpg', '').replace('video/', '')
    ])


print('Sort frames')
imgs.sort(key=lambda img: int(img[1]))

for i in range(len(imgs)):
    print(imgs[i][1])
    images.append(imgs[i][0])

length = len(images)
print('Render GIF from', length, 'images')

images[0].save('loop.gif',
    save_all=True,
    append_images=images[1:],
    duration=40,
    loop=1)

print('Done!')


### backup: ffmpeg -framerate 30 -pattern_type glob -i '*.jpg' -vf scale=1280:960 -c:v libx264 -r 30 -pix_fmt yuv420p circles.mp4