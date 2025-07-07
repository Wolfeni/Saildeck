import tkinter as tk
from tkinter import filedialog, messagebox
from gui import ModManagerGUI
from utils import get_game_path, set_game_path, is_valid_game_dir
from version import __version__
import time


def ask_game_path():
    """Demande à l'utilisateur de sélectionner le dossier du jeu."""
    root = tk.Tk()
    root.withdraw()
    selected_path = filedialog.askdirectory(title="Select your Ship of Harkinian Folder")
    root.destroy()

    if selected_path and is_valid_game_dir(selected_path):
        set_game_path(selected_path)
        time.sleep(0.1)
        main()
    else:
        messagebox.showerror("Error", "Selected folder doesn't caontain 'soh.exe'")
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
