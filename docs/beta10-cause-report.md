# Beta.10 Ursachenbericht

Stand: 2026-10-27 · Ausgangspunkt: `v0.1.0-beta.9`

## Evidenzgrenzen

- **Live verifiziert:** Home Assistant 2026.10.4, Camper Weather geladen, Tracker `device_tracker.wohnmobil_zoe` gültig, HACS 2.0.5 meldet `installed_version=v0.1.0-beta.9`, `available_version=c0f3b36`, `beta=false`, `selected_tag=null`, `ref=main`, `releases=[]`.
- **Statisch bewiesen:** Die Beta.9-Karte ersetzt das Panel bei normalen State-Updates; die frühere Korrektur prüfte nur Fokus/aktives Element. Es gab keinen expliziten Pointer-/Touch-Lock für den nativen iOS-Picker.
- **Statisch bewiesen:** DWD-District-Datensätze ohne Polygon wurden trotz `location_uncertain` in `apply_official_warning_risks()` anhand ihrer Stufe bewertet und konnten damit Orange/55 auslösen.
- **Statisch bewiesen:** `suggest_activity_windows()` bewertete jede einzelne Startstunde, sortierte nur nach Score und gab die ersten drei zurück. Eine 48-Stunden-Grenze und Mindestabstände fehlten.
- **Statisch bewiesen:** Das Temperaturdiagramm enthielt nur eine Polyline ohne Achsen oder Skalenbeschriftung.
- **Nicht verifiziert:** Ein echter iOS-Safari-Picker. WebKit startet in der Entwicklungsumgebung wegen fehlender Systembibliotheken nicht.

## Korrekturregeln

1. DOM-Replacement wird während `pointerdown`, `touchstart`, Fokus und Eingabe verschoben; nach `change`/`pointerup` wird der ausstehende Render einmalig ausgeführt. Event-Listener werden nur beim initialen Shell-Aufbau registriert.
2. DWD-Warnungen erhalten `location_relevance`: `confirmed` bei enthaltener CAP-Geometrie, `possible` bei plausibler Gebietsnamensübereinstimmung ohne Polygon, `unknown` bei fehlender belastbarer Zuordnung. Marinegebiete werden ohne bestätigendes Polygon ausgeschlossen.
3. Nur bestätigte Warnungen beeinflussen den Komfort-/Camping-Score als offizielle Strafung. Unbestimmte Warnungen bleiben sichtbar und führen zu einem transparenten Sicherheitsstatus Gelb statt zu einer unberechtigten Orange-Einstufung.
4. Aktivitätsfenster werden auf 48 Stunden begrenzt, über die gesamte Dauer bewertet, nach Score und Startzeit deterministisch ausgewählt und mit mindestens der Aktivitätsdauer bzw. drei Stunden Abstand getrennt.
5. Diagramme erhalten lokale Zeitlabels, Min-/Max-Puffer, Temperaturlinien und drei Zeitachsenpunkte; fehlende Temperaturwerte bleiben sichtbar unbekannt.

## HACS-Abgrenzung

Der HACS-Commit-Updatefehler ist ein unabhängiger Live-Zustand. Die unterstützte Informationsaktualisierung änderte `beta`, `selected_tag` und `ref` nicht. Es wird weder HACS-Storage direkt manipuliert noch ein Commit installiert. Die Beta-Kanal-Auswahl bleibt ein separater manueller Abnahmepunkt.
