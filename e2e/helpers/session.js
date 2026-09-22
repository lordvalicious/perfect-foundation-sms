import fs from "node:fs";
import path from "node:path";

const ROLE_FILES = {
  SUPER_ADMIN: "sa_frostfire.txt",
  ADMIN: "sa_flora.txt",
  TEACHER: "sa_SA-EMP-0001.txt",
  STUDENT: "sa_SA-ST-0001.txt",
  STAFF: "sa_DI-staff.txt",
};

export const ROLES = Object.keys(ROLE_FILES);

export function resolveRoleEnvName(role) {
  return `P43_${role}_SESSIONID`;
}

export function getSessionId(role) {
  const fromEnv = process.env[resolveRoleEnvName(role)];
  if (fromEnv) return fromEnv.trim();
  const dir = process.env.P43_SESSIONS_DIR || "";
  const file = ROLE_FILES[role];
  if (dir && file) {
    const full = path.join(dir, file);
    if (fs.existsSync(full)) {
      const raw = fs.readFileSync(full, "utf8");
      for (const line of raw.split(/\r?\n/)) {
        let l = line;
        if (l.startsWith("#HttpOnly_")) l = l.slice("#HttpOnly_".length);
        if (!l || l.startsWith("#")) continue;
        const parts = l.split("\t");
        if (parts.length >= 7 && parts[5] === "sessionid") return parts[6];
      }
    }
  }
  return null;
}

export function hasSession(role) {
  return Boolean(getSessionId(role));
}