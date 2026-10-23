#!/usr/bin/env python3
"""Build playlist/master.m3u from the public, all-country IPTV-org catalogue.

VAVOO deliberately does not belong here: the Android app uses VavooProvider and
resolves a selected stream natively at playback time.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from pathlib import Path

SOURCE_URL = "https://iptv-org.github.io/iptv/index.country.m3u"
OUTPUT_PATH = Path("playlist/master.m3u")
MAX_BYTES = 40 * 1024 * 1024
TIMEOUT_SECONDS = 30
USER_AGENT = "KENZINISS-IPTV-org-master/1.0 (+https://github.com/Nissay8z/KENZINISS)"


def attribute(extinf: str, key: str) -> str:
    """Read a quoted or unquoted M3U attribute without matching part of a name."""
    pattern = re.compile(
        r"(?<![\w-])" + re.escape(key)
        + r"\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s,]+))",
        re.IGNORECASE,
    )
    match = pattern.search(extinf)
    if not match:
        return ""
    return next((value for value in match.groups() if value is not None), "").strip()


def set_attribute(extinf: str, key: str, value: str) -> str:
    """Add a missing attribute before the channel-name comma."""
    if attribute(extinf, key):
        return extinf
    comma = extinf.rfind(",")
    metadata = extinf if comma < 0 else extinf[:comma]
    title = "" if comma < 0 else extinf[comma:]
    safe_value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'{metadata} {key}="{safe_value}"{title}'


def normalize_extinf(extinf: str) -> str:
    # index.country.m3u is country-grouped. Keep all upstream metadata; copy
    # the country field into whichever of group-title/tvg-country is missing.
    country = attribute(extinf, "tvg-country") or attribute(extinf, "country")
    group = attribute(extinf, "group-title")
    if not country and group:
        extinf = set_attribute(extinf, "tvg-country", group)
    elif country and not group:
        extinf = set_attribute(extinf, "group-title", country)
    return extinf


def download_source() -> str:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.apple.mpegurl,*/*"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise RuntimeError("La playlist IPTV-org dépasse la limite de 40 Mo.")
    text = data.decode("utf-8-sig", errors="replace")
    if "#EXTM3U" not in text[:2048]:
        raise RuntimeError("La réponse IPTV-org n'est pas une playlist M3U valide.")
    return text


def build_master(text: str) -> tuple[str, int]:
    lines = text.splitlines()
    header = next((line.strip() for line in lines if line.strip().startswith("#EXTM3U")), "#EXTM3U")
    output = [header]
    seen_urls: set[str] = set()
    block: list[str] = []
    count = 0

    def flush_pending() -> None:
        nonlocal count, block
        if not block:
            return
        uri_index = next(
            (i for i, value in enumerate(block)
             if value.strip().lower().startswith(("http://", "https://"))),
            -1,
        )
        extinf_index = next(
            (i for i, value in enumerate(block) if value.lstrip().startswith("#EXTINF:")),
            -1,
        )
        if uri_index < 0 or extinf_index < 0:
            block = []
            return

        url = block[uri_index].strip()
        if url in seen_urls:
            block = []
            return

        block[extinf_index] = normalize_extinf(block[extinf_index])
        output.extend(block[:uri_index])
        output.append(url)
        seen_urls.add(url)
        count += 1
        block = []

    for raw_line in lines:
        line = raw_line.strip().lstrip("\ufeff")
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF:"):
            flush_pending()
            block = [line]
        elif block:
            if line.startswith("http://") or line.startswith("https://"):
                block.append(line)
                flush_pending()
            elif line.startswith("#"):
                block.append(line)
            else:
                # Discard malformed/non-HTTP records rather than publishing bad
                # entries that could poison the app's local Room catalogue.
                block = []

    flush_pending()
    if count == 0:
        raise RuntimeError("IPTV-org n'a renvoyé aucune chaîne valide ; master.m3u conservé.")
    return "\n".join(output) + "\n", count


def generate_m3u() -> None:
    print(f"Téléchargement de la playlist mondiale IPTV-org : {SOURCE_URL}")
    source = download_source()
    master, count = build_master(source)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT_PATH.with_suffix(".m3u.tmp")
    temporary.write_text(master, encoding="utf-8", newline="\n")
    temporary.replace(OUTPUT_PATH)
    print(f"Master prêt : {count} chaînes IPTV-org, doublons supprimés, pays conservés.")
    print(f"Fichier : {OUTPUT_PATH.as_posix()}")


if __name__ == "__main__":
    try:
        generate_m3u()
    except (OSError, urllib.error.URLError, RuntimeError) as error:
        raise SystemExit(f"Échec de génération : {error}") from error
