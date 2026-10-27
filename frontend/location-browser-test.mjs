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
  const context = await browser.newContext({viewport:{width:390, height:844}, colorScheme:"dark", isMobile:true});
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
  for (let index = 0; index < 4; index += 1) {
    await page.evaluate(() => { const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
  }
  if (await page.locator("[data-plan-field=\"activity\"]").inputValue() !== "cycling") throw new Error("planner activity selection was replaced");
  if (await page.locator("[data-plan-field=\"location_mode\"]").inputValue() !== "manual") throw new Error("planner location selection was replaced");
  console.log("Location browser test passed: mobile dark-mode location and planner selections survive repeated HA updates");
} finally { await browser.close(); server.close(); }
