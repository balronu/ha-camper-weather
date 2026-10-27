# Camper Weather – User Guide

## 1. Overview

Camper Weather combines weather forecasts, DWD warnings, camping score and activity planning in one Lovelace card. Safety and comfort are intentionally shown as separate assessments.

The card loads in a compact collapsed state. The first row keeps the safety color, full title and toggle visible; the lower rows show the version, temperature, wind and camping score. On narrow displays, weather values may wrap without truncating the title. Tap or click the card header to open all seven sections; the header remains available to collapse it again. Home Assistant state updates do not change this state.

![Actual collapsed card in a desktop browser](assets/camper-weather-collapsed-desktop.png)

![Actual collapsed card at mobile width](assets/camper-weather-collapsed-mobile.png)

## 2. Choosing a location

Choose **Motorhome GPS**, **Home**, **Manual location** or a saved destination. For a manual location, enter a place, press **Search** or use Enter, then select a unique result. The global weather location changes only after an overview result is selected.

## 3. Reading the forecast

Use **24 h**, **48 h** or **7 days**. The green line shows temperature and blue bars show actual precipitation in mm. Use **Show wind** to add a separate dashed wind curve. Symbols below the time axis are derived from the weather code and local day/night phase. A point can be selected with mouse or touch to show its detail values. The 7-day view uses daily minimum/maximum temperature and daily precipitation totals instead of 168 individual points. Missing values remain unavailable; precipitation probability (%) is kept separate from precipitation amount (mm).

![Actual desktop chart](assets/camper-weather-chart-desktop.png)

![Actual mobile-width chart](assets/camper-weather-chart-mobile.png)

## 4. Safety and comfort

Green means no critical risks were detected. Yellow and orange indicate increased attention or restrictions. Red indicates a critical weather situation. Gray means that the available data is insufficient for a reliable safety assessment. The comfort score is separate and is not a safety guarantee.

## 5. DWD warnings

Confirmed warnings have a supported local relationship. Missing geometry or unverifiable elevation is shown as possible or undetermined. A provider failure is not an all-clear.

## 6. Activity planner

1. Choose an activity, date, start time and duration.
2. Choose **Manual target location** when the activity is not at the current motorhome location.
3. Search for and select a target place.
4. Press **Assess** and review comfort, safety and reasons.
5. Press **Save**. Saved activities can be edited later.

Planner targets are assessed with their own coordinates and never change the global weather location. Past activities are not silently reassessed.

## 7. Map and radar

The **Map** tab shows the location, map layers and available RainViewer radar frames. The map initializes only when opened and reports provider errors explicitly.

## 8. Missing data

Check the **Providers** tab for service status, last successful update and technical diagnostics. If the tracker is unavailable, Home or a manual location can be used temporarily.

## 9. Privacy

Camper Weather does not store a GPS history. Location and activity data remain tied to the Home Assistant config entry. Public providers receive only the location and weather parameters required for the request.
