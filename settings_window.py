import tkinter as tk
from tkinter import ttk
import json
import os

SETTINGS_FILE = "saildeck.data"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

def show_settings(parent):
    win = tk.Toplevel(parent)

    # Définir l'icône de la fenêtre de réglages
    icon_path = os.path.join(os.path.dirname(__file__), "icon", "icon_question.ico")
    if os.path.exists(icon_path):
        try:
            win.iconbitmap(icon_path)
        except Exception as e:
            print(f"[!] Impossible de charger l’icône : {e}")

    win.title("Settings")
    win.geometry("300x200")

    # Centrer la fenêtre par rapport au parent
    win.update_idletasks()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()
    win_w = win.winfo_width()
    win_h = win.winfo_height()
    pos_x = parent_x + (parent_w // 2) - (win_w // 2)
    pos_y = parent_y + (parent_h // 2) - (win_h // 2)
    win.geometry(f"+{pos_x}+{pos_y}")

    win.resizable(False, False)

    settings = load_settings()

    var_skip_update = tk.BooleanVar(value=settings.get("skip_update", False))
    var_enable_altassets = tk.BooleanVar(value=settings.get("enable_altassets", True))

    ttk.Checkbutton(
        win,
        text="Skip update check",
        variable=var_skip_update
    ).pack(pady=(15, 5))

    ttk.Checkbutton(
        win,
        text="Auto-enable AltAssets when mods are active",
        variable=var_enable_altassets
    ).pack(pady=5)

    def on_close():
        settings["skip_update"] = var_skip_update.get()
        settings["enable_altassets"] = var_enable_altassets.get()
        save_settings(settings)
        win.destroy()

    ttk.Button(win, text="Close", command=on_close).pack(pady=10)
