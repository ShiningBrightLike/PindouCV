import cv2
import numpy as np


def detect_grid(img, debug=False):
    """
    自动检测拼豆网格（适用于规则图纸）
    """

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. 边缘检测
    edges = cv2.Canny(gray, 50, 150)

    # 2. 水平/垂直投影
    vertical_sum = np.sum(edges, axis=0)
    horizontal_sum = np.sum(edges, axis=1)

    # 3. 找网格线位置
    x_lines = find_peaks(vertical_sum)
    y_lines = find_peaks(horizontal_sum)

    # 4. 去重 + 排序
    x_lines = merge_close_lines(x_lines)
    y_lines = merge_close_lines(y_lines)

    # 5. 构建 grid
    grid = []
    for i in range(len(y_lines) - 1):
        for j in range(len(x_lines) - 1):
            x1 = x_lines[j]
            x2 = x_lines[j + 1]
            y1 = y_lines[i]
            y2 = y_lines[i + 1]

            # 过滤太小的格子（防止噪声）
            if (x2 - x1) > 5 and (y2 - y1) > 5:
                grid.append((x1, y1, x2, y2))
    # 输出格子数量
    print(f"Detected {len(grid)} grid cells")

    if debug:
        debug_draw(img, x_lines, y_lines)

    return grid


# =============================
# 🔍 工具函数
# =============================

def find_peaks(projection, threshold_ratio=0.2):
    """
    找投影中的“网格线峰值”
    """
    threshold = np.max(projection) * threshold_ratio

    peaks = []
    for i in range(1, len(projection) - 1):
        if projection[i] > threshold and projection[i] > projection[i - 1] and projection[i] > projection[i + 1]:
            peaks.append(i)

    return peaks


def merge_close_lines(lines, min_distance=5):
    """
    合并太近的线（避免一条线被检测成多条）
    """
    if not lines:
        return []

    lines = sorted(lines)
    merged = [lines[0]]

    for l in lines[1:]:
        if l - merged[-1] > min_distance:
            merged.append(l)

    return merged


def debug_draw(img, x_lines, y_lines):
    """
    可视化检测结果
    """
    vis = img.copy()

    for x in x_lines:
        cv2.line(vis, (x, 0), (x, vis.shape[0]), (0, 0, 255), 1)

    for y in y_lines:
        cv2.line(vis, (0, y), (vis.shape[1], y), (255, 0, 0), 1)

    cv2.imshow("grid", vis)
    cv2.waitKey(0)