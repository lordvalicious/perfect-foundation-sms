import { getSessionId } from "./session.js";

const BASE_URL =
  process.env.P43_BASE_URL || "https://perfect-foundation-sms.vercel.app";

function cookieDomain() {
  try {
    const { hostname } = new URL(BASE_URL);
    if (hostname === "localhost" || hostname === "127.0.0.1") return hostname;
    return `.${hostname}`;
  } catch {
    return ".perfect-foundation-sms.vercel.app";
  }
}

export async function authenticatedContext(browser, role, extra = {}) {
  const sessionId = getSessionId(role);
  const context = await browser.newContext(extra);
  if (sessionId) {
    await context.addCookies([
      {
        name: "sessionid",
        value: sessionId,
        domain: cookieDomain(),
        path: "/",
        httpOnly: true,
        secure: true,
      },
    ]);
  }
  return context;
}

export async function authenticatedPage(browser, role, extra = {}) {
  const context = await authenticatedContext(browser, role, extra);
  const page = await context.newPage();
  return { context, page };
}

export async function meSummary(page) {
  const resp = await page.request.get("/api/auth/me/");
  let body = null;
  try {
    body = await resp.json();
  } catch {
    body = {};
  }
  const memberships = (body.memberships || []).map((m) => ({
    roles: (m.roles || []).map((r) => r.role),
  }));
  return {
    status: resp.status(),
    id: body.id,
    username: body.username,
    is_superuser: body.is_superuser,
    primary_role: body.primary_role,
    memberships,
  };
}