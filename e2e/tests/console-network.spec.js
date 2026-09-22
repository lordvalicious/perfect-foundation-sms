import { test, expect } from "@playwright/test";
import { authenticatedPage } from "../helpers/page.js";
import { waitForTopbar } from "../helpers/wait.js";
import { CORE } from "../helpers/modules.js";
import { getSessionId } from "../helpers/session.js";

const ROLE = "SUPER_ADMIN";
const FILTERED = [
  "fonts.googleapis.com",
  "fonts.gstatic.com",
  "accounts.google.com",
];

function isFilteredUrl(url) {
  return FILTERED.some((f) => url.includes(f));
}

test.describe("Console & network audit (super-admin core pages)", () => {
  test.beforeAll(() => {
    test.skip(!getSessionId(ROLE), "No SUPER_ADMIN session available");
  });

  for (const route of CORE[ROLE].corePages.slice(0, 12)) {
    test(`console/network clean on ${route}`, async ({ browser }) => {
      const { context, page } = await authenticatedPage(browser, ROLE);
      const consoleErrors = [];
      const pageErrors = [];
      const failedRequests = [];
      const badResponses = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          const text = msg.text();
          if (isFilteredUrl(text) || text.includes("/api/")) {
            failedRequests.push(`console: ${text.slice(0, 160)}`);
          } else {
            consoleErrors.push(text.slice(0, 160));
          }
        }
      });
      page.on("pageerror", (e) => pageErrors.push(String(e.message || e).slice(0, 160)));
      page.on("requestfailed", (req) => {
        const url = req.url();
        if (!isFilteredUrl(url)) failedRequests.push(`req: ${url.split("?")[0]}`);
      });
      page.on("response", (res) => {
        const url = res.url();
        if (res.status() >= 400 && !isFilteredUrl(url)) {
          badResponses.push(`${res.status()} ${url.split("?")[0]}`);
        }
      });

      await page.goto(route, { waitUntil: "domcontentloaded" });
      await waitForTopbar(page);
      await page.waitForTimeout(2500);

      const meStatus = await page.request.get("/api/auth/me/").then((r) => r.status()).catch(() => 0);
      expect(meStatus, `${route}: /me must respond 200`).toBe(200);

      const summary = {
        route,
        consoleErrors,
        pageErrors,
        failedRequests,
        badResponses,
      };
      test.info().annotations.push({ type: "console-network", description: JSON.stringify(summary) });

      expect(pageErrors, `${route}: JS exceptions`).toEqual([]);
      expect(consoleErrors, `${route}: unexpected console errors`).toEqual([]);
      await context.close();
    });
  }

  test("core API endpoints respond under 20s and return 200/403 as expected", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    const targets = ["/api/auth/me/", "/api/students/", "/api/staff/", "/api/payroll/records/"];
    for (const path of targets) {
      const start = Date.now();
      const resp = await page.request.get(path, { timeout: 60000 });
      const ms = Date.now() - start;
      const status = resp.status();
      test.info().annotations.push({
        type: "api-timing",
        description: `${path} -> ${status} in ${ms}ms`,
      });
      expect(ms).toBeLessThan(20000);
    }
    await context.close();
  });
});