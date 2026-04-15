# Karpischek Haus — WorkAdventure Maps

WA-Karten für das L7-Haus in Krems, auto-generiert aus der HausPlan-Collective.

## Struktur

```
karpischek/
├── build_maps.py          Generator: rooms.json → 5× .tmj
├── rooms.json             40 Räume aus Nextcloud Collective (Snapshot)
└── maps/
    ├── erdgeschoss.tmj    9 Räume  [Start-Karte]
    ├── 1_stock.tmj        14 Räume (Zimmer 12–22, Flure, Wäschekammer)
    ├── 2_stock.tmj        3 Räume  (Yogaraum, Flur, Treppe)
    ├── 1_hof.tmj          11 Räume (Garagen, Werkstätten, HofCafé)
    └── 2_hof.tmj          3 Räume  (Barn, Man-Cave, Scheunentrakt)
```

## Was die Karten enthalten

- **Jeder Raum = 8×6 Tiles** mit Tür nach Süden, auf ein Korridor-Raster gesetzt
- **Website-Zone pro Raum** → SPACE drücken öffnet die Collective-Seite
  (z. B. `https://own.fe80.eu/apps/collectives/HausPlan/1.%20Stock/Zimmer%2014`)
- **Named Areas** zeigen "Zimmer 14 (Captains Quarter)" als Floor-Label
- **Inter-Floor-Exits** zwischen Stockwerken (links = vorheriges, rechts = nächstes)
- **Spawn-Punkt** oben mittig

## Workflow

```bash
# 1. rooms.json ggf. neu aus der Collective bauen (nur lokal möglich):
#    siehe https://own.fe80.eu/apps/collectives/HausPlan
# 2. Maps neu generieren:
cd karpischek/
python3 build_maps.py

# 3. In Tiled öffnen und Layout manuell verfeinern
```

Die Tilesets liegen im Repo-Root unter `../tilesets/` und werden geteilt mit
den Rössl-Maps (`office.tmj`, `conference.tmj`).

## Status: Scaffolding

Das ist **Grundgerüst, nicht Finalversion**. Der Generator macht ein Raster-Layout
ohne Architekturbezug.

### Noch zu tun

- [ ] DXF-Grundrisse (`Laserscan_TD_Haider/`) als Referenz-PNG unterlegen und
      echte Wandverläufe in Tiled nachziehen
- [ ] Treppen visuell darstellen (aktuell nur unsichtbare Exit-Zonen)
- [ ] Möbel aus dem Collective (`# Gegenstände`-Section) übernehmen
- [ ] Jitsi-Zonen für Konferenz-Räume (Büro, Holodeck, HofCafé)
- [ ] silent-Zonen für Meditations-/Yoga-Räume
- [ ] Photo-Zonen mit Verlinkung auf `ZimmerPhotos/`
- [ ] Start-Spawn an korrekter Treppen-Position je nach Herkunftsfloor

### Raumtypen-Empfehlungen

| Raum                          | Property-Idee                |
|-------------------------------|-------------------------------|
| Büro, Backoffice              | `jitsiRoom: buero`            |
| Salon                         | `silent: true` + Radio-URL    |
| Mu-Fu dunkel (Holodeck)       | Video-Embed property          |
| Garage 6 (Podcaststudio)      | `jitsiRoom: studio`           |
| Garage 7 (Proberaum)          | Audio-Stream-Embed            |
| HofCafé                       | Jitsi + Menü-Website          |
| Yogaraum                      | `silent: true`                |
| Zimmer 14 (Captains Quarter)  | Collective-Seite (✓)          |

## Quelle

- Collective: `https://own.fe80.eu/apps/collectives/HausPlan`
- Laserscan-Daten: L7 Nextcloud (TD Haider, Mai 2025)
- Generator entstand aus Haus-Tour-Projekt (siehe `haus.html`, `handplans/`)
