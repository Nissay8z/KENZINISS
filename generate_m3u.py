import requests
import os

def generate_m3u():
    # L'adresse interne générée par ton serveur Waifly
    waifly_ip_interne = "172.18.0.115:8080" 
    # Ton adresse publique Waifly
    waifly_ip_publique = "node4.waifly.com:25177" 
    
    # Les pays que tu veux récupérer
    lists_to_get = ["France.m3u8", "France_hls.m3u8", "Germany.m3u8", "United_Kingdom.m3u8"]

    os.makedirs("playlist", exist_ok=True)
    m3u_path = "playlist/vavoo.m3u"
    
    total_count = 0
    
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for list_name in lists_to_get:
            print(f"Téléchargement de {list_name} depuis Waifly...")
            url = f"http://node4.waifly.com:25177/{list_name}"
            
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                content = response.text
                
                # On remplace l'adresse interne par l'adresse publique pour que ta TV puisse y accéder
                content_fixed = content.replace(waifly_ip_interne, waifly_ip_publique)
                
                lines = content_fixed.split('\n')
                for line in lines:
                    if line.startswith("#EXTM3U"):
                        continue
                    if line.strip():
                        f.write(line + "\n")
                        if line.startswith("#EXTINF"):
                            total_count += 1
                            
                print(f"✅ {list_name} ajouté !")
            except Exception as e:
                print(f"❌ Impossible de récupérer {list_name} : {e}")

    print(f"🎉 GÉNÉRATION TERMINÉE : {total_count} chaînes sauvegardées.")

if __name__ == "__main__":
    generate_m3u()
