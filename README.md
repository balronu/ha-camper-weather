# Camper Weather

🇩🇪 **Deutsch** | [🇬🇧 English](README.en.md)

**Wetterplanung, Warnungen und Freizeitplanung für Wohnmobile in Home Assistant.**

> **v0.1.3 Stable** ergänzt eine robuste, standardmäßig eingeklappte Lovelace-Karte mit vollständigem Titel und responsivem Statuskopf. Ein Klick zeigt die vollständige Wetteroberfläche.

![Camper Weather – Produktübersicht](docs/assets/camper-weather-overview.png)

*Werbegrafik/Produktübersicht. Die Darstellung ist kein einzelner Live-Screenshot und ersetzt keine individuelle Home-Assistant-Abnahme.*

## Funktionen

- Wettervorhersagen für 24 Stunden, 48 Stunden und 7 Tage
- Wetterdiagramm mit grüner Temperaturlinie, echten Niederschlagsmengen in mm, optionaler Windkurve in km/h, Wettercodes und lokalen Tag-/Nacht-Symbolen
- Sicherheitsstatus **Grün, Gelb, Orange, Rot oder Grau** und separater Komfortscore von 0–100
- Camping-Score mit nachvollziehbaren Wettergründen
- DWD-Warnungen mit zeitlicher, geografischer und – soweit verfügbar – höhenbezogener Prüfung
- Standortmodi: Wohnmobil-GPS, Zuhause, manueller Ort und gespeichertes Reiseziel
- Freizeitplaner mit Zielortsuche, Bewertung, Speichern, Bearbeiten und Löschen
- Interaktive MapLibre-Karte und RainViewer-Regenradar
- Sensoren und die Home-Assistant-Action `camper_weather.evaluate_window`
- Keine automatische Steuerung von Markise, Ventilen oder anderen Geräten

## Installation über HACS

1. In Home Assistant **HACS → Integrationen** öffnen.
2. Nach **Camper Weather** suchen und die stabile Version `v0.1.3` installieren, sobald die offene [HACS-Katalogaufnahme](https://github.com/hacs/default/pull/12942) von den Maintainer:innen freigegeben wurde.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen.
4. **Camper Weather** auswählen und Wetteranbieter, Standortquelle und Aktualisierungsintervall konfigurieren.
5. Eine Lovelace-Karte über den Karten-Editor hinzufügen. Die Integration registriert die Kartenressource automatisch.

Bis zur Katalogaufnahme kann das Repository als benutzerdefiniertes HACS-Repository (`Integration`) hinzugefügt werden: **HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories**.

## Einrichtung und Standort

Die Erstkonfiguration unterstützt einen Home-Assistant-Tracker, die Home-Zone oder feste Koordinaten. Der tägliche Modus kann anschließend in der Karte gewechselt werden:

- **Wohnmobil-GPS:** verwendet die aktuelle Trackerposition.
- **Zuhause:** verwendet die Home-Zone.
- **Manueller Ort:** sucht einen Ort über die vorhandene Ortssuche.
- **Gespeichertes Reiseziel:** verwendet einen zuvor gespeicherten Ort.

Ein Zielort des Freizeitplaners bleibt vom globalen Wetterstandort getrennt. Gespeicherte Aktivitäten behalten ihre Zielkoordinaten und werden beim Bearbeiten wiederhergestellt.

## Lovelace-Karte

Die Karte kann über den visuellen Editor oder YAML hinzugefügt werden:

```yaml
type: custom:camper-weather-card
entry_id: YOUR_CONFIG_ENTRY_ID
```

Die `entry_id` ist nur erforderlich, wenn mehrere Camper-Weather-Einträge vorhanden sind. Die Karte enthält Übersicht, Vorhersage, Warnungen, Aktivitäten, Planer, Karte und Anbieterstatus. Native Auswahlfelder und Eingabefelder bleiben während Home-Assistant-State-Updates stabil.

Beim Laden des Dashboards erscheint die Karte zunächst kompakt und eingeklappt mit Temperatur, Wind, Camping-Score und Sicherheitsfarbe. Der Kartenkopf bleibt sichtbar; ein Klick öffnet oder schließt die vollständige Oberfläche. Im eingeklappten Zustand werden keine Karte, kein Radar und keine Diagramme initialisiert.

## Status, Scores und Vorhersage

- **Sicherheit** beschreibt erkannte Wetter- und Warnrisiken. Grau bedeutet, dass keine ausreichenden Daten für eine sichere Einstufung vorliegen.
- **Komfort** ist ein separater Wert für Temperatur, Wind und weitere Komfortfaktoren.
- **Camping-Score** fasst die Eignung der Wetterlage für Camping zusammen.
- Die Vorhersage bietet 24 Stunden, 48 Stunden und 7 Tage mit Temperatur-, Niederschlags- und Windangaben. Die Wochenansicht zeigt Tages-Minimum/-Maximum und Tagessumme; fehlende Niederschlagswerte bleiben unbekannt.
- Die Windreihe kann separat ein- und ausgeblendet werden. Ein Klick oder Touch auf einen Diagrammpunkt zeigt Zeit/Tag, Temperatur, Niederschlag und Wind.
- Vergangene Planner-Aktivitäten werden nicht unbemerkt neu bewertet.

## DWD-Warnungen

DWD-Warnungen werden nur dann als lokal bestätigt behandelt, wenn die verfügbaren Warncell-/Küstengeometrien, der Zeitraum und die Höheninformation den Standort stützen. Unklare Warnungen werden als möglich oder nicht bestimmbar angezeigt und dürfen nicht automatisch als lokale Entwarnung oder als bestätigtes lokales Risiko interpretiert werden. Ein DWD-Ausfall wird als nicht erreichbar angezeigt und erzeugt keine falsche Entwarnung.

## Aktivitäten und Home-Assistant-Action

Der Freizeitplaner bewertet unter anderem Spazieren, Wandern, Fahrrad, E-Bike, Joggen, Skifahren, Schwimmen, Grillen und Angeln. Für Automationen steht die Antwort-Action bereit:

```yaml
action: camper_weather.evaluate_window
data:
  entry_id: YOUR_CONFIG_ENTRY_ID
  activity: hiking
  start_at: "2026-10-28T10:00:00+01:00"
  duration_minutes: 120
```

Die Action liefert eine strukturierte Bewertung mit Komfortscore, Sicherheitsstatus, Datenqualität und Gründen. Sie steuert keine Geräte.

## Karte und Radar

Die Karte wird erst beim Öffnen initialisiert. MapLibre zeigt den Standort und die Wetterdarstellung; RainViewer stellt verfügbare Radarframes bereit. Bei fehlenden oder nicht erreichbaren Kartendiensten wird ein verständlicher Fehler angezeigt. Quellenangaben bleiben sichtbar.

## Datenquellen und Datenschutz

Camper Weather nutzt je nach Konfiguration Open-Meteo, optional MET Norway, DWD-Warnungen, RainViewer und OpenFreeMap. Diese öffentlichen Dienste können eigene Nutzungsbedingungen und Verfügbarkeitsgrenzen haben. Die Integration speichert keine GPS-Historie und enthält keine Zugangsdaten im Frontend. Weitere Hinweise stehen in [docs/provider-api-keys.md](docs/provider-api-keys.md).

## Fehlerbehebung

- **Keine Wetterdaten:** Anbieterstatus und Datenqualität in der Karte prüfen; bei einem vorübergehenden Ausfall später erneut laden.
- **Tracker nicht verfügbar:** Home-Zone oder einen manuellen Standort wählen und die Tracker-Konfiguration prüfen.
- **DWD nicht erreichbar:** Dies ist keine Entwarnung; der Providerstatus weist ausdrücklich auf den Ausfall hin.
- **Karte leer:** Netzwerkzugriff auf MapLibre/OpenFreeMap/RainViewer und die Browser-Konsole prüfen.
- **Mehrere Einträge:** In Karten und Actions die passende `entry_id` angeben.

## Bekannte Einschränkungen

Die Genauigkeit von Warnungszuordnung hängt von den verfügbaren DWD-Geometrien und der Höhenangabe ab. Öffentliche Karten-, Radar- und Geocoding-Dienste haben keine Verfügbarkeitsgarantie. Schwimmen, Skifahren und ähnliche Aktivitäten werden ohne spezialisierte Wasser-, Schnee- oder Lawinendaten nicht als vollständig sicher bewertet.

## Dokumentation

- [Deutsche Benutzeranleitung](docs/USER_GUIDE_DE.md)
- [English user guide](docs/USER_GUIDE_EN.md)
- [Deutsche Installation](docs/INSTALLATION_DE.md)
- [English installation](docs/INSTALLATION_EN.md)
- [Architektur](docs/architecture.md)
- [Changelog](CHANGELOG.md)

## Lizenz und Danksagungen

Camper Weather steht unter der im Repository enthaltenen [Lizenz](LICENSE). Danke an Home Assistant, Open-Meteo, MET Norway, DWD, MapLibre, OpenFreeMap und RainViewer für die verwendeten Plattformen und Datenangebote.

## English

The complete English presentation is available in [README.en.md](README.en.md). It covers the same verified v0.1.3 feature set, installation status, screenshots, provider limitations and troubleshooting guidance.

## Links

- Website: https://www.smartcamper765.de
- Repository: https://github.com/balronu/ha-camper-weather
- Stable release: https://github.com/balronu/ha-camper-weather/releases/tag/v0.1.3
