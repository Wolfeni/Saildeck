import os
import tkinter as tk
from tkinter import filedialog, messagebox
from gui import ModManagerGUI
from utils import get_game_path, set_game_path, is_valid_game_dir
import time


def ask_game_path():
    """Demande à l'utilisateur de sélectionner le dossier du jeu."""
    root = tk.Tk()
    root.withdraw()
    selected_path = filedialog.askdirectory(title="Sélectionner le dossier du jeu")
    root.destroy()

    if selected_path and is_valid_game_dir(selected_path):
        set_game_path(selected_path)
        time.sleep(0.1)
        main()
    else:
        messagebox.showerror("Erreur", "Dossier invalide. L'application va se fermer.")
        exit(1)

def main():
    game_path = get_game_path()

    if not game_path or not is_valid_game_dir(game_path):
        ask_game_path()
        return

    app = ModManagerGUI(game_path)
    app.mainloop()

if __name__ == "__main__":
    main()
