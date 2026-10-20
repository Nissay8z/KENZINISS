import requests
import os
import re

def generate_m3u():
    # --- 1. CONFIGURATION DU PROXY (Tes infos Webshare) ---
    PROXY_USER = "iagazvbg"
    PROXY_PASS = "5is8kx1h8tn5"
    PROXY_IP = "p.webshare.io"
    PROXY_PORT = "80"
    
    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_IP}:{PROXY_PORT}"
    proxies = {"http": proxy_url, "https": proxy_url}

    # --- 2. RÉCUPÉRATION DE LA LISTE (Via le proxy pour ne pas être bloqué) ---
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    try:
        print("Connexion à Vavoo via le proxy...")
        response = requests.get(url_api, proxies=proxies, timeout=30)
        response.raise_for_status()
        channels = response.json()
    except Exception as e:
        print(f"Erreur de récupération (Le proxy est peut-être bloqué) : {e}")
        return

    # --- 3. URL DE TON WORKER CLOUDFLARE ---
    # ⚠️ VÉRIFIE BIEN QUE C'EST TON LIEN (sans le /ID= à la fin)
    base_worker_url = "https://playlist-perso.yraseloued.workers.dev" 

    # --- 4. ÉCRITURE DU FICHIER M3U ---
    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    count = 0
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "Inconnu")
            group = ch.get("group", "Général")
            logo = ch.get("logo", "")
            channel_id = ch.get("id") 
            
            if not channel_id:
                continue

            # On dirige le lien vers TON Worker Cloudflare
            stream_url = f"{base_worker_url}/ID={channel_id}"

            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
            f.write(f"{stream_url}\n")
            count += 1
    
    print(f"✅ Succès : {count} chaînes générées dans {m3u_path}")

if __name__ == "__main__":
    generate_m3u()
