# Camper Weather – Installation

## Voraussetzungen

- Home Assistant 2026.10.4 oder neuer empfohlen
- HACS oder eine manuelle Custom-Integration-Installation
- Internetzugriff für die konfigurierten Wetter-, Warnungs-, Karten- und Radarprovider

## HACS

1. HACS öffnen und **Integrationen** wählen.
2. `Camper Weather` suchen.
3. Die stabile Version `v0.1.3` installieren.
4. Home Assistant die Integration laden lassen.
5. Unter **Einstellungen → Geräte & Dienste → Hinzufügen** `Camper Weather` auswählen.

## Konfiguration

Vergib einen Namen, wähle Open-Meteo oder den konfigurierten Anbieter und lege Tracker, Home-Zone oder Koordinaten fest. MET Norway, DWD und RainViewer können je nach Bedarf aktiviert werden. Eine zusätzliche kostenpflichtige API ist für die Standardkonfiguration nicht erforderlich; Nutzungsbedingungen der Anbieter gelten.

## Karte hinzufügen

Über den Lovelace-Karteneditor **Camper Weather** auswählen. Bei mehreren Einträgen `entry_id` setzen:

```yaml
type: custom:camper-weather-card
entry_id: YOUR_CONFIG_ENTRY_ID
```

Die Integration registriert das JavaScript automatisch über Home Assistant. Eine manuelle Dashboard-Ressource ist nicht erforderlich.

## Prüfen

Öffne die Karte, wähle einen Standort und prüfe den Tab **Anbieter**. Bei Problemen siehe [Benutzeranleitung](USER_GUIDE_DE.md) und [provider-api-keys.md](provider-api-keys.md).
