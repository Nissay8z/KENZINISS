# KENZINISS — IPTV-org master

Ce dépôt publie une seule playlist publique : `playlist/master.m3u`.

- Source unique : le catalogue mondial par pays d'IPTV-org (`index.country.m3u`).
- Le générateur conserve `group-title`, `tvg-country`, les logos et les identifiants EPG, et déduplique les URLs.
- GitHub Actions régénère la playlist toutes les 6 heures. Un déclencheur après modification du générateur crée aussi la playlist initiale.
- Pluto TV, Samsung TV Plus, les proxys et les listes VAVOO ne sont pas générés ici. L'application Android utilise son `VavooProvider` natif pour VAVOO et résout le flux uniquement au clic.

URL utilisée dans l'application :
`https://raw.githubusercontent.com/Nissay8z/KENZINISS/main/playlist/master.m3u`

Le catalogue amont peut contenir des chaînes dont la disponibilité évolue ; la génération préserve leurs URLs sans garantir leur fonctionnement continu.
