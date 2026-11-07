#!/usr/bin/env python3
"""TV-only Onyx/onyxia feeds for Vstro. Never publishes logins, tokens or DRM."""
import collections, datetime, ipaddress, json, pathlib, re, urllib.parse, urllib.request
out = pathlib.Path("playlist")
out.mkdir(exist_ok=True)
SOURCES = [
  ("Onyxia Live", "https://raw.githubusercontent.com/rikital/onyxia-data/main/data.m3u"),
  ("Onyxia Fast", "https://raw.githubusercontent.com/rikital/onyxia-data/main/data-fast.m3u")
]
WORLD = "https://box.xtemus.com/?playlist=u256y494u21596x2"
BLOCK = re.compile("pluto|samsung|musique|music|radio|vevo|spotify|deezer|adult|porn|xxx",re.I)
PROTECTED = re.compile(r"/(?:live|movie|series)/[^/]+/[^/]+/|/portal\.php|/get\.php|/player_api\.php|stalker|token|access_key|auth|jwt|signature|key=",re.I)
ATTR = re.compile(r'\b([a-zA-Z][a-zA-Z0-9_-]*)="([^"]*)"')
entries=[]; seen=set();rejected=collections.Counter();sources={}

def fetch(url,limit=9000000):
    req=urllib.request.Request(url,headers={"User-Agent":"Vstro-TV-Sync/1.0","Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=22) as response:
        data=response.read(limit+1)
        if len(data)>limit:raise ValueError("Source exceeds size limit")
        return data.decode("utf-8-sig","replace")

def safe(url):
    try:
        p=urllib.parse.urlsplit(url)
        if p.scheme not in ("http","https") or not p.hostname or p.username or p.password or p.query or p.fragment:return False
        if BLOCK.search(url) or PROTECTED.search(url):return False
        if not re.search(r"\.(?:m3u8|ts)$",p.path,re.I):return False
        if p.hostname.lower() in ("localhost",) or p.hostname.lower().endswith((".local",".internal")):return False
        try:
            if not ipaddress.ip_address(p.hostname).is_global:return False
        except ValueError:pass
        if any(c in p.hostname for c in "@:/\\"):return False
        return True
    except Exception:return False

def group(name,origin):
    s=(name+" "+origin).casefold()
    if re.search(r"maroc|morocco|arryadia|al aoula|2m maroc|medi 1",s):return "Maroc"
    if re.search(r"alg[ée]rie|algeria|ennahar|echourouk|\bentv\b",s):return "Algérie"
    if re.search(r"tunisie|tunisia|wataniya|nessma|hannibal",s):return "Tunisie"
    if re.search(r"arabia sport|arabic sport|ssc sport|alkass|al kass",s):return "Arabia Sport"
    if re.search(r"france sport|bein sports? [1-9]|canal\+ live|rmc sport|eurosport|foot\+|ligue 1\+",s):return "France Sport"
    if re.search(r"france|french|\btf1\b|\btmc\b|\btfx\b|\bm6\b|\barte\b|bfmtv|cnews",s):return "France"
    if re.search(r"sport|dazn|espn|bein",s):return "Sport International"
    return "TV International"

def add(name,category,logo,url,origin):
    if not name or BLOCK.search(name) or BLOCK.search(category):
        rejected["category"]+=1;return
    # Onyxia also lists event recordings and concert clips; TV Live only.
    if re.match(r"^\d+\.\s",name) or re.search(r"\[(?:720p|1080p)-france\.tv\]",name,re.I) or re.search(r"\b(?:concert|festival|replay|rediffusion)\b",name,re.I):
        rejected["event_or_replay"]+=1;return
    if not safe(url):
        rejected["unsafe_or_unplayable_url"]+=1;return
    key=(name.casefold(),url)
    if key in seen:
        rejected["duplicate"]+=1;return
    seen.add(key)
    entries.append((name,group(name,category),logo,url,origin))

def parse_m3u(body,origin,default_category=""):
    if not body.lstrip().startswith("#EXTM3U"):raise ValueError("Invalid M3U header")
    before=len(entries);info=None;drm=False
    for ln in body.splitlines():
        ln=ln.strip()
        if ln.startswith("#EXTINF:"):
            a=dict(ATTR.findall(ln));name=ln.split(",",1)[-1].strip() if "," in ln else a.get("tvg-name","")
            info=(name,a.get("group-title",default_category),a.get("tvg-logo",""));drm=False
        elif info and ln.startswith(("#KODIPROP:","#EXTVLCOPT:","#EXTHTTP:")):
            if re.search("license|drm|widevine|clearkey|cookie|referer|user-agent",ln,re.I):drm=True
        elif info and ln.startswith(("http://","https://")):
            if drm:rejected["drm_or_headers"]+=1
            else:add(*info,ln,origin)
            info=None
        elif info and ln and not ln.startswith("#"):info=None
    return len(entries)-before

def find_directories(x):
    if isinstance(x,list):
        for y in x:yield from find_directories(y)
    elif isinstance(x,dict):
        if isinstance(x.get("url"),str) and ("name" in x or "title" in x):
            yield str(x.get("name") or x.get("title")),x["url"]
        for key in ("playlists","groups","items","stations","data","list"):
            if key in x:yield from find_directories(x[key])

for label,url in SOURCES:
    try:
        content=fetch(url)
        sources[label]={"status":"ok","accepted":parse_m3u(content,label),"bytes":len(content.encode("utf8"))}
    except Exception as e:sources[label]={"status":"unavailable","reason":str(e)[:140]}


# Port du Dric4rTvProvider.kt de projet-nx : source JSON -> catégories Live natives Vstro.
# Ni musique, ni radio, ni films/series mal classés en Live, ni liens protégés.
def dric_json(body):
    try:return json.loads(body)
    except json.JSONDecodeError:
        # Réparation ciblée de DricJson.kt : accolade manquante avant ].
        # N'essaye qu'un seul candidat pour éviter de masquer d'autres anomalies.
        candidates=list(re.finditer(r'"(?:[^"\\]|\\.)*"\s*]',body))
        for m in reversed(candidates[:1000]):
            pos=m.end()-1
            repaired=body[:pos]+'}'+body[pos:]
            try:return json.loads(repaired)
            except json.JSONDecodeError:pass
        raise

def dric_add_station(st, category, title=None):
    if not isinstance(st,dict):return
    if st.get("headers") or st.get("referer") or st.get("userAgent"):
        rejected["dric_requires_custom_headers"]+=1
        return
    url=str(st.get("url") or "").strip()
    name=str(title or st.get("name") or "").strip()
    if not name or not safe(url):return
    if category=="Ligue1+":
        cat="France Sport"
    elif category in ("US Sports & NBA","Horse"):
        cat="Sport International"
    elif category=="Nature & Découverte":
        cat="Documentaire"
    else:
        cat="France"
    # The group() classifier uses title and category, but not the category's
    # original taxonomy. Explicit country/sport group is retained here.
    k=(name.casefold(),url)
    if k in seen:return
    seen.add(k)
    entries.append((name,cat,str(st.get("image") or ""),url,"Onyx Dric4rTV"))

def sync_dric4r():
    origin="http://dric4rt.free.fr/1.json"
    kept={"Ligue1+","US Sports & NBA","Horse","Nature & Découverte","Locales TV"}
    source={"status":"ok","groups_seen":0,"accepted":0,"errors":[]}
    before=len(entries)
    idx=dric_json(fetch(origin,2500000))
    groups=idx.get("groups",[])
    source["groups_seen"]=len(groups)
    for group_item in groups[:80]:
        if not isinstance(group_item,dict):continue
        name=str(group_item.get("name") or "").strip()
        if name not in kept:continue
        url=str(group_item.get("url") or "").strip()
        if not url.startswith(("http://","https://")) or "rebrand.ly" in url:continue
        try:
            cat=dric_json(fetch(url,2500000))
            stations=cat.get("stations",[])
            if isinstance(stations,list):
                for st in stations[:2000]:dric_add_station(st,name)
            else:
                for sub in cat.get("groups",[])[:120]:
                    if not isinstance(sub,dict):continue
                    for st in sub.get("stations",[])[:100]:
                        dric_add_station(st,name,str(sub.get("name") or ""))
        except Exception as e:
            source["errors"].append({"category":name,"error":type(e).__name__})
    source["accepted"]=len(entries)-before
    return source

try:
    sources["Onyx Dric4rTV"]=sync_dric4r()
except Exception as e:
    sources["Onyx Dric4rTV"]={"status":"unavailable","reason":type(e).__name__}



# Port des sources TV ReneVeo incluses dans projet-nx/assets/reneveo_channels.json.
# Seule la liste publique de chaînes est importée, pas la clé Supabase.
def sync_reneveo():
    origin="https://raw.githubusercontent.com/linkinep61/projet-nx/main/app/src/main/assets/reneveo_channels.json"
    body=json.loads(fetch(origin,1000000))
    channels=body.get("channels",[])
    if isinstance(channels,dict):channels=list(channels.values())
    before=len(entries)
    categories={"generaliste":"France","cinema":"France","sport":"France Sport",
      "information":"France Info","jeunesse":"France Enfants",
      "documentaire":"Documentaire","divers":"France"}
    for channel in channels[:300]:
        if not isinstance(channel,dict):continue
        name=str(channel.get("name") or "").strip()
        c=str(channel.get("category") or "").lower()
        if c not in categories or not name or BLOCK.search(name):continue
        logo=str(channel.get("logo") or "")
        for url in channel.get("sources",[])[:8]:
            if not isinstance(url,str) or not safe(url):continue
            key=(name.casefold(),url)
            if key in seen:continue
            seen.add(key)
            entries.append((name,categories[c],logo,url,"Onyx ReneVeo"))
    return {"status":"ok","catalogue_channels":len(channels),"accepted":len(entries)-before}

try:
    sources["Onyx ReneVeo"]=sync_reneveo()
except Exception as e:
    sources["Onyx ReneVeo"]={"status":"unavailable","reason":type(e).__name__}

try:
    directories=list(find_directories(json.loads(fetch(WORLD,3000000))))
    n=0
    for name,url in directories[:100]:
        p=urllib.parse.urlsplit(url)
        if BLOCK.search(name) or BLOCK.search(url) or p.scheme!="https" or p.query or not p.path.lower().endswith(".m3u"):continue
        if not safe(url[:-1]+"8"):continue
        try:n+=parse_m3u(fetch(url,3000000),"Onyx World Live",name)
        except Exception:continue
    sources["Onyx World Live"]={"status":"ok","directories":len(directories),"accepted":n}
except Exception as e:sources["Onyx World Live"]={"status":"unavailable","reason":str(e)[:140]}

entries.sort(key=lambda e:(e[1].casefold(),e[0].casefold(),e[3]))
lines=["#EXTM3U"]
def esc(x):return re.sub(r'[\r\n"<>]',' ',str(x)).strip()[:160]
for name,cat,logo,url,origin in entries:
    logo=logo if logo.startswith(("https://","http://")) and not BLOCK.search(logo) else ""
    lines.extend(['#EXTINF:-1 provider="vstroextras" tvg-name="%s" tvg-logo="%s" group-title="%s",%s [%s]'%(esc(name),esc(logo),esc(cat),esc(name),esc(origin)),url])
if entries:
    (out/"vstro-extras.m3u").write_text("\n".join(lines)+"\n",encoding="utf8")
status={"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"sources":sources,
    "total_entries":len(entries),"groups":dict(collections.Counter(x[1] for x in entries)),
    "rejected":dict(rejected),"result":"updated" if entries else "preserved_previous_no_valid_entries",
    "excluded":["Pluto","Samsung","music/radio","DRM","Xtream/Stalker credentials"],
    "reference":["linkinep61/projet-nx","rikital/onyxia-data"]}
(out/"vstro-extras-status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(status,ensure_ascii=False,indent=2))
