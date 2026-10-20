import requests
import os

def generate_m3u():
    # 1. Récupération du catalogue JSON de Vavoo (cette partie ne nécessite pas d'authentification)
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    try:
        response = requests.get(url_api, timeout=30)
        response.raise_for_status()
        channels = response.json()
    except Exception as e:
        print(f"Erreur lors de la récupération de l'API : {e}")
        return

    # 2. URL de base pour la lecture directe (méthode "scraper")
    # C'est ce format qui contourne le besoin d'authentification (token/addonSig).
    base_play_url = "https://vavoo.to/play"

    # 3. Écriture du fichier M3U
    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "Inconnu")
            group = ch.get("group", "Général")
            logo = ch.get("logo", "")
            channel_id = ch.get("id") 
            
            if not channel_id:
                continue

            # Construction de l'URL de lecture directe
            # Format : https://vavoo.to/play/{ID}/index.m3u8
            stream_url = f"{base_play_url}/{channel_id}/index.m3u8"

            # Ligne EXTINF avec les métadonnées
            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
            # On écrit l'URL de lecture directe
            f.write(f"{stream_url}\n")
    
    print(f"Fichier généré avec succès : {m3u_path}")

if __name__ == "__main__":
    generate_m3u()
