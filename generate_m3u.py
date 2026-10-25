import requests
import re
import os

def generer_catalogue():
    url_api = "https://www2.vavoo.to/live2/index?countries=all&output=json"
    print("⏳ Téléchargement du catalogue Vavoo...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url_api, headers=headers, timeout=30)
        response.raise_for_status()
        channels = response.json()
        print(f"✅ {len(channels)} chaînes récupérées depuis l'API.")
    except Exception as e:
        print(f"❌ Erreur réseau : {e}")
        return

    # --- TEST : ON REPÈRE LES VRAIS GROUPES ---
    groupes_trouves = set()
    for ch in channels:
        g = ch.get("group", "Inconnu")
        groupes_trouves.add(g)
    
    print("\n📊 LISTE DES VRAIS GROUPES DÉTECTÉS PAR VAVOO :")
    for g in sorted(groupes_trouves):
        print(f"  - {g}")
    print("----------------------------------------------\n")

    # On trie les chaînes par groupe
    channels.sort(key=lambda x: str(x.get("group", "Inconnu")))

    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    count = 0
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "Inconnu")
            group = ch.get("group", "Inconnu") # C'est ici que se trouve Arabia, France...
            logo = ch.get("logo", "")
            stream_url = ch.get("url", "")
            
            if not stream_url: continue

            match = re.search(r'/([^/]+)\.m3u8', stream_url)
            if match:
                channel_id = match.group(1)
                final_url = f"vavoo://{channel_id}"
                
                # On écrit le groupe dans group-title
                f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f"{final_url}\n")
                count += 1
    
    print(f"🎉 TERMINÉ : Le fichier 'playlist/vavoo.m3u' est généré avec {count} chaînes !")

if __name__ == "__main__":
    generer_catalogue()
