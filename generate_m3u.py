import requests
import os

def generate_m3u():
    # --- 1. CONFIGURATION DES PROXYS WEBSHARE ---
    PROXY_USER = "iagazvbg"
    PROXY_PASS = "5is8kx1h8tn5"
    
    proxy_list = [
        "64.137.10.153:5803", # Allemagne
        "45.38.107.97:6014",  # UK
        "84.247.60.125:6095", # Pologne
    ]

    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    
    # --- 2. LES HEADERS MAGIQUES (Pour que Vavoo nous donne la liste) ---
    headers = {
        'User-Agent': 'VAVOO/2.6 (Linux; Android 13)',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }

    channels = None

    # --- 3. RÉCUPÉRATION ---
    for proxy_addr in proxy_list:
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{proxy_addr}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        try:
            print(f"Tentative via le proxy : {proxy_addr}...")
            # On ajoute headers=headers ici
            response = requests.get(url_api, headers=headers, proxies=proxies, timeout=15)
            response.raise_for_status()
            
            # On affiche un bout de la réponse pour voir si c'est vide ou non
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                channels = data
                print(f"✅ SUCCÈS avec le proxy {proxy_addr} ! ({len(channels)} chaînes trouvées)")
                break
            else:
                print(f"⚠️ Le proxy a répondu, mais Vavoo a renvoyé une liste vide. Début de la réponse : {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ Échec avec {proxy_addr} : {e}")

    if not channels:
        print("Désolé, impossible de récupérer les chaînes.")
        return

    # --- 4. ÉCRITURE DU FICHIER M3U ---
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
