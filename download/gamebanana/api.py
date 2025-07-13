import requests

def get_soh_mod_ids(limit=10):
    try:
        url = "https://api.gamebanana.com/Core/List/New"
        params = {
            "itemtype": "Mod",
            "gameid": "16121",
            "fields": "_idRow",
            "limit": str(limit),
            "page": "1"
        }

        response = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()

        ids = []
        for entry in data:
            if isinstance(entry, list) and len(entry) == 2 and entry[0] == "Mod":
                ids.append(entry[1])

        return ids

    except Exception as e:
        print(f"[API] Erreur lors de la récupération des IDs : {e}")
        return []
