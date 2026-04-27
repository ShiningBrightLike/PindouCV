# utils/postprocess.py
import json
import os
from threading import Lock

DATA_PATH = "data/users.json"

# 简单文件锁（防止并发写坏）
file_lock = Lock()


# =========================
# 🧱 基础读写
# =========================
def load_users():
    """
    读取用户数据（自动容错）
    """
    if not os.path.exists(DATA_PATH):
        return {}

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_users(users):
    """
    保存用户数据（带锁）
    """
    with file_lock:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)


# =========================
# 👤 用户相关
# =========================
def register(username, password):
    """
    注册用户（如果存在则失败）
    """
    users = load_users()

    if username in users:
        return False, "用户已存在"
    if not username or not password:
        return False, "用户名和密码不能为空"
    if len(password) < 6:
        return False, "密码长度不能少于 6 位"

    # 读取颜色配置
    with open("data/artkal_colors.json", "r", encoding="utf-8") as f:
        color_data = json.load(f)
    inventory = {item["code"]: 0 for item in color_data}

    users[username] = {
        "password": password,
        "inventory": inventory
    }

    save_users(users)
    return True, "注册成功"


def login(username, password):
    """
    登录验证
    """
    users = load_users()

    if username not in users:
        return False, "用户不存在"

    if users[username]["password"] != password:
        return False, "密码错误"

    return True, "登录成功"


# =========================
# 📦 库存相关
# =========================
def get_inventory(username):
    """
    获取库存
    """
    users = load_users()

    if username not in users:
        return {}

    return users[username].get("inventory", {})


def set_inventory(username, inventory_dict):
    """
    覆盖库存（用于初始化）
    """
    users = load_users()

    if username not in users:
        return False, "用户不存在"

    users[username]["inventory"] = inventory_dict

    save_users(users)
    return True, "库存已更新"


def use_inventory(username, used_colors):
    """
    扣库存（来自 pipeline 结果）
    used_colors = [
        {"color": "H2", "count": 2000},
        ...
    ]
    """
    users = load_users()

    if username not in users:
        return False, "用户不存在", {}

    inventory = users[username].setdefault("inventory", {})

    warning = []

    for item in used_colors:
        color = item["color"]
        count = item["count"]

        current = inventory.get(color, 0)
        new_value = current - count

        if new_value < 0:
            warning.append(f"{color} 库存不足（当前 {current}）")
            new_value = 0

        inventory[color] = new_value

    save_users(users)

    return True, warning, inventory


def add_inventory(username, color, count):
    """
    单个颜色增加库存
    """
    users = load_users()

    if username not in users:
        return False, "用户不存在", {}

    inventory = users[username].setdefault("inventory", {})

    inventory[color] = inventory.get(color, 0) + int(count)

    save_users(users)

    return True, f"{color} 添加成功 🔢 库存现有 {inventory[color]}", inventory


def batch_add_inventory(username, items):
    """
    批量增加库存
    items = [{"color": "H2", "count": 100}, ...]
    """
    users = load_users()

    if username not in users:
        return False, "用户不存在", {}

    inventory = users[username].setdefault("inventory", {})

    for item in items:
        color = item["color"]
        count = int(item["count"])

        inventory[color] = inventory.get(color, 0) + count

    save_users(users)

    return True, "批量添加成功", inventory


# =========================
# 📊 工具函数
# =========================
def inventory_to_list(inventory_dict):
    """
    转成 pipeline 风格（方便复用 UI）
    """
    return [
        {"color": k, "count": v}
        for k, v in inventory_dict.items()
    ]


def clear_inventory(username):
    """
    清空库存
    """
    users = load_users()

    if username not in users:
        return False, "用户不存在"

    users[username]["inventory"] = {}

    save_users(users)

    return True, "库存已清空"