import requests
import os
import re

def generate_m3u():
    # 1. On lit TON fichier de 20 proxys
    proxy_url = "https://raw.githubusercontent.com/Nissay8z/KENZINISS/main/valid_proxies.txt"
    print(f"Lecture de la liste de proxys : {proxy_url}")
    
    try:
        res = requests.get(proxy_url, timeout=10)
        proxys = [p.strip() for p in res.text.splitlines() if p.strip()]
        print(f"✅ {len(proxys)} proxys trouvés.")
    except Exception as e:
        print(f"❌ Impossible de lire le fichier : {e}")
        return

    proxy_valide = None
    headers = {'User-Agent': 'VAVOO/2.6 (Linux; Android 13)', 'Accept': 'application/json'}
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"

    # 2. On teste les 20 proxys pour trouver un survivant
    print("Test des proxys sur Vavoo...")
    for proxy in proxys:
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        try:
            print(f"Test de {proxy}...")
            response = requests.get(url_api, headers=headers, proxies=proxies, timeout=10)
            if response.status_code == 200:
                proxy_valide = proxy
                print(f"🎯 Proxy VALIDE trouvé : {proxy}")
                channels = response.json()
                break
        except Exception:
            continue 

    if not proxy_valide:
        print("❌ Aucun des 20 proxys n'a fonctionné. Abandon.")
        return

    # 3. Génération du fichier M3U
    print("Génération de la playlist...")
    
    # ⚠️ METS TON IP ICI (Ton téléphone ou ton PC)
    # Si tu testes sur ton PC, laisse "http://127.0.0.1:8080/channel/"
    base_url = "http://127.0.0.1:8080/channel/"

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
            
            if not stream_url_vavoo: continue

            match = re.search(r'/([^/]+)\.m3u8', stream_url_vavoo)
            if match:
                channel_id = match.group(1)
                final_url = f"{base_url}{channel_id}"
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f"{final_url}\n")
                count += 1
    
    print(f"🎉 TERMINÉ : {count} chaînes générées !")

if __name__ == "__main__":
    generate_m3u()
