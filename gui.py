import os
import ttkbootstrap as tb
import time
from ttkbootstrap.constants import *
from tkinter import messagebox, PhotoImage, simpledialog
from PIL import Image, ImageTk
from mod_manager import load_mods, toggle_mod_state, toggle_mods_in_folder
from utils import get_mods_folder
from menubar import init_menubar
from launch import launch_game
from download.downloader_window import open_downloader_window
from save_modpacks import save_modpack, list_modpacks, load_modpack
from delete import delete_mod

def normalize_path(path):
    # Normalise le chemin Windows, remplace les slashes par backslashes
    path = os.path.normpath(path)
    return path

class ModManagerGUI(tb.Window):
    def __init__(self, game_dir):
        super().__init__(themename="darkly")
        self.title("Saildeck — Mod manager for Ship of Harkinian")
        self.geometry("700x600")
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
        self.status_var = tb.StringVar(value="Ready")
        self.create_widgets()

        self.after(100, self.force_style_reload)
        self.after(100, self.refresh_mod_list)

        self.lift()
        self.attributes('-topmost', True)
        self.after(500, lambda: self.attributes('-topmost', False))

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
        top_container = tb.Frame(self)
        top_container.pack(side="top", fill="x", padx=10, pady=(5, 0))

        topbar = tb.Frame(top_container)
        topbar.pack(side="top", fill="x")

        if self.logo_small_img:
            tb.Label(topbar, image=self.logo_small_img).pack(side="left", padx=(0, 10))

        tb.Button(topbar, text="🚀 Launch game", command=self.launch_game, bootstyle="success", cursor="hand2").pack(side="right", padx=5)

        self.tree = tb.Treeview(self, show="tree", selectmode="browse", bootstyle="success")
        self.tree.heading("#0", text="Nom")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Motion>", self.on_tree_hover)
        self._last_item_clicked = None
        self._last_click_time = 0

        # --- bottom container pour regrouper boutons + status ---
        bottom_container = tb.Frame(self)
        bottom_container.pack(side="bottom", fill="x")

        bottom = tb.Frame(bottom_container)
        bottom.pack(side="top", fill="x", pady=5)

        tb.Button(bottom, text="⚙️ Toggle state", command=self.toggle_selected_mod, bootstyle="warning", cursor="hand2").pack(side="left", padx=10)
        tb.Button(bottom, text="🗑️ Delete", command=self.delete_selected_mod, bootstyle="danger", cursor="hand2").pack(side="left", padx=10)

        # Groupe "Mods profile" dans topbar (avec message à droite)
        modpack_group = tb.Frame(topbar)
        modpack_group.pack(side="left", padx=(10, 10), expand=True, fill="x")

        profile_row = tb.Frame(modpack_group)
        profile_row.pack(side="left")

        tb.Label(profile_row, text="Mods profile:").pack(side="left", padx=(0, 5))

        self.modpack_combobox = tb.Combobox(profile_row, state="readonly", width=20)
        self.modpack_combobox.pack(side="left", padx=(0, 5))

        style = tb.Style()
        style.configure("Tiny.TButton", font=("Segoe UI", 8))

        save_btn = tb.Button(profile_row, text="Save", command=self.prompt_and_save_modpack,
                            bootstyle="secondary", cursor="hand2", width=6, style="Tiny.TButton")
        save_btn.pack(side="left", padx=(0, 3))

        load_btn = tb.Button(profile_row, text="Load", command=self.prompt_and_load_modpack,
                            bootstyle="secondary", cursor="hand2", width=6, style="Tiny.TButton")
        load_btn.pack(side="left", padx=(0, 10))

        #tb.Button(
        #    bottom,
        #    text="⬇️ Download Mods",
        #    command=lambda: open_downloader_window(self),
        #    bootstyle="primary",
        #    cursor="hand2"
        #).pack(side="right", padx=10)

        self.tree.bind("<Delete>", self.on_delete_key)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_open_close)
        self.tree.bind("<<TreeviewClose>>", self.on_tree_open_close)

        # Barre d'état (status bar) **en bas du bottom_container**
        status_bar = tb.Label(bottom_container, textvariable=self.status_var, anchor="w", font=("Segoe UI", 9), padding=5)
        status_bar.pack(side="bottom", fill="x")

        self.refresh_modpack_list()


    def prompt_and_save_modpack(self):
        selected = self.modpack_combobox.get()
        if selected == "──────────":
            self.status_var.set("⚠️ Please select a valid mod profile.")
            return

        if selected == "New mods profile...":
            name = simpledialog.askstring("Create New Modpack", "Enter a name for your new modpack:")
            if not name:
                self.status_var.set("⚠️ Modpack creation cancelled.")
                return
        else:
            name = selected
            confirm = messagebox.askyesno("Overwrite Modpack", f"Modpack '{name}' exists. Overwrite?")
            if not confirm:
                self.status_var.set("⚠️ Save cancelled.")
                return

        try:
            save_modpack(name, self.mods_dir)
            self.refresh_modpack_list()
            self.status_var.set(f"✅ Saved '{name}'")
            self.modpack_combobox.set(name)
        except Exception as e:
            self.status_var.set(f"❌ Save failed: {e}")

    def prompt_and_load_modpack(self):
        selected = self.modpack_combobox.get()
        if selected == "──────────":
            self.status_var.set("⚠️ Please select a valid mod profile.")
            return
        if not selected or selected == "New mods profile...":
            self.status_var.set("⚠️ Select a mod profile first.")
            return
        try:
            load_modpack(selected, self.mods_dir)
            self.refresh_mod_list()
            self.status_var.set(f"✅ Loaded '{selected}'")
        except Exception as e:
            self.status_var.set(f"❌ Load failed: {e}")

    def refresh_modpack_list(self):
        try:
            modpacks = list_modpacks()
            values = ["New mods profile..."] + modpacks
            self.modpack_combobox["values"] = values
            self.modpack_combobox.set("New mods profile...")
        except Exception as e:
            self.status_var.set(f"❌ Failed to load modpacks: {e}")

    def on_tree_hover(self, event):
        element = self.tree.identify("element", event.x, event.y)
        if element == "Treeitem.indicator":
            self.tree.config(cursor="hand2")
        else:
            self.tree.config(cursor="")

    def on_tree_double_click(self, event):
        return "break"

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        current_time = time.time()
        if self._last_item_clicked == item_id and (current_time - self._last_click_time) < 0.4:
            self._last_item_clicked = None
            self.handle_tree_toggle(item_id)
        else:
            self._last_click_time = current_time
            self._last_item_clicked = item_id

    def handle_tree_toggle(self, item_id):
        if item_id == "mods_root":
            # Toggle récursif sur tout le dossier mods
            try:
                toggle_mods_in_folder(self.mods_dir)
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return
        else:
            abs_path = os.path.join(self.mods_dir, item_id)
            is_dir = os.path.isdir(abs_path)
            rel_base = os.path.splitext(item_id)[0] if not is_dir else item_id
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

        expanded = self.get_all_expanded_nodes()
        self.refresh_mod_list()
        for iid in expanded:
            if self.tree.exists(iid):
                self.tree.item(iid, open=True)

        if item_id == "mods":
            # sélectionne le dossier mods et scroll dessus
            if self.tree.exists("mods"):
                self.tree.selection_set("mods")
                self.tree.see("mods")
        else:
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

        # Ajout du dossier racine "mods" (toujours affiché en haut, toujours ouvert)
        root_id = "mods_root"
        root_label = " | 📁 mods"
        # Icône pour dossier "mods" : peut être celle retournée par get_folder_icon
        root_icon = self.get_folder_icon(self.mods_dir)
        if root_icon:
            self.tree_images[root_id] = root_icon

        self.tree.insert("", "end", iid=root_id, text=root_label, image=self.tree_images.get(root_id, ""), open=True)

        # Ajout des mods en enfants de "mods_root"
        for mod in self.mods:
            rel_path = os.path.relpath(mod["path"], self.mods_dir)
            parts = rel_path.split(os.sep)
            parent = root_id  # ici on force comme parent le dossier racine

            full_path = ""

            for i, part in enumerate(parts):
                full_path = os.path.join(full_path, part)
                is_leaf = (i == len(parts) - 1)
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

        # On restaure l'état des noeuds ouverts sauf pour root_id qu'on force ouvert
        for iid in expanded:
            if self.tree.exists(iid) and iid != root_id:
                self.tree.item(iid, open=True)
        # Forcer toujours root_id ouvert
        if self.tree.exists(root_id):
            self.tree.item(root_id, open=True)

    def on_tree_open_close(self, event):
        # Empêche la fermeture du dossier "mods_root"
        item = self.tree.focus()
        if item == "mods_root":
            self.tree.item(item, open=True)  # Forcer ouvert

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
        parts = node_id.replace("/", os.sep).replace("\\", os.sep).split(os.sep)
        abs_path = os.path.join(self.mods_dir, *parts)
        abs_path = os.path.normpath(abs_path)

        if os.path.isdir(abs_path):
            return abs_path
        elif os.path.isfile(abs_path):
            return abs_path
        else:
            for ext in [".otr", ".o2r", ".disabled", ".di2abled"]:
                full_path = abs_path + ext
                if os.path.isfile(full_path):
                    return full_path
        return None

    def toggle_selected_mod(self):
        selection = self.tree.selection()
        if not selection:
            self.status_var.set("⚠️ Select a mod or a folder to toggle.")
            return
        node_id = selection[0]

        try:
            # Le noeud racine est "mods_root" dans refresh_mod_list
            if node_id == "mods_root":
                toggle_mods_in_folder(self.mods_dir)
            else:
                abs_path = os.path.normpath(os.path.join(self.mods_dir, node_id))
                is_dir = os.path.isdir(abs_path)
                if is_dir:
                    toggle_mods_in_folder(abs_path)
                else:
                    toggle_mod_state(abs_path)
        except Exception as e:
            self.status_var.set(f"❌ Can't change mod state: {e}")
            return

        expanded = self.get_all_expanded_nodes()
        self.refresh_mod_list()
        for iid in expanded:
            if self.tree.exists(iid):
                self.tree.item(iid, open=True)

        # Rétablir sélection et scroll
        if node_id == "mods_root":
            if self.tree.exists("mods_root"):
                self.tree.selection_set("mods_root")
                self.tree.see("mods_root")
        else:
            if is_dir:
                if self.tree.exists(node_id):
                    self.tree.selection_set(node_id)
                    self.tree.see(node_id)
            else:
                for mod in self.mods:
                    rel_path = os.path.relpath(mod["path"], self.mods_dir)
                    if os.path.splitext(rel_path)[0] == os.path.splitext(node_id)[0]:
                        iid = os.path.normpath(rel_path)
                        if self.tree.exists(iid):
                            self.tree.selection_set(iid)
                            self.tree.see(iid)
                        break

    def delete_selected_mod(self):
        path = self.get_selected_mod()
        if not path:
            self.status_var.set("⚠️ Select a mod or folder to delete.")
            return

        # Appelle la fonction externe avec callbacks pour UI
        delete_mod(
            path=path,
            refresh_callback=self.refresh_mod_list,
            status_callback=lambda text: self.status_var.set(text)
        )
    
    def on_delete_key(self, event):
        path = self.get_selected_mod()
        if not path:
            self.status_var.set("⚠️ Select a mod or folder to delete.")
            return "break"  # stop propagation

        # Appelle la fonction delete_mod avec callbacks
        from delete import delete_mod  # au cas où ce n'est pas déjà importé

        delete_mod(
            path=path,
            refresh_callback=self.refresh_mod_list,
            status_callback=lambda text: self.status_var.set(text)
        )

        return "break"  # stop propagation de l'événement (évite comportement par défaut)

    def open_mods_folder(self):
        os.startfile(self.mods_dir)

    def launch_game(self):
        try:
            mods_path = os.path.join(self.game_dir, "mods")
            launch_game(self.game_dir, mods_path)
            self.destroy()
        except FileNotFoundError as e:
            self.status_var.set(str(e))
        except Exception as e:
            self.status_var.set(f"Unexpected error: {e}")

    def open_downloader_window(self):
        downloader_window = tb.Toplevel(self)
        downloader_window.title("Download Mods")
        downloader_window.geometry("500x400")
        downloader_window.resizable(False, False)

        label = tb.Label(downloader_window, text="Gestion des mods (provenant de GameBanana...)", font=("Segoe UI", 12))
        label.pack(pady=20)

        tb.Label(downloader_window, text="Fonctionnalité en cours de développement").pack(pady=10)
    
    @property
    def selected_modpack(self):
        return self.modpack_combobox.get()

def launch_gui(game_dir):
    app = ModManagerGUI(game_dir)
    app.mainloop()
