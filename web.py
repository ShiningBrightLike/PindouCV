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
    rename_blueprint,
    delete_blueprint,
    get_blueprint_image
)

# =========================
# 🎨 颜色统计UI
# =========================
def render_color_stats(result, color_map, title="🎯 颜色统计"):
    html = f"""
    <div style="font-family:Arial;">
    <h3>{title}</h3>
    <div style="display:grid; grid-template-columns:repeat(auto-fill,120px); gap:12px;">
    """

    for item in result:
        code = item["color"]
        count = item["count"]
        r, g, b = color_map.get(code, [128,128,128])

        html += f"""
        <div style="border-radius:12px;padding:10px;background:white;text-align:center;
        box-shadow:0 4px 10px rgba(0,0,0,0.08);">
            <div style="width:40px;height:40px;margin:auto;border-radius:8px;
            background:rgb({r},{g},{b});border:1px solid #ccc;"></div>
            <div><b>{code}</b></div>
            <div>{count}</div>
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
        (int(x1*scale_x), int(y1*scale_y),
         int(x2*scale_x), int(y2*scale_y))
        for (x1,y1,x2,y2) in grid
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

    with open("data/artkal_colors.json","r") as f:
        color_data = json.load(f)

    color_map = {i["code"]: i["rgb"] for i in color_data}

    label_img = visualize_with_labels(
        grid_colors,
        color_map,
        (rows, cols)
    )

    label_img = cv2.cvtColor(label_img, cv2.COLOR_BGR2RGB)

    html = render_color_stats(result, color_map)

    return label_img, html, result, "✅ 识别完成"


# =========================
# 🔐 用户
# =========================
def login_ui(username, password):
    ok, msg = login(username, password)
    return (username if ok else None), f"{'✅' if ok else '❌'} {msg}"

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

    with open("data/artkal_colors.json","r") as f:
        color_data = json.load(f)

    color_map = {i["code"]: i["rgb"] for i in color_data}
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

    with open("data/artkal_colors.json","r") as f:
        valid = {i["code"] for i in json.load(f)}

    if color not in valid:
        return f"❌ 颜色不存在：{color}"

    ok, msg, _ = add_inventory(username, color, int(count))
    return f"{'✅' if ok else '❌'} {msg}"


# =========================
# 📁 图纸（修复版🔥）
# =========================
def show_blueprints_ui(username):
    if not username:
        return [], []

    bps = get_blueprints(username)

    gallery = []
    for bp in bps:
        img = get_blueprint_image(bp["id"])  # ✅ 正确加载方式
        gallery.append((img, f'{bp["name"]}\nID:{bp["id"]}'))

    return gallery, bps


def on_select(evt: gr.SelectData, bps):
    if not bps:
        return ""
    return bps[evt.index]["id"]


def save_blueprint_ui(username, image):
    ok, msg = save_blueprint(username, image)
    return f"{'✅' if ok else '❌'} {msg}"


def rename_bp_ui(username, bp_id, new_name):
    ok, msg = rename_blueprint(username, bp_id, new_name)
    return f"{'✅' if ok else '❌'} {msg}"


def delete_bp_ui(username, bp_id):
    ok, msg = delete_blueprint(username, bp_id)
    return f"{'✅' if ok else '❌'} {msg}"


def view_bp_ui(bp_id):
    return get_blueprint_image(bp_id)


# =========================
# 🌐 UI
# =========================
with gr.Blocks(theme=gr.themes.Soft()) as demo:

    user_state = gr.State(None)
    result_state = gr.State(None)
    bp_state = gr.State([])

    gr.Markdown("# 🎨 拼豆图生成系统")

    with gr.Tabs():

        # 🎯 图像识别
        with gr.Tab("🎯 图像识别"):
            with gr.Row():

                with gr.Column(scale=1):
                    input_img = gr.Image(type="numpy")

                    with gr.Row():
                        run_btn = gr.Button("🚀 识别", variant="primary")
                        use_btn = gr.Button("📉 扣库存")

                    detect_msg = gr.Textbox(label="识别结果")

                with gr.Column(scale=1.2):
                    output_img = gr.Image()
                    output_html = gr.HTML()


        # 📦 库存
        with gr.Tab("📦 库存管理"):
            with gr.Row():

                with gr.Column(scale=2):
                    show_btn = gr.Button("刷新库存", variant="primary")
                    inventory_html = gr.HTML()

                with gr.Column(scale=1):
                    add_color = gr.Textbox(label="颜色")
                    add_count = gr.Number(label="数量")
                    add_btn = gr.Button("添加库存")
                    inventory_msg = gr.Textbox(label="库存操作结果")


        # 📁 图纸（最终版）
        with gr.Tab("📁 图纸管理"):
            with gr.Row():

                with gr.Column(scale=2):
                    refresh_bp_btn = gr.Button("刷新图纸", variant="primary")
                    bp_gallery = gr.Gallery(columns=4, height=400)

                with gr.Column(scale=1):
                    selected_bp = gr.Textbox(label="选中图纸ID", interactive=False)
                    rename_input = gr.Textbox(label="新名称")

                    view_btn = gr.Button("查看")
                    rename_btn = gr.Button("重命名")
                    delete_btn = gr.Button("删除")

                    bp_msg = gr.Textbox(label="图纸操作结果")

                    bp_view = gr.Image(label="预览")

                    bp_input = gr.Image(type="numpy")
                    save_bp_btn = gr.Button("保存图纸")

                    upload_msg = gr.Textbox(label="上传结果")


        # 🔐 用户
        with gr.Tab("🔐 用户"):
            username = gr.Textbox(label="用户名")
            password = gr.Textbox(label="密码", type="password")

            with gr.Row():
                login_btn = gr.Button("登录", variant="primary")
                register_btn = gr.Button("注册")

            login_msg = gr.Textbox(label="登录状态")


    # ======================
    # 🔗 绑定
    # ======================
    login_btn.click(login_ui, [username, password], [user_state, login_msg])
    register_btn.click(register_ui, [username, password], login_msg)

    run_btn.click(
        pipeline_web,
        input_img,
        [output_img, output_html, result_state, detect_msg]
    )

    use_btn.click(use_result, [user_state, result_state], detect_msg)

    show_btn.click(show_inventory, user_state, inventory_html)

    add_btn.click(
        add_stock,
        [user_state, add_color, add_count],
        inventory_msg
    )

    refresh_bp_btn.click(
        show_blueprints_ui,
        user_state,
        [bp_gallery, bp_state]
    )

    bp_gallery.select(on_select, bp_state, selected_bp)

    save_bp_btn.click(
        save_blueprint_ui,
        [user_state, bp_input],
        upload_msg
    )

    rename_btn.click(
        rename_bp_ui,
        [user_state, selected_bp, rename_input],
        bp_msg
    )

    delete_btn.click(
        delete_bp_ui,
        [user_state, selected_bp],
        bp_msg
    )

    view_btn.click(view_bp_ui, selected_bp, bp_view)


# =========================
# 🚀 启动
# =========================
if __name__ == "__main__":
    demo.launch()