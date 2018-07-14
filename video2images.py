import os

import cv2 as cv

VIDEO_FILE = "./source_video/source.mkv"
IMAGE_DIR = "./source_images"
RATIO = 8;

def store_image(filename, content):
    with open(filename, "wb") as fd:
        fd.write(content)

cap = cv.VideoCapture(VIDEO_FILE)

index = 0
while True:
    cap.set(cv.CAP_PROP_POS_MSEC, index * RATIO * 1000)                      
    success, image = cap.read()
    if not success:
        break
    
    #face_detective(image.tobytes())
    success, image = cv.imencode(".jpg", image, [cv.IMWRITE_JPEG_QUALITY, 80])

    store_image(os.path.join(IMAGE_DIR, "{0}.jpg".format(index)), image)

    index += 1


cap.release()
