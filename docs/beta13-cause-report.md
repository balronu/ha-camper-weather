# Camper Weather v0.1.0-beta.13 – Standort- und Planner-Ursachenbericht

## Nachgewiesene Ursachen

### A/C – Übersichtssuche und Fokus

Die Suche las den Wert erst beim Button-Klick direkt aus dem DOM, hatte keinen
Enter-Handler und behandelte den Fokusverlust eines Textfelds wie das Ende
einer vollständigen Interaktion. Beim `focusout` konnte ein verzögerter
`hass`-Render deshalb den Such-Button oder das Eingabefeld vor dem
anschließenden Click ersetzen. Die Suchantwort wurde dann nicht zuverlässig
angezeigt; auf mobilen Geräten wirkte das wie ein erforderlicher zweiter
Klick.

Beta.13 führt einen eigenen Textfeld-Interaktionszustand ein. Eingaben werden
über `input` im Entwurf gehalten, `focusout` löst keinen Panel-Rebuild aus,
und Suche wird genau einmal über Click oder Enter gestartet. Ergebnisse werden
gezielt in den Ergebnisbereich geschrieben, statt das gesamte Panel zu
montieren.

### B/D – Planner-Zielort und Standortfehler

Der Planner übermittelte bisher nur `location_mode`. Für `manual` fehlten
Name und Koordinaten; das Backend bewertete deshalb mit dem globalen
Coordinator-Standort. Zusätzlich war der Planner an die globale
Standortauswahl gekoppelt, wodurch die Fehlermeldung des globalen
Standortwechsels erscheinen konnte.

Beta.13 hält Planner-Zielort, Suchtext und Suchergebnisse separat vom globalen
Standort. Die vorhandene Geocoding-WebSocket-Suche wird wiederverwendet. Name
und Koordinaten werden in der bestehenden Aktivität gespeichert. Die
Bewertung lädt für einen manuellen Planner-Zielort die bestehende Wetterquelle
für dessen Koordinaten und verwendet diesen Forecast; der globale
Camper-Weather-Standort bleibt unverändert.

### Backend-Sequenzschutz

Planner-Eingaben werden weiterhin aus dem lokalen Entwurf an Bewertung und
Speicherung übergeben. Der bestehende Standort-Token schützt globale
Standortantworten; Planner-Zielorte verwenden keinen globalen
`location/set`-Request. Gespeicherte Aktivitäten mit Zielname und Koordinaten
werden beim Bearbeiten wiederhergestellt.

## Regressionsevidenz

- 51 Python-Tests einschließlich manueller Zielortvalidierung und
  Zielkoordinaten-Kontext.
- Desktop Chromium: helle Ansicht, vollständige Texteingabe, wiederholte
  HA-Updates, Click- und Enter-Suche, genau ein Suchrequest, Auswahl und
  globale Standorttrennung.
- Mobile Chromium: dunkle Ansicht, Touch-/Pointer-Interaktion, dieselben
  Such- und Planner-Flows, DOM-Identität und verzögerte Updates.
- Planner: Aktivität, manueller Zielort Trier, Bewertung, Speichern,
  Tab-Wechsel und erneutes Bearbeiten mit wiederhergestelltem Zielort.
- Bestehende State-Update- und MapLibre-Lifecycle-Tests bleiben grün.
- WebKit/iPhone ist separat zu bewerten; der Host kann Playwright-WebKit nur
  mit fehlenden Systembibliotheken nicht starten.

## Scope

Unverändert bleiben DWD-Warnungen, Wetter-/Score-Logik außerhalb der
Planner-Zielortbewertung, Vorhersage-/Diagramm-UI, MapLibre/RainViewer,
Entity-IDs, gespeicherte Aktivitätsstruktur, HACS-Daten und VM 104.

