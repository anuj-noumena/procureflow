import { defineConfig } from "@playwright/test";
import { randomBytes } from "node:crypto";
process.env.PF_E2E_PASSWORD ||= randomBytes(20).toString("hex");
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 45000,
  use: {
    baseURL: "http://127.0.0.1:5187",
    headless: true,
    launchOptions: { executablePath: process.env.PF_CHROMIUM },
  },
  webServer: [
    {
      command: "../.venv/bin/python ../scripts/browser_backend.py",
      url: "http://127.0.0.1:8187/api/v1/health",
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5187 --strictPort",
      url: "http://127.0.0.1:5187",
      env: { PF_API_TARGET: "http://127.0.0.1:8187" },
      reuseExistingServer: false,
    },
  ],
});
