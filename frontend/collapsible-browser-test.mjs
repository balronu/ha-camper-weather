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
  for (const width of [320, 390, 768, 1280]) {
    const mobile = width <= 390;
    const context = await browser.newContext({viewport:{width, height:mobile ? 844 : 900}, colorScheme:mobile ? "dark" : "light", isMobile:mobile});
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:${server.address().port}/frontend/collapsible-fixture.html`);
    const toggle = page.locator("[data-card-toggle]");
    await page.waitForSelector("[data-card-toggle]");
    const label = `${width}px`;
    if (await toggle.getAttribute("aria-expanded") !== "false") throw new Error(`${label}: card did not start collapsed`);
    if (await page.locator(".card-body").getAttribute("hidden") === null) throw new Error(`${label}: body visible initially`);
    if ((await page.locator("script[src*='maplibre']").count()) !== 0) throw new Error(`${label}: MapLibre initialized while collapsed`);
    const layout = await page.evaluate(() => {
      const card = document.querySelector("camper-weather-card");
      const header = card.querySelector(".card-header");
      const title = card.querySelector(".card-title h2");
      const toggle = card.querySelector(".expand-icon");
      const summary = card.querySelector(".card-summary");
      const subtitle = card.querySelector(".subtitle");
      const bounds = (node) => { const r = node.getBoundingClientRect(); return {left:r.left, right:r.right, top:r.top, bottom:r.bottom, width:r.width, height:r.height}; };
      return {card:bounds(card), header:bounds(header), title:bounds(title), toggle:bounds(toggle), summary:bounds(summary), subtitle:bounds(subtitle), titleText:title.textContent, scrollWidth:card.scrollWidth, clientWidth:card.clientWidth};
    });
    if (layout.titleText !== "Camper Weather") throw new Error(`${label}: title text changed`);
    if (layout.title.width <= 0 || layout.title.right > layout.header.right + 1) throw new Error(`${label}: title is clipped`);
    if (layout.toggle.width <= 0 || layout.toggle.height <= 0 || layout.toggle.left < layout.header.left || layout.toggle.right > layout.header.right + 1) throw new Error(`${label}: toggle is not visible or leaves header`);
    if (layout.scrollWidth > layout.clientWidth + 1) throw new Error(`${label}: horizontal overflow detected`);
    if (layout.subtitle.width <= 0 || layout.summary.width <= 0 || layout.summary.right > layout.header.right + 1) throw new Error(`${label}: lower status row leaves header`);
    if (!(await page.locator(".summary-temperature").innerText()).includes("9.9")) throw new Error("temperature summary missing");
    if (!(await page.locator(".summary-wind").innerText()).includes("7 km/h")) throw new Error("wind summary missing");
    if (width === 390 || width === 1280) await page.locator("camper-weather-card").screenshot({path:`${root}/docs/assets/camper-weather-collapsed-${mobile ? "mobile" : "desktop"}.png`});
    await page.evaluate(() => { const element = document.querySelector("[data-card-toggle]"); element.dispatchEvent(new PointerEvent("pointerdown", {bubbles:true})); element.click(); });
    await page.waitForSelector(".panel");
    if (await toggle.getAttribute("aria-expanded") !== "true") throw new Error(`${label}: click did not expand card`);
    if (await page.locator("[data-tab]").count() !== 7) throw new Error("expanded card did not retain all seven sections");
    await page.evaluate(() => { window.__setSnapshot({current:{temperature:12.4, wind:11}, camping_score:72, safety_status:"yellow"}); const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
    await page.waitForTimeout(250);
    if (await toggle.getAttribute("aria-expanded") !== "true") throw new Error(`${label}: HA update collapsed expanded card`);
    if (!(await page.locator(".summary-temperature").innerText()).includes("12.4")) throw new Error("temperature did not update");
    if (!(await page.locator(".status-dot").getAttribute("class")).includes("status-yellow")) throw new Error("safety color did not update");
    for (const [temperature, wind, score] of [[13.1, 8, 81], [14.2, 9, 88], [12.8, 6, 76]]) {
      await page.evaluate(([nextTemperature, nextWind, nextScore]) => { window.__setSnapshot({current:{temperature:nextTemperature, wind:nextWind}, camping_score:nextScore, safety_status:"orange"}); const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; }, [temperature, wind, score]);
      await page.waitForTimeout(80);
      if (await toggle.getAttribute("aria-expanded") !== "true") throw new Error(`${label}: repeated HA update changed expanded state`);
    }
    await toggle.click();
    await page.waitForTimeout(50);
    if (await toggle.getAttribute("aria-expanded") !== "false") throw new Error(`${label}: second click did not collapse card`);
    await page.evaluate(() => { window.__setSnapshot({current:{temperature:null, wind:null}, camping_score:null, safety_status:undefined}); const card = document.querySelector("camper-weather-card"); card.hass = {connection:card._hass.connection, callWS:card._hass.callWS}; });
    await page.waitForTimeout(250);
    if (!(await page.locator(".summary-temperature").innerText()).includes("—")) throw new Error("missing temperature was not rendered safely");
    if (!(await page.locator(".summary-wind").innerText()).includes("—")) throw new Error("missing wind was not rendered safely");
    if (!(await page.locator(".status-dot").getAttribute("class")).includes("status-gray")) throw new Error("missing safety data was not gray");
    await context.close();
  }
  console.log("Collapsible browser test passed: 320/390/768/1280px layout, full title, visible toggle, wrapping, repeated state updates, pointer/click toggle, dynamic summary, missing data and seven sections");
} finally { await browser.close(); server.close(); }
