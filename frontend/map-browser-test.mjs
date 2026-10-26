import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { createReadStream } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium, webkit } from "playwright";

const root = join(fileURLToPath(new URL("..", import.meta.url)));
const server = createServer((req, res) => {
  const path = normalize(join(root, decodeURIComponent(req.url === "/" ? "/frontend/fixture.html" : req.url)));
  if (!path.startsWith(root)) { res.writeHead(403); res.end(); return; }
  const type = {".js":"text/javascript", ".html":"text/html", ".css":"text/css"}[extname(path)] || "application/octet-stream";
  createReadStream(path).on("error", () => { res.writeHead(404); res.end(); }).on("open", () => { res.writeHead(200, {"content-type": type}); }).pipe(res);
});

await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const port = server.address().port;
const browser = await (process.env.BROWSER === "webkit" ? webkit : chromium).launch({headless: true});
try {
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:${port}/frontend/fixture.html`);
  await page.waitForSelector(".map-container canvas", {timeout: 30000});
  await page.waitForFunction(() => !document.querySelector(".map-loading"), null, {timeout: 30000});
  console.log("MapLibre browser test passed: rendered canvas and no loading state");
} finally {
  await browser.close();
  server.close();
}
