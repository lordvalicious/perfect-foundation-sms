import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

const AuthContext = createContext(null);

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }

  return null;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchMe = useCallback(() => {
    return fetch("/api/auth/me/", {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("not authenticated");
        }

        return response.json();
      })
      .then((data) => {
        setUser(data);
        setError("");
      })
      .catch(() => {
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const login = useCallback(
    async (username, password) => {
      setError("");

      await fetch("/api/auth/csrf/", {
        method: "GET",
        credentials: "include",
      });

      const response = await fetch("/api/auth/login/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") || "",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        let message = "Unable to sign in.";

        if (data.detail) {
          message = Array.isArray(data.detail)
            ? data.detail.join(", ")
            : data.detail;
        }

        throw new Error(message);
      }

      setUser(data);
      return data;
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await fetch("/api/auth/logout/", {
        method: "POST",
        credentials: "include",
        headers: {
          "X-CSRFToken": getCookie("csrftoken") || "",
        },
      });
    } finally {
      setUser(null);
    }
  }, []);

  const hasRole = useCallback(
    (roles) => {
      if (!user) return false;

      const userRoles = new Set();

      for (const membership of user.memberships || []) {
        for (const assignment of membership.roles || []) {
          userRoles.add(assignment.role);
        }
      }

      if (user.is_superuser) return true;

      return roles.some((role) => userRoles.has(role));
    },
    [user]
  );

  const value = useMemo(
    () => ({
      user,
      loading,
      error,
      login,
      logout,
      hasRole,
      refresh: fetchMe,
    }),
    [user, loading, error, login, logout, hasRole, fetchMe]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === null) {
    throw new Error(
      "useAuth must be used within an AuthProvider."
    );
  }

  return context;
}
