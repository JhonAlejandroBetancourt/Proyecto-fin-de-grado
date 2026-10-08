const { defineConfig, devices } = require("@playwright/test");

const systemEdge = process.platform === "win32";
const liveGemini = process.env.E2E_LIVE_GEMINI === "1";
const appPort = liveGemini ? 8053 : 8052;
const baseURL = `http://127.0.0.1:${appPort}`;

module.exports = defineConfig({
  testDir: "./tests/e2e",
  testMatch: "**/*.spec.js",
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  timeout: 180000,
  expect: {
    timeout: 15000,
  },
  use: {
    ...devices["Desktop Chrome"],
    ...(systemEdge ? { channel: "msedge" } : {}),
    baseURL,
    acceptDownloads: true,
    locale: "es-CO",
    timezoneId: "America/Bogota",
    viewport: { width: 1440, height: 1000 },
    trace: "retain-on-failure",
  },
  webServer: liveGemini
    ? {
        command: "python run.py",
        url: baseURL,
        reuseExistingServer: false,
        timeout: 120000,
        stdout: "ignore",
        stderr: "pipe",
        env: { PORT: String(appPort) },
      }
    : [
        {
          name: "mock-gemini",
          command: "node tests/e2e/support/mock-gemini.js",
          url: "http://127.0.0.1:8051/health",
          reuseExistingServer: false,
          timeout: 15000,
          stdout: "ignore",
          stderr: "pipe",
        },
        {
          name: "quiron-e2e",
          command: "python run.py",
          url: baseURL,
          reuseExistingServer: false,
          timeout: 120000,
          stdout: "ignore",
          stderr: "pipe",
          env: {
            PORT: String(appPort),
            GEMINI_API_KEY: "playwright-test-key-not-a-secret",
            GEMINI_API_BASE_URL: "http://127.0.0.1:8051/v1beta/models",
          },
          dependencies: ["mock-gemini"],
        },
      ],
});
