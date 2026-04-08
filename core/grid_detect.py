# core/grid_detect.py
import numpy as np

def detect_grid(img, grid_size=(48, 48)):
    h, w, _ = img.shape
    rows, cols = grid_size

    cell_h = h // rows
    cell_w = w // cols

    grid = []

    for i in range(rows):
        for j in range(cols):
            x1 = j * cell_w
            y1 = i * cell_h
            x2 = x1 + cell_w
            y2 = y1 + cell_h

            grid.append((x1, y1, x2, y2))

    return grid