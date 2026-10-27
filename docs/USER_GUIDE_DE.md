# Camper Weather – Benutzeranleitung

## 1. Überblick

Camper Weather verbindet Wettervorhersage, DWD-Warnungen, Camping-Score und Freizeitplanung in einer Lovelace-Karte. Sicherheit und Komfort werden bewusst getrennt dargestellt.

## 2. Standort verwenden

Wähle in der Übersicht **Wohnmobil-GPS**, **Zuhause**, **Manueller Ort** oder ein gespeichertes Reiseziel. Bei einem manuellen Ort den Namen eingeben, **Suchen** drücken oder Enter verwenden und anschließend ein eindeutiges Ergebnis auswählen. Der aktuelle globale Wetterstandort wird erst nach Auswahl eines Übersichtsergebnisses geändert.

## 3. Vorhersage lesen

Nutze die Umschaltung **24 h**, **48 h** oder **7 Tage**. Temperaturverlauf, Niederschlag und Wind werden mit lokaler Zeit dargestellt. Fehlende Daten werden als nicht verfügbar angezeigt.

## 4. Sicherheit und Komfort

Grün bedeutet keine erkannten kritischen Risiken. Gelb und Orange weisen auf erhöhte Aufmerksamkeit oder Einschränkungen hin. Rot steht für eine kritische Wetterlage. Grau bedeutet, dass die Datenlage für eine belastbare Sicherheitsbewertung nicht ausreicht. Der Komfortscore ist unabhängig davon und kein Sicherheitsversprechen.

## 5. DWD-Warnungen

Bestätigte Warnungen haben einen nachvollziehbaren Standortbezug. Bei fehlender Geometrie oder nicht prüfbarer Höhe wird die Zuordnung als möglich oder nicht bestimmbar markiert. Ein Providerfehler ist keine Entwarnung.

## 6. Freizeitplaner

1. Aktivität, Datum, Startzeit und Dauer auswählen.
2. **Manueller Zielort** wählen, wenn die Aktivität nicht am aktuellen Wohnmobilstandort stattfinden soll.
3. Zielort suchen und ein Ergebnis auswählen.
4. **Bewerten** drücken und Komfort, Sicherheit und Gründe prüfen.
5. Mit **Speichern** ablegen. Gespeicherte Aktivitäten können später bearbeitet werden.

Der Planner-Zielort wird mit eigenen Koordinaten bewertet und verändert den globalen Wetterstandort nicht. Vergangene Aktivitäten werden nicht automatisch neu bewertet.

## 7. Karte und Radar

Im Tab **Karte** werden Standort, Kartenebenen und verfügbare RainViewer-Radarframes angezeigt. Die Karte lädt erst beim Öffnen; bei einem Dienstfehler erscheint ein Hinweis.

## 8. Fehlende Daten

Prüfe den Tab **Anbieter**. Dort stehen Betriebsstatus, letzte erfolgreiche Aktualisierung und technische Diagnose. Bei einem Trackerfehler kann vorübergehend Zuhause oder ein manueller Ort verwendet werden.

## 9. Datenschutz

Camper Weather speichert keine GPS-Historie. Standort- und Aktivitätsdaten bleiben an den Home-Assistant-Eintrag gebunden. Öffentliche Datenanbieter erhalten nur die für die jeweilige Anfrage erforderlichen Standort- und Wetterparameter.
