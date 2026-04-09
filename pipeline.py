# pipeline.py
from core.preprocess import preprocess_image
from core.grid_detect import detect_grid
from core.color_extract import extract_colors
from core.color_map import map_to_artkal, map_to_artkal_new
from core.postprocess import (
    format_output,
    visualize_bead_result,
    show_comparison,
    visualize_with_labels
)

import cv2
import json
import numpy as np


def build_grid_2d(mapped, grid):
    """
    根据 grid 坐标还原 2D 结构（关键修复点）
    grid: [(x, y, w, h), ...]
    """

    # 按 y 排序（行）
    sorted_items = sorted(zip(grid, mapped), key=lambda x: (x[0][1], x[0][0]))

    rows = []
    current_row = []
    last_y = None
    threshold = 10  # 行判断阈值（可调）

    for (x, y, w, h), color in sorted_items:
        if last_y is None:
            last_y = y

        # 新一行
        if abs(y - last_y) > threshold:
            rows.append(current_row)
            current_row = []
            last_y = y

        current_row.append(color)

    if current_row:
        rows.append(current_row)

    return rows


def run_pipeline(image, visualize=True):
    # 1. 预处理
    img = preprocess_image(image)

    # 2. 网格检测
    grid = detect_grid(img)
    print(f"Detected {len(grid)} grid cells")

    # 3. 提取颜色
    colors = extract_colors(img, grid)

    # 4. 映射色号
    mapped = map_to_artkal(colors)

    # 5. 统计输出
    result = format_output(mapped)

    # =========================
    # 🎨 可视化
    # =========================
    if visualize:
        # ✅ 构建 2D grid（关键）
        grid_colors = build_grid_2d(mapped, grid)

        rows = len(grid_colors)
        cols = max(len(r) for r in grid_colors)

        print(f"Grid shape: {rows} x {cols}")

        # 读取色卡
        with open("data/artkal_colors.json", "r") as f:
            color_data = json.load(f)

        color_map = {
            item["code"]: item["rgb"]
            for item in color_data
        }

        # 补齐不规则行（防止崩）
        for r in grid_colors:
            while len(r) < cols:
                r.append("UNKNOWN")

        grid_size = (rows, cols)

        # 🎨 1. 重建图
        result_img = visualize_bead_result(
            grid_colors,
            color_map,
            grid_size
        )

        # 🆚 2. 对比图
        show_comparison(image, result_img)

        # 🔤 3. 标注图
        label_img = visualize_with_labels(
            grid_colors,
            color_map,
            grid_size
        )

        cv2.imshow("Labeled Result", label_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return result


if __name__ == "__main__":
    image = cv2.imread("data/test.jpeg")

    result = run_pipeline(image, visualize=True)

    print("\n🎯 Color Summary:")
    print(result)