import requests
import os
import re
import random

def generate_m3u():
    # 1. Récupération des proxys
    proxy_url = "https://raw.githubusercontent.com/Nissay8z/KENZINISS/main/valid_proxies.txt"
    try:
        res = requests.get(proxy_url, timeout=10)
        proxys = [p.strip() for p in res.text.splitlines() if p.strip()]
        random.shuffle(proxys)
    except Exception as e:
        print(f"Erreur proxys : {e}")
        return

    headers = {'User-Agent': 'VAVOO/2.6 (Linux; Android 13)', 'Accept': 'application/json'}
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    channels = None
    proxy_valide = None

    # 2. Test des proxys
    for proxy in proxys[:15]:
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        try:
            print(f"Test du proxy {proxy}...")
            response = requests.get(url_api, headers=headers, proxies=proxies, timeout=10)
            if response.status_code == 200:
                channels = response.json()
                proxy_valide = proxy
                print(f"✅ Proxy validé : {proxy}")
                break
        except Exception:
            continue

    if not channels:
        print("❌ Aucun proxy n'a fonctionné.")
        return

    # 3. Écriture du fichier M3U (Format IPTV complet)
    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    count = 0
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "Inconnu")
            # C'est ici que Vavoo stocke le pays (ex: "France", "Germany")
            country = ch.get("group", "Général") 
            logo = ch.get("logo", "")
            stream_url_vavoo = ch.get("url", "")
            
            if not stream_url_vavoo: continue

            # On extrait l'ID de la chaîne
            match = re.search(r'/([^/]+)\.m3u8', stream_url_vavoo)
            if match:
                channel_id = match.group(1)
                # L'URL locale que ton appli Android va intercepter
                final_url = f"vavoo://{channel_id}"
                
                # On écrit TOUTES les infos : Pays, Logo, Nom, et ID
                f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{country}" tvg-country="{country}",{name}\n')
                f.write(f"{final_url}\n")
                count += 1
    
    print(f"🎉 Succès : {count} chaînes générées avec les catégories de pays !")

if __name__ == "__main__":
    generate_m3u()
