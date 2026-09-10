import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useAuth } from "./auth";
import { apiFetch, jsonHeaders } from "./api";

const SchoolContext = createContext(null);

export function SchoolProvider({ children }) {
  const { user } = useAuth();
  const [currentSchool, setCurrentSchool] = useState(null);
  const [currentRoles, setCurrentRoles] = useState([]);
  const [availableSchools, setAvailableSchools] = useState([]);
  const [activeCampus, setActiveCampus] = useState(null);
  const [campusList, setCampusList] = useState([]);
  const [modules, setModules] = useState({
    loaded: false,
    enabled: [],
    isPlatformAdmin: false,
    schoolStatus: "active",
  });
  const [loading, setLoading] = useState(true);
  const [isSwitching, setIsSwitching] = useState(false);
  const [error, setError] = useState("");
  const [schoolScopeVersion, setSchoolScopeVersion] = useState(0);
  const [branding, setBranding] = useState({
    school_name: "",
    short_name: "",
    motto: "",
    primary_color: "",
    logo_url: "",
  });

  // Sequence + abort tokens guard against stale responses overwriting the
  // current school during rapid switching (last-write-wins per latest request).
  const seqRef = useRef(0);
  const abortRef = useRef(null);

  const fetchActiveInstitution = useCallback(
    (mode = "initial") => {
      // Abort any in-flight request from a previous switch/refresh.
      if (abortRef.current) abortRef.current.abort();

      const controller = new AbortController();
      abortRef.current = controller;
      const token = ++seqRef.current;

      const apply = (school, roles, modData, campusData, allSchools) => {
        // Ignore the result if a newer request has already started.
        if (token !== seqRef.current) return;

        setCurrentSchool(school);
        setCurrentRoles(roles);
        setActiveCampus(campusData?.campus || null);
        setCampusList(campusData?.campuses || []);
        if (modData) {
          setModules({
            loaded: true,
            enabled: modData.enabled || [],
            isPlatformAdmin: !!modData.is_platform_admin,
            schoolStatus: modData.school_status || "active",
          });
        }

        // Platform admins can switch into every school, not only the ones they
        // hold membership rows for. Merge the memberships with the admin list.
        const membershipSchools = (user?.memberships || [])
          .filter((m) => m.status === "active")
          .map((m) => ({
            id: m.institution,
            name: m.institution_name,
            roles: m.roles.map((r) => r.role),
          }));

        if (Array.isArray(allSchools) && allSchools.length > 0) {
          const seen = new Set();
          const merged = [];
          for (const s of [...allSchools, ...membershipSchools]) {
            if (s && s.id != null && !seen.has(s.id)) {
              seen.add(s.id);
              merged.push({
                id: s.id,
                name: s.name || "Untitled School",
                roles: s.roles || [],
              });
            }
          }
          setAvailableSchools(merged);
        } else {
          setAvailableSchools(membershipSchools);
        }

        setError("");
        setLoading(false);
        if (mode === "switch") setIsSwitching(false);
      };

      if (!user) {
        setCurrentSchool(null);
        setCurrentRoles([]);
        setActiveCampus(null);
        setCampusList([]);
        setAvailableSchools([]);
        setModules({ loaded: false, enabled: [], isPlatformAdmin: false, schoolStatus: "active" });
        setLoading(false);
        if (mode === "switch") setIsSwitching(false);
        return Promise.resolve();
      }

      setLoading(true);
      if (mode === "switch") setIsSwitching(true);

      return Promise.allSettled([
        apiFetch(
          "/api/auth/active-institution/",
          { signal: controller.signal },
          "Could not load active institution."
        ),
        apiFetch(
          "/api/schools/modules/current/",
          { signal: controller.signal },
          "Could not load modules."
        ),
        apiFetch(
          "/api/auth/active-campus/",
          { signal: controller.signal },
          "Could not load active campus."
        ),
        // Only platform admins can read this; for everyone else it 403s and is
        // ignored below.
        apiFetch(
          "/api/auth/super-admin/schools/",
          { signal: controller.signal },
          "Could not load schools."
        ),
      ]).then(([instResult, modsResult, campusResult, schoolsResult]) => {
        if (controller.signal.aborted) return;

        const inst = instResult.status === "fulfilled" ? instResult.value : null;
        const mods = modsResult.status === "fulfilled" ? modsResult.value : null;
        const campusData =
          campusResult.status === "fulfilled" ? campusResult.value : null;
        const allSchools =
          schoolsResult.status === "fulfilled" ? schoolsResult.value : null;

        const school =
          inst?.institution ||
          (user.memberships?.length > 0
            ? {
                id: user.memberships[0].institution,
                name: user.memberships[0].institution_name,
                institution_type: "school",
              }
            : null);
        const roles =
          inst?.roles?.length > 0
            ? inst.roles
            : user.memberships?.length > 0 && !inst
            ? user.memberships[0].roles.map((r) => r.role)
            : inst?.roles || [];

        apply(school, roles, mods, campusData, allSchools);
      });
    },
    [user]
  );

  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  useEffect(() => {
    fetchActiveInstitution("initial");
  }, [fetchActiveInstitution]);

  // White-label: apply the school's saved branding to the shell (document
  // title, brand accent color, mobile theme-color). Cosmetic only — failures
  // fall back to the institution name and are never surfaced as errors.
  useEffect(() => {
    const name = currentSchool?.name || "School Management System";
    if (!currentSchool?.id) return undefined;
    let cancelled = false;

    apiFetch("/api/schools/branding/", {}, "Could not load branding.")
      .then((data) => {
        if (cancelled) return;
        const next = {
          school_name: data.school_name || name,
          short_name: data.short_name || "",
          motto: data.motto || "",
          primary_color: data.primary_color || "",
          logo_url: data.logo_url || "",
        };
        setBranding(next);
        document.title = next.school_name;
        const color =
          typeof next.primary_color === "string" && next.primary_color
            ? next.primary_color
            : "";
        if (color) {
          document.documentElement.style.setProperty("--brand-color", color);
          let meta = document.querySelector('meta[name="theme-color"]');
          if (!meta) {
            meta = document.createElement("meta");
            meta.setAttribute("name", "theme-color");
            document.head.appendChild(meta);
          }
          meta.setAttribute("content", color);
        } else {
          document.documentElement.style.removeProperty("--brand-color");
          const meta = document.querySelector('meta[name="theme-color"]');
          if (meta) meta.setAttribute("content", "");
        }
      })
      .catch(() => {
        if (cancelled) return;
        setBranding((p) => ({ ...p, school_name: name }));
        document.title = name;
      });

    return () => {
      cancelled = true;
    };
  }, [currentSchool]);

  const switchSchool = useCallback(
    async (institutionId) => {
      if (abortRef.current) abortRef.current.abort();

      const seq = ++seqRef.current;
      setError("");
      setIsSwitching(true);

      try {
        await apiFetch(
          "/api/auth/active-institution/",
          {
            method: "POST",
            headers: jsonHeaders(),
            body: JSON.stringify({ institution_id: institutionId }),
          },
          "Failed to switch school."
        );

        // Only refetch + bump scope if this switch is still the latest action.
        if (seq === seqRef.current) {
          await fetchActiveInstitution("switch");
          setSchoolScopeVersion((v) => v + 1);
        }
      } catch (err) {
        // A stale switch (superseded by a newer one) aborts; do not surface it.
        if (seq === seqRef.current) {
          setError(err.message);
          setIsSwitching(false);
          setLoading(false);
          throw err;
        }
      }
    },
    [fetchActiveInstitution]
  );

  // Persist the active campus for the current school context. Pass null to
  // clear the selection ("all campuses").
  const setActiveCampusId = useCallback(async (campusId) => {
    setError("");
    try {
      const data = await apiFetch(
        "/api/auth/active-campus/",
        {
          method: "POST",
          headers: jsonHeaders(),
          body: JSON.stringify({ campus_id: campusId }),
        },
        "Failed to switch campus."
      );
      const campus = data?.campus || null;
      setActiveCampus(campus);
      setSchoolScopeVersion((v) => v + 1);
      return campus;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const refreshSchool = useCallback(() => {
    return fetchActiveInstitution("refresh");
  }, [fetchActiveInstitution]);

  // Role check scoped to the ACTIVE school only. This is what nav, route guards
  // and role-aware views use so that a user only gets UI/access for the school
  // they are currently scoped to — never roles held in another school.
  //
  // Platform/super users keep global access. We fall back to the active
  // membership's roles if the active-institution payload has no role list yet.
  const scopedHasRole = useCallback(
    (roles) => {
      if (!user) return false;
      if (user.is_superuser) return true;
      if (modules.isPlatformAdmin) return true;
      if (!roles || roles.length === 0) return true;

      const activeSet = new Set(
        currentRoles && currentRoles.length > 0
          ? currentRoles
          : user.memberships
              ?.find((m) => m.institution === currentSchool?.id)
              ?.roles?.map((r) => r.role) || []
      );

      return roles.some((role) => activeSet.has(role));
    },
    [user, modules.isPlatformAdmin, currentRoles, currentSchool]
  );

  const value = useMemo(
    () => ({
      currentSchool,
      currentRoles,
      availableSchools,
      activeCampus,
      campusList,
      modules,
      loading,
      isSwitching,
      error,
      schoolScopeVersion,
      branding,
      switchSchool,
      setActiveCampusId,
      refreshSchool,
      scopedHasRole,
    }),
    [
      currentSchool,
      currentRoles,
      availableSchools,
      activeCampus,
      campusList,
      modules,
      loading,
      isSwitching,
      error,
      schoolScopeVersion,
      branding,
      switchSchool,
      setActiveCampusId,
      refreshSchool,
      scopedHasRole,
    ]
  );

  return (
    <SchoolContext.Provider value={value}>
      {children}
    </SchoolContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components -- hook must live beside the provider
export function useSchool() {
  const context = useContext(SchoolContext);

  if (context === null) {
    throw new Error("useSchool must be used within a SchoolProvider.");
  }

  return context;
}