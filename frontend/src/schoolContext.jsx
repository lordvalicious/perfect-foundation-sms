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
import { apiFetch } from "./api";

const SchoolContext = createContext(null);

export function SchoolProvider({ children }) {
  const { user } = useAuth();
  const [currentSchool, setCurrentSchool] = useState(null);
  const [currentRoles, setCurrentRoles] = useState([]);
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

  // Sequence + abort tokens guard against stale responses overwriting the
  // current school during rapid switching (last-write-wins per latest request).
  const seqRef = useRef(0);
  const abortRef = useRef(null);

  const availableSchools = useMemo(() => {
    if (!user?.memberships) return [];
    return user.memberships
      .filter((m) => m.status === "active")
      .map((m) => ({
        id: m.institution,
        name: m.institution_name,
        roles: m.roles.map((r) => r.role),
      }));
  }, [user]);

  const fetchActiveInstitution = useCallback(
    (mode = "initial") => {
      // Abort any in-flight request from a previous switch/refresh.
      if (abortRef.current) abortRef.current.abort();

      const controller = new AbortController();
      abortRef.current = controller;
      const token = ++seqRef.current;

      const apply = (school, roles, modData) => {
        // Ignore the result if a newer request has already started.
        if (token !== seqRef.current) return;

        setCurrentSchool(school);
        setCurrentRoles(roles);
        if (modData) {
          setModules({
            loaded: true,
            enabled: modData.enabled || [],
            isPlatformAdmin: !!modData.is_platform_admin,
            schoolStatus: modData.school_status || "active",
          });
        }
        setError("");
        setLoading(false);
        if (mode === "switch") setIsSwitching(false);
      };

      if (!user) {
        setCurrentSchool(null);
        setCurrentRoles([]);
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
      ]).then(([instResult, modsResult]) => {
        if (controller.signal.aborted) return;

        const inst = instResult.status === "fulfilled" ? instResult.value : null;
        const mods = modsResult.status === "fulfilled" ? modsResult.value : null;

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

        apply(school, roles, mods);
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
            headers: { "Content-Type": "application/json" },
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
      modules,
      loading,
      isSwitching,
      error,
      schoolScopeVersion,
      switchSchool,
      refreshSchool,
      scopedHasRole,
    }),
    [
      currentSchool,
      currentRoles,
      availableSchools,
      modules,
      loading,
      isSwitching,
      error,
      schoolScopeVersion,
      switchSchool,
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
