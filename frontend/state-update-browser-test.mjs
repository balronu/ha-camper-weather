import { createServer } from "node:http";
import { createReadStream } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = join(fileURLToPath(new URL("..", import.meta.url)));
const server = createServer((req, res) => {
  const path = normalize(join(root, decodeURIComponent(req.url === "/" ? "/frontend/location-fixture.html" : req.url)));
  if (!path.startsWith(root)) { res.writeHead(403); res.end(); return; }
  const type = {".js":"text/javascript", ".html":"text/html", ".css":"text/css"}[extname(path)] || "application/octet-stream";
  createReadStream(path).on("error", () => { res.writeHead(404); res.end(); }).on("open", () => { res.writeHead(200, {"content-type": type}); }).pipe(res);
});

await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const browser = await chromium.launch({headless:true, ...(process.env.CHROMIUM_PATH ? {executablePath:process.env.CHROMIUM_PATH} : {})});
try {
  const page = await browser.newPage({viewport:{width:390, height:844}, colorScheme:"dark", isMobile:true});
  await page.goto(`http://127.0.0.1:${server.address().port}/frontend/location-fixture.html`);
  await page.waitForSelector("[data-location-query]");
  const details = page.locator(".location-panel");
  await details.evaluate((element) => { element.open = true; });
  const query = page.locator("[data-location-query]");
  await query.fill("Saarbrücken");
  await page.evaluate(() => {
    const card = document.querySelector("camper-weather-card");
    for (let index = 0; index < 4; index += 1) card.hass = {connection:card._hass.connection, callWS:card._hass.callWS};
  });
  await page.waitForTimeout(700);
  if (await query.inputValue() !== "Saarbrücken") throw new Error("active input was replaced by a state update");
  if (await details.getAttribute("open") !== "") throw new Error("open details state was lost");
  console.log("State-update browser test passed: input and open details survive repeated HA updates");
} finally { await browser.close(); server.close(); }
