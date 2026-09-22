import { expect } from "@playwright/test";

export async function waitForShell(page, { login = false, timeout = 100000 } = {}) {
  await page.waitForSelector(".app, .login-page", { timeout });
  if (login) {
    await page.waitForSelector(".login-card, .login-page .login-error", { timeout });
  } else {
    await page.waitForSelector(".topbar, .auth-loading", { timeout });
    await page.waitForSelector(".topbar", { timeout });
  }
}

export async function waitForTopbar(page, timeout = 120000) {
  await page.waitForSelector("header.topbar", { timeout });
}

export async function isLoginPage(page) {
  return (await page.locator(".login-page").count()) > 0;
}

export async function isAccessDenied(page) {
  const card = page.locator(".state-card.error");
  if ((await card.count()) === 0) return false;
  const text = await card.innerText();
  return text.includes("Access denied");
}

export async function isNotFoundPage(page) {
  const crumb = page.locator(".breadcrumb");
  if ((await crumb.count()) === 0) return false;
  const text = await crumb.innerText();
  return /not found/i.test(text);
}

export async function expectNoPageErrors(page) {
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e.message || e)));
  await page.waitForTimeout(1200);
  expect(errors, `pageerror: ${errors.join(" | ")}`).toEqual([]);
}

export async function statusOf(page, url) {
  const resp = await page.request.get(url);
  return { status: resp.status(), url };
}

export async function collectConsole(page) {
  const entries = [];
  page.on("console", (msg) => {
    entries.push({ type: msg.type(), text: msg.text().slice(0, 300) });
  });
  return entries;
}