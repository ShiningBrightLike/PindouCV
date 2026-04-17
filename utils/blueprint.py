# blueprint.py
import json
import os
from datetime import datetime
from threading import Lock

DATA_PATH = "data/blueprints.json"
file_lock = Lock()


def load_data():
    if not os.path.exists(DATA_PATH):
        return {}

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_data(data):
    with file_lock:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# =========================
# 📄 保存图纸
# =========================
def save_blueprint(username, name, result):
    data = load_data()

    user_list = data.setdefault(username, [])

    user_list.append({
        "name": name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "colors": result
    })

    save_data(data)

    return True, "保存成功"


# =========================
# 📄 获取图纸
# =========================
def get_blueprints(username):
    data = load_data()
    return data.get(username, [])