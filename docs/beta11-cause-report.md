# Beta.11 Ursachenbericht

Stand: 2026-10-27 · Ausgangspunkt: `v0.1.0-beta.10`

## Nachgewiesene Ursachen

- **Standort:** Der Config Entry verwendet `device_tracker.wohnmobil_zoe`; die Koordinaten werden im Coordinator gelesen und an Open-Meteo übergeben. Die Standortauswahl wird persistent gespeichert und wartet auf den Refresh. Der offene Fehler war nicht ein stiller Home-Zone-Wechsel, sondern dass Warnungen vor der geografischen Prüfung als globale Feed-Einträge weitergereicht wurden.
- **DWD:** Der WarnWetter-Feed enthält WarncellIDs wie `501000002` (Helgoland) und `903452002` (Kreis Aurich – Küste). Beta.10 prüfte ohne gelieferte CAP-Geometrie nur `unknown`; diese Einträge blieben dadurch in der lokalen Darstellung und erzeugten wiederholte unbekannte Warnungsrisiken.
- **Geografie:** Der DWD dokumentiert WarncellID/AGS und veröffentlicht offizielle Shape-Dateien für Landkreis- und Küstenwarngebiete. Der bisherige CAP-Index-Lookup verwendete nur den aktuellen Status-ZIP; im Live-Lauf enthielt dieses ZIP keine passenden Landwarnungsgeometrien.
- **UI:** Die Karte schützt den Panel-Render inzwischen während aktiver Interaktion, lädt aber weiterhin asynchron neue Daten. Beta.11 testet die vollständige Sequenz mit wiederholten HA-Updates einschließlich Planerfeldern; ein iOS/WebKit-Nachweis bleibt eine Geräte-/Runner-Grenze.

## Beta.11-Korrekturen

1. Offizielle DWD-CUSTOMER-/COAST-Polygone werden best-effort geladen und anhand der WarncellID verwendet. Ein Geometrieausfall bleibt `unknown`; er wird nicht als Entwarnung behandelt.
2. Helgoland- und Aurich-Warnungen werden für den Saarland-Punkt anhand offizieller Geometrie ausgeschlossen. Polygone werden weiterhin gegen den aktuellen Standort geprüft, inklusive Höhen- und Zeitfenster.
3. Unklare Warnungsrisiken werden als eine zusammengefasste Meldung dargestellt; bestätigte Warnungen bleiben einzeln und score-relevant.
4. Version, Manifest, Frontend-Bundle, Release-Dokumentation und Regressionstests werden auf Beta.11 angehoben.

## Grenzen

- WebKit/iPhone ist in der lokalen Umgebung wegen fehlender Systembibliotheken nicht ausführbar.
- VM 104 bleibt unverändert; HACS-Pre-Release-Auswahl und Installation sind eine manuelle UI-Abnahme.
- Der DWD-Geometrieabruf ist ein öffentlicher Dienst ohne SLA. Bei Ausfall wird eine Warnung vorsorglich separat als geografisch unklar angezeigt.
