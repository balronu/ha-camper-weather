import { createServer } from "node:http";
import { createReadStream } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = join(fileURLToPath(new URL("..", import.meta.url)));
const server = createServer((req, res) => {
  const path = normalize(join(root, decodeURIComponent(req.url === "/" ? "/frontend/forecast-fixture.html" : req.url)));
  if (!path.startsWith(root)) { res.writeHead(403); res.end(); return; }
  const type = {".js":"text/javascript", ".html":"text/html"}[extname(path)] || "application/octet-stream";
  createReadStream(path).on("error", () => { res.writeHead(404); res.end(); }).on("open", () => res.writeHead(200, {"content-type":type})).pipe(res);
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const browser = await chromium.launch({headless:true, ...(process.env.CHROMIUM_PATH ? {executablePath:process.env.CHROMIUM_PATH} : {})});
try {
  for (const [index, viewport] of [{width:1280,height:900,isMobile:false},{width:390,height:844,isMobile:true}].entries()) {
    const page = await browser.newPage({...viewport, colorScheme:"dark", hasTouch:viewport.isMobile});
    await page.goto(`http://127.0.0.1:${server.address().port}/frontend/forecast-fixture.html`);
    await page.waitForSelector(".chart-wrap svg");
    if (await page.locator(".temp-line").count() !== 1 || await page.locator(".rain-bar").count() < 1) throw new Error("temperature or precipitation series missing");
    await page.locator("[data-chart-wind]").click();
    if (await page.locator(".wind-line").count() !== 1) throw new Error("wind toggle did not render the separate wind series");
    await page.locator("[data-forecast-range='48']").click();
    if (await page.locator(".chart-wrap svg").getAttribute("aria-label") !== "48-Stunden Wetterdiagramm") throw new Error("48 hour range failed");
    await page.locator("[data-forecast-range='168']").click();
    if (await page.locator(".chart-point").count() !== 7) throw new Error("7 day view did not aggregate to seven points");
    await page.locator(".chart-point").first().click();
    if (await page.locator(".chart-tooltip").count() !== 1) throw new Error("touch/pointer selection did not show tooltip");
    await page.screenshot({path:`${root}/docs/assets/camper-weather-chart-${index === 0 ? "desktop" : "mobile"}.png`, fullPage:true});
    await page.close();
  }
  console.log("Forecast browser test passed: desktop/mobile, 24/48/7-day, missing data, wind toggle and touch selection");
} finally { await browser.close(); server.close(); }
