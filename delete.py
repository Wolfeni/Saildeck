import os
from tkinter import messagebox
from send2trash import send2trash

def delete_mod(path, refresh_callback=None, status_callback=None):
    """
    Supprime le mod ou dossier donné, avec confirmation.
    refresh_callback : fonction à appeler pour rafraîchir l'UI après suppression
    status_callback : fonction pour mettre à jour le status (ex: lambda texte: window.status_var.set(texte))
    """
    if not os.path.exists(path):
        messagebox.showerror("Error", f"The path does not exist:\n{path}")
        if status_callback:
            status_callback(f"❌ Le chemin n'existe pas: {path}")
        return False

    confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete '{os.path.basename(path)}'?")
    if not confirm:
        if status_callback:
            status_callback("⚠️ Suppression annulée.")
        return False

    try:
        send2trash(path)
        if status_callback:
            status_callback(f"✅ Deleted '{os.path.basename(path)}'")
        if refresh_callback:
            refresh_callback()
        return True
    except Exception as e:
        if status_callback:
            status_callback(f"❌ Failed to delete: {e}")
        messagebox.showerror("Error", f"Failed to delete:\n{e}")
        return False
