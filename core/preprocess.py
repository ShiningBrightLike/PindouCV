# core/preprocess.py
import cv2
import numpy as np

def preprocess_image(image):
    img = np.array(image)

    # 👉 只用于 grid 检测
    img_detect = cv2.resize(img, (512, 512))
    img_detect = cv2.GaussianBlur(img_detect, (5, 5), 0)

    return img, img_detect