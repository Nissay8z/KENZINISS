# KENZINISS

## VAVOO Live

Le script `generate_m3u.py` interroge le **catalogue MediaHubMX de VAVOO**, et le renouvelle automatiquement toutes les 6 heures avec GitHub Actions.

- La playlist principale conservée pour les anciens lecteurs est `playlist/vavoo-net.m3u`.
- `vavoo-to.m3u`, `vavoo-top.m3u` et `kool-to.m3u` sont des **alias historiques du même catalogue VAVOO**, pas quatre fournisseurs indépendants.
- Toutes les chaînes et variantes restent dans leur catégorie réelle (France, France Sport, Arabia, etc.) ; aucune catégorie artificielle « Doublons ».
- L'attribut `vavoo-source-url` conserve l'URL exacte renvoyée par le catalogue.

**Important :** les entrées `vavoo://...` du M3U ne sont pas des vidéos HTTP directement lisibles. Elles exigent un lecteur intégrant un résolveur VAVOO (ou un proxy local) qui appelle `mediahubmx-resolve.json` au moment de la lecture. Les URL de flux résolues sont temporaires : les écrire dans un fichier M3U statique sur GitHub produirait des liens rapidement périmés.

Si la récupération du catalogue échoue, le générateur échoue sans remplacer les playlists valides précédentes.

[Exécutions du générateur](https://github.com/Nissay8z/KENZINISS/actions/workflows/update-m3u.yml)
