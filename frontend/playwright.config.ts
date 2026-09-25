import { defineConfig, devices } from "@playwright/test";

const BASE_URL = process.env.PW_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    locale: "es-PE",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
      testIgnore: "**/accessibility.spec.ts",
    },
    {
      name: "edge",
      use: { ...devices["Desktop Edge"], channel: "msedge" },
      testIgnore: "**/accessibility.spec.ts",
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
      testIgnore: "**/accessibility.spec.ts",
    },
    {
      name: "a11y-axe",
      testMatch: "**/accessibility.spec.ts",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});