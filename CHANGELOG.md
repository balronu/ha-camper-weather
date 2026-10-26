# Changelog

## [0.1.0-beta.6] – 2026-10-26

### Deutsch
- DWD-Warnungen werden anhand offizieller Kennungen beziehungsweise stabiler fachlicher Merkmale dedupliziert, nach Schweregrad sortiert und nicht über unterschiedliche Zeiträume oder Gebiete zusammengeführt.
- Aktivitätswarnungen werden einmalig und mit kurzen Zusammenfassungen angezeigt; vollständige Warntexte bleiben aufklappbar.
- GPS-Tracker-Zustände unterscheiden gültige Koordinaten, fehlende/unbekannte Tracker, nicht verfügbare Tracker, veraltete Positionen und technische Ersatzstandorte.
- Mobile Stundenprognose nutzt Tag-/Nacht-Symbole, `is_day`, lokale Zeitdarstellung und eine gepufferte Temperaturskala.
- Providerstatus werden deutsch/englisch verständlich dargestellt; technische Fehlercodes bleiben in einer Diagnoseansicht verfügbar.
- Plan-Löschen erfordert eine Bestätigung. Bestehende Einstellungen, Ziele und Aktivitäten bleiben erhalten.

### English
- DWD warnings are deduplicated by official identifiers or stable domain attributes, sorted by severity, and kept separate across periods and areas.
- Activity warnings are counted once and shown as short summaries with expandable full text.
- GPS tracker states distinguish valid coordinates, missing/unknown/unavailable trackers, stale positions, and technical fallback locations.
- The mobile hourly forecast now uses day/night icons, `is_day`, local time formatting, and a padded temperature scale.
- Provider statuses have German/English user-facing labels while raw error codes remain available in a diagnostic disclosure.
- Deleting a saved plan requires confirmation. Existing settings, destinations, and activities are preserved.

## [0.1.0-beta.5] – 2026-10-26

### Deutsch
- GPS-Tracker-Overrides korrigiert: Eine Auswahl von `device_tracker.wohnmobil_zoe` bleibt vom Home-Zone-Config-Modus getrennt.
- Tracker-Ausfälle werden als veraltet oder technischer Ersatzstandort gekennzeichnet, nie als aktuelle GPS-Position.
- Standortrevisionen verhindern das Speichern von Freizeitplänen mit veralteten Koordinaten.
- DWD-Warnungen werden zeitlich, höhenbezogen und – sofern Geometrie vorliegt – geometrisch gefiltert; unbekannte Gültigkeit bleibt als Unsicherheit sichtbar.
- Amtliche Warnstufen fließen konservativ in den Camping-Score ein.
- Aktivitätsbewertungen berücksichtigen Tageslicht; Schwimmen und Skifahren behaupten ohne Spezialdaten keine vollständige Sicherheit bzw. Tauglichkeit.
- WebSocket-Registrierung und Standort-/DWD-Regressionsfälle erweitert.

### English
- Fixed GPS tracker overrides so selecting `device_tracker.wohnmobil_zoe` remains separate from a Home Zone config mode.
- Tracker failures are marked stale or technical fallback, never as the current GPS position.
- Location revisions prevent saving plans against stale coordinates.
- DWD warnings are filtered by time, altitude, and geometry where available; unknown scope remains visible as uncertainty.
- Official warning levels now conservatively affect the camping score.
- Activity scores account for daylight; swimming and skiing do not claim complete safety or suitability without specialist data.
- Expanded WebSocket registration and location/DWD regression coverage.

## [0.1.0-beta.4] – 2026-10-26

### Deutsch
- MapLibre-Lifecycle mit Timeout, ResizeObserver und verständlichem Fehlerzustand stabilisiert.
- Aktivitätsspeicherung auf einen bestätigten Persistenz-Request verkürzt.
- Lovelace-Standortauswahl für GPS, Home-Zone, manuelle Orte und gespeicherte Reiseziele ergänzt.
- Responsive Navigation, einklappbare Bereiche, kompakte Vorhersage und SVG-Wettericons verbessert.
- DWD- und Radarabrufe mit begrenztem Timeout und Cache entlastet.

### English
- Stabilized the MapLibre lifecycle with timeout, resize handling, and an explicit error state.
- Reduced activity saving to one confirmed persistence request.
- Added Lovelace location selection for GPS, home zone, manual places, and saved destinations.
- Improved responsive navigation, collapsible sections, compact forecasts, and SVG weather icons.
- Added bounded DWD and radar caching to reduce repeated provider load.

## [0.1.0-beta.3] – 2026-10-26

### Deutsch
- Planer-IDs werden unabhängig vom Frontend-Typ kanonisch als Zeichenketten gespeichert; CRUD bleibt restartfest.
- DWD-JSONP wird korrekt verarbeitet und Statuswerte unterscheiden Warnungen, keine Warnungen und Providerfehler.
- Empfehlungen werden an die Karte übergeben und die Standortmodi Tracker, Home-Zone, manuell und Zielort werden unterstützt.
- OpenStreetMap-Rasterkacheln durch OpenFreeMap/MapLibre mit sichtbarer Attribution ersetzt.
- Kompakte Temperaturgrafik, mobile Navigation, dynamische Fahrzeugauswahl und verständlichere Provider-/Zeitdarstellung.

### English
- Planner IDs are canonicalized to strings across frontend types and remain restart-safe through CRUD operations.
- DWD JSONP is parsed correctly and status values distinguish active warnings, no warnings, and provider failures.
- Recommendations are exposed to the card and tracker, Home Zone, manual, and destination location modes are supported.
- OpenStreetMap raster tiles are replaced by OpenFreeMap/MapLibre with visible attribution.
- Added compact temperature chart, mobile navigation, dynamic vehicle selection, and clearer provider/time display.

## [0.1.0-beta.2] – 2026-10-26

### Deutsch
- Freizeitplaner mit persistenter Speicherung, vollständiger Zeitfensterbewertung und Empfehlungen.
- OSM-Karte mit echten RainViewer-Radarkacheln, Frame-Zeitleiste und Start/Pause.
- Stabilere Lovelace-DOM-Aktualisierung, iOS-freundliche Eingaben und grafischer Karteneditor.
- Erweiterte Provider-, Planer- und Versionsverträge in den automatisierten Tests.

### English
- Activity planner with persistent storage, complete-window assessment, and recommendations.
- OSM map with real RainViewer radar tiles, frame timeline, and play/pause controls.
- More stable Lovelace DOM updates, iOS-friendly inputs, and a graphical card editor.
- Extended provider, planner, and version-contract coverage in automated tests.

## [0.1.0-beta.1] – 2026-10-26

### Deutsch
- Erste HACS-fähige Beta mit Config Flow und Options Flow.
- Open-Meteo, MET-Norway-Fallback, DWD-Warnungen und RainViewer-Metadaten.
- Tracker-/manueller Standort, Camping- und Warnsensoren, Score-Engine und eigene Lovelace-Karte.

### English
- First HACS-ready beta with Config Flow and Options Flow.
- Open-Meteo, MET Norway fallback, DWD warnings and RainViewer metadata.
- Tracker/manual location, camping and warning sensors, score engine and custom Lovelace card.
