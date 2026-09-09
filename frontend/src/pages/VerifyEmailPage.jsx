import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, MailCheck, MailX, Loader } from "lucide-react";
import { useLang } from "../i18n";


export default function VerifyEmailPage() {
  const { lang } = useLang();
  const [state, setState] = useState("verifying");
  const [detail, setDetail] = useState("");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token") || "";

    if (!token) {
      setState("error");
      setDetail("This verification link is missing its token.");
      return;
    }

    fetch("/api/auth/email-verify/confirm/", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (response.ok) {
          setState("success");
        } else {
          setState("error");
          setDetail(data.detail || "This verification link is invalid or has expired.");
        }
      })
      .catch(() => {
        setState("error");
        setDetail("Could not reach the server. Please try again later.");
      });
  }, []);

  return (
    <div className="login-page" dir={lang === "ur" ? "rtl" : "ltr"}>
      <div className="login-card verify-card">
        <div className="login-emblem">
          <ShieldCheck size={32} />
        </div>

        {state === "verifying" && (
          <>
            <h1>Verifying email</h1>
            <p className="login-subtitle">Please wait while we confirm your address…</p>
            <div className="verify-loading">
              <Loader size={20} />
            </div>
          </>
        )}

        {state === "success" && (
          <>
            <div className="verify-icon success">
              <MailCheck size={40} />
            </div>
            <h1>Email verified</h1>
            <p className="login-subtitle">
              Your email address has been confirmed. You can now sign in.
            </p>
            <Link to="/login" className="primary-button login-button verify-button">
              Go to Sign In
            </Link>
          </>
        )}

        {state === "error" && (
          <>
            <div className="verify-icon error">
              <MailX size={40} />
            </div>
            <h1>Verification failed</h1>
            <p className="login-subtitle">{detail}</p>
            <Link to="/login" className="secondary-button login-button verify-button">
              Back to Sign In
            </Link>
          </>
        )}
      </div>
    </div>
  );
}