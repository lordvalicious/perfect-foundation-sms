import { test, expect } from "@playwright/test";
import { authenticatedPage } from "../helpers/page.js";
import { waitForTopbar, isLoginPage } from "../helpers/wait.js";
import { CORE } from "../helpers/modules.js";
import { getSessionId } from "../helpers/session.js";

const ROLE = "SUPER_ADMIN";

test.describe("Navigation (super-admin)", () => {
  test.beforeAll(() => {
    test.skip(!getSessionId(ROLE), "No SUPER_ADMIN session available");
  });

  test("topbar groups match configured nav map", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await page.waitForSelector(".topbar-nav .nav-group-trigger", { timeout: 60000 });
    const triggers = await page.locator(".topbar-nav .nav-group-trigger").allInnerTexts();
    const joined = triggers.join(" | ");
    expect(joined).toContain("People");
    expect(joined).toContain("Academics");
    expect(joined).toContain("More");
    await context.close();
  });

  test("mobile toggle present but hidden on desktop viewport", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await expect(page.locator("button.mobile-nav-toggle")).toHaveCount(1, { timeout: 60000 });
    await expect(page.locator("button.mobile-nav-toggle")).toBeHidden({ timeout: 60000 });
    await context.close();
  });

  test("mobile drawer lists permitted links", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE, {
      viewport: { width: 390, height: 844 },
    });
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await expect(page.locator("button.mobile-nav-toggle")).toBeVisible({ timeout: 60000 });
    await page.locator("button.mobile-nav-toggle").click();
    await expect(page.locator("nav.mobile-nav")).toBeVisible({ timeout: 60000 });
    const links = await page.locator("nav.mobile-nav a.mobile-nav-link").allInnerTexts();
    expect(links.some((l) => l.includes("Students"))).toBe(true);
    expect(links.some((l) => l.includes("Finance"))).toBe(true);
    await context.close();
  });

  test("nav link navigation changes route and renders content", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await page.waitForSelector("nav.mobile-nav", { timeout: 60000, state: "visible" }).catch(() => {});
    await page.goto("/students", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await page.waitForTimeout(3000);
    expect(page.url()).toContain("/students");
    expect(await isLoginPage(page)).toBe(false);
    const body = await page.locator("#main-content").innerText().catch(() => "");
    expect(body.trim()).not.toBe("");
    await context.close();
  });

  test("breadcrumb present on subpage", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/staff", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await page.waitForSelector(".breadcrumb", { timeout: 60000 });
    const crumb = await page.locator(".breadcrumb").innerText();
    expect(crumb.toLowerCase()).toContain("staff");
    await context.close();
  });

  test("browser back navigates correctly", async ({ browser }) => {
    const { context, page } = await authenticatedPage(browser, ROLE);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await page.goto("/students", { waitUntil: "domcontentloaded" });
    await waitForTopbar(page);
    await page.goBack();
    await waitForTopbar(page);
    expect(page.url()).not.toContain("/students");
    await context.close();
  });
});