import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogIn, ShieldCheck } from "lucide-react";
import { useAuth } from "../auth";
import { useLang } from "../i18n";

export default function LoginPage() {
  const { login } = useAuth();
  const { t, lang, setLang } = useLang();
  const navigate = useNavigate();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpRequired, setOtpRequired] = useState(false);
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
      await login(identifier, password, schoolCode, otp);
      navigate("/", { replace: true });
    } catch (err) {
      if (err.otpRequired) {
        setOtpRequired(true);
      }

      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleLang = () => {
    const next = lang === "en" ? "ur" : "en";
    setLang(next);

    document
      .querySelectorAll("input")
      .forEach((input) => {
        input.dir = next === "ur" ? "rtl" : "ltr";
      });
  };

  return (
    <div className="login-page" dir={lang === "ur" ? "rtl" : "ltr"}>
      <div style={{ position: "absolute", top: 16, insetInlineEnd: 16 }}>
        <button
          className="theme-toggle"
          onClick={toggleLang}
          title={lang === "en" ? "اردو میں دیکھیں" : "Switch to English"}
        >
          {lang === "en" ? "اردو" : "EN"}
        </button>
      </div>

      <div className="login-card">
        <div className="login-emblem" style={branding?.primary_color ? { background: branding.primary_color } : undefined}>
          {branding?.logo_url ? <img src={branding.logo_url} alt="" /> : <ShieldCheck size={32} />}
        </div>

        <h1>{branding?.school_name || "School Management"}</h1>

        <p className="login-subtitle">
          {lang === "ur"
            ? "اسکول مینجمنٹ پورٹل"
            : branding?.motto || "School Management Portal"}
        </p>

        <form onSubmit={handleSubmit}>
          <label>
            {t("Username or Email")}
            <input
              type="text"
              value={identifier}
              onChange={(event) =>
                setIdentifier(event.target.value)
              }
              placeholder={t("Username or Email")}
              autoComplete="username"
              required
            />
          </label>

          <label>
            {t("Password")}
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

          {otpRequired && (
            <label>
              {t("Authenticator code")}
              <input
                type="text"
                inputMode="numeric"
                value={otp}
                onChange={(event) => setOtp(event.target.value)}
                placeholder="6-digit code"
                autoComplete="one-time-code"
                maxLength={6}
                autoFocus
              />
            </label>
          )}

          {error && (
            <div className="login-error">{error}</div>
          )}

          <button
            type="submit"
            className="primary-button login-button"
            disabled={submitting}
          >
            <LogIn size={17} />
            {submitting ? t("Signing in...") : t("Sign In")}
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
