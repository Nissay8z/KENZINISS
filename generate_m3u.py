import requests
import os

def generate_m3u():
    # --- 1. CONFIGURATION DES PROXYS WEBSHARE ---
    PROXY_USER = "iagazvbg"
    PROXY_PASS = "5is8kx1h8tn5"
    
    # On met l'Allemagne en premier (le plus proche de la France)
    proxy_list = [
        "64.137.10.153:5803", # Allemagne (Frankfurt) - TOP
        "45.38.107.97:6014",  # UK (Londres)
        "84.247.60.125:6095", # Pologne
        "64.137.96.74:6641",  # Espagne
        "198.23.243.226:6361" # US
    ]

    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    channels = None

    # --- 2. RÉCUPÉRATION (On teste les proxys un par un) ---
    for proxy_addr in proxy_list:
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{proxy_addr}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        try:
            print(f"Tentative de connexion via le proxy : {proxy_addr}...")
            response = requests.get(url_api, proxies=proxies, timeout=15)
            response.raise_for_status()
            channels = response.json()
            print(f"✅ SUCCÈS avec le proxy {proxy_addr} !")
            break # Si ça marche, on s'arrête là
        except Exception as e:
            print(f"❌ Échec avec {proxy_addr} : {e}")

    if not channels:
        print("Désolé, Vavoo a bloqué tous les proxys de la liste.")
        return

    # --- 3. URL DE TON WORKER CLOUDFLARE ---
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

            stream_url = f"{base_worker_url}/ID={channel_id}"

            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
            f.write(f"{stream_url}\n")
            count += 1
    
    print(f"🎉 GÉNÉRATION TERMINÉE : {count} chaînes sauvegardées dans {m3u_path}")

if __name__ == "__main__":
    generate_m3u()
