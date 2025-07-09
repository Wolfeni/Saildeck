import requests
import os
import sys
import json
import tkinter as tk
from tkinter import messagebox
from version import __version__

SETTINGS_FILE = "saildeck.data"
GITHUB_API = "https://api.github.com/repos/Wolfeni/Saildeck/releases/latest"


def read_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Failed to read settings: {e}")
    return {}


def write_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"[!] Failed to write settings: {e}")


def get_latest_release_info():
    try:
        headers = {'User-Agent': 'Saildeck-Updater'}
        response = requests.get(GITHUB_API, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[!] Failed to fetch release info: {e}")
        return None


def get_latest_version_tag(data):
    tag = data.get("tag_name", "")
    if tag.startswith("Saildeck_"):
        return tag.replace("Saildeck_", "")
    return tag


def find_exe_asset(data):
    for asset in data.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith(".exe"):
            return asset.get("browser_download_url"), asset.get("name"), asset.get("size", 0)
    return None, None, None


def prompt_and_update_if_needed(parent=None):
    settings = read_settings()
    if settings.get("skip_update", False):
        print("[i] Skipping update check (user preference)")
        return

    data = get_latest_release_info()
    if not data:
        return

    latest_version = get_latest_version_tag(data)
    if latest_version == __version__:
        return

    msg = (
        f"A new version of Saildeck is available: {latest_version}\n"
        f"You are using: {__version__}\n\n"
        f"Do you want to download and launch it now?"
    )

    if not messagebox.askyesno("Saildeck Update", msg):
        return

    url, filename, size = find_exe_asset(data)
    if not url or not filename:
        messagebox.showerror("Error", "No .exe file found in the latest release.")
        return

    try:
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        exe_path = os.path.join(base_dir, filename)
        print(f"[📂] Running from: {base_dir}")

        download_file_if_needed(url, exe_path, size)

        print(f"[🚀] Launching: {exe_path}")
        os.startfile(exe_path)
        sys.exit(0)

    except Exception as e:
        messagebox.showerror("Update Failed", f"Failed to download or launch update:\n{e}")


def download_file_if_needed(url, dest_path, expected_size):
    print(f"[↓] Download URL: {url}")
    print(f"[📁] Destination: {dest_path}")
    print(f"[🔍] Expected size: {expected_size} bytes")

    if os.path.exists(dest_path):
        local_size = os.path.getsize(dest_path)
        if local_size == expected_size:
            print("[✓] File is already complete. Skipping download.")
            return
        else:
            print("[!] File is incomplete. Re-downloading.")

    headers = {'User-Agent': 'Saildeck-Updater'}
    with requests.get(url, headers=headers, stream=True) as r:
        print(f"[↪] HTTP status: {r.status_code} {r.reason}")
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print("[✓] Download complete")
