import { createServer } from "node:http";
import { createReadStream } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = join(fileURLToPath(new URL("..", import.meta.url)));
const server = createServer((req, res) => {
  const path = normalize(join(root, decodeURIComponent(req.url === "/" ? "/frontend/collapsible-fixture.html" : req.url)));
  if (!path.startsWith(root)) { res.writeHead(403); res.end(); return; }
  const type = {".js":"text/javascript", ".html":"text/html", ".css":"text/css"}[extname(path)] || "application/octet-stream";
  createReadStream(path).on("error", () => { res.writeHead(404); res.end(); }).on("open", () => { res.writeHead(200, {"content-type": type}); }).pipe(res);
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const browser = await chromium.launch({headless:true, ...(process.env.CHROMIUM_PATH ? {executablePath:process.env.CHROMIUM_PATH} : {})});
try {
  for (const mobile of [false, true]) {
    const context = await browser.newContext({viewport:mobile ? {width:390, height:844} : {width:1280, height:900}, colorScheme:mobile ? "dark" : "light", isMobile:mobile});
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:${server.address().port}/frontend/collapsible-fixture.html`);
    const toggle = page.locator("[data-card-toggle]");
    await page.waitForSelector("[data-card-toggle]");
    if (await toggle.getAttribute("aria-expanded") !== "false") throw new Error(`${mobile ? "mobile" : "desktop"}: card did not start collapsed`);
    if (await page.locator(".card-body").getAttribute("hidden") === null) throw new Error(`${mobile ? "mobile" : "desktop"}: body visible initially`);
    if ((await page.locator("script[src*='maplibre']").count()) !== 0) throw new Error(`${mobile ? "mobile" : "desktop"}: MapLibre initialized while collapsed`);
    if (!(await page.locator(".summary-temperature").innerText()).includes("9.9")) throw new Error("temperature summary missing");
    if (!(await page.locator(".summary-wind").innerText()).includes("7 km/h")) throw new Error("wind summary missing");
    await page.locator("camper-weather-card").screenshot({path:`${root}/docs/assets/camper-weather-collapsed-${mobile ? "mobile" : "desktop"}.png`});
    await page.evaluate(() => { const element = document.querySelector("[data-card-toggle]"); element.dispatchEvent(new PointerEvent("pointerdown", {bubbles:true})); element.click(); });
    await page.waitForSelector(".panel");
    if (await toggle.getAttribute("aria-expanded") !== "true") throw new Error(`${mobile ? "mobile" : "desktop"}: click did not expand card`);
    if (await page.locator("[data-tab]").count() !== 7) throw new Error("expanded card did not retain all seven sections");
    await page.evaluate(() => { window.__setSnapshot({current:{temperature:12.4, wind:11}, camping_score:72, safety_status:"yellow"}); const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
    await page.waitForTimeout(250);
    if (await toggle.getAttribute("aria-expanded") !== "true") throw new Error(`${mobile ? "mobile" : "desktop"}: HA update collapsed expanded card`);
    if (!(await page.locator(".summary-temperature").innerText()).includes("12.4")) throw new Error("temperature did not update");
    if (!(await page.locator(".status-dot").getAttribute("class")).includes("status-yellow")) throw new Error("safety color did not update");
    await toggle.click();
    await page.waitForTimeout(50);
    if (await toggle.getAttribute("aria-expanded") !== "false") throw new Error(`${mobile ? "mobile" : "desktop"}: second click did not collapse card`);
    await page.evaluate(() => { window.__setSnapshot({current:{temperature:null, wind:null}, camping_score:null, safety_status:undefined}); const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
    await page.waitForTimeout(250);
    if (!(await page.locator(".summary-temperature").innerText()).includes("—")) throw new Error("missing temperature was not rendered safely");
    if (!(await page.locator(".summary-wind").innerText()).includes("—")) throw new Error("missing wind was not rendered safely");
    if (!(await page.locator(".status-dot").getAttribute("class")).includes("status-gray")) throw new Error("missing safety data was not gray");
    await context.close();
  }
  console.log("Collapsible browser test passed: desktop/mobile initial state, pointer/click toggle, state updates, dynamic summary, missing data and seven sections");
} finally { await browser.close(); server.close(); }
