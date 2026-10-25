import requests
import os
import re

def generate_m3u():
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    print("⏳ Récupération du catalogue...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url_api, headers=headers, timeout=30)
        response.raise_for_status()
        channels = response.json()
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return

    # --- LA MAGIE EST ICI ---
    # On trie toutes les chaînes par "group" (Arabia, France, etc.)
    print("🔄 Tri des chaînes par groupe...")
    channels.sort(key=lambda x: str(x.get("group", "Inconnu")))

    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    count = 0
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "Inconnu")
            # On récupère exactement le nom du groupe (Arabia, France, etc.)
            group = ch.get("group", "Inconnu") 
            logo = ch.get("logo", "")
            stream_url_vavoo = ch.get("url", "")
            
            if not stream_url_vavoo: continue

            match = re.search(r'/([^/]+)\.m3u8', stream_url_vavoo)
            if match:
                channel_id = match.group(1)
                final_url = f"vavoo://{channel_id}"
                
                # On écrit le groupe dans group-title
                f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f"{final_url}\n")
                count += 1
    
    print(f"🎉 TERMINÉ : {count} chaînes générées avec les groupes (Arabia, France, etc.) !")

if __name__ == "__main__":
    generate_m3u()
