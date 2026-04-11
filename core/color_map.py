# core/color_map.py
import json
import numpy as np
from functools import lru_cache
from skimage.color import rgb2lab, deltaE_ciede2000

# ✅ 只加载一次
@lru_cache(maxsize=1)
def load_palette():
    with open("data/artkal_colors.json", "r") as f:
        palette = json.load(f)

    codes = [p["code"] for p in palette]
    rgbs = np.array([p["rgb"] for p in palette], dtype=np.float32)

    return codes, rgbs


# ✅ 向量化距离计算（超级快）
def map_to_artkal(colors):
    """
    colors: List[[R,G,B], ...]
    """
    codes, palette_rgbs = load_palette()

    colors = np.array(colors, dtype=np.float32)

    # shape:
    # colors: (N, 3)
    # palette: (M, 3)

    # 扩展维度做广播
    diff = colors[:, None, :] - palette_rgbs[None, :, :]

    # 欧氏距离
    dist = np.linalg.norm(diff, axis=2)  # (N, M)

    # 找最小索引
    indices = np.argmin(dist, axis=1)

    # 映射 code
    return [codes[i] for i in indices]

def map_to_artkal_new(colors):
    codes, palette_rgbs = load_palette()

    colors = np.array(colors, dtype=np.float32)

    colors_lab = rgb2lab(colors / 255.0)
    palette_lab = rgb2lab(palette_rgbs / 255.0)

    # 👉 ΔE2000
    dist = deltaE_ciede2000(
        colors_lab[:, None, :],
        palette_lab[None, :, :]
    )

    indices = np.argmin(dist, axis=1)

    return [codes[i] for i in indices]