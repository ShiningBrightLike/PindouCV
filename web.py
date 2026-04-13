import gradio as gr
import cv2
import numpy as np
import json

from pipeline import build_grid_2d

from core.preprocess import preprocess_image
from core.grid_detect import detect_grid
from core.color_extract import extract_colors
from core.color_map import map_to_artkal_new
from core.postprocess import visualize_with_labels, format_output


# =========================
# 🎨 颜色统计 HTML 渲染
# =========================
def render_color_stats(result, color_map):
    """
    生成 HTML 可视化颜色统计（卡片版）
    """

    # 按数量排序
    result = sorted(result, key=lambda x: -x["count"])

    html = """
    <div style="font-family: Arial;">
    <h3>🎯 颜色统计</h3>
    <div style="display:flex; flex-wrap:wrap; gap:10px;">
    """

    for item in result:
        code = item["color"]
        count = item["count"]

        rgb = color_map.get(code, [128, 128, 128])
        r, g, b = rgb

        html += f"""
        <div style="
            width:120px;
            border-radius:10px;
            padding:10px;
            background:#f5f5f5;
            text-align:center;
            box-shadow:0 2px 5px rgba(0,0,0,0.1);
        ">
            <div style="
                width:40px;
                height:40px;
                margin:auto;
                background:rgb({r},{g},{b});
                border:1px solid #000;
            "></div>

            <div style="margin-top:5px; font-weight:bold;">{code}</div>
            <div>{count}</div>
        </div>
        """

    html += "</div></div>"

    return html


# =========================
# 🚀 主 pipeline（Web版）
# =========================
def pipeline_web(image):

    if image is None:
        return None, "请上传图片"

    # RGB → BGR
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # ===== 1. 预处理 =====
    img_raw, img_detect = preprocess_image(image)

    # ===== 2. 网格检测 =====
    grid = detect_grid(img_detect)

    # ===== 坐标缩放 =====
    h0, w0 = img_raw.shape[:2]
    h1, w1 = img_detect.shape[:2]

    scale_x = w0 / w1
    scale_y = h0 / h1

    grid_scaled = [
        (int(x1 * scale_x), int(y1 * scale_y),
         int(x2 * scale_x), int(y2 * scale_y))
        for (x1, y1, x2, y2) in grid
    ]

    # ===== 3. 颜色提取 =====
    colors = extract_colors(img_raw, grid_scaled)

    # ===== 4. 映射色号 =====
    mapped = map_to_artkal_new(colors)

    # ===== 5. 统计 =====
    result = format_output(mapped)

    # ===== 构建 2D grid =====
    grid_colors = build_grid_2d(mapped, grid)

    rows = len(grid_colors)
    cols = max(len(r) for r in grid_colors)

    # 补齐不规则
    for r in grid_colors:
        while len(r) < cols:
            r.append("UNKNOWN")

    grid_size = (rows, cols)

    # ===== 读取色卡 =====
    with open("data/artkal_colors.json", "r") as f:
        color_data = json.load(f)

    color_map = {
        item["code"]: item["rgb"]
        for item in color_data
    }

    # ===== 6. 可视化 =====
    label_img = visualize_with_labels(
        grid_colors,
        color_map,
        grid_size
    )

    # BGR → RGB（给 Gradio）
    label_img = cv2.cvtColor(label_img, cv2.COLOR_BGR2RGB)

    # ===== 7. HTML 统计 =====
    result_html = render_color_stats(result, color_map)

    return label_img, result_html


# =========================
# 🌐 Gradio UI
# =========================
with gr.Blocks() as demo:
    gr.Markdown("## 🎨 拼豆图自动生成工具（Artkal Beads）")

    with gr.Row():
        with gr.Column():
            input_img = gr.Image(label="上传图片", type="numpy")
            btn = gr.Button("🚀 运行生成")

        with gr.Column():
            output_img = gr.Image(label="生成结果（带标注）")
            output_html = gr.HTML(label="颜色统计")

    btn.click(
        fn=pipeline_web,
        inputs=input_img,
        outputs=[output_img, output_html]
    )


# =========================
# 🚀 启动
# =========================
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)