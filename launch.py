import os
import sys
import json
import subprocess

SETTINGS_FILE = "saildeck.data"

def should_enable_altassets():
    """Vérifie si l'utilisateur souhaite que AltAssets soit forcé"""
    if not os.path.exists(SETTINGS_FILE):
        print("[ℹ] Aucun fichier de configuration trouvé, AltAssets activé par défaut.")
        return True
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
            enabled = settings.get("enable_altassets", True)
            print(f"[ℹ] AltAssets auto-activation : {'activé' if enabled else 'désactivé'}")
            return enabled
    except Exception as e:
        print(f"[!] Erreur lors de la lecture de {SETTINGS_FILE} : {e}")
        return True

def has_enabled_mod(mods_dir):
    """Retourne True si un .otr ou .o2r actif est trouvé n'importe où dans /mods"""
    print(f"[🔍] Recherche récursive de mods actifs dans : {mods_dir}")
    if not os.path.exists(mods_dir):
        print("[⚠] Dossier des mods introuvable.")
        return False

    for root, _, files in os.walk(mods_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in [".otr", ".o2r"]:
                full_path = os.path.join(root, file)
                print(f"[✓] Mod actif détecté : {full_path}")
                return True

    print("[ℹ] Aucun fichier .otr ou .o2r actif détecté dans les sous-dossiers.")
    return False

def ensure_altassets_enabled(config_path):
    """Active AltAssets dans CVars > gSettings uniquement"""
    print(f"[🔧] Activation de AltAssets dans gSettings : {config_path}")
    if not os.path.exists(config_path):
        print("[⚠] Fichier shipofharkinian.json introuvable.")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        settings = config.get("CVars", {}).get("gSettings", None)
        if settings is None:
            print("[⚠] CVars > gSettings non trouvé.")
            return

        if settings.get("AltAssets") != 1:
            settings["AltAssets"] = 1
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            print("[✓] AltAssets (gSettings) activé.")
        else:
            print("[ℹ] AltAssets (gSettings) est déjà activé.")

    except Exception as e:
        print(f"[!] Erreur lors de la mise à jour de AltAssets : {e}")

def launch_game(soh_path, mods_dir):
    """Lance soh.exe après avoir forcé AltAssets si nécessaire"""
    exe_path = os.path.join(soh_path, "soh.exe")
    config_path = os.path.join(soh_path, "shipofharkinian.json")

    print(f"[▶] Lancement du jeu depuis : {soh_path}")

    if has_enabled_mod(mods_dir) and should_enable_altassets():
        ensure_altassets_enabled(config_path)
    else:
        print("[ℹ] Aucun mod actif ou option AltAssets désactivée.")

    if os.path.exists(exe_path):
        subprocess.Popen([exe_path], cwd=soh_path)
        print("[🚀] Jeu lancé. Fermeture de Saildeck...")
        sys.exit(0)
    else:
        print("[❌] soh.exe introuvable.")
