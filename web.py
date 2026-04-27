# web.py
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

from utils.inventory import (
    login,
    register,
    get_inventory,
    use_inventory,
    add_inventory,
    inventory_to_list
)
from utils.blueprint import (
    save_blueprint,
    get_blueprints,
    render_blueprints
)


# =========================
# 🎨 美化颜色统计
# =========================
def render_color_stats(result, color_map, title="🎯 颜色统计"):
    html = f"""
    <div style="font-family:Arial;">
    <h3 style="margin-bottom:10px;">{title}</h3>
    <div style="display:grid; grid-template-columns:repeat(auto-fill,120px); gap:12px;">
    """

    for item in result:
        code = item["color"]
        count = item["count"]

        rgb = color_map.get(code, [128, 128, 128])
        r, g, b = rgb

        html += f"""
        <div style="
            border-radius:12px;
            padding:10px;
            background:white;
            text-align:center;
            box-shadow:0 4px 12px rgba(0,0,0,0.08);
        ">
            <div style="
                width:42px;height:42px;margin:auto;
                border-radius:8px;
                background:rgb({r},{g},{b});
                border:1px solid #ccc;
            "></div>

            <div style="margin-top:6px;font-weight:bold;">{code}</div>
            <div style="color:#666;">{count}</div>
        </div>
        """

    html += "</div></div>"
    return html


# =========================
# 🚀 pipeline
# =========================
def pipeline_web(image):
    if image is None:
        return None, "请上传图片", None, "⚠️ 请上传图片"

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    img_raw, img_detect = preprocess_image(image)
    grid = detect_grid(img_detect)

    h0, w0 = img_raw.shape[:2]
    h1, w1 = img_detect.shape[:2]

    scale_x = w0 / w1
    scale_y = h0 / h1

    grid_scaled = [
        (int(x1 * scale_x), int(y1 * scale_y),
         int(x2 * scale_x), int(y2 * scale_y))
        for (x1, y1, x2, y2) in grid
    ]

    colors = extract_colors(img_raw, grid_scaled)
    mapped = map_to_artkal_new(colors)
    result = format_output(mapped)

    grid_colors = build_grid_2d(mapped, grid)

    rows = len(grid_colors)
    cols = max(len(r) for r in grid_colors)

    for r in grid_colors:
        while len(r) < cols:
            r.append("UNKNOWN")

    grid_size = (rows, cols)

    with open("data/artkal_colors.json", "r") as f:
        color_data = json.load(f)

    color_map = {item["code"]: item["rgb"] for item in color_data}

    label_img = visualize_with_labels(
        grid_colors,
        color_map,
        grid_size
    )

    label_img = cv2.cvtColor(label_img, cv2.COLOR_BGR2RGB)

    result_html = render_color_stats(result, color_map)

    return label_img, result_html, result, "✅ 识别完成"


# =========================
# 🔐 用户
# =========================
def login_ui(username, password):
    ok, msg = login(username, password)
    if ok:
        return username, f"✅ {msg}"
    return None, f"❌ {msg}"


def register_ui(username, password):
    ok, msg = register(username, password)
    return f"{'✅' if ok else '❌'} {msg}"


# =========================
# 📦 库存
# =========================
def show_inventory(username):
    if not username:
        return "⚠️ 请先登录"

    inv = get_inventory(username)

    with open("data/artkal_colors.json", "r") as f:
        color_data = json.load(f)

    color_map = {item["code"]: item["rgb"] for item in color_data}

    inv_list = inventory_to_list(inv)

    return render_color_stats(inv_list, color_map, "📦 当前库存")


def use_result(username, result):
    if not username:
        return "⚠️ 请先登录"

    ok, warning, _ = use_inventory(username, result)

    msg = "✅ 已扣库存"
    if warning:
        msg += "\n⚠️ 库存不足:\n" + "\n".join(warning)

    return msg


def add_stock(username, color, count):
    if not username:
        return "⚠️ 请先登录"

    color = color.strip().upper()

    with open("data/artkal_colors.json", "r") as f:
        color_data = json.load(f)

    valid_codes = set(item["code"] for item in color_data)

    if color not in valid_codes:
        return f"❌ 颜色编号错误：{color} 不存在"

    ok, msg, _ = add_inventory(username, color, int(count))
    return f"{'✅' if ok else '❌'} {msg}"


# =========================
# 📁 图纸
# =========================
def save_blueprint_ui(username, image):
    ok, msg = save_blueprint(username, image)
    return f"{'✅' if ok else '❌'} {msg}"


def show_blueprints_ui(username):
    bps = get_blueprints(username)
    return render_blueprints(bps)


# =========================
# 🌐 UI
# =========================
with gr.Blocks(theme=gr.themes.Soft()) as demo:

    user_state = gr.State(None)
    result_state = gr.State(None)

    gr.Markdown("# 🎨 拼豆图生成 & 库存管理系统")

    with gr.Tabs():

        # 🎯 图像识别
        with gr.Tab("🎯 图像识别"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📤 输入")
                    input_img = gr.Image(type="numpy", label="上传图片")
                    run_btn = gr.Button("🚀 开始识别", variant="primary")
                    use_btn = gr.Button("📉 扣除库存")
                    detect_msg = gr.Textbox(label="操作结果")

                with gr.Column(scale=1):
                    gr.Markdown("### 📊 输出")
                    output_img = gr.Image(label="识别结果")
                    output_html = gr.HTML()

        # 📦 库存管理
        with gr.Tab("📦 库存管理"):
            show_btn = gr.Button("🔄 刷新库存", variant="primary")
            inventory_html = gr.HTML()

            gr.Markdown("### ➕ 添加库存")

            with gr.Row():
                add_color = gr.Textbox(label="颜色编号")
                add_count = gr.Number(label="数量")
                add_btn = gr.Button("添加", variant="secondary")

            inventory_msg = gr.Textbox(label="库存操作结果")

        # 📁 图纸管理
        with gr.Tab("📁 图纸管理"):
            gr.Markdown("### 📤 上传图纸")

            bp_input = gr.Image(type="numpy", label="上传图纸")
            save_bp_btn = gr.Button("💾 保存图纸", variant="primary")
            bp_msg = gr.Textbox(label="图纸操作结果")

            gr.Markdown("### 📚 我的图纸")

            refresh_bp_btn = gr.Button("🔄 刷新图纸")
            bp_gallery = gr.HTML()

        # 🔐 用户
        with gr.Tab("🔐 用户"):
            with gr.Row():
                username = gr.Textbox(label="用户名")
                password = gr.Textbox(label="密码", type="password")

            with gr.Row():
                login_btn = gr.Button("登录", variant="primary")
                register_btn = gr.Button("注册")

            login_msg = gr.Textbox(label="状态")

    # ======================
    # 🔗 绑定
    # ======================
    login_btn.click(
        login_ui,
        inputs=[username, password],
        outputs=[user_state, login_msg]
    )

    register_btn.click(
        register_ui,
        inputs=[username, password],
        outputs=login_msg
    )

    run_btn.click(
        pipeline_web,
        inputs=input_img,
        outputs=[output_img, output_html, result_state, detect_msg]
    )

    use_btn.click(
        use_result,
        inputs=[user_state, result_state],
        outputs=detect_msg
    )

    show_btn.click(
        show_inventory,
        inputs=user_state,
        outputs=inventory_html
    )

    add_btn.click(
        add_stock,
        inputs=[user_state, add_color, add_count],
        outputs=inventory_msg
    )

    save_bp_btn.click(
        save_blueprint_ui,
        inputs=[user_state, bp_input],
        outputs=bp_msg
    )

    refresh_bp_btn.click(
        show_blueprints_ui,
        inputs=user_state,
        outputs=bp_gallery
    )


# =========================
# 🚀 启动
# =========================
if __name__ == "__main__":
    demo.launch(share=False)