import sys
import os
from gui import ModManagerGUI
from utils import get_game_path, set_game_path, is_valid_game_dir, init_settings_file
from check_version import prompt_and_update_if_needed
import time
import tkinter as tk
from tkinter import filedialog

def ask_game_path():
    root = tk.Tk()
    root.withdraw()  # Ne pas afficher la fenêtre principale
    selected_path = filedialog.askdirectory(title="Select Ship of Harkinian folder")
    root.destroy()

    if selected_path and os.path.isdir(selected_path) and is_valid_game_dir(selected_path):
        set_game_path(selected_path)
        time.sleep(0.1)
        return selected_path
    else:
        print("❌ Selected folder doesn't contain 'soh.exe'.")
        sys.exit(1)


def main():
    init_settings_file()
    # ✅ Vérification de mise à jour (plus de parent/root)
    prompt_and_update_if_needed()

    # ✅ Lecture du chemin du jeu
    game_path = get_game_path()
    if not game_path or not is_valid_game_dir(game_path):
        game_path = ask_game_path()
        if not game_path:
            return
        set_game_path(game_path)

    # ✅ Lancement de l'application principale
    app = ModManagerGUI(game_path)
    app.mainloop()

if __name__ == "__main__":
    main()
