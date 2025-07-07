import os
import webbrowser
from tkinter import Toplevel, Label, Frame, Button, Canvas
from PIL import Image, ImageTk
import ttkbootstrap as tb
from version import __version__

def show_about_window(parent):
    win = Toplevel(parent)
    win.title("About Saildeck")
    win.geometry("420x360")
    win.resizable(False, False)
    win.configure(bg="#222222")
    win.transient(parent)
    win.grab_set()  # Rend la fenêtre modale

    # === Définir l'icône ===
    icon_path = os.path.join(os.path.dirname(__file__), "icon", "icon.ico")
    if os.path.exists(icon_path):
        try:
            win.iconbitmap(icon_path)
        except Exception as e:
            print(f"[!] Erreur chargement icon.ico : {e}")

    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    logo_path = os.path.join(assets_dir, "logo_name.png")

    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 210
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 180
    win.geometry(f"+{x}+{y}")

    # === Logo Saildeck via Canvas (pas de fond parasite) ===
    if os.path.exists(logo_path):
        try:
            pil_img = Image.open(logo_path)
            pil_img = pil_img.resize((300, int(pil_img.height * 300 / pil_img.width)), Image.LANCZOS)
            logo_img = ImageTk.PhotoImage(pil_img)

            canvas = Canvas(win, width=300, height=logo_img.height(), bg="#222222", highlightthickness=0, bd=0)
            canvas.create_image(0, 0, anchor="nw", image=logo_img)
            canvas.image = logo_img
            canvas.pack(pady=(20, 10))
        except Exception as e:
            print(f"[!] Erreur chargement logo_name.png : {e}")

    # === Texte centré ===
    Label(
        win,
        text="Saildeck Mod Manager",
        font=("Segoe UI", 14, "bold"),
        fg="#ffffff",
        bg="#222222"
    ).pack(pady=(0, 5))

    # === Lien GitHub cliquable ===
    link = Label(
        win,
        text="Visit GitHub page",
        font=("Segoe UI", 10, "underline"),
        fg="#4da6ff",
        bg="#222222",
        cursor="hand2"
    )
    link.pack(pady=(0, 15))
    link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Wolfeni/Saildeck"))

    # === Remerciement personnalisé ===
    thanks_frame = Frame(win, bg="#222222")
    thanks_frame.pack(pady=(0, 10))

    thanks_label = Label(
        thanks_frame,
        text="Thanks Purple Hato for the help and for",
        font=("Segoe UI", 9),
        fg="#bbbbbb",
        bg="#222222"
    )
    thanks_label.pack(side="left")

    shiploader_link = Label(
        thanks_frame,
        text="Shiploader",
        font=("Segoe UI", 9, "underline"),
        fg="#4da6ff",
        bg="#222222",
        cursor="hand2"
    )
    shiploader_link.pack(side="left")
    shiploader_link.bind("<Button-1>", lambda e: webbrowser.open("https://gamebanana.com/tools/16326"))

    # === Bouton Fermer ===
    Button(
        win,
        text="Close",
        command=win.destroy,
        font=("Segoe UI", 10),
        bg="#2e2e2e",
        fg="#ffffff",
        activebackground="#3c3c3c",
        activeforeground="#ffffff",
        relief="flat",
        padx=10,
        pady=5
    ).pack(pady=(0, 10))
    
    version_label = Label(
        win,
        text=f"v{__version__}",
        font=("Segoe UI", 8),
        fg="#888888",
        bg="#222222"
    )
    version_label.place(x=10, y=335)