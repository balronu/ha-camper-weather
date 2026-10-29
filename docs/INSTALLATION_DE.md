# Camper Weather – Installation

## Voraussetzungen

- Home Assistant 2026.10.4 oder neuer empfohlen
- HACS oder eine manuelle Custom-Integration-Installation
- Internetzugriff für die konfigurierten Wetter-, Warnungs-, Karten- und Radarprovider

## HACS

Die Aufnahme in das offizielle [HACS-Standardrepository](https://github.com/hacs/default/pull/12942) ist beantragt, aber noch nicht von den Maintainer:innen freigegeben.

Bis dahin:

1. HACS öffnen und **Integrationen → ⋮ → Benutzerdefinierte Repositories** wählen.
2. `balronu/ha-camper-weather` als Repository vom Typ **Integration** hinzufügen.
3. Die stabile Version `v0.1.3` installieren.
4. Home Assistant die Integration laden lassen.
5. Unter **Einstellungen → Geräte & Dienste → Hinzufügen** `Camper Weather` auswählen.

Nach einer offiziellen Katalogaufnahme kann die Integration direkt über die HACS-Suche installiert werden. Es wird keine zweite Einreichung erstellt.

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
