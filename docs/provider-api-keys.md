# Wetteranbieter und API-Schlüssel

## Open-Meteo
Kein API-Key für die öffentliche, nicht-kommerzielle Nutzung erforderlich. Camper Weather sendet Koordinaten mit vier Nachkommastellen und cached über den Coordinator. Kommerzielle Nutzung und höhere Kontingente benötigen einen passenden Open-Meteo-Vertrag. Fehler werden im Anbieterstatus angezeigt.

## MET Norway
Kein API-Key erforderlich. Der HTTP-User-Agent identifiziert Camper Weather und verweist auf die Projektwebsite; ohne eindeutigen User-Agent kann der Dienst 403 liefern. Die API-Regeln und die Creative-Commons-Bedingungen sind zu beachten.

## DWD
Kein API-Key erforderlich. Die Beta ruft amtliche Warnungsdaten aus dem DWD-WarnApp-Endpunkt ab. Die Warnungen bleiben als amtliche Daten getrennt von den berechneten Campingrisiken.

## RainViewer
Kein API-Key erforderlich. Die Beta lädt nur die öffentlich verfügbaren Radar-Frame-Metadaten und verwendet sie für die Kartendarstellung. Verfügbarkeit, Attribution und Nutzungsbedingungen des Dienstes können sich ändern.

## Nicht implementiert
OpenWeatherMap, Meteoalarm, Lawinen- und Badegewässerdaten sind in dieser Beta nicht aktiv. Es werden keine Platzhalterdaten erzeugt.

