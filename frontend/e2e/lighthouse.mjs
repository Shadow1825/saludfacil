import fs from "fs";
import path from "path";
import lighthouse from "lighthouse";
import * as chromeLauncher from "chrome-launcher";

const BASE = process.env.PW_BASE_URL ?? "http://localhost:3000";
const DIR = path.join(process.cwd(), "..", "docs", "fase8");
const URLS = [
  { ruta: "/login", nombre: "login" },
  { ruta: "/registro", nombre: "registro" },
  { ruta: "/inicio", nombre: "inicio" },
];

fs.mkdirSync(DIR, { recursive: true });

async function main() {
  const chrome = await chromeLauncher.launch({
    chromeFlags: ["--headless", "--no-sandbox", "--disable-gpu", "--no-first-run"],
    chromePath: process.env.CHROME_PATH,
    logLevel: "silent",
  });
  const config = {
    extends: "lighthouse:default",
    settings: {
      formFactor: "desktop",
      screenEmulation: { mobile: false, width: 1366, height: 768, deviceScaleFactor: 1 },
      onlyCategories: ["accessibility"],
    },
  };

  const resumen = { fecha: new Date().toISOString(), urls: [] };
  try {
    for (const { ruta, nombre } of URLS) {
      const { lhr, report } = await lighthouse(`${BASE}${ruta}`, {
        port: chrome.port,
        output: "json",
        logLevel: "silent",
      }, config);
      const pct = lhr.categories.accessibility.score;
      resumen.urls.push({ ruta, accessibility: `${pct}`, umbral: 90, cumple: pct >= 0.9 });
      fs.writeFileSync(path.join(DIR, `lighthouse-${nombre}-report.json`), report);
      console.log(`${ruta.padEnd(12)} accesibilidad=${pct}`);
    }
  } finally {
    await chrome.kill();
  }
  fs.writeFileSync(path.join(DIR, "lighthouse-summary.json"), JSON.stringify(resumen, null, 2), "utf8");
  console.log(`Resumen: ${path.join(DIR, "lighthouse-summary.json")}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});