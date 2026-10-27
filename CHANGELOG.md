# Changelog

## [0.1.0-beta.11] – 2026-10-27

### Deutsch

- DWD-Warnungen werden mit den offiziellen Warncell-Polygonen für Landkreis- und Küstengebiete gegen den tatsächlich ausgewählten Standort geprüft.
- Eindeutig ortsfremde Warnungen werden ausgeschlossen; unklare Zuordnungen bleiben separat und beeinflussen den lokalen Camping-Score nicht.
- Standortdiagnose, veraltete Antworten und native Auswahl-/Planer-Eingaben wurden gegen wiederholte HA-Updates abgesichert.
- Prognose-/Aktivitätsdarstellung und Warnungszusammenfassungen wurden dedupliziert und klarer zwischen Komfort und Sicherheit getrennt.

### English

- DWD warnings now use the official Warncell polygons for county and coastal areas to evaluate the selected location.
- Clearly unrelated warnings are excluded; genuinely unresolved geography remains separate and does not change the local camping score.
- Location diagnostics, stale responses, and native location/planner inputs are protected against repeated HA updates.
- Forecast/activity presentation and warning summaries are deduplicated and separate comfort from safety.

This remains a beta. No productive Home Assistant installation or iPhone/WebKit acceptance is included in this release.

## [0.1.0-beta.10] – 2026-10-27

### Deutsch

- Native Dropdowns und Touch-/Pointer-Interaktionen werden während HA-State-Updates geschützt.
- DWD-Warnungen erhalten eine explizite Standortrelevanz; unbekannte Geometrie wird nicht mehr als bestätigte lokale Gefahr bewertet.
- Warnungsdarstellung zeigt Gebiet, Zeitraum, Stufe und Zuordnungsbegründung kompakt.
- Aktivitätsempfehlungen nutzen getrennte, deterministische Zeitfenster innerhalb der nächsten 48 Stunden.
- Temperaturdiagramme enthalten Zeitachse, Temperaturskala und lokale Zeitdarstellung.
- Planner-Historie, Datenqualität und Anbieterstatus werden verständlicher dargestellt.

### English

- Native dropdowns and touch/pointer interactions are protected during Home Assistant state updates.
- DWD warnings now expose explicit location relevance; unknown geometry is no longer treated as a confirmed local hazard.
- Warning cards compactly show area, period, level, and matching rationale.
- Activity recommendations use separated, deterministic windows within the next 48 hours.
- Temperature charts include a time axis, temperature scale, and local time display.
- Planner history, data quality, and provider status are presented more clearly.

## [0.1.0-beta.9] – 2026-10-27

### Deutsch

- Frontend-State bei Home-Assistant-Updates stabilisiert: offene Bereiche, Eingaben und native Auswahlfelder bleiben erhalten.
- MapLibre wird bei gewöhnlichen State-Updates nicht unnötig neu initialisiert.
- Planner-Ladefehler werden nicht mehr als leere Aktivitätsliste dargestellt; der Backend-Vertrag ist korrigiert.
- Tracker-State-Änderungen lösen einen gezielten Coordinator-Refresh aus.
- Sicherheitsstatus, Komfortscore und nächstes Risiko werden getrennt und nachvollziehbar angezeigt.

### English

- Stabilized frontend state across Home Assistant updates: open sections, inputs, and native selects are preserved.
- MapLibre is no longer reinitialized for ordinary state updates.
- Planner load failures are no longer rendered as an empty activity list; the backend contract is corrected.
- Tracker state changes trigger a targeted coordinator refresh.
- Safety status, comfort score, and next risk are shown separately and transparently.

## [0.1.0-beta.8] – 2026-10-27

### Deutsch

- GitHub-Default-Branch auf `main` korrigiert; HACS-Branchauswahl wird nicht mehr durch den alten Beta-Foundation-Commit bestimmt.
- Gemeinsame Wetter-Engine mit Standortbindung, Datenqualität, getrenntem Sicherheitsstatus und Komfortscore ergänzt.
- Sicherheitsstatus Grün/Gelb/Orange/Rot/Grau, nachvollziehbare Gründe, Wind-/Regen-/Temperaturtrends und zweisprachige Zusammenfassungen ergänzt.
- Warnungszustände werden pro Config Entry persistent dedupliziert; Beginn, Änderung und Ende erzeugen nur bei echten Zustandsänderungen Events.
- Neue Sensoren für Sicherheit, Komfort, Zusammenfassung, nächstes Risiko und Datenqualität sowie die Action `camper_weather.evaluate_window` ergänzt.
- Bestehende Standortwahl, DWD-Marine-/Geometrieprüfung, Radar, Karte, Aktivitäten und gespeicherte Pläne bleiben erhalten.

### English

- Corrected the GitHub default branch to `main`; HACS no longer uses the old beta-foundation commit as the repository branch reference.
- Added a shared weather engine with explicit location binding, data quality, separate safety status and comfort score.
- Added Green/Yellow/Orange/Red/Gray safety states, explainable reasons, wind/rain/temperature trends and bilingual summaries.
- Warning states are persisted and deduplicated per config entry; start, change and end events are emitted only for real state transitions.
- Added safety, comfort, summary, next-risk and data-quality sensors plus the `camper_weather.evaluate_window` action.
- Existing location selection, DWD marine/geometry checks, radar, map, activities and saved plans are preserved.

**Limitations / Hinweise:** Kein Zugriff auf VM 104 und kein produktiver HA-/iPhone-Test. HACS muss auf VM 104 nach der Repository-Korrektur aktualisiert und lokal auf die Beta-Version eingestellt werden.

## [0.1.0-beta.7] – 2026-10-26

### Deutsch

- Standortwechsel wartet auf den tatsächlichen Wetter-Refresh, schützt schnelle GPS/Home/manuelle/Reiseziel-Wechsel vor verspäteten Antworten und stellt bei Fehlern die vorherige Auswahl wieder her.
- Aktiver Standortmodus und aufgelöster Standort werden getrennt angezeigt; Standortänderungen aktualisieren Wetter, Warnungen, Scores und Kartenposition konsistent.
- Offizielle DWD-Seewettergebiete aus dem strukturierten `501000…`-Gebietsnummernraum werden nicht mehr als lokale Campingwarnungen bewertet. Verfügbare CAP-Geometrien werden für Landwarnungen übernommen; unbekannte Geografie bleibt unsicher.
- Mobile Chromium-Regression für echte Standortauswahlereignisse sowie neue DWD-Saarland-/Seewettertests ergänzt.

### English

- Location changes now wait for the actual weather refresh, protect rapid GPS/home/manual/destination switches from stale responses, and restore the previous selection on errors.
- The active location mode and resolved location are displayed separately; weather, warnings, scores, and map position update consistently.
- Official DWD marine areas in the structured `501000…` area namespace are no longer scored as local camping warnings. Available CAP geometries enrich land warnings; unknown geography remains explicitly uncertain.
- Added mobile Chromium regression coverage for real location selection events and DWD Saarland/marine cases.

**Limitations / Hinweise:** Kein produktiver Test auf VM 104 und kein echter iPhone-Abnahmetest. WebKit bleibt abhängig von den verfügbaren Systembibliotheken und wird separat berichtet.

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
