import requests
import os
import re

def generate_m3u():
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    headers = {'User-Agent': 'VAVOO/2.6 (Linux; Android 13)', 'Accept': 'application/json'}

    # On récupère un proxy valide pour GitHub
    try:
        r = requests.get("https://raw.githubusercontent.com/Nissay8z/KENZINISS/main/valid_proxies.txt")
        proxys = [p.strip() for p in r.text.splitlines() if p.strip()]
        proxy = proxys[0] if proxys else None
    except:
        proxy = None

    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None

    print("Récupération des chaînes...")
    try:
        response = requests.get(url_api, headers=headers, proxies=proxies, timeout=20)
        channels = response.json()
        print(f"✅ {len(channels)} chaînes récupérées.")
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return

    # ⚠️ METS TON ADRESSE WAIFLY ICI
    base_worker_url = "http://node4.waifly.com:25177/channel/"

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
                final_url = f"{base_worker_url}{channel_id}"
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f"{final_url}\n")
                count += 1
    
    print(f"🎉 TERMINÉ : {count} chaînes générées.")

if __name__ == "__main__":
    generate_m3u()
