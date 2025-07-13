import os
import sys
import json
import zipfile
from tkinter import filedialog, messagebox
import threading

if getattr(sys, 'frozen', False):
    # exe packagé
    base_path = os.path.dirname(sys.executable)
else:
    # mode script python
    base_path = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(base_path, "saildeck.data")

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Error reading data", f"Can't load data: {e}")
        return None

def export_selected_modpack(window, status_var):
    export_path = filedialog.asksaveasfilename(
        defaultextension=".zip",
        filetypes=[("ZIP file", "*.zip")],
        title="Export modpack as..."
    )
    if not export_path:
        return

    def update_status(text):
        window.after(0, lambda: status_var.set(text))

    def export_task():
        data = load_data()
        if data is None:
            update_status("❌ Error: Can't load data.")
            return

        modpack_name = window.selected_modpack
        if not modpack_name or modpack_name == "New mods profile...":
            update_status("❌ Error: Choose a valid modpack.")
            return

        mod_paths = data.get("modpacks", {}).get(modpack_name)
        if not mod_paths:
            update_status(f"❌ Error: Can't find modpack {modpack_name}")
            return

        game_path = data.get("game_path", "")
        mods_root = os.path.join(game_path, "mods")

        update_status(f"📦 Exporting modpack '{modpack_name}' ...")

        try:
            # Trier les chemins relatifs complets (dossiers + fichiers) par ordre alphabétique
            sorted_mods = sorted(mod_paths, key=lambda p: p.lower())

            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i, mod_rel_path in enumerate(sorted_mods):
                    mod_full_path = os.path.join(mods_root, mod_rel_path)
                    if os.path.isfile(mod_full_path):
                        base_name = os.path.basename(mod_full_path)
                        prefix = f"{i:04d}-"  # Ex: 0000-, 0001-, ...
                        arcname = prefix + base_name
                        zipf.write(mod_full_path, arcname)
                        update_status(f"✅ Exported ({i+1}/{len(sorted_mods)}) : {arcname}")
                    else:
                        update_status(f"⚠️ Can't find files: {mod_rel_path}")

            update_status(f"✅ Finished export: '{modpack_name}'")
        except Exception as e:
            update_status(f"❌ Error exporting: {e}")

    threading.Thread(target=export_task, daemon=True).start()

def import_modpack(window):
    if not hasattr(window, "mods_dir") or not os.path.isdir(window.mods_dir):
        messagebox.showerror("Error", "Invalid mods folder in GUI context.")
        return

    filepath = filedialog.askopenfilename(
        title="Select a modpack to import",
        filetypes=[("Modpack ZIP", "*.zip")],
    )
    if not filepath:
        window.status_var.set("⚠️ Import cancelled.")
        return

    if not filepath.lower().endswith(".zip"):
        window.status_var.set("❌ Invalid file type (must be .zip).")
        return

    modpack_name = os.path.splitext(os.path.basename(filepath))[0]
    target_dir = os.path.join(window.mods_dir, modpack_name)

    if os.path.exists(target_dir):
        confirm = messagebox.askyesno("Overwrite?", f"The folder '{modpack_name}' already exists. Overwrite it?")
        if not confirm:
            window.status_var.set("⚠️ Import cancelled (folder already exists).")
            return
        import shutil
        shutil.rmtree(target_dir)

    os.makedirs(target_dir, exist_ok=True)

    def import_task():
        try:
            with zipfile.ZipFile(filepath, 'r') as zipf:
                members = zipf.namelist()
                total = len(members)
                for i, member in enumerate(members, 1):
                    # Extract single file/folder
                    zipf.extract(member, target_dir)

                    # Mise à jour status
                    display_name = os.path.basename(member.rstrip('/\\'))
                    if display_name:  # ignore empty names (folders usually end with /)
                        window.after(0, lambda text=f"📥 Importé ({i}/{total}) : {display_name}": window.status_var.set(text))
                        # Refresh mod list after each file extracted
                        window.after(0, window.refresh_mod_list)

            window.after(0, lambda: window.status_var.set(f"✅ Import terminé dans '{modpack_name}/'"))
            window.after(0, lambda: messagebox.showinfo("Import réussi", f"Modpack '{modpack_name}' importé avec succès."))
        except Exception as e:
            window.after(0, lambda: window.status_var.set(f"❌ Import failed: {e}"))
            window.after(0, lambda: messagebox.showerror("Import Error", str(e)))

    threading.Thread(target=import_task, daemon=True).start()