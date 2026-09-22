import { test, expect } from "@playwright/test";
import { authenticatedPage, meSummary } from "../helpers/page.js";
import { waitForTopbar, isAccessDenied } from "../helpers/wait.js";
import { checkDeniedRoute } from "../helpers/role.js";
import { CORE } from "../helpers/modules.js";
import { getSessionId } from "../helpers/session.js";

const ROLES = ["SUPER_ADMIN", "ADMIN", "TEACHER", "STUDENT", "STAFF"];

test.describe("Authorization / role isolation", () => {
  test.describe("backend enforcement", () => {
    for (const role of ROLES) {
      test(`${role}: /me returns own identity`, async ({ browser }) => {
        test.skip(!getSessionId(role), `No ${role} session available`);
        const { context, page } = await authenticatedPage(browser, role);
        const me = await meSummary(page);
        expect(me.status).toBe(200);
        expect(me.username).toBeTruthy();
        await context.close();
      });
    }

    const probes = {
      TEACHER: ["/api/finance/invoices/", "/api/finance/payments/", "/api/payroll/records/"],
      STAFF: ["/api/finance/invoices/", "/api/finance/payments/", "/api/payroll/records/"],
    };
    for (const [role, probesList] of Object.entries(probes)) {
      for (const path of probesList) {
        test(`${role}: ${path} blocked by backend`, async ({ browser }) => {
          test.skip(!getSessionId(role), `No ${role} session available`);
          const { context, page } = await authenticatedPage(browser, role);
          const resp = await page.request.get(path);
          expect(resp.status(), `expected 403 for ${role} GET ${path}`).toBe(403);
          await context.close();
        });
      }
    }

    const scopedEmptyRoles = {
      STUDENT: ["/api/finance/invoices/", "/api/finance/payments/", "/api/exams/", "/api/attendance/"],
    };
    for (const [role, paths] of Object.entries(scopedEmptyRoles)) {
      for (const path of paths) {
        test(`${role}: ${path} returns 403 or empty self-scope (no cross-scope data)`, async ({ browser }) => {
          test.skip(!getSessionId(role), `No ${role} session available`);
          const { context, page } = await authenticatedPage(browser, role);
          const resp = await page.request.get(path);
          const status = resp.status();
          if (status === 403) {
            await context.close();
            return;
          }
          expect(status).toBe(200);
          const json = await resp.json().catch(() => ({}));
          const records = Array.isArray(json) ? json : json.results || [];
          const count = Array.isArray(json) ? records.length : Number(json.count ?? records.length ?? 0);
          expect(count, `${role} GET ${path} held non-empty cross-scope data`).toBe(0);
          await context.close();
        });
      }
    }

    const scopedProbes = {
      STUDENT: ["/api/students/", "/api/hr/employees/", "/api/staff/"],
      TEACHER: ["/api/students/", "/api/hr/employees/", "/api/staff/"],
      STAFF: ["/api/students/", "/api/hr/employees/", "/api/staff/"],
      ADMIN: ["/api/students/", "/api/hr/employees/", "/api/staff/"],
    };
    for (const [role, paths] of Object.entries(scopedProbes)) {
      for (const path of paths) {
        test(`${role}: ${path} does not 500 (scoped read ok)`, async ({ browser }) => {
          test.skip(!getSessionId(role), `No ${role} session available`);
          const { context, page } = await authenticatedPage(browser, role);
          const resp = await page.request.get(path);
          expect(resp.status(), `GET ${path}`).toBeLessThan(500);
          await context.close();
        });
      }
    }

    test.skip("SUPER_ADMIN: platform endpoints reachable", async ({ browser }) => {
      test.skip(!getSessionId("SUPER_ADMIN"), "No SUPER_ADMIN session available");
      const { context, page } = await authenticatedPage(browser, "SUPER_ADMIN");
      for (const path of ["/api/audit-logs/", "/api/payroll/records/"]) {
        const resp = await page.request.get(path);
        expect.soft(resp.status(), `GET ${path}`).toBeGreaterThanOrEqual(200);
        expect.soft(resp.status(), `GET ${path}`).toBeLessThan(500);
      }
      await context.close();
    });
  });

  test.describe("UI hiding & denied cards", () => {
    test("teacher denied routes show Access denied", async ({ browser }) => {
      test.skip(!getSessionId("TEACHER"), "No TEACHER session available");
      for (const route of ["/finance", "/payroll", "/hr", "/settings"]) {
        const { denied } = await checkDeniedRoute(browser, "TEACHER", route);
        expect(denied, `teacher sees denied card for ${route}`).toBe(true);
      }
    });

    test("student denied routes show Access denied", async ({ browser }) => {
      test.skip(!getSessionId("STUDENT"), "No STUDENT session available");
      for (const route of ["/finance", "/payroll", "/attendance", "/exams", "/report-cards", "/teachers", "/settings"]) {
        const { denied } = await checkDeniedRoute(browser, "STUDENT", route);
        expect(denied, `student sees denied card for ${route}`).toBe(true);
      }
    });

    test("staff denied routes show Access denied", async ({ browser }) => {
      test.skip(!getSessionId("STAFF"), "No STAFF session available");
      for (const route of ["/finance", "/payroll", "/hr", "/staff", "/students", "/reports"]) {
        const { denied } = await checkDeniedRoute(browser, "STAFF", route);
        expect(denied, `staff sees denied card for ${route}`).toBe(true);
      }
    });

    test("admin allowed pages do NOT show denied card", async ({ browser }) => {
      test.skip(!getSessionId("ADMIN"), "No ADMIN session available");
      const { context, page } = await authenticatedPage(browser, "ADMIN");
      await page.goto("/finance", { waitUntil: "domcontentloaded" });
      await waitForTopbar(page);
      await page.waitForTimeout(3000);
      expect(await isAccessDenied(page)).toBe(false);
      await context.close();
    });
  });
});