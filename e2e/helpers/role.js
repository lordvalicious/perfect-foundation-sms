import { authenticatedPage, meSummary } from "./page.js";
import { waitForTopbar, isLoginPage, isAccessDenied, isNotFoundPage, collectConsole } from "./wait.js";

async function settledBodyText(page, timeout = 45000) {
  const deadline = Date.now() + timeout;
  let last = "";
  while (Date.now() < deadline) {
    last = (await page.locator("#main-content, main").innerText().catch(() => "")).trim();
    const normalized = last.replace(/\s+/g, " ").trim();
    if (normalized && !normalized.endsWith("...") && normalized !== "Loading" && !normalized.startsWith("Loading")) {
      return last;
    }
    await page.waitForTimeout(1500);
  }
  return last;
}

export async function checkAllowedRoute(browser, role, route) {
  const { context, page } = await authenticatedPage(browser, role);
  const consoleEntries = collectConsole(page);
  const failedResponses = [];
  page.on("response", (res) => {
    if (res.status() >= 400) failedResponses.push(`${res.status()} ${res.url().split("?")[0]}`);
  });
  await page.goto(route, { waitUntil: "domcontentloaded" });
  await waitForTopbar(page);
  const bodyText = (await settledBodyText(page)).trim();
  const onLogin = await isLoginPage(page);
  const denied = await isAccessDenied(page);
  await context.close();
  return { onLogin, denied, bodyText, failedResponses, consoleEntries };
}

export async function assertAllowedRenders(expect, result, route) {
  expect(result.onLogin, `${route}: unauthenticated redirect`).toBe(false);
  expect(result.denied, `${route}: denied unexpectedly`).toBe(false);
  expect(result.bodyText, `${route}: empty body`).not.toBe("");
}

export async function checkDeniedRoute(browser, role, route) {
  const { context, page } = await authenticatedPage(browser, role);
  await page.goto(route, { waitUntil: "domcontentloaded" });
  await waitForTopbar(page);
  const bodyText = (await settledBodyText(page)).trim();
  const denied = (await isAccessDenied(page)) || (await isNotFoundPage(page));
  const deniedText = denied
    ? (await page.locator(".state-card.error").count()) > 0
      ? await page.locator(".state-card.error").innerText()
      : (await page.locator("h1, h2").first().innerText()).slice(0, 200)
    : bodyText.slice(0, 200) || "NOT DENIED / EMPTY";
  await context.close();
  return { denied, deniedText };
}