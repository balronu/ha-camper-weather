# Architektur und Beta-Grenzen

Camper Weather besitzt eine Config Entry pro Fahrzeug/Standortprofil. Der Coordinator lädt eine ausgewählte Quelle, nutzt MET Norway nur als explizit aktivierten Open-Meteo-Fallback und hält DWD/RainViewer getrennt. Es gibt keine GPS-Historie und keine Gerätesteuerung.

Die Lovelace-Karte wird durch die Integration über eine versionierte Extra-JS-URL registriert. Der WebSocket liefert nur aktuelle Wetter-/Warn-/Radar-Daten und keine API-Schlüssel. Browser-Cache-Busting ist auf die eigene Ressource begrenzt; ein einmaliger Reload kann bei HA-/WebView-Caches nötig bleiben.

Die Beta enthält eine mobile Übersicht, Vorhersage, Warnungen, Anbieterstatus und eine einfache Standortkarte. Aktivitätsprofile und Planer sind im Backend als Bewertungs-Engine vorbereitet, der vollständige grafische Planer folgt nach dem ersten Praxistest.

