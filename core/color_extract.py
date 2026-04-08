# core/color_extract.py
import numpy as np

def extract_colors(img, grid):
    colors = []

    for (x1, y1, x2, y2) in grid:
        cell = img[y1:y2, x1:x2]

        # 取中心区域（避免边缘干扰）
        h, w, _ = cell.shape
        center = cell[h//4:3*h//4, w//4:3*w//4]

        avg_color = np.mean(center.reshape(-1, 3), axis=0)
        colors.append(avg_color)

    return colors