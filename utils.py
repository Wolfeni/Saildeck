import os
import json

SETTINGS_FILE = "saildeck.data"

def is_valid_game_dir(path: str) -> bool:
    """
    Vérifie si le dossier contient 'soh.exe'.
    """
    return os.path.isfile(os.path.join(path, "soh.exe"))

def ensure_mods_folder(game_dir: str):
    """
    Crée le dossier 'mods' dans le répertoire du jeu s’il n’existe pas.
    """
    mods_path = os.path.join(game_dir, "mods")
    os.makedirs(mods_path, exist_ok=True)

def get_mods_folder(game_dir: str) -> str:
    """
    Retourne le chemin complet du dossier 'mods'.
    """
    return os.path.join(game_dir, "mods")

def list_mod_files(mods_dir: str) -> list:
    """
    Liste récursivement tous les fichiers .otr, .o2r, .disabled, .di2abled
    """
    mods = []
    for root, _, files in os.walk(mods_dir):
        for file in files:
            if file.endswith((".otr", ".o2r", ".disabled", ".di2abled")):
                mods.append(os.path.join(root, file))
    return mods

def read_json(path: str, default: dict = {}) -> dict:
    """
    Charge un fichier JSON. Retourne `default` si erreur.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path: str, data: dict):
    """
    Écrit un dictionnaire dans un fichier JSON.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ==== SETTINGS.JSON SPECIFIQUES ====

def load_settings() -> dict:
    """
    Charge les paramètres depuis 'settings.json'.
    """
    return read_json(SETTINGS_FILE, default={})

def save_settings(settings: dict):
    """
    Sauvegarde les paramètres dans 'settings.json'.
    """
    write_json(SETTINGS_FILE, settings)

def get_game_path() -> str | None:
    """
    Retourne le chemin du jeu depuis les paramètres (ou None si non défini).
    """
    settings = load_settings()
    return settings.get("game_path")

def set_game_path(path: str):
    """
    Définit et sauvegarde le chemin du jeu dans les paramètres.
    """
    settings = load_settings()
    settings["game_path"] = path
    save_settings(settings)
