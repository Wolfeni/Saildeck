import os
import sys
import subprocess
import threading
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, PhotoImage
from PIL import Image, ImageTk
from mod_manager import load_mods, toggle_mod_state, delete_mod, toggle_mods_in_folder
from utils import get_mods_folder

class ModManagerGUI(tb.Window):
    def __init__(self, game_dir):
        super().__init__(themename="darkly")
        self.title("Saildeck — Mod manager for Ship of Harkinian")
        self.geometry("600x750")
        self.resizable(True, True)
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

        self.root = self
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))

        self.tree_images = {}

        self.game_dir = game_dir
        self.mods_dir = get_mods_folder(game_dir)
        self.mods = []

        self.after(100, self.create_widgets)
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
        # === Logo en haut ===
        logo_path = os.path.join(self.assets_dir, "logo_name.png")
        if os.path.exists(logo_path):
            try:
                pil_image = Image.open(logo_path)
                pil_image = pil_image.resize((512, int(512 * pil_image.height / pil_image.width)))
                self.logo_img = ImageTk.PhotoImage(pil_image)
                logo_label = tb.Label(self, image=self.logo_img)
                logo_label.pack(pady=(10, 5))
            except Exception as e:
                print(f"[!] Erreur chargement logo : {e}")

        # === Toolbar ===
        toolbar = tb.Frame(self)
        toolbar.pack(side="top", fill="x", padx=10, pady=5)

        tb.Button(toolbar, text="🔄 Rafraîchir", command=self.refresh_mod_list, bootstyle="success").pack(side="left", padx=5)
        tb.Button(toolbar, text="📁 Ouvrir Mods", command=self.open_mods_folder, bootstyle="success").pack(side="left", padx=5)
        tb.Button(toolbar, text="🚀 Lancer le jeu", command=self.launch_game, bootstyle="success").pack(side="right", padx=5)

        # === Treeview ===
        self.tree = tb.Treeview(self, show="tree", selectmode="browse", bootstyle="success")
        self.tree.heading("#0", text="Nom")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.on_treeview_double_click)

        # === Bas de fenêtre ===
        bottom = tb.Frame(self)
        bottom.pack(side="bottom", fill="x", pady=10)

        tb.Button(bottom, text="🟢 Activer / ❌ Désactiver", command=self.toggle_selected_mod, bootstyle="warning").pack(side="left", padx=10)
        tb.Button(bottom, text="🗑️ Supprimer", command=self.delete_selected_mod, bootstyle="danger").pack(side="left", padx=10)

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

    def on_treeview_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        abs_path = os.path.join(self.mods_dir, item_id)

        if os.path.isdir(abs_path):
            try:
                self.tree.item(item_id, open=False)
                toggle_mods_in_folder(abs_path)
                self.refresh_mod_list()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
            return "break"

        self.toggle_selected_mod()
        return "break"

    def refresh_mod_list(self):
        self.tree.delete(*self.tree.get_children())
        expanded = set()
        for item in self.tree.get_children():
            expanded.update(self.get_expanded_nodes(item))

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

    def get_expanded_nodes(self, node):
        result = set()
        if self.tree.item(node, "open"):
            result.add(node)
            for child in self.tree.get_children(node):
                result.update(self.get_expanded_nodes(child))
        return result

    def get_selected_mod(self):
        selection = self.tree.selection()
        if not selection:
            return None
        node_id = selection[0]
        base_path = os.path.join(self.mods_dir, node_id)

        # Recherche l'extension existante
        for ext in [".otr", ".o2r", ".disabled", ".di2abled"]:
            full_path = base_path + ext
            if os.path.isfile(full_path):
                return full_path
        return None

    def toggle_selected_mod(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aucun mod sélectionné", "Sélectionnez un mod ou un dossier.")
            return

        node_id = selection[0]
        abs_path = os.path.join(self.mods_dir, node_id)

        try:
            if os.path.isdir(abs_path):
                # On applique le changement à tous les mods du dossier sélectionné
                toggle_mods_in_folder(abs_path)
            else:
                # On bascule l'état du fichier individuel
                toggle_mod_state(abs_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de changer l'état du mod :\n{e}")
        else:
            self.refresh_mod_list()

    def delete_selected_mod(self):
        path = self.get_selected_mod()
        if not path:
            messagebox.showwarning("Aucun mod sélectionné", "Sélectionnez un mod à supprimer.")
            return
        confirm = messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce mod ?")
        if confirm:
            delete_mod(path)
            self.refresh_mod_list()

    def open_mods_folder(self):
        os.startfile(self.mods_dir)

    def launch_game(self):
        exe_path = os.path.join(self.game_dir, "soh.exe")
        if not os.path.isfile(exe_path):
            messagebox.showerror("Erreur", "Impossible de trouver 'soh.exe'.")
            return

        def run_and_quit():
            subprocess.Popen(exe_path, cwd=self.game_dir, close_fds=True)
            self.destroy()
            sys.exit(0)

        threading.Thread(target=run_and_quit, daemon=True).start()

def launch_gui(game_dir):
    app = ModManagerGUI(game_dir)
    app.mainloop()
