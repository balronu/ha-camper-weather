# Wetteranbieter und API-Schlüssel

## Open-Meteo
Kein API-Key für die öffentliche, nicht-kommerzielle Nutzung erforderlich. Camper Weather sendet Koordinaten mit vier Nachkommastellen und cached über den Coordinator. Kommerzielle Nutzung und höhere Kontingente benötigen einen passenden Open-Meteo-Vertrag. Fehler werden im Anbieterstatus angezeigt.

## MET Norway
Kein API-Key erforderlich. Der HTTP-User-Agent identifiziert Camper Weather und verweist auf die Projektwebsite; ohne eindeutigen User-Agent kann der Dienst 403 liefern. Die API-Regeln und die Creative-Commons-Bedingungen sind zu beachten.

## DWD
Kein API-Key erforderlich. Die Beta ruft amtliche Warnungsdaten aus dem DWD-WarnApp-Endpunkt ab. Die Warnungen bleiben als amtliche Daten getrennt von den berechneten Campingrisiken.

Die Antwort ist JSONP (`warnWetter.loadWarnings(...)`) und wird vor der Auswertung normalisiert. Der Anbieterstatus unterscheidet aktive Warnungen, keine Warnungen und einen nicht erreichbaren DWD; ein Fehler wird niemals als Entwarnung dargestellt.

## RainViewer
Kein API-Key erforderlich. Die Beta lädt die öffentlich verfügbaren Radar-Frames und verwendet sie als geografisch positioniertes Overlay. Die Karte zeigt die vorgeschriebene Attribution. Verfügbarkeit, Attribution und Nutzungsbedingungen des Dienstes können sich ändern.

## OpenFreeMap / MapLibre
Kein API-Key erforderlich. Die Basiskarte verwendet die öffentliche OpenFreeMap-Style-URL und MapLibre GL JS. OpenFreeMap basiert auf OpenStreetMap-/OpenMapTiles-Daten; die Karte zeigt `© OpenFreeMap · © OpenStreetMap contributors`. Der Dienst ist öffentlich und ohne SLA. Es werden keine Tiles vorab heruntergeladen oder offline gespeichert.

## Nicht implementiert
OpenWeatherMap, Meteoalarm, Lawinen- und Badegewässerdaten sind in dieser Beta nicht aktiv. Es werden keine Platzhalterdaten erzeugt.
