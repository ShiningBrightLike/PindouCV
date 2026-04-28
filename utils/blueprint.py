# utils/blueprint.py
import os
import json
import uuid
import cv2
import base64
from threading import Lock

BLUEPRINT_DIR = "data/blueprints"
META_FILE = os.path.join(BLUEPRINT_DIR, "meta.json")

os.makedirs(BLUEPRINT_DIR, exist_ok=True)

# 🔒 文件锁
blueprint_lock = Lock()


# =========================
# 📦 工具函数（内部用）
# =========================
def _load_meta_unlocked():
    if not os.path.exists(META_FILE):
        return []
    with open(META_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []


def _save_meta_unlocked(meta):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _atomic_meta_update(update_fn):
    """
    🔥 所有 meta 修改必须走这里
    """
    with blueprint_lock:
        meta = _load_meta_unlocked()
        result = update_fn(meta)
        _save_meta_unlocked(meta)
        return result


# =========================
# ➕ 保存图纸
# =========================
def save_blueprint(username, image):
    if username is None:
        return False, "请先登录"

    def _update(meta):
        bp_id = str(uuid.uuid4())[:8]
        filename = f"{bp_id}.png"
        path = os.path.join(BLUEPRINT_DIR, filename)

        # ✅ 先写文件（仍在锁内，保证一致性）
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(path, image_bgr)

        meta.append({
            "id": bp_id,
            "user": username,
            "file": filename,
            "name": f"图纸_{bp_id}"
        })

        return True, "图纸已保存"

    return _atomic_meta_update(_update)


# =========================
# 🗑 删除图纸
# =========================
def delete_blueprint(username, bp_id):
    def _update(meta):
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

        meta.clear()
        meta.extend(new_meta)

        if deleted:
            return True, "删除成功"
        return False, "未找到图纸"

    return _atomic_meta_update(_update)


# =========================
# ✏️ 重命名
# =========================
def rename_blueprint(username, bp_id, new_name):
    def _update(meta):
        for m in meta:
            if m["id"] == bp_id and m["user"] == username:
                m["name"] = new_name
                return True, "重命名成功"
        return False, "未找到图纸"

    return _atomic_meta_update(_update)


# =========================
# 📖 查询（读也加锁）
# =========================
def get_blueprint_image(bp_id):
    with blueprint_lock:
        meta = _load_meta_unlocked()

        for m in meta:
            if m["id"] == bp_id:
                path = os.path.join(BLUEPRINT_DIR, m["file"])
                if os.path.exists(path):
                    img = cv2.imread(path)
                    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return None


def get_blueprints(username):
    if username is None:
        return []

    with blueprint_lock:
        meta = _load_meta_unlocked()
        return [m for m in meta if m["user"] == username]


# =========================
# 🎨 渲染图纸列表（读文件）
# =========================
def render_blueprints(blueprints):
    if not blueprints:
        return "<p>暂无图纸</p>"

    html = """
    <div style="display:grid;grid-template-columns:repeat(auto-fill,160px);gap:16px;">
    """

    # ⚠️ 这里不建议全局锁，否则UI会卡
    # 👉 单个文件读即可（文件系统本身安全）

    for bp in blueprints:
        img_path = f"data/blueprints/{bp['file']}"

        if not os.path.exists(img_path):
            continue

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