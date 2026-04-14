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


# =========================
# 🎨 颜色统计 HTML 渲染
# =========================
def render_color_stats(result, color_map, title="🎯 颜色统计"):
    result = sorted(result, key=lambda x: -x["count"])

    html = f"""
    <div style="font-family: Arial;">
    <h3>{title}</h3>
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
# 🚀 pipeline（增加返回result）
# =========================
def pipeline_web(image):

    if image is None:
        return None, "请上传图片", None

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

    return label_img, result_html, result  # ✅ 多返回一个 result


# =========================
# 🔐 登录
# =========================
def login_ui(username, password):
    ok, msg = login(username, password)
    if ok:
        return username, f"✅ {msg}"
    return None, f"❌ {msg}"


# =========================
# 🆕 注册
# =========================
def register_ui(username, password):
    ok, msg = register(username, password)
    if ok:
        return f"✅ {msg}"
    return f"❌ {msg}"


# =========================
# 📦 显示库存
# =========================
def show_inventory(username):
    if not username:
        return "请先登录"

    inv = get_inventory(username)

    with open("data/artkal_colors.json", "r") as f:
        color_data = json.load(f)

    color_map = {item["code"]: item["rgb"] for item in color_data}

    inv_list = inventory_to_list(inv)

    return render_color_stats(inv_list, color_map, "📦 当前库存")


# =========================
# ➖ 使用库存
# =========================
def use_result(username, result):
    if not username:
        return "请先登录"

    ok, warning, inv = use_inventory(username, result)

    msg = "✅ 已扣库存\n"
    if warning:
        msg += "\n".join(warning)

    return msg


# =========================
# ➕ 手动加库存
# =========================
def add_stock(username, color, count):
    if not username:
        return "请先登录"

    ok, msg, _ = add_inventory(username, color, int(count))
    return msg


# =========================
# 🌐 UI
# =========================
with gr.Blocks() as demo:

    user_state = gr.State(None)
    result_state = gr.State(None)

    gr.Markdown("## 🎨 拼豆图 + 库存管理系统")

    # ===== 登录 =====
    with gr.Row():
        username = gr.Textbox(label="用户名")
        password = gr.Textbox(label="密码", type="password")
        login_btn = gr.Button("登录")
        register_btn = gr.Button("注册")

    login_msg = gr.Textbox(label="登录状态")

    # ===== 主界面 =====
    with gr.Row():
        with gr.Column():
            input_img = gr.Image(label="上传图片", type="numpy")
            run_btn = gr.Button("🚀 识别")

            use_btn = gr.Button("📉 使用本次结果（扣库存）")

        with gr.Column():
            output_img = gr.Image(label="识别结果")
            output_html = gr.HTML(label="颜色统计")

    # ===== 库存区 =====
    gr.Markdown("## 📦 库存管理")

    show_btn = gr.Button("刷新库存")
    inventory_html = gr.HTML()

    with gr.Row():
        add_color = gr.Textbox(label="颜色编号（如 H2）")
        add_count = gr.Number(label="数量")
        add_btn = gr.Button("➕ 添加库存")

    add_msg = gr.Textbox(label="操作结果")

    # ===== 绑定 =====
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
        outputs=[output_img, output_html, result_state]
    )

    use_btn.click(
        use_result,
        inputs=[user_state, result_state],
        outputs=add_msg
    )

    show_btn.click(
        show_inventory,
        inputs=user_state,
        outputs=inventory_html
    )

    add_btn.click(
        add_stock,
        inputs=[user_state, add_color, add_count],
        outputs=add_msg
    )


# =========================
# 🚀 启动
# =========================
if __name__ == "__main__":
    demo.launch(share=False) # http://localhost:7860