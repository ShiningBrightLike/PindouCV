# core/postprocess.py
from collections import Counter
import numpy as np
import cv2


def format_output(mapped_colors):
    counter = Counter(mapped_colors)

    result = []
    for color, count in counter.items():
        result.append({
            "color": color,
            "count": count
        })

    return sorted(result, key=lambda x: -x["count"])


def visualize_bead_result(grid_colors, color_map, grid_size, cell_size=20):
    """
    grid_colors: 2D list，例如 [["A1","A2"], ...]
    color_map: {"A1": [r,g,b], ...}
    grid_size: (rows, cols)
    """

    rows, cols = grid_size
    img = np.zeros((rows * cell_size, cols * cell_size, 3), dtype=np.uint8)

    for r in range(rows):
        for c in range(cols):
            code = grid_colors[r][c]
            rgb = color_map.get(code, [0, 0, 0])

            # OpenCV 用 BGR
            color = (rgb[2], rgb[1], rgb[0])

            y1, y2 = r * cell_size, (r + 1) * cell_size
            x1, x2 = c * cell_size, (c + 1) * cell_size

            img[y1:y2, x1:x2] = color

    return img


def show_comparison(original, reconstructed):
    h = min(original.shape[0], reconstructed.shape[0])

    original = cv2.resize(original, (h, h))
    reconstructed = cv2.resize(reconstructed, (h, h))

    combined = np.hstack([original, reconstructed])
    cv2.imshow("Original vs Reconstructed", combined)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def visualize_with_labels(grid_colors, color_map, grid_size, cell_size=40):
    rows, cols = grid_size
    img = np.zeros((rows * cell_size, cols * cell_size, 3), dtype=np.uint8)

    for r in range(rows):
        for c in range(cols):
            code = grid_colors[r][c]
            rgb = color_map.get(code, [0, 0, 0])
            color = (rgb[2], rgb[1], rgb[0])

            y1, y2 = r * cell_size, (r + 1) * cell_size
            x1, x2 = c * cell_size, (c + 1) * cell_size

            img[y1:y2, x1:x2] = color

            # 写字
            cv2.putText(
                img,
                code,
                (x1 + 5, y1 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )
    # 保存
    cv2.imwrite("data/output.png", img)

    return img