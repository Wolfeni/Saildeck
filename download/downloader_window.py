import os
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

import threading
from download.gamebanana.api import get_soh_mod_ids
from download.gamebanana.scraper import get_mod_details_from_id
from download.gamebanana.widgets import render_mod_card

# -------- Tooltip minimal --------
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.label = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)
        widget.bind("<Motion>", self.move_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        self.tip_window = tw = tb.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)
        self.label = tb.Label(
            tw,
            text=self.text,
            background="#2b2b2b",
            foreground="#ffffff",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padding=5
        )
        self.label.pack()
        self.move_tip(event)

    def move_tip(self, event=None):
        if self.tip_window:
            x = self.widget.winfo_pointerx() + 12
            y = self.widget.winfo_pointery() + 12
            self.tip_window.wm_geometry(f"+{x}+{y}")

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

# -------- Fenêtre principale --------
def open_downloader_window(parent):
    window = tb.Toplevel(parent)
    window.title("Download Mods")
    window.geometry("700x450")
    window.resizable(False, False)

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    icon_path = os.path.join(root_dir, "icon", "icon_working.ico")
    if os.path.exists(icon_path):
        window.iconbitmap(icon_path)
    else:
        print("[!] Icône non trouvée :", icon_path)

    main_frame = tb.Frame(window)
    main_frame.pack(fill="both", expand=True)

    assets_dir = os.path.join(root_dir, "assets")

    # 🖼️ Logos
    logos = {}
    logo_files = {
        "Gamebanana": "gb_logo.png",
        "Thunderstore": "th_logo.png"
    }

    for name, filename in logo_files.items():
        path = os.path.join(assets_dir, filename)
        if os.path.exists(path):
            img = Image.open(path).resize((40, 40), Image.LANCZOS)
            logos[name] = ImageTk.PhotoImage(img)
        else:
            print(f"[!] Logo manquant : {filename}")

    # 🟦 Barre latérale
    sidebar = tb.Frame(main_frame, width=150)
    sidebar.pack(side="left", fill="y", padx=5, pady=5)

    tb.Label(sidebar, text="Mods websites", font=("Segoe UI", 11, "bold")).pack(pady=(0, 10))

    selected_source = {"value": None}
    mod_source_buttons = {}

    # ➕ Zone dynamique à droite
    content_area = tb.Frame(main_frame)
    content_area.pack(side="right", fill="both", expand=True, padx=5, pady=5)

    dynamic_frame = tb.Frame(content_area)
    dynamic_frame.pack(fill="both", expand=True)

    def clear_dynamic_content():
        for widget in dynamic_frame.winfo_children():
            widget.destroy()

    def select_source(name):
        for source_name, button in mod_source_buttons.items():
            button.config(bootstyle="success" if source_name == name else "secondary")
        selected_source["value"] = name
        print(f"Sélectionné : {name}")
        clear_dynamic_content()

        if name == "Gamebanana":
            def threaded_load_mods():
                mod_ids = get_soh_mod_ids(limit=15)
                for mod_id in mod_ids:
                    mod = get_mod_details_from_id(mod_id)
                    dynamic_frame.after(0, lambda m=mod: render_mod_card(dynamic_frame, m))

            threading.Thread(target=threaded_load_mods, daemon=True).start()
        else:
            tb.Label(dynamic_frame, text=f"{name} - coming soon", font=("Segoe UI", 10)).pack(pady=20)

    for name in logo_files:
        logo = logos.get(name)
        if logo:
            btn = tb.Button(
                sidebar,
                image=logo,
                command=lambda s=name: select_source(s),
                bootstyle="secondary",
                cursor="hand2"
            )
            btn.image = logo
            btn.pack(pady=5)
            ToolTip(btn, text=name)
            mod_source_buttons[name] = btn

    # ➖ Séparateur vertical
    separator = tb.Separator(main_frame, orient=VERTICAL)
    separator.pack(side="left", fill="y", padx=0, pady=10)

    # Message initial
    tb.Label(dynamic_frame, text="Select mods website", font=("Segoe UI", 10)).pack(pady=20)
