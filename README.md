# Camper Weather

**Wetter-, Camping- und Freizeitassistent für Wohnmobile in Home Assistant.**

> **v0.1.0-beta.9:** Hotfix für stabile mobile Interaktion, Planner-Ladefehler, Tracker-Refresh und konsistente Risikoanzeige. Beta für isolierte Tests und einen manuellen Home-Assistant-/iPhone-Praxistest. Nicht automatisch in VM 104 installieren.

## Deutsch

Camper Weather unterstützt Open-Meteo als primäre Prognosequelle, MET Norway als optionalen Fallback, DWD-Warnungen für Deutschland und RainViewer-Radarframes. Der Standort kann aus Tracker, Home-Zone, manuellem Standort oder Zielort kommen. Die Integration erzeugt Wetter-, Sicherheits-, Komfort- und Warnsensoren sowie die eigene `camper-weather-card`.

### Installation über HACS
1. HACS → Integrationen → **Camper Weather** suchen.
2. Für die Beta „Vorabversionen anzeigen“ aktivieren und `v0.1.0-beta.9` auswählen.
3. Home Assistant neu laden und **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen.
4. `Camper Weather` wählen, den Tracker `device_tracker.wohnmobil_zoe` prüfen und den Standort speichern.
5. Eine Lovelace-Karte über den Karten-Editor hinzufügen. Die Ressource wird automatisch registriert.

### Grenzen der Beta
Die tägliche Standortwahl erfolgt in der Lovelace-Karte; Tracker und technische Fallbacks werden in der Integration konfiguriert. Es gibt keine automatische Markisen-/Ventilsteuerung und keine GPS-Historie. RainViewer, OpenFreeMap und die Ortssuche sind öffentliche Dienste ohne SLA; die Karte blendet Quellenangaben ein und zeigt nach einem begrenzten Timeout einen Fehler. Ein vollständiger HA-/iPhone-Praxistest ist vor der ausdrücklichen Freigabe noch offen.

Amtliche DWD-Warnungen werden zeitlich und, sofern die Antwort dies liefert, nach Geometrie und Höhe geprüft. Bei district-basierten Antworten bleibt der Gültigkeitsbereich ausdrücklich unsicher und wird konservativ in den Camping-Score einbezogen. Tageslicht fließt in Aktivitätsempfehlungen ein; Schwimmen und Skifahren bleiben ohne Wasser-, Schnee- und Lawinendaten eingeschränkt.

## English

Camper Weather is a Home Assistant custom integration for camper weather, camping risks and outdoor planning. It supports Open-Meteo, an optional MET Norway fallback, DWD warnings for Germany, RainViewer radar frames, tracker, Home Zone, manual and destination locations, persistent activity plans, sensors and a custom Lovelace card.

Install the beta from HACS with pre-releases enabled, configure it from the Home Assistant UI, and select `device_tracker.wohnmobil_zoe` where available. No production Home Assistant instance is changed by development or CI.

The beta does not control awnings or valves or keep GPS history. RainViewer and OpenFreeMap are public services without an SLA; missing data is handled as unavailable and attribution is shown. Safety status and comfort score are separate, and the optional `camper_weather.evaluate_window` action returns a structured assessment. A full HA/iPhone practical test remains pending. See `docs/provider-api-keys.md` and `docs/architecture.md`.

DWD district-only responses are kept visibly uncertain and conservatively affect the camping score; daylight is part of activity scoring, while swimming and skiing remain limited without specialist water, snow, or avalanche data.

## Links
- Website: https://www.smartcamper765.de
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Provider/API help: [docs/provider-api-keys.md](docs/provider-api-keys.md)
