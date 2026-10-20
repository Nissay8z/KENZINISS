import requests
import re
import os

def generate_m3u():
    # 1. On télécharge une liste existante (qui contient les IDs des chaînes)
    source_url = "https://raw.githubusercontent.com/joaquinito2070/VAVOO-IPTV/main/index.m3u"
    try:
        response = requests.get(source_url, timeout=30)
        response.raise_for_status()
        content = response.text
    except Exception as e:
        print(f"Erreur de téléchargement de la liste source : {e}")
        return

    # 2. L'URL DE TON WORKER CLOUDFLARE
    # ⚠️ REMPLACE CE LIEN PAR L'URL DE TON PROPRE WORKER
    base_worker_url = "https://trumit-python.umittv.workers.dev"

    # 3. Écriture du nouveau fichier M3U
    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    count = 0
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            if line.startswith("#EXTINF"):
                f.write(f"{line}\n")
                if i + 1 < len(lines):
                    stream_url = lines[i+1].strip()
                    # On cherche l'ID de la chaîne dans l'URL d'origine
                    match = re.search(r'ID=([^&/]+)', stream_url)
                    
                    if match:
                        channel_id = match.group(1)
                        # On recrée l'URL avec TON Worker
                        new_url = f"{base_worker_url}/ID={channel_id}"
                        f.write(f"{new_url}\n")
                        count += 1
                    else:
                        f.write(f"{stream_url}\n")
                        
    print(f"Succès : {count} chaînes générées dans {m3u_path}")

if __name__ == "__main__":
    generate_m3u()
