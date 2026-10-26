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
  const context = await browser.newContext({viewport:{width:390, height:844}, colorScheme:"dark", isMobile:true});
  const page = await context.newPage();
  await page.goto(`http://127.0.0.1:${server.address().port}/frontend/location-fixture.html`);
  await page.waitForSelector("[data-location-mode]");
  await page.locator("[data-location-mode]").evaluate((el) => {
    el.value = "home_zone"; el.dispatchEvent(new Event("change", {bubbles:true}));
    el.value = "tracker"; el.dispatchEvent(new Event("change", {bubbles:true}));
  });
  await page.waitForTimeout(600);
  const state = await page.locator("[data-location-mode]").inputValue();
  const text = await page.locator(".location-panel").innerText();
  const calls = await page.evaluate(() => window.__calls);
  if (state !== "tracker" || !text.includes("tracker")) throw new Error(`stale location state: ${state} / ${text} / ${JSON.stringify(calls)}`);
  await page.locator("[data-location-mode]").evaluate((el) => { el.value = "home_zone"; el.dispatchEvent(new Event("change", {bubbles:true})); });
  await page.waitForTimeout(150);
  if (await page.locator("[data-location-mode]").inputValue() !== "home_zone") throw new Error("home-zone selection was not retained");
  console.log("Location browser test passed: mobile dark-mode rapid GPS/Home/GPS transitions are current");
} finally { await browser.close(); server.close(); }
