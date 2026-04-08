# core/color_map.py
import json
import numpy as np

def load_palette():
    with open("data/artkal_colors.json", "r") as f:
        return json.load(f)

def color_distance(c1, c2):
    return np.linalg.norm(np.array(c1) - np.array(c2))

def map_to_artkal(colors):
    palette = load_palette()
    result = []

    for c in colors:
        best = None
        min_dist = float("inf")

        for p in palette:
            dist = color_distance(c, p["rgb"])
            if dist < min_dist:
                min_dist = dist
                best = p["code"]

        result.append(best)

    return result