import { test, expect } from "@playwright/test";
import { authenticatedPage, meSummary } from "../helpers/page.js";
import { waitForTopbar, waitForShell, isLoginPage, isAccessDenied, collectConsole } from "../helpers/wait.js";
import { checkAllowedRoute, assertAllowedRenders } from "../helpers/role.js";
import { ROLE_INFO, CORE } from "../helpers/modules.js";
import { getSessionId } from "../helpers/session.js";

const ROLE = "SUPER_ADMIN";
const ROLES = CORE[ROLE];

test.describe("Super admin (FrostFire) browser tests", () => {
  test.beforeAll(() => {
    test.skip(!getSessionId(ROLE), "No SUPER_ADMIN session available");
  });

  test("identity / role verified via /api/auth/me/", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    const me = await meSummary(page);
    expect(me.status).toBe(200);
    expect(me.username).toBe("FrostFire");
    expect(me.is_superuser).toBe(true);
    await context.close();
  });

  test("dashboard renders for super-admin", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    expect(await isLoginPage(page)).toBe(false);
    expect((await page.locator("#main-content").innerText().catch(() => "")).trim()).not.toBe("");
    await context.close();
  });

  test("topbar nav shows core groups", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await page.waitForSelector(".topbar-nav .nav-group-trigger", { timeout: 60000 });
    const triggers = await page.locator(".topbar-nav .nav-group-trigger").allInnerTexts();
    expect(triggers.join(" ")).toContain("People");
    await context.close();
  });

  for (const route of CORE[ROLE].corePages) {
    test(`core module renders: ${route}`, async ({ browser }) => {
      const result = await checkAllowedRoute(browser, ROLE, route);
      assertAllowedRenders(expect, result, route);
    });
  }

  for (const route of CORE[ROLE].tailPages) {
    test(`tail module renders: ${route}`, async ({ browser }) => {
      const result = await checkAllowedRoute(browser, ROLE, route);
      assertAllowedRenders(expect, result, route);
    });
  }
});