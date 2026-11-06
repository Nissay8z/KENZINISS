#!/usr/bin/env python3
"""Vstro Next test build: integrate genuine Onyx Kotlin providers and disable unwanted folders.
Apache-2.0 upstream; do not distribute credentials or private login data.
"""
from pathlib import Path
import re

root=Path("source")
p=root/"app/src/main/java/com/streamflixreborn/streamflix/providers/Provider.kt"
s=p.read_text(encoding="utf-8")
active=[m.group(1) for m in re.finditer(r"(?m)^[ \t]*([A-Za-z]\w*Provider)\s+to ProviderSupport\(",s)]
assert len(active)>=20, f"Unexpected Onyx provider registry: {len(active)}"
assert "VavooProvider" in active and "VegetaTvProvider" in active and "CloudstreamProvider" in active
# World Live is mostly a platform directory (Pluto/Samsung, audio), excluded for user preference.
# TV Hub, VAVOO, OLA, Vegeta, Xtream/M3U + VOD and Anime continue to function.
pattern=r"(?m)^([ \t]*)LiveTvHubPlusProvider to ProviderSupport\(.*$"
s,count=re.subn(pattern,r"\1// Vstro: World Live platform bundle disabled (Pluto/Samsung/music exclusion)",s)
assert count==1
p.write_text(s,encoding="utf-8")

hub=root/"app/src/main/java/com/streamflixreborn/streamflix/providers/LiveTvHubProvider.kt"
h=hub.read_text(encoding="utf-8")
old='val folderShows = defs.sortedBy { d ->'
new='val folderShows = defs.filterNot { it.key in setOf("musique", "samsung_tvplus", "pluto_tv") }.sortedBy { d ->'
assert old in h
h=h.replace(old,new,1)
h=h.replace('"Généraliste", "Cinéma", "Info", "Sport", "Musique", "Documentaire", "Enfants",','"Généraliste", "Cinéma", "Info", "Sport", "Documentaire", "Enfants",',1)
old='val dansChainesTv = setOf("stream4cf", "otf", "samsung_tvplus", "pluto_tv", "plex_tv", "lg_channels")'
new='val dansChainesTv = setOf("stream4cf", "otf", "plex_tv", "lg_channels")'
assert old in h
h=h.replace(old,new,1)
h=h.replace('"francetv", "arte", "musique", "tf1plus", "m6plus", "bfmplay",','"francetv", "arte", "tf1plus", "m6plus", "bfmplay",',1)
# Hide catch-all music sections after building categories, not only the folders.
old='        return result\n    }\n\n    /** 2026-06-08'
new='        return result.filterNot { it.name.contains("Musique", ignoreCase = true) || it.name.contains("Pluto", ignoreCase = true) || it.name.contains("Samsung", ignoreCase = true) }\n    }\n\n    /** 2026-06-08'
assert old in h
h=h.replace(old,new,1)
hub.write_text(h,encoding="utf-8")

# Brand as separate application to avoid overwriting the user's current Vstro/Onyx.
g=root/"app/build.gradle"
t=g.read_text(encoding="utf-8")
assert 'applicationId "com.streamfr.app"' in t
t=t.replace('applicationId "com.streamfr.app"','applicationId "com.vstro.next"',1)
t=t.replace('versionName "1.8.14"','versionName "20.0.0-test"',1)
t=t.replace('applicationIdSuffix ".debug"','applicationIdSuffix ""',1)
g.write_text(t,encoding="utf-8")

strings=root/"app/src/main/res/values/strings.xml"
u=strings.read_text(encoding="utf-8")
assert '<string name="app_name">ONYX</string>' in u
u=u.replace('<string name="app_name">ONYX</string>','<string name="app_name">Vstro Next</string>',1)
strings.write_text(u,encoding="utf-8")

# Minimize unsolicited storage permissions in the test app if source doesn't need audio.
m=root/"app/src/main/tv/AndroidManifest.xml"
if m.exists():
    txt=m.read_text(encoding="utf-8")
    txt=re.sub(r'(?m)^\s*<uses-permission android:name="android.permission.READ_MEDIA_AUDIO" />\s*', "\n",txt)
    m.write_text(txt,encoding="utf-8")

assets=root/"app/src/main/assets"
assets.mkdir(parents=True,exist_ok=True)
(assets/"UPSTREAM_LICENSE.txt").write_bytes((root/"LICENSE").read_bytes())
(assets/"VSTRO_NEXT_INFO.txt").write_text(
    "Vstro Next 20.0.0-test\nBuilt from https://github.com/linkinep61/projet-nx\n"
    "Native Onyx provider engine. Exclusions: Pluto, Samsung, music/radio Home folders.\n"
    "Sources that require credentials must use the user's own authorized account.\n"
    "This is a test build, not a patch to the original Vstro binary.\n",
    encoding="utf-8"
)
print("Integrated Onyx provider registry:",len(active)-1,"enabled providers")
print("Vstro Next base ready; package com.vstro.next (test).")
