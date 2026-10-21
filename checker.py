import requests
import concurrent.futures

SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
]

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
    proxys = set()
    for url in SOURCES:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    if ":" in line: proxys.add(line.strip())
        except: pass
    
    liste_proxys = list(proxys)
    print(f"2. Test de {len(liste_proxys)} proxys sur Vavoo...")
    
    valides = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        for res in executor.map(tester_proxy, liste_proxys[:1000]): # On teste les 1000 premiers
            if res:
                valides.append(res)
                print(f"✅ Trouvé : {res}")
                if len(valides) >= 20: # On s'arrête à 20 bons proxys
                    break

    with open("valid_proxies.txt", "w") as f:
        for p in valides:
            f.write(f"{p}\n")
    print(f"🎉 {len(valides)} proxys sauvegardés dans valid_proxies.txt")

if __name__ == "__main__":
    main()
