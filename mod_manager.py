import os
from utils import list_mod_files


def toggle_mod_state(mod_path: str):
    """
    Bascule l'état du mod entre activé/désactivé.
    - .o2r <-> .di2abled
    - .otr <-> .disabled
    """
    if mod_path.endswith(".di2abled"):
        new_path = os.path.splitext(mod_path)[0] + ".o2r"
    elif mod_path.endswith(".disabled"):
        new_path = os.path.splitext(mod_path)[0] + ".otr"
    elif mod_path.endswith(".o2r"):
        new_path = os.path.splitext(mod_path)[0] + ".di2abled"
    elif mod_path.endswith(".otr"):
        new_path = os.path.splitext(mod_path)[0] + ".disabled"
    else:
        return  # Ignorer les autres fichiers

    os.rename(mod_path, new_path)


def delete_mod(mod_path: str):
    if os.path.exists(mod_path):
        os.remove(mod_path)


def load_mods(mods_dir: str) -> list:
    mods = []
    files = list_mod_files(mods_dir)

    for path in files:
        is_enabled = not (path.endswith(".disabled") or path.endswith(".di2abled"))
        mods.append({
            "path": path,
            "enabled": is_enabled
        })

    return mods


def find_mods_root(path: str) -> str:
    """
    Remonte jusqu’au dossier "mods".
    """
    current = os.path.abspath(path)
    while True:
        if os.path.basename(current) == "mods":
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.dirname(path)


def toggle_mods_in_folder(folder_path: str):
    """
    Active ou désactive tous les mods dans un dossier (récursivement).
    """
    if not os.path.isdir(folder_path):
        raise ValueError("Le chemin spécifié n'est pas un dossier.")

    mod_files = []

    for root, _, files in os.walk(folder_path):
        for f in files:
            if f.endswith((".otr", ".o2r", ".disabled", ".di2abled")):
                mod_files.append(os.path.join(root, f))

    if not mod_files:
        raise ValueError("Aucun mod trouvable à activer/désactiver dans ce dossier.")

    # Déterminer si au moins un est désactivé
    has_disabled = any(
        f.endswith(".disabled") or f.endswith(".di2abled") for f in mod_files
    )

    for mod in mod_files:
        # Si on veut activer tous les désactivés
        if has_disabled:
            if mod.endswith(".disabled") or mod.endswith(".di2abled"):
                toggle_mod_state(mod)
        else:
            if mod.endswith(".otr") or mod.endswith(".o2r"):
                toggle_mod_state(mod)
