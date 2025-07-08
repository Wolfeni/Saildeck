import os
import sys
import subprocess
import threading
import ttkbootstrap as tb
import time
from ttkbootstrap.constants import *
from tkinter import messagebox, PhotoImage
from PIL import Image, ImageTk
from mod_manager import load_mods, toggle_mod_state, delete_mod, toggle_mods_in_folder
from utils import get_mods_folder
from menubar import init_menubar

class ModManagerGUI(tb.Window):
    def __init__(self, game_dir):
        super().__init__(themename="darkly")
        self.title("Saildeck — Mod manager for Ship of Harkinian")
        self.geometry("600x600")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        icon_path = os.path.join(os.path.dirname(__file__), "icon", "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.icons = {
            "check": PhotoImage(file=os.path.join(self.assets_dir, "check.png")),
            "cross": PhotoImage(file=os.path.join(self.assets_dir, "cross.png")),
            "dash": PhotoImage(file=os.path.join(self.assets_dir, "dash.png")),
        }

        # 🔽 Chargement du petit logo pour affichage à droite
        self.logo_small_img = None
        logo_path = os.path.join(self.assets_dir, "logo_small.png")
        if os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)
                pil_image = pil_image.resize((int(32 * pil_image.width / pil_image.height), 32), Image.LANCZOS)
                self.logo_small_img = ImageTk.PhotoImage(pil_image)
            except Exception as e:
                print(f"[!] Erreur chargement logo_small.png : {e}")

        self.tree_images = {}
        self.game_dir = game_dir
        self.mods_dir = get_mods_folder(game_dir)
        self.mods = []

        self._last_click_time = 0
        init_menubar(self)
        self.create_widgets()

        self.after(100, self.force_style_reload)
        self.after(100, self.refresh_mod_list)

    def on_close(self):
        self.destroy()
        os._exit(0)

    def force_style_reload(self):
        try:
            style = tb.Style()
            style.theme_use("darkly")
            style.configure("TButton", font=("Segoe UI", 10))
            style.configure("Treeview", rowheight=28)
            self.update_idletasks()
        except Exception as e:
            print(f"[!] Erreur lors du rechargement du thème : {e}")

    def create_widgets(self):
        # === Conteneur principal supérieur ===
        top_container = tb.Frame(self)
        top_container.pack(side="top", fill="x", padx=10, pady=(5, 0))

        # === Ligne du haut avec logo à gauche et Launch game à droite ===
        topbar = tb.Frame(top_container)
        topbar.pack(side="top", fill="x")

        # Logo à gauche
        if self.logo_small_img:
            tb.Label(topbar, image=self.logo_small_img).pack(side="left", padx=(0, 10))

        # Launch game à droite
        tb.Button(topbar, text="🚀 Launch game", command=self.launch_game, bootstyle="success").pack(side="right", padx=5)

        # === Arbre des mods ===
        self.tree = tb.Treeview(self, show="tree", selectmode="browse", bootstyle="success")
        self.tree.heading("#0", text="Nom")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self._last_item_clicked = None
        self._last_click_time = 0

        # === Bas de fenêtre ===
        bottom = tb.Frame(self)
        bottom.pack(side="bottom", fill="x", pady=10)

        tb.Button(bottom, text="⚙️ Toggle state", command=self.toggle_selected_mod, bootstyle="warning").pack(side="left", padx=10)
        tb.Button(bottom, text="🗑️ Delete", command=self.delete_selected_mod, bootstyle="danger").pack(side="left", padx=10)
    
    def on_tree_double_click(self, event):
        # Empêche Treeview d'ouvrir/fermer les dossiers automatiquement
        return "break"

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        current_time = time.time()
        DOUBLE_CLICK_DELAY = 0.4  # secondes

        if self._last_item_clicked == item_id and (current_time - self._last_click_time) < DOUBLE_CLICK_DELAY:
            self._last_item_clicked = None
            self.handle_tree_toggle(item_id)
        else:
            self._last_click_time = current_time
            self._last_item_clicked = item_id

    def handle_tree_toggle(self, item_id):
        abs_path = os.path.join(self.mods_dir, item_id)
        is_dir = os.path.isdir(abs_path)
        rel_base = os.path.splitext(item_id)[0] if not is_dir else item_id
        expanded = self.get_all_expanded_nodes()

        try:
            if is_dir:
                toggle_mods_in_folder(abs_path)
            elif os.path.isfile(abs_path):
                toggle_mod_state(abs_path)
            else:
                return
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.refresh_mod_list()

        # Restaurer les dossiers ouverts
        for iid in expanded:
            if self.tree.exists(iid):
                self.tree.item(iid, open=True)

        # Restaurer la sélection
        if is_dir:
            if self.tree.exists(rel_base):
                self.tree.selection_set(rel_base)
                self.tree.see(rel_base)
        else:
            for mod in self.mods:
                rel_path = os.path.relpath(mod["path"], self.mods_dir)
                if os.path.splitext(rel_path)[0] == rel_base:
                    iid = os.path.normpath(rel_path)
                    if self.tree.exists(iid):
                        self.tree.selection_set(iid)
                        self.tree.see(iid)
                    break

    def get_folder_icon(self, path):
        enabled_exts = {".otr", ".o2r"}
        disabled_exts = {".disabled", ".di2abled"}
        has_enabled = has_disabled = False
        for root, _, files in os.walk(path):
            for f in files:
                if any(f.endswith(ext) for ext in disabled_exts):
                    has_disabled = True
                elif any(f.endswith(ext) for ext in enabled_exts):
                    has_enabled = True
        if has_enabled and has_disabled:
            return self.icons["dash"]
        elif has_enabled:
            return self.icons["check"]
        elif has_disabled:
            return self.icons["cross"]
        return ""

    def refresh_mod_list(self):
        expanded = self.get_all_expanded_nodes()
        self.tree.delete(*self.tree.get_children())

        self.mods = load_mods(self.mods_dir)
        self.tree_images = {}
        node_map = {}

        for mod in self.mods:
            rel_path = os.path.relpath(mod["path"], self.mods_dir)
            parts = rel_path.split(os.sep)
            parent = ""
            full_path = ""

            for i, part in enumerate(parts):
                full_path = os.path.join(full_path, part)
                is_leaf = (i == len(parts) - 1)

                # ✅ Si c’est un fichier (dernier niveau), on garde l’extension dans l’ID
                if is_leaf:
                    node_id = os.path.normpath(rel_path)
                else:
                    node_id = os.path.normpath(os.path.join(*parts[:i + 1]))

                if node_id not in node_map:
                    if is_leaf:
                        icon_type = "check" if mod["enabled"] else "cross"
                        icon = self.icons.get(icon_type)
                        if icon:
                            self.tree_images[node_id] = icon
                        name, _ = os.path.splitext(part)
                        label = f" | 📄 {name}"
                    else:
                        folder_path = os.path.join(self.mods_dir, node_id)
                        folder_icon = self.get_folder_icon(folder_path)
                        if folder_icon:
                            self.tree_images[node_id] = folder_icon
                        label = f" | 📁 {part}"

                    node = self.tree.insert(
                        parent, "end",
                        iid=node_id,
                        text=label,
                        image=self.tree_images.get(node_id, "")
                    )
                    node_map[node_id] = node

                parent = node_id

        for iid in expanded:
            if self.tree.exists(iid):
                self.tree.item(iid, open=True)


    def get_all_expanded_nodes(self):
        def recurse(node):
            result = set()
            if self.tree.item(node, "open"):
                result.add(node)
                for child in self.tree.get_children(node):
                    result.update(recurse(child))
            return result

        all_expanded = set()
        for child in self.tree.get_children():
            all_expanded.update(recurse(child))
        return all_expanded

    def get_selected_mod(self):
        selection = self.tree.selection()
        if not selection:
            return None
        node_id = selection[0]
        base_path = os.path.join(self.mods_dir, node_id)

        for ext in [".otr", ".o2r", ".disabled", ".di2abled"]:
            full_path = base_path + ext
            if os.path.isfile(full_path):
                return full_path
        return None

    def toggle_selected_mod(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No mod selected", "Select a mod or a folder.")
            return

        node_id = selection[0]
        abs_path = os.path.join(self.mods_dir, node_id)

        is_dir = os.path.isdir(abs_path)
        rel_base = os.path.splitext(node_id)[0] if not is_dir else node_id
        expanded = self.get_all_expanded_nodes()

        try:
            if is_dir:
                toggle_mods_in_folder(abs_path)
            else:
                toggle_mod_state(abs_path)
        except Exception as e:
            messagebox.showerror("Error", f"Can't change mod state:\n{e}")
            return

        self.refresh_mod_list()

        # Restaurer nœuds ouverts
        for iid in expanded:
            if self.tree.exists(iid):
                self.tree.item(iid, open=True)

        # 🔁 Restaurer la sélection
        if is_dir:
            # Le dossier est identifié par son chemin relatif brut
            if self.tree.exists(rel_base):
                self.tree.selection_set(rel_base)
                self.tree.see(rel_base)
        else:
            # Rechercher le fichier avec le même "base path" peu importe son extension
            for mod in self.mods:
                rel_path = os.path.relpath(mod["path"], self.mods_dir)
                if os.path.splitext(rel_path)[0] == rel_base:
                    iid = os.path.normpath(rel_path)
                    if self.tree.exists(iid):
                        self.tree.selection_set(iid)
                        self.tree.see(iid)
                    break

    def delete_selected_mod(self):
        path = self.get_selected_mod()
        if not path:
            messagebox.showwarning("No mod selected", "Select a mod to delete.")
            return
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete this mod?")
        if confirm:
            delete_mod(path)
            self.refresh_mod_list()

    def open_mods_folder(self):
        os.startfile(self.mods_dir)

    def launch_game(self):
        exe_path = os.path.join(self.game_dir, "soh.exe")
        if not os.path.isfile(exe_path):
            messagebox.showerror("Error", "Can't find 'soh.exe'.")
            return

        def run_and_quit():
            subprocess.Popen(exe_path, cwd=self.game_dir, close_fds=True)
            self.destroy()
            sys.exit(0)

        threading.Thread(target=run_and_quit, daemon=True).start()

def launch_gui(game_dir):
    app = ModManagerGUI(game_dir)
    app.mainloop()
