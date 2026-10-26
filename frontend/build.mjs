import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";

const source = "../custom_components/camper_weather/www/camper-weather-card.js";
const input = await readFile(new URL(source, import.meta.url), "utf8");
if (!input.includes('const VERSION = "0.1.0-beta.5"') || !input.includes("customElements.define")) {
  throw new Error("card source is not a beta.5 custom card");
}
const digest = createHash("sha256").update(input).digest("hex").slice(0, 12);
await mkdir(new URL("./dist/", import.meta.url), {recursive: true});
await writeFile(new URL("./dist/camper-weather-card.js", import.meta.url), `/* build ${digest} */\n${input}`);
console.log(`built camper-weather-card.js (${digest})`);
