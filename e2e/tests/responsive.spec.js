import { test, expect } from "@playwright/test";
import { authenticatedPage } from "../helpers/page.js";
import { waitForTopbar, isLoginPage } from "../helpers/wait.js";
import { getSessionId } from "../helpers/session.js";

const ROLE = "SUPER_ADMIN";
const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "mobile", width: 390, height: 844 },
];

test.describe("Responsive", () => {
  test.beforeAll(() => {
    test.skip(!getSessionId(ROLE), "No SUPER_ADMIN session available");
  });

  test("login page is usable at all viewports", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".login-page", { timeout: 120000 });
    await expect(page.locator(".login-card")).toBeVisible({ timeout: 60000 });
  });

  test("dashboard renders at tablet and mobile viewports", async ({ browser }) => {
    for (const vp of VIEWPORTS) {
      const { context, page } = await authenticatedPage(browser, ROLE, {
        viewport: { width: vp.width, height: vp.height },
      });
      await page.goto("/", { waitUntil: "domcontentloaded" });
      await waitForTopbar(page);
      expect(await isLoginPage(page)).toBe(false);
      const toggle = page.locator("button.mobile-nav-toggle");
      await expect(toggle, `mobile toggle present at ${vp.name}`).toHaveCount(1, { timeout: 60000 });
      if (vp.name === "mobile") {
        await expect(toggle, "mobile toggle visible on mobile viewport").toBeVisible({ timeout: 60000 });
      }
      const mainText = await page.locator("#main-content").innerText().catch(() => "");
      expect(mainText.trim()).not.toBe("");
      await context.close();
    }
  });

  test("mobile drawer opens and closes", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE, {
      viewport: { width: 390, height: 844 },
    });
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    const toggle = page.locator("button.mobile-nav-toggle");
    await expect(toggle).toBeVisible({ timeout: 60000 });
    await toggle.click();
    const drawer = page.locator("nav.mobile-nav");
    await expect(drawer).toBeVisible({ timeout: 60000 });
    await page.keyboard.press("Escape");
    await expect(drawer).toBeHidden({ timeout: 60000 });
    await expect(page.locator("button.mobile-nav-toggle")).toBeVisible({ timeout: 60000 });
    await context.close();
  });

  test("tables do not overflow viewport horizontally", async ({ browser }) => {
    for (const vp of VIEWPORTS) {
      const { context, page } = await authenticatedPage(browser, ROLE, {
        viewport: { width: vp.width, height: vp.height },
      });
      await page.goto("/students", { waitUntil: "domcontentloaded" });
      await waitForTopbar(page);
      await page.waitForTimeout(4000);
      const tableInfo = await page.evaluate(() => {
        const tables = Array.from(document.querySelectorAll("table.data-table"));
        return tables.map((t) => {
          const wrapper = t.closest(".table-wrapper, .students-table-wrapper");
          const rect = t.getBoundingClientRect();
          return {
            width: Math.round(rect.width),
            viewport: window.innerWidth,
            wrapped: Boolean(wrapper),
            wrapperScrollable: wrapper
              ? ["auto", "scroll"].includes(getComputedStyle(wrapper).overflowX)
              : false,
          };
        });
      });
      for (const t of tableInfo) {
        expect(
          t.wrapped && t.wrapperScrollable,
          `${vp.name}: table w=${t.width} in scrollable wrapper (viewport ${t.viewport})`
        ).toBe(true);
      }
      await context.close();
    }
  });

  test("profile page renders on mobile", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE, {
      viewport: { width: 390, height: 844 },
    });
    await page.goto("/profile", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await page.waitForTimeout(3000);
    const text = await page.locator("#main-content").innerText().catch(() => "");
    expect(text.trim()).not.toBe("");
    await context.close();
  });

  test("tablet page has no document horizontal overflow", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE, {
      viewport: { width: 768, height: 1024 },
    });
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await page.waitForSelector(".topbar-nav-measure", { state: "attached", timeout: 60000 });
    await page.waitForTimeout(4000);
    const m = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      measureDisplay: getComputedStyle(document.querySelector(".topbar-nav-measure")).display,
    }));
    expect(m.measureDisplay, "measure element hidden at tablet width").toBe("none");
    expect(m.scrollWidth, `tablet horizontal overflow`).toBeLessThanOrEqual(m.clientWidth + 2);
    await context.close();
  });
});