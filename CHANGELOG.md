# Changelog

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
