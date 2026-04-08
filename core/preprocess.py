# core/preprocess.py
import cv2
import numpy as np

def preprocess_image(image):
    img = np.array(image)

    # resize（可选）
    img = cv2.resize(img, (512, 512))

    # 去噪
    img = cv2.GaussianBlur(img, (5, 5), 0)

    return img