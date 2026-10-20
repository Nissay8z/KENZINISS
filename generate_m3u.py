# generate_m3u.py
import requests
import os

def generate_m3u():
    # 1. Récupération du catalogue JSON de Vavoo
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    try:
        response = requests.get(url_api, timeout=30)
        response.raise_for_status()
        channels = response.json()
    except Exception as e:
        print(f"Erreur lors de la récupération de l'API : {e}")
        return

    # 2. Écriture du fichier M3U
    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "Inconnu")
            group = ch.get("group", "Général")
            logo = ch.get("logo", "")
            stream_url = ch.get("url", "")
            
            if not stream_url:
                continue

            # Ligne EXTINF avec les métadonnées
            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
            # Options pour le lecteur (User-Agent et Referer exigés par Vavoo)
            f.write('#EXTVLCOPT:http-user-agent=VAVOO/1.0\n')
            f.write('#EXTVLCOPT:http-referrer=https://vavoo.to/\n')
            f.write('#KODIPROP:http-user-agent=VAVOO/1.0\n')
            f.write('#KODIPROP:http-referrer=https://vavoo.to/\n')
            f.write(f"{stream_url}\n")
    
    print(f"Fichier généré : {m3u_path}")

if __name__ == "__main__":
    generate_m3u()
