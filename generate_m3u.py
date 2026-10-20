import requests
import os
import re

def generate_m3u():
    PROXY_USER = "iagazvbg"
    PROXY_PASS = "5is8kx1h8tn5"
    
    proxy_list = [
        "45.38.107.97:6014",  # UK (Celui qui marche bien)
        "84.247.60.125:6095", # Pologne
        "64.137.96.74:6641"   # Espagne
    ]

    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    
    headers = {
        'User-Agent': 'VAVOO/2.6 (Linux; Android 13)',
        'Accept': 'application/json',
    }

    channels = None

    for proxy_addr in proxy_list:
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{proxy_addr}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        try:
            print(f"Tentative via le proxy : {proxy_addr}...")
            response = requests.get(url_api, headers=headers, proxies=proxies, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                channels = data
                print(f"✅ SUCCÈS ! {len(channels)} chaînes trouvées.")
                break
        except Exception as e:
            print(f"❌ Échec avec {proxy_addr} : {e}")

    if not channels:
        print("Désolé, impossible de récupérer les chaînes.")
        return

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

            # --- LA CORRECTION EST ICI ---
            # On cherche le nombre juste avant le .m3u8 (ex: 51258455)
            match = re.search(r'/([^/]+)\.m3u8', stream_url_vavoo)
            if match:
                channel_id = match.group(1)
            else:
                continue # Si on ne trouve pas d'ID, on ignore la chaîne

            final_url = f"{base_worker_url}/ID={channel_id}"

            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
            f.write(f"{final_url}\n")
            count += 1
    
    print(f"🎉 GÉNÉRATION TERMINÉE : {count} chaînes sauvegardées dans {m3u_path}")

if __name__ == "__main__":
    generate_m3u()
