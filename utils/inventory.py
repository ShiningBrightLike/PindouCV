# utils/postprocess.py
import json
import os
from threading import Lock

DATA_PATH = "data/users.json"

file_lock = Lock()


# =========================
# 🧱 基础读写
# =========================
def _load_users_unlocked():
    if not os.path.exists(DATA_PATH):
        return {}

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}


def _save_users_unlocked(users):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def load_users():
    """
    带锁读取（防止读写冲突）
    """
    with file_lock:
        return _load_users_unlocked()


def save_users(users):
    """
    带锁写入
    """
    with file_lock:
        _save_users_unlocked(users)


# =========================
# 🔥 原子更新（核心）
# =========================
def atomic_update(update_fn):
    """
    所有“读->改->写”必须走这里
    """
    with file_lock:
        users = _load_users_unlocked()
        result = update_fn(users)
        _save_users_unlocked(users)
        return result


# =========================
# 👤 用户相关
# =========================
def register(username, password):
    def _update(users):
        if username in users:
            return False, "用户已存在"
        if not username or not password:
            return False, "用户名和密码不能为空"
        if len(password) < 6:
            return False, "密码长度不能少于 6 位"

        with open("data/artkal_colors.json", "r", encoding="utf-8") as f:
            color_data = json.load(f)

        inventory = {item["code"]: 0 for item in color_data}

        users[username] = {
            "password": password,
            "inventory": inventory
        }

        return True, "注册成功"

    return atomic_update(_update)


def login(username, password):
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
    users = load_users()

    if username not in users:
        return {}

    return users[username].get("inventory", {})


def set_inventory(username, inventory_dict):
    def _update(users):
        if username not in users:
            return False, "用户不存在"

        users[username]["inventory"] = inventory_dict
        return True, "库存已更新"

    return atomic_update(_update)


def use_inventory(username, used_colors):
    def _update(users):
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

        return True, warning, inventory

    return atomic_update(_update)


def add_inventory(username, color, count):
    def _update(users):
        if username not in users:
            return False, "用户不存在", {}

        inventory = users[username].setdefault("inventory", {})
        inventory[color] = inventory.get(color, 0) + int(count)

        return True, f"{color} 添加成功 🔢 库存现有 {inventory[color]}", inventory

    return atomic_update(_update)


def batch_add_inventory(username, items):
    def _update(users):
        if username not in users:
            return False, "用户不存在", {}

        inventory = users[username].setdefault("inventory", {})

        for item in items:
            color = item["color"]
            count = int(item["count"])
            inventory[color] = inventory.get(color, 0) + count

        return True, "批量添加成功", inventory

    return atomic_update(_update)


def clear_inventory(username):
    def _update(users):
        if username not in users:
            return False, "用户不存在"

        users[username]["inventory"] = {}
        return True, "库存已清空"

    return atomic_update(_update)


# =========================
# 📊 工具函数
# =========================
def inventory_to_list(inventory_dict):
    return [{"color": k, "count": v} for k, v in inventory_dict.items()]