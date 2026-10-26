# Architektur und Beta-Grenzen

Camper Weather besitzt eine Config Entry pro Fahrzeug/Standortprofil. Der Coordinator lädt eine ausgewählte Quelle, nutzt MET Norway nur als explizit aktivierten Open-Meteo-Fallback und hält DWD/RainViewer getrennt. Standortquellen sind Tracker, Home-Zone, manueller Standort und temporärer Zielort; eine letzte gültige Trackerposition wird als veraltet gekennzeichnet. Es gibt keine GPS-Historie und keine Gerätesteuerung.

Die Lovelace-Karte wird durch die Integration über eine versionierte Extra-JS-URL registriert. Der WebSocket liefert nur aktuelle Wetter-/Warn-/Radar-Daten und keine API-Schlüssel. Browser-Cache-Busting ist auf die eigene Ressource begrenzt; ein einmaliger Reload kann bei HA-/WebView-Caches nötig bleiben.

Die Beta enthält eine mobile Übersicht, kompakte Temperaturgrafik, Warnungen, Anbieterstatus, persistenten Planer und eine OpenFreeMap/MapLibre-Karte mit RainViewer-Overlay. Der Planer verwendet persistente HA-Storage-Daten und kanonische String-IDs. MapLibre wird bei Bedarf einmalig geladen; bei fehlender Kartenverbindung bleiben Koordinaten und Radarstatus sichtbar.
