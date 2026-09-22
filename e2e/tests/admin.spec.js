import { test, expect } from "@playwright/test";
import { authenticatedPage, meSummary } from "../helpers/page.js";
import { waitForTopbar, isLoginPage } from "../helpers/wait.js";
import { checkAllowedRoute, checkDeniedRoute, assertAllowedRenders } from "../helpers/role.js";
import { CORE } from "../helpers/modules.js";
import { getSessionId } from "../helpers/session.js";

const ROLE = "ADMIN";

test.describe("Admin (Flora / principal) browser tests", () => {
  test.beforeAll(() => {
    test.skip(!getSessionId(ROLE), "No ADMIN session available");
  });

  test("identity / role verified via /api/auth/me/", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    const me = await meSummary(page);
    expect(me.status).toBe(200);
    expect(me.username).toBe("Flora");
    const roles = (me.memberships || []).flatMap((m) => (m.roles || []).map((r) => r));
    expect(roles).toContain("principal");
    await context.close();
  });

  test("dashboard renders for admin", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    expect(await isLoginPage(page)).toBe(false);
    expect((await page.locator("#main-content").innerText().catch(() => "")).trim()).not.toBe("");
    await context.close();
  });

  for (const route of CORE[ROLE].allowed) {
    test(`allowed module renders: ${route}`, async ({ browser }) => {
      const result = await checkAllowedRoute(browser, ROLE, route);
      assertAllowedRenders(expect, result, route);
    });
  }

  for (const route of CORE[ROLE].deniedUI) {
    test(`denied module is blocked on UI: ${route}`, async ({ browser }) => {
      const { denied, deniedText } = await checkDeniedRoute(browser, ROLE, route);
      expect(denied, `expected denied card for ${route} (got: ${deniedText})`).toBe(true);
    });
  }

  test("backend blocks audit-logs / branding / tenants APIs", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    for (const path of ["/api/audit-logs/", "/api/settings/branding/", "/api/schools/tenants/"]) {
      const resp = await page.request.get(path);
      expect.soft(resp.status(), `GET ${path}`).toBeGreaterThanOrEqual(403);
    }
    await context.close();
  });
});