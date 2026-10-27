import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../custom_components/camper_weather/www/camper-weather-card.js", import.meta.url), "utf8");
const required = [
  'const VERSION = "0.1.0-beta.10"',
  "getStubConfig() { return {}; }",
  'type:"camper_weather/list_entries"',
  "openfreemap.org/styles/liberty",
  "maplibre-gl@5.6.2",
  "ResizeObserver",
  "camper_weather/location/geocode",
  "data-location-mode",
  "weather-glyph",
  "item.is_day",
  "statusLabels",
  "window.confirm",
  "camper_weather/planner/save",
  "camper_weather/planner/delete",
  "data-forecast-range",
  "window.customCards",
];
for (const marker of required) {
  if (!source.includes(marker)) throw new Error(`missing frontend contract: ${marker}`);
}
if (source.includes("tile.openstreetmap.org")) throw new Error("blocked OSM raster endpoint is still embedded");
if (!/type:CARD_TYPE/.test(source)) throw new Error("custom card picker metadata is missing bare type");
console.log(`frontend contracts passed (${required.length})`);
