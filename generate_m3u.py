import requests
import os
import re
import concurrent.futures

SOURCES_PROXYS = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
]

def telecharger_proxys():
    proxys = set()
    for url in SOURCES_PROXYS:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for ligne in r.text.splitlines():
                    if ":" in ligne:
                        proxys.add(ligne.strip())
        except: pass
    return list(proxys)

def tester_proxy(proxy):
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        r = requests.get("https://www.vavoo.tv/", proxies=proxies, timeout=5)
        if r.status_code == 200:
            return proxy
    except: return None
    return None

def main():
    print("1. Téléchargement des proxys...")
    proxys_bruts = telecharger_proxys()
    
    proxy_valide = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for resultat in executor.map(tester_proxy, proxys_bruts[:300]):
            if resultat:
                proxy_valide = resultat
                print(f"✅ Proxy validé : {proxy_valide}")
                break

    if not proxy_valide:
        print("❌ Aucun proxy valide trouvé.")
        return

    print("2. Récupération des chaînes Vavoo...")
    proxies = {"http": f"http://{proxy_valide}", "https": f"http://{proxy_valide}"}
    headers = {'User-Agent': 'VAVOO/2.6 (Linux; Android 13)', 'Accept': 'application/json'}
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    
    try:
        response = requests.get(url_api, headers=headers, proxies=proxies, timeout=20)
        channels = response.json()
        print(f"✅ {len(channels)} chaînes récupérées.")
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return

    print("3. Génération du fichier M3U...")
    
    # ⚠️ TON IP EST ICI
    base_url = "http://192.168.1.33:8080/channel/"

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
    
    print(f"🎉 TERMINÉ : {count} chaînes générées dans la playlist.")

if __name__ == "__main__":
    main()
