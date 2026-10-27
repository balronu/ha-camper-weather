import { createServer } from "node:http";
import { createReadStream } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium, webkit } from "playwright";

const root = join(fileURLToPath(new URL("..", import.meta.url)));
const server = createServer((req, res) => {
  const path = normalize(join(root, decodeURIComponent(req.url === "/" ? "/frontend/location-fixture.html" : req.url)));
  if (!path.startsWith(root)) { res.writeHead(403); res.end(); return; }
  const type = {".js":"text/javascript", ".html":"text/html", ".css":"text/css"}[extname(path)] || "application/octet-stream";
  createReadStream(path).on("error", () => { res.writeHead(404); res.end(); }).on("open", () => { res.writeHead(200, {"content-type": type}); }).pipe(res);
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const browserType = process.env.BROWSER === "webkit" ? webkit : chromium;
const browser = await browserType.launch({headless:true, ...(process.env.CHROMIUM_PATH && process.env.BROWSER !== "webkit" ? {executablePath:process.env.CHROMIUM_PATH} : {})});
try {
  const desktop = process.env.DESKTOP === "1";
  const context = await browser.newContext({viewport:desktop ? {width:1280, height:900} : {width:390, height:844}, colorScheme:desktop ? "light" : "dark", isMobile:!desktop});
  const page = await context.newPage();
  await page.goto(`http://127.0.0.1:${server.address().port}/frontend/location-fixture.html`);
  await page.waitForSelector("[data-location-mode]");
  const mode = page.locator("[data-location-mode]");
  await mode.dispatchEvent("pointerdown");
  await mode.dispatchEvent("pointerup");
  await page.evaluate(() => { window.__openLocationSelect = document.querySelector("[data-location-mode]"); });
  for (let index = 0; index < 5; index += 1) {
    await page.evaluate(() => { const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
  }
  await page.waitForTimeout(250);
  if (!(await mode.evaluate((element) => element === window.__openLocationSelect))) throw new Error("open location select was remounted during repeated HA updates");
  await mode.selectOption("home_zone");
  await page.waitForTimeout(250);
  if (await mode.inputValue() !== "home_zone") throw new Error("location selection after deferred update was not retained");
  for (const requested of ["home_zone", "tracker", "manual", "destination", "tracker"]) {
    await mode.selectOption(requested);
    for (let index = 0; index < 3; index += 1) {
      await page.evaluate(() => { const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
    }
    await page.waitForTimeout(120);
    if (await mode.inputValue() !== requested) throw new Error(`location selection was replaced: ${requested} / ${await mode.inputValue()}`);
  }
  const state = await mode.inputValue();
  const text = await page.locator(".location-panel").innerText();
  const calls = await page.evaluate(() => window.__calls);
  if (state !== "tracker" || !text.includes("tracker")) throw new Error(`stale location state: ${state} / ${text} / ${JSON.stringify(calls)}`);
  const query = page.locator("[data-location-query]");
  await mode.selectOption("manual");
  await query.fill("Trier");
  await page.evaluate(() => { window.__openQueryInput = document.querySelector("[data-location-query]"); });
  for (let index = 0; index < 5; index += 1) {
    await page.evaluate(() => { const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
  }
  await page.waitForTimeout(250);
  if (!(await query.evaluate((element) => element === window.__openQueryInput))) throw new Error("manual location input was remounted during typing");
  const geocodeBefore = (await page.evaluate(() => window.__calls)).filter((call) => call.type === "camper_weather/location/geocode").length;
  await page.locator("[data-location-action=\"search\"]").click();
  await page.waitForSelector("[data-location-result]");
  const geocodeAfter = (await page.evaluate(() => window.__calls)).filter((call) => call.type === "camper_weather/location/geocode").length;
  if (geocodeAfter - geocodeBefore !== 1) throw new Error(`manual location search ran ${geocodeAfter - geocodeBefore} times`);
  const geocodeBeforeEnter = geocodeAfter;
  await query.press("Enter");
  await page.waitForSelector("[data-location-result]");
  const geocodeAfterEnter = (await page.evaluate(() => window.__calls)).filter((call) => call.type === "camper_weather/location/geocode").length;
  if (geocodeAfterEnter - geocodeBeforeEnter !== 1) throw new Error(`manual Enter search ran ${geocodeAfterEnter - geocodeBeforeEnter} times`);
  await page.locator("[data-location-result]").first().click();
  await page.waitForTimeout(250);
  if (await mode.inputValue() !== "manual") throw new Error("manual location result was not applied");
  await mode.selectOption("tracker");
  await page.waitForTimeout(250);
  const globalModeBeforePlanner = await mode.inputValue();
  await page.locator("[data-tab=\"4\"]").click();
  await page.waitForTimeout(200);
  const activity = page.locator("[data-plan-field=\"activity\"]");
  await activity.dispatchEvent("pointerdown");
  await activity.dispatchEvent("pointerup");
  await page.evaluate(() => { window.__openActivitySelect = document.querySelector("[data-plan-field=\"activity\"]"); });
  for (let index = 0; index < 5; index += 1) {
    await page.evaluate(() => { const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
  }
  await page.waitForTimeout(250);
  if (!(await activity.evaluate((element) => element === window.__openActivitySelect))) throw new Error("open planner activity select was remounted during repeated HA updates");
  await activity.selectOption("cycling");
  await page.locator("[data-plan-field=\"location_mode\"]").selectOption("manual");
  await page.waitForSelector("[data-plan-location-query]");
  const plannerQuery = page.locator("[data-plan-location-query]");
  await plannerQuery.fill("Trier");
  await page.evaluate(() => { window.__openPlannerQueryInput = document.querySelector("[data-plan-location-query]"); });
  for (let index = 0; index < 4; index += 1) {
    await page.evaluate(() => { const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
  }
  if (await page.locator("[data-plan-field=\"activity\"]").inputValue() !== "cycling") throw new Error("planner activity selection was replaced");
  if (await page.locator("[data-plan-field=\"location_mode\"]").inputValue() !== "manual") throw new Error("planner location selection was replaced");
  if (!(await plannerQuery.evaluate((element) => element === window.__openPlannerQueryInput))) throw new Error("planner target input was remounted during typing");
  await page.locator("[data-plan-location-action=\"search\"]").click();
  await page.waitForSelector("[data-plan-location-result]");
  await page.locator("[data-plan-location-result]").first().click();
  if (!(await page.locator(".selected-location").innerText()).includes("Trier")) throw new Error("planner target was not selected");
  await page.locator("[data-plan-action=\"assess\"]").click();
  await page.waitForTimeout(100);
  const assessment = await page.evaluate(() => window.__lastPlanAssessment);
  if (assessment.location_name !== "Trier, Rheinland-Pfalz, Deutschland" || assessment.latitude !== 49.75 || assessment.longitude !== 6.64) throw new Error(`planner assessment used wrong target: ${JSON.stringify(assessment)}`);
  await page.locator("[data-plan-action=\"save\"]").click();
  await page.waitForTimeout(100);
  const saved = await page.evaluate(() => window.__lastPlanSave);
  if (saved.location_name !== "Trier, Rheinland-Pfalz, Deutschland" || saved.latitude !== 49.75 || saved.longitude !== 6.64) throw new Error(`planner target was not persisted: ${JSON.stringify(saved)}`);
  await page.locator("[data-tab=\"0\"]").click();
  if (await page.locator("[data-location-mode]").inputValue() !== globalModeBeforePlanner) throw new Error("planner target changed the global weather location");
  await page.locator("[data-tab=\"4\"]").click();
  await page.waitForSelector("[data-edit-plan]");
  await page.locator("[data-edit-plan]").click();
  await page.waitForSelector(".selected-location");
  if (!(await page.locator(".selected-location").innerText()).includes("Trier")) throw new Error("saved planner target was not restored on edit");
  console.log("Location browser test passed: desktop/mobile-style search, focus stability, planner target assessment and persistence");
} finally { await browser.close(); server.close(); }
