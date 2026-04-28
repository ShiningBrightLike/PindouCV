# utils/blueprint.py
import os
import json
import uuid
import cv2
import base64

BLUEPRINT_DIR = "data/blueprints"
META_FILE = os.path.join(BLUEPRINT_DIR, "meta.json")

os.makedirs(BLUEPRINT_DIR, exist_ok=True)


# =========================
# 📦 工具函数
# =========================
def _load_meta():
    if not os.path.exists(META_FILE):
        return []
    with open(META_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_meta(meta):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


# =========================
# ➕ 保存图纸
# =========================
def save_blueprint(username, image):
    if username is None:
        return False, "请先登录"

    meta = _load_meta()

    bp_id = str(uuid.uuid4())[:8]
    filename = f"{bp_id}.png"
    path = os.path.join(BLUEPRINT_DIR, filename)

    # 保存图片
    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, image_bgr)

    meta.append({
        "id": bp_id,
        "user": username,
        "file": filename,
        "name": f"图纸_{bp_id}"
    })

    _save_meta(meta)

    return True, "图纸已保存"


def delete_blueprint(username, bp_id):
    meta = _load_meta()

    new_meta = []
    deleted = False

    for m in meta:
        if m["id"] == bp_id and m["user"] == username:
            file_path = os.path.join(BLUEPRINT_DIR, m["file"])
            if os.path.exists(file_path):
                os.remove(file_path)
            deleted = True
        else:
            new_meta.append(m)

    _save_meta(new_meta)

    if deleted:
        return True, "删除成功"
    return False, "未找到图纸"


def rename_blueprint(username, bp_id, new_name):
    meta = _load_meta()

    for m in meta:
        if m["id"] == bp_id and m["user"] == username:
            m["name"] = new_name
            _save_meta(meta)
            return True, "重命名成功"

    return False, "未找到图纸"


def get_blueprint_image(bp_id):
    meta = _load_meta()

    for m in meta:
        if m["id"] == bp_id:
            path = os.path.join(BLUEPRINT_DIR, m["file"])
            if os.path.exists(path):
                img = cv2.imread(path)
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return None


# =========================
# 📖 获取图纸
# =========================
def get_blueprints(username):
    if username is None:
        return []

    meta = _load_meta()
    return [m for m in meta if m["user"] == username]


# =========================
# 🎨 渲染图纸列表
# =========================
def render_blueprints(blueprints):
    if not blueprints:
        return "<p>暂无图纸</p>"

    html = """
    <div style="display:grid;grid-template-columns:repeat(auto-fill,160px);gap:16px;">
    """

    for bp in blueprints:
        img_path = f"data/blueprints/{bp['file']}"

        # 👉 转 base64
        with open(img_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()

        html += f"""
        <div style="
            background:white;
            border-radius:12px;
            padding:10px;
            box-shadow:0 4px 12px rgba(0,0,0,0.08);
            text-align:center;
        ">
            <img src="data:image/png;base64,{img_base64}" 
                 style="width:100%;border-radius:8px;" />

            <div style="margin-top:6px;font-size:12px;color:#666;">
                {bp.get("name", "未命名")}
            </div>

            <div style="font-size:10px;color:#aaa;">
                ID: {bp['id']}
            </div>
        </div>
        """

    html += "</div>"
    return html