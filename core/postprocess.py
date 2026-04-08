# core/postprocess.py
from collections import Counter

def format_output(mapped_colors):
    counter = Counter(mapped_colors)

    result = []
    for color, count in counter.items():
        result.append({
            "color": color,
            "count": count
        })

    return sorted(result, key=lambda x: -x["count"])