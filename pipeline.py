# pipeline.py
from core.preprocess import preprocess_image
from core.grid_detect import detect_grid
from core.color_extract import extract_colors
from core.color_map import map_to_artkal
from core.postprocess import format_output
import cv2

def run_pipeline(image):
    # 1. 预处理
    img = preprocess_image(image)

    # 2. 网格检测（关键）
    grid = detect_grid(img)

    # 3. 每个格子提取颜色
    colors = extract_colors(img, grid)

    # 4. 映射到 Artkal 色号
    mapped = map_to_artkal(colors)

    # 5. 输出整理
    result = format_output(mapped)

    return result

if __name__ == "__main__":

    image = cv2.imread("data/test.jpeg")
    result = run_pipeline(image)
    print(result)