# Camper Weather

**Wetter-, Camping- und Freizeitassistent für Wohnmobile in Home Assistant.**

> **v0.1.0-beta.1:** Beta für isolierte Tests und einen manuellen Home-Assistant-Praxistest. Nicht automatisch in VM 104 installieren.

## Deutsch

Camper Weather unterstützt Open-Meteo als primäre Prognosequelle, MET Norway als optionalen Fallback, DWD-Warnungen für Deutschland und RainViewer-Radar-Metadaten. Der Standort kann aus einem Device Tracker oder manuell kommen. Die Integration erzeugt Wetter-, Camping- und Warnsensoren sowie die eigene `camper-weather-card`.

### Installation über HACS
1. HACS → Integrationen → **Camper Weather** suchen.
2. Für die Beta „Vorabversionen anzeigen“ aktivieren und `v0.1.0-beta.1` auswählen.
3. Home Assistant neu laden und **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen.
4. `Camper Weather` wählen, den Tracker `device_tracker.wohnmobil_zoe` prüfen und den Standort speichern.
5. Eine Lovelace-Karte über den Karten-Editor hinzufügen. Die Ressource wird automatisch registriert.

### Grenzen der Beta
Es gibt keine automatische Markisen-/Ventilsteuerung, keine GPS-Historie, keine Live-Provider-Authentifizierung im Releaseprozess und noch keinen vollständigen grafischen Freizeitplaner. Die Karte nutzt in dieser Beta eine kontrollierte OpenStreetMap-basierte Standortfläche; Radar-Frame-Metadaten werden angezeigt, die vollständige Tile-Zeitsteuerung ist der nächste Ausbau. Diese Punkte werden nicht als fertig ausgegeben.

## English

Camper Weather is a Home Assistant custom integration for camper weather, camping risks and outdoor planning. It supports Open-Meteo, an optional MET Norway fallback, DWD warnings for Germany, RainViewer radar metadata, tracker/manual locations, sensors and a custom Lovelace card.

Install the beta from HACS with pre-releases enabled, configure it from the Home Assistant UI, and select `device_tracker.wohnmobil_zoe` where available. No production Home Assistant instance is changed by development or CI.

The beta does not control awnings or valves, keep GPS history, provide live provider credentials, or claim a complete activity planner/radar tile timeline. See `docs/provider-api-keys.md` and `docs/architecture.md`.

## Links
- Website: https://www.smartcamper765.de
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Provider/API help: [docs/provider-api-keys.md](docs/provider-api-keys.md)

