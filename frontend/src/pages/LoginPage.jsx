import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogIn, ShieldCheck } from "lucide-react";
import { useAuth } from "../auth";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [branding, setBranding] = useState(null);
  const schoolCode = new URLSearchParams(window.location.search).get("school_code") || "";

  useEffect(() => {
    if (!schoolCode) return undefined;

    fetch(`/api/schools/tenant-config/?school_code=${encodeURIComponent(schoolCode)}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (data) {
          setBranding(data);
          document.title = data.school_name;
          if (data.favicon_url) {
            const favicon = document.querySelector("link[rel='icon']") || document.createElement("link");
            favicon.rel = "icon";
            favicon.href = data.favicon_url;
            document.head.appendChild(favicon);
          }
        }
      })
      .catch(() => {});

    return undefined;
  }, [schoolCode]);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSubmitting(true);
    setError("");

    try {
      await login(identifier, password, schoolCode);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-emblem" style={branding?.primary_color ? { background: branding.primary_color } : undefined}>
          {branding?.logo_url ? <img src={branding.logo_url} alt="" /> : <ShieldCheck size={32} />}
        </div>

        <h1>{branding?.school_name || "School Management"}</h1>

        <p className="login-subtitle">
          {branding?.motto || "School Management Portal"}
        </p>

        <form onSubmit={handleSubmit}>
          <label>
            Username or Email
            <input
              type="text"
              value={identifier}
              onChange={(event) =>
                setIdentifier(event.target.value)
              }
              placeholder="Username or email"
              autoComplete="username"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </label>

          {error && (
            <div className="login-error">{error}</div>
          )}

          <button
            type="submit"
            className="primary-button login-button"
            disabled={submitting}
          >
            <LogIn size={17} />
            {submitting ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="login-hint">
          <strong>Demo accounts</strong>
          <span>admin / Admin123!</span>
          <span>accountant / Accountant123!</span>
          <span>teacher / Teacher123!</span>
          <span>student / Student123!</span>
        </div>
      </div>
    </div>
  );
}
