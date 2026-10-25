#!/usr/bin/env python3
"""
Generate four domain-named VAVOO M3U lists using MediaHubMX.

Each playlist URL is vavoo://<upstream-id>. The matching Android resolver
rebuilds https://vavoo.to/vavoo-iptv/play/<upstream-id> before calling
mediahubmx-resolve.json.
"""
from __future__ import annotations

import json
import platform
import re
import unicodedata
import sys
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

PING_URLS = (
    "https://www.vavoo.tv/api/app/ping",
    "https://vavoo.tv/api/app/ping",
)
BASE_URLS = (
    "https://vavoo.to",
    "https://kool.to",
    "https://vavoo.top",
    "https://vavoo.net",
)

LANGUAGE = "fr"
REGION = "US"
CLIENT_VERSION = "3.0.2"
USER_AGENT = "VAVOO/2.6"
MEDIAHUB_USER_AGENT = "MediaHubMX/2"
MAX_PAGES = 300
REQUEST_TIMEOUT = (15, 30)
# Exactly four entries are exposed in Shamel's Playlist screen.
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
    """Same MediaHubMX paging payload as VavooProvider.loadCatalogFromBase()."""
    last_error: Exception | None = None

    for base in BASE_URLS:
        channels: list[dict] = []
        cursor = None
        try:
            for page_number in range(1, MAX_PAGES + 1):
                payload = {
                    "language": LANGUAGE,
                    "region": REGION,
                    "catalogId": "iptv",
                    "id": "iptv",
                    "adult": False,
                    "search": "",
                    "sort": "",
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
                if not isinstance(body, dict):
                    raise ValueError(f"Format catalogue inattendu depuis {base}.")
                items = body.get("items") or []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("type", "")).lower() != "iptv":
                        continue
                    if not str(item.get("url") or "").strip():
                        continue
                    channels.append(item)

                next_cursor = body.get("nextCursor")
                if next_cursor is None or str(next_cursor).strip() == "":
                    print(f"Catalogue reçu via {urlparse(base).netloc}: {len(channels)} chaînes, {page_number} page(s).")
                    if channels:
                        return channels
                    raise ValueError(f"Le catalogue VAVOO reçu depuis {base} est vide.")
                cursor = next_cursor
            raise RuntimeError(f"Le catalogue dépasse la limite de {MAX_PAGES} pages.")
        except Exception as exc:
            last_error = exc
            print(f"Source {urlparse(base).netloc} indisponible: {exc}", file=sys.stderr)

    raise RuntimeError(f"Tous les serveurs catalogue VAVOO ont échoué: {last_error}")


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


def strip_internal_variant(name: str) -> str:
    """Remove VAVOO's technical .c/.s/.b suffix from the displayed station name."""
    return re.sub(r"\\s+\\.[csb]$", "", (name or "").strip(), flags=re.IGNORECASE).strip()


def canonical_channel_name(name: str) -> str:
    """Normalize obvious stream variants but never remove the country/group key."""
    value = strip_internal_variant(name)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.casefold()
    value = re.sub(r"\\b(full\\s*hd|uhd|fhd|2160p|1440p|1080p|720p|576p|480p|4320p|2160|1080|720|4k|8k|hevc|h\\.?265|h\\.?264|hd|sd)\\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def quality_score(name: str) -> int:
    """Use explicit quality tokens only; the upstream catalog provides no bitrate field."""
    value = (name or "").casefold().replace("_", " ")
    if re.search(r"\\b(8k|4320p|uhd|2160p|2160)\\b", value):
        return 90
    if re.search(r"\\b(4k)\\b", value):
        return 88
    if re.search(r"\\b(full\\s*hd|fhd|1080p|1080)\\b", value):
        return 78
    if re.search(r"\\b(hd|720p|720)\\b", value):
        return 62
    if re.search(r"\\b(576p|480p|sd)\\b", value):
        return 35
    return 50


def candidate_rank(entry: tuple[str, str, str, str]) -> tuple:
    group, name, channel_id, logo = entry
    # Explicit resolution wins first, a usable logo is the next tie-breaker.
    # If the catalog does not expose quality metadata, choose a stable deterministic
    # candidate rather than claiming an unverified bitrate/stream-health result.
    suffix = bool(re.search(r"\\s+\\.[csb]$", name, flags=re.IGNORECASE))
    return (
        quality_score(name),
        1 if logo.strip() else 0,
        0 if suffix else 1,
        -len(name),
        name.casefold(),
        channel_id,
    )


def build_playlist(items: list[dict]) -> list[str]:
    # Keep a best candidate for each (exact group, normalized station name).
    # Variants go into a separate "Doublons" category instead of being mixed with
    # the preferred version in France, France Sport, Arabia, etc.
    winners: dict[tuple[str, str], tuple[str, str, str, str]] = {}
    alternatives: list[tuple[str, str, str, str]] = []
    skipped_no_id = 0
    duplicate_count = 0

    for item in items:
        raw_name = str(item.get("name") or "Chaîne VAVOO").strip()
        source_url = str(item.get("url") or "").strip()
        channel_id = extract_stream_id(source_url)
        if not channel_id:
            skipped_no_id += 1
            continue

        group = channel_group(item)
        logo = str(item.get("logo") or "").strip()
        entry = (group, raw_name, channel_id, logo)
        key = (group.casefold(), canonical_channel_name(raw_name))
        if not key[1]:
            key = (group.casefold(), raw_name.casefold())

        previous = winners.get(key)
        if previous is None:
            winners[key] = entry
            continue
        if previous[2] == channel_id:
            # Same upstream stream repeated in the catalog; do not create an
            # alternative row that would open the exact same ID.
            continue

        duplicate_count += 1
        if candidate_rank(entry) > candidate_rank(previous):
            alternatives.append(previous)
            winners[key] = entry
        else:
            alternatives.append(entry)

    primary: list[tuple[str, str, str, str]] = []
    for group, name, channel_id, logo in winners.values():
        # Strip only the provider's internal suffix, retaining real HD/4K labels.
        primary.append((group, strip_internal_variant(name), channel_id, logo))

    drawer: list[tuple[str, str, str, str]] = []
    seen_alternative_ids: set[str] = set()
    for original_group, name, channel_id, logo in alternatives:
        if channel_id in seen_alternative_ids:
            continue
        seen_alternative_ids.add(channel_id)
        drawer.append(("Doublons", f"{name} — {original_group}", channel_id, logo))

    entries = primary + drawer
    # Put the alternative drawer last in category order; keep all other groups intact.
    entries.sort(key=lambda row: (
        1 if row[0].casefold() == "doublons" else 0,
        row[0].casefold(),
        row[1].casefold(),
        row[2],
    ))
    if not entries:
        raise RuntimeError(
            "Aucune chaîne n'a fourni un ID reconnaissable dans son URL catalogue. "
            "Le fichier existant n'a pas été remplacé."
        )

    lines = ["#EXTM3U"]
    for group, name, channel_id, logo in entries:
        group_attr = safe_attribute(group)
        name_attr = safe_attribute(name)
        logo_attr = safe_attribute(logo)
        id_attr = safe_attribute(channel_id)
        lines.append(
            f'#EXTINF:-1 tvg-id="{id_attr}" tvg-name="{name_attr}" '
            f'tvg-logo="{logo_attr}" group-title="{group_attr}",{name_attr}'
        )
        lines.append(f"vavoo://{channel_id}")

    from collections import Counter
    groups = Counter(group for group, _name, _id, _logo in entries)
    print(
        f"Chaînes principales: {len(primary)}; alternatives dans Doublons: {len(drawer)}; "
        f"doublons détectés: {duplicate_count}; IDs invalides ignorés: {skipped_no_id}."
    )
    print("Groupes M3U: " + ", ".join(
        f"{name} ({count})" for name, count in groups.most_common(30)
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
