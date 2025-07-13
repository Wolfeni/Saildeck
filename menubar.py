from tkinter import Menu
import about
import settings_window
import export_modpacks

def init_menubar(window):
    menubar = Menu(window)

    # === Saildeck menu ===
    saildeck_menu = Menu(menubar, tearoff=0)
    saildeck_menu.add_command(label="Open mods folder", command=window.open_mods_folder)
    saildeck_menu.add_command(label="Refresh mods list", command=window.refresh_mod_list)
    menubar.add_cascade(label="Saildeck", menu=saildeck_menu)

    # === Option menu ===
    option_menu = Menu(menubar, tearoff=0)
    option_menu.add_command(label="Settings", command=lambda: settings_window.show_settings(window))
    option_menu.add_separator()
    option_menu.add_command(label="Export Modpack", command=lambda: export_modpacks.export_selected_modpack(window, window.status_var))
    option_menu.add_command(label="Import Modpack", command=lambda: export_modpacks.import_modpack(window))
    menubar.add_cascade(label="Option", menu=option_menu)

    # === About menu ===
    help_menu = Menu(menubar, tearoff=0)
    help_menu.add_command(label="Credits", command=lambda: about.show_about_window(window))
    menubar.add_cascade(label="About", menu=help_menu)

    window.config(menu=menubar)
