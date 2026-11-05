#!/usr/bin/env python3
"""
Generate VAVOO catalogue playlists directly from the live MediaHubMX API.

The four historic file names are compatibility aliases, NOT independent
sources. They all contain the latest successfully retrieved real VAVOO
catalogue, preserving every upstream variant and group. There is no
"Doublons" drawer or synthetic group.

The entries are vavoo:// references, NOT direct .m3u8 streams: the
VavooProvider running in the player must call mediahubmx-resolve.json
at playback time. Resolved stream links are short lived and must never
be baked into a public GitHub M3U.
"""
from __future__ import annotations

import json
import platform
import sys
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

PING_URLS = (
    "https://www.vavoo.tv/api/app/ping",
    "https://vavoo.tv/api/app/ping",
)
# Try current VAVOO cluster endpoints first; legacy paths only as fallback.
# A response is usable only if a complete, non-empty IPTV catalog is returned.
CATALOG_ENDPOINTS = (
    ("https://vavoo.to/vto-cluster", "vto-iptv"),
    ("https://vavoo.net/vto-cluster", "vto-iptv"),
    ("https://vavoo.top/vto-cluster", "vto-iptv"),
    ("https://kool.to/kool-cluster", "kool-iptv"),
    ("https://vavoo.to", "iptv"),
    ("https://vavoo.net", "iptv"),
)


LANGUAGE = "fr"
REGION = "US"
CLIENT_VERSION = "3.0.2"
USER_AGENT = "VAVOO/2.6"
MEDIAHUB_USER_AGENT = "MediaHubMX/2"
MAX_PAGES = 300
REQUEST_TIMEOUT = (15, 30)
# Historic file names remain for compatibility. These are aliases of ONE VAVOO catalogue.
OUTPUTS = {
    "vavoo.to": Path("playlist/vavoo-to.m3u"),
    "kool.to": Path("playlist/kool-to.m3u"),
    "vavoo.top": Path("playlist/vavoo-top.m3u"),
    "vavoo.net": Path("playlist/vavoo-net.m3u"),
}

session = requests.Session()
session.headers.update(
    {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": USER_AGENT,
        "Accept-Language": LANGUAGE,
        "Connection": "close",
    }
)


def post_json(address: str, payload: dict, signature: str | None = None,
              mediahub: bool = False) -> dict | list:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "Connection": "close",
        "User-Agent": MEDIAHUB_USER_AGENT if mediahub else USER_AGENT,
    }
    if mediahub:
        headers["Accept-Language"] = LANGUAGE
        headers["mediahubmx-signature"] = signature or ""
    response = session.post(
        address,
        json=payload,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    if not response.ok:
        body = (response.text or "").strip().replace("\n", " ")
        raise requests.HTTPError(
            f"HTTP {response.status_code} sur {urlparse(address).netloc}: {body[:240]}",
            response=response,
        )
    data = response.json()
    if data is None:
        raise ValueError(f"Réponse JSON vide depuis {address}")
    return data


def get_addon_signature() -> str:
    """Same ping endpoint and payload structure as VavooProvider.java."""
    now_ms = int(__import__("time").time() * 1000)
    machine = platform.machine() or "unknown"
    payload = {
        "reason": "app-focus",
        "locale": LANGUAGE,
        "theme": "dark",
        "metadata": {
            "device": {
                "type": "mobile",
                "uniqueId": "nisskenzi-" + str(uuid.uuid4()),
            },
            "os": {
                "name": "android",
                "version": platform.release() or "unknown",
                "abis": [machine],
                "host": platform.node() or "android",
            },
            "app": {"platform": "android"},
            "version": {
                "package": "tv.vavoo.app",
                "binary": "3.1.8",
                "js": "3.1.8",
            },
        },
        "appFocusTime": 0,
        "playerActive": False,
        "playDuration": 0,
        "devMode": False,
        "hasAddon": True,
        "castConnected": False,
        "package": "tv.vavoo.app",
        "version": "3.1.8",
        "process": "app",
        "firstAppStart": now_ms,
        "lastAppStart": now_ms,
        "ipLocation": None,
        "adblockEnabled": True,
        "proxy": {
            "supported": ["ss"],
            "engine": "Mu",
            "enabled": False,
            "autoServer": True,
        },
        "iap": {"supported": False},
    }

    last_error: Exception | None = None
    for ping_url in PING_URLS:
        try:
            reply = post_json(ping_url, payload, mediahub=False)
            if isinstance(reply, dict):
                signature = str(reply.get("addonSig") or "").strip()
                if signature:
                    return signature
                last_error = ValueError("La réponse VAVOO ne contient pas addonSig.")
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Impossible d'obtenir addonSig VAVOO: {last_error}")


def fetch_catalog(signature: str) -> list[dict]:
    """Fetch and paginate a real VAVOO catalog, trying documented cluster routes."""
    last_error: Exception | None = None

    for base, catalog_id in CATALOG_ENDPOINTS:
        channels: list[dict] = []
        cursor = None
        seen_cursors = set()
        try:
            for page_number in range(1, MAX_PAGES + 1):
                payload = {
                    "language": LANGUAGE,
                    "region": REGION,
                    "catalogId": catalog_id,
                    "id": catalog_id,
                    "adult": False,
                    "search": "",
                    "sort": "name",
                    "filter": {},
                    "cursor": cursor,
                    "clientVersion": CLIENT_VERSION,
                }
                body = post_json(
                    base + "/mediahubmx-catalog.json",
                    payload,
                    signature=signature,
                    mediahub=True,
                )
                if not isinstance(body, dict) or not isinstance(body.get("items"), list):
                    raise ValueError(f"Format de catalogue inattendu : {base}")
                for item in body["items"]:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("type", "iptv")).lower() != "iptv":
                        continue
                    if str(item.get("url") or "").strip():
                        channels.append(item)

                next_cursor = body.get("nextCursor")
                if next_cursor is None or str(next_cursor).strip() in ("", "null"):
                    if not channels:
                        raise ValueError(f"Catalogue vide : {base}")
                    print(f"Catalogue VAVOO réel reçu de {base} : {len(channels)} références en {page_number} pages.")
                    return channels

                marker = json.dumps(next_cursor, sort_keys=True)
                if marker in seen_cursors:
                    raise RuntimeError("Curseur de pagination répété")
                seen_cursors.add(marker)
                cursor = next_cursor
            raise RuntimeError(f"Plus de {MAX_PAGES} pages de catalogue : {base}")
        except Exception as exc:
            last_error = exc
            print(f"Source VAVOO indisponible ({base}): {exc}", file=sys.stderr)

    raise RuntimeError(f"Aucun catalogue VAVOO valide. Dernière erreur : {last_error}")


def extract_country(group: str) -> str:
    """Exact same group separator handling as VavooProvider.extractCountry()."""
    group = (group or "").strip()
    if not group:
        return "default"
    for separator in ("➾", "⟾", "->", "→", "»", "›"):
        if separator in group:
            country = group.split(separator, 1)[0].strip()
            return country or "default"
    return group


def extract_stream_id(source_url: str) -> str:
    """
    MediaHub items normally point to /vavoo-iptv/play/<id>.
    A few generations include the ID as a final .m3u8 path segment; handle that too.
    """
    parsed = urlparse((source_url or "").strip())
    path = unquote(parsed.path or "").rstrip("/")
    if not path:
        return ""

    marker = "/vavoo-iptv/play/"
    if marker in path:
        value = path.split(marker, 1)[1].split("/", 1)[0]
    else:
        value = path.rsplit("/", 1)[-1]
        if value.endswith(".m3u8"):
            value = value[:-5]

    value = value.strip()
    if not value or value.lower() in {"play", "index"}:
        return ""
    if any(ch in value for ch in ("\r", "\n", "/", "?", "#")):
        return ""
    return value


def safe_attribute(value: object) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    return text.replace('"', "'")


def channel_group(item: dict) -> str:
    # Preserve each exact MediaHubMX group string. Never merge France Sport into France.
    group = str(item.get("group") or "").strip()
    if group and group.lower() not in {"default", "vavoo live"}:
        return group

    country = str(
        item.get("country")
        or item.get("countryName")
        or item.get("country_name")
        or ""
    ).strip()
    return country if country and country.lower() not in {"default", "vavoo live"} else "Autres"


def build_playlist(items: list[dict]) -> list[str]:
    """Preserve every real source and its exact original category.

    We only collapse byte-for-byte repeated source URLs within the same
    category. HD/FHD/4K, .c/.s/.b and fallback streams remain in the
    original VAVOO categories, never in a drawer.
    """
    entries: list[tuple[str, str, str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    invalid = 0

    for item in items:
        source_url = str(item.get("url") or "").strip()
        channel_id = extract_stream_id(source_url)
        if not channel_id:
            invalid += 1
            continue

        group = channel_group(item)
        name = str(item.get("name") or "Chaîne VAVOO").strip()
        logo = str(item.get("logo") or "").strip()
        key = (group, source_url)
        if key in seen:
            continue
        seen.add(key)
        entries.append((group, name, channel_id, logo, source_url))

    entries.sort(key=lambda row: (row[0].casefold(), row[1].casefold(), row[2], row[4]))
    if not entries:
        raise RuntimeError("Aucune chaîne VAVOO exploitable : les fichiers existants restent inchangés.")

    lines = ["#EXTM3U"]
    for group, name, channel_id, logo, source_url in entries:
        # Store the actual catalogue reference for native app resolvers.
        # vavoo:// remains a virtual URI; it requires a playback-time provider.
        lines.append(
            f'#EXTINF:-1 tvg-id="{safe_attribute(channel_id)}" '
            f'tvg-name="{safe_attribute(name)}" tvg-logo="{safe_attribute(logo)}" '
            f'group-title="{safe_attribute(group)}" '
            f'vavoo-source-url="{safe_attribute(source_url)}",{safe_attribute(name)}'
        )
        lines.append(f"vavoo://{channel_id}")

    from collections import Counter
    groups = Counter(row[0] for row in entries)
    print(f"VAVOO : {len(entries)} sources, {len(groups)} catégories, {invalid} URLs sans identifiant.")
    print("Principales catégories : " + ", ".join(
        f"{key} ({count})" for key, count in groups.most_common(20)
    ))
    return lines



def main() -> None:
    print("Obtention de la signature VAVOO…")
    signature = get_addon_signature()
    print("Chargement du catalogue MediaHubMX…")
    catalog = fetch_catalog(signature)
    lines = build_playlist(catalog)

    payload = "\n".join(lines) + "\n"
    for label, output in OUTPUTS.items():
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(output)
        print(f"Playlist générée : {label} -> {output} ({len(lines) - 1} lignes de contenu)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        raise SystemExit(1)
