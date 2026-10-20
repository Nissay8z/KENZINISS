import requests
import os
import re

def generate_m3u():
    # On récupère la liste directement (plus besoin de proxy !)
    print("Récupération de la liste des chaînes...")
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    
    try:
        response = requests.get(url_api, timeout=30)
        response.raise_for_status()
        channels = response.json()
    except Exception as e:
        print(f"Erreur : {e}")
        return

    # L'adresse de TON Worker Cloudflare
    base_worker_url = "https://playlist-perso.yraseloued.workers.dev"

    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    count = 0
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "Inconnu")
            group = ch.get("group", "Général")
            logo = ch.get("logo", "")
            stream_url_vavoo = ch.get("url", "")
            
            if not stream_url_vavoo:
                continue

            # On extrait l'ID de la chaîne
            match = re.search(r'/([^/]+)\.m3u8', stream_url_vavoo)
            if match:
                channel_id = match.group(1)
            else:
                continue 

            final_url = f"{base_worker_url}/ID={channel_id}"

            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
            f.write(f"{final_url}\n")
            count += 1
    
    print(f"🎉 SUCCÈS : {count} chaînes générées !")

if __name__ == "__main__":
    generate_m3u()
