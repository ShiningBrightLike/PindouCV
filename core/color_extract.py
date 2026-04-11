# core/color_extract.py
import numpy as np

def extract_colors(img, grid):
    colors = []

    for (x1, y1, x2, y2) in grid:
        cell = img[y1:y2, x1:x2]

        # 取中心区域（避免边缘干扰）
        h, w, _ = cell.shape
        margin = int(min(h, w) * 0.3)
        center = cell[margin:h-margin, margin:w-margin]

        avg_color = np.mean(center.reshape(-1, 3), axis=0)
        avg_color = avg_color[::-1] # BGR to RGB
        colors.append(avg_color)

    return colors