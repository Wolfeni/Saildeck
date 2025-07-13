import os
import sys
import json
from mod_manager import set_mod_enabled

# 📍 Fonction pour obtenir le bon chemin (VSC ou exe PyInstaller)
def get_save_file_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)  # ← dossier du .exe
    else:
        base_path = os.path.dirname(__file__)         # ← dossier du script
    return os.path.join(base_path, "saildeck.data")


def load_all_data():
    path = get_save_file_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_all_data(data):
    with open(get_save_file_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_modpack(name, mods_dir):
    data = load_all_data()

    if "modpacks" not in data:
        data["modpacks"] = {}

    mod_list = []
    for root, _, files in os.walk(mods_dir):
        for file in files:
            if file.endswith(".otr") or file.endswith(".o2r"):
                rel_path = os.path.relpath(os.path.join(root, file), mods_dir)
                mod_list.append(rel_path)

    data["modpacks"][name] = mod_list
    save_all_data(data)


def list_modpacks():
    data = load_all_data()
    return list(data.get("modpacks", {}).keys())


def load_modpack(name, mods_dir):
    data = load_all_data()
    modpacks = data.get("modpacks", {})

    if name not in modpacks:
        print(f"Modpack '{name}' not found.")
        return

    active_mods = modpacks[name]

    for root, _, files in os.walk(mods_dir):
        for file in files:
            if file.endswith(".otr") or file.endswith(".o2r"):
                path = os.path.join(root, file)
                set_mod_enabled(path, enable=False)

    for mod_rel_path in active_mods:
        full_path = os.path.join(mods_dir, mod_rel_path)

        if os.path.exists(full_path):
            continue

        base, _ = os.path.splitext(full_path)
        candidates = [base + ".disabled", base + ".di2abled"]

        for candidate in candidates:
            if os.path.exists(candidate):
                set_mod_enabled(candidate, enable=True)
                break
