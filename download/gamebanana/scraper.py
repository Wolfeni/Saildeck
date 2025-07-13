import requests
from bs4 import BeautifulSoup

def get_mod_details_from_id(mod_id):
    try:
        url = f"https://gamebanana.com/mods/{mod_id}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title else f"Mod #{mod_id}"

        # Priorité : image dans <a class="PrimaryPreview">
        image_url = None

        preview_link = soup.select_one("a.PrimaryPreview")
        if preview_link and preview_link.get("href", "").startswith("https://images.gamebanana.com"):
            image_url = preview_link["href"]
        else:
            # Fallback : première image plausible
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if "images.gamebanana.com/img/ss/mods/" in src and not src.startswith("https://images.gamebanana.com/img/ss/mods/100-90"):
                    image_url = src
                    break

        return {
            "mod_id": mod_id,
            "name": title.replace("[Mods]", "").strip(),
            "url": url,
            "author": "inconnu",
            "image_url": image_url
        }

    except Exception as e:
        print(f"[Scraper] Erreur pour le mod {mod_id} : {e}")
        return {
            "mod_id": mod_id,
            "name": f"Mod #{mod_id}",
            "url": f"https://gamebanana.com/mods/{mod_id}",
            "author": "inconnu",
            "image_url": None
        }

def fetch_soh_mods_from_scraper(limit=10):
    from download.gamebanana.api import get_soh_mod_ids

    mod_ids = get_soh_mod_ids(limit=limit)
    mods = [get_mod_details_from_id(mod_id) for mod_id in mod_ids]
    return mods
