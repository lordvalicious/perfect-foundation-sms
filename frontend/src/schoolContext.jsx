import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
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
  const [error, setError] = useState("");

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

  const fetchActiveInstitution = useCallback(async () => {
    if (!user) {
      setCurrentSchool(null);
      setCurrentRoles([]);
      setModules({ loaded: false, enabled: [], isPlatformAdmin: false, schoolStatus: "active" });
      setLoading(false);
      return;
    }

    try {
      const data = await apiFetch("/api/auth/active-institution/", {}, "Could not load active institution.");
      setCurrentSchool(data.institution);
      setCurrentRoles(data.roles || []);
      setError("");
    } catch {
      if (user.memberships?.length > 0) {
        const m = user.memberships[0];
        setCurrentSchool({
          id: m.institution,
          name: m.institution_name,
          institution_type: "school",
        });
        setCurrentRoles(m.roles.map((r) => r.role));
      }
      setError("");
    }

    try {
      const modData = await apiFetch("/api/schools/modules/current/", {}, "Could not load modules.");
      setModules({
        loaded: true,
        enabled: modData.enabled || [],
        isPlatformAdmin: !!modData.is_platform_admin,
        schoolStatus: modData.school_status || "active",
      });
    } catch {
      setModules({ loaded: true, enabled: [], isPlatformAdmin: false, schoolStatus: "active" });
    }

    setLoading(false);
  }, [user]);

  useEffect(() => {
    fetchActiveInstitution();
  }, [fetchActiveInstitution]);

  const switchSchool = useCallback(
    async (institutionId) => {
      setLoading(true);
      setError("");

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

        await fetchActiveInstitution();
      } catch (err) {
        setError(err.message);
        setLoading(false);
        throw err;
      }
    },
    [fetchActiveInstitution]
  );

  const refreshSchool = useCallback(() => {
    setLoading(true);
    return fetchActiveInstitution();
  }, [fetchActiveInstitution]);

  const value = useMemo(
    () => ({
      currentSchool,
      currentRoles,
      availableSchools,
      modules,
      loading,
      error,
      switchSchool,
      refreshSchool,
    }),
    [currentSchool, currentRoles, availableSchools, modules, loading, error, switchSchool, refreshSchool]
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
