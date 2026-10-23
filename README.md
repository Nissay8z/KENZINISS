# KENZINISS

Builds a single public M3U bouquet from community-maintained public playlists. GitHub Actions refreshes it every six hours.

## Master playlist

Raw URL for NISSKENZI+:

`https://raw.githubusercontent.com/Nissay8z/KENZINISS/main/playlist/master.m3u`

Web view: `https://github.com/Nissay8z/KENZINISS/blob/main/playlist/master.m3u`

Each channel entry carries `x-source-id` and `x-source-name` M3U attributes so the Android app can keep source categories separate while reading one file.

## Included sources

- IPTV-org France
- IPTV-org Monde arabe
- IPTV-org Afrique
- Pluto TV France (community M3U endpoint)
- Samsung TV Plus France (community M3U endpoint)
- Free-TV International

Edit `SOURCES` in `generate_m3u.py` to add or remove inputs. All streams are copied as-is from those public playlist sources; the script does not resolve streams or scrape VAVOO.

## VAVOO is separate

This repository does **not** publish a VAVOO playlist. VAVOO channel listing and stream resolution remain in the native Android app via `VavooProvider`; resolution happens only after a channel is selected.

## Schedule

The `Build public master M3U` workflow runs every six hours, on relevant pushes to `main`, or manually with **Actions → Build public master M3U → Run workflow**. If any configured input is unavailable, generation fails without replacing the last good `playlist/master.m3u`.
