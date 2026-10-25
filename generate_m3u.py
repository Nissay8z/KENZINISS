import requests
import os
import re

def generate_m3u():
    # L'API publique de Vavoo (pas besoin de token pour le catalogue)
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    
    print("⏳ Téléchargement direct du catalogue depuis Vavoo...")
    
    try:
        # On utilise un User-Agent de navigateur classique pour éviter d'être bloqué
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url_api, headers=headers, timeout=30)
        response.raise_for_status()
        channels = response.json()
        print(f"✅ {len(channels)} chaînes récupérées !")
    except Exception as e:
        print(f"❌ Erreur de téléchargement : {e}")
        return

    # Création du fichier M3U
    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    count = 0
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "Inconnu")
            # Le pays est dans le champ "group" de Vavoo
            country = ch.get("group", "Général") 
            logo = ch.get("logo", "")
            stream_url_vavoo = ch.get("url", "")
            
            if not stream_url_vavoo: continue

            # Extraction de l'ID de la chaîne
            match = re.search(r'/([^/]+)\.m3u8', stream_url_vavoo)
            if match:
                channel_id = match.group(1)
                # L'URL que ton application Android va reconnaître
                final_url = f"vavoo://{channel_id}"
                
                # On écrit le pays dans group-title
                f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{country}",{name}\n')
                f.write(f"{final_url}\n")
                count += 1
    
    print(f"🎉 TERMINÉ : {count} chaînes avec pays générées dans {m3u_path}")

if __name__ == "__main__":
    generate_m3u()
