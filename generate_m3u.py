import requests
import re
import os

def generate_m3u():
    # 1. On télécharge une liste M3U publique maintenue par la communauté
    source_url = "https://raw.githubusercontent.com/joaquinito2070/VAVOO-IPTV/main/index.m3u"
    try:
        response = requests.get(source_url, timeout=30)
        response.raise_for_status()
        content = response.text
    except Exception as e:
        print(f"Erreur de téléchargement de la liste source : {e}")
        return

    # 2. URL DE TON WORKER CLOUDFLARE
    # ⚠️ REMPLACE CE LIEN PAR L'URL DE TON PROPRE WORKER
    base_worker_url = "https://ton-worker.ton-nom.workers.dev"

    # 3. Écriture du nouveau fichier M3U
    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    count = 0
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        lines = content.splitlines()
        
        # On parcourt la liste ligne par ligne
        for i, line in enumerate(lines):
            if line.startswith("#EXTINF"):
                # On écrit la ligne d'information (nom, logo, catégorie)
                f.write(f"{line}\n")
                
                # La ligne suivante contient l'URL de la chaîne
                if i + 1 < len(lines):
                    stream_url = lines[i+1].strip()
                    
                    # On extrait l'ID de la chaîne de l'URL d'origine
                    # (ex: si l'URL est ".../ID=367788", on récupère "367788")
                    match = re.search(r'ID=([^&/]+)', stream_url)
                    
                    if match:
                        channel_id = match.group(1)
                        # On recrée l'URL en utilisant TON Worker
                        new_url = f"{base_worker_url}/ID={channel_id}"
                        f.write(f"{new_url}\n")
                        count += 1
                    else:
                        # Si on ne trouve pas d'ID, on garde l'ancien lien par sécurité
                        f.write(f"{stream_url}\n")
                        
    print(f"Fichier généré avec succès avec {count} chaînes : {m3u_path}")

if __name__ == "__main__":
    generate_m3u()
