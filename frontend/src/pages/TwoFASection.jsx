import { useEffect, useState } from "react";
import { ShieldCheck, ShieldOff } from "lucide-react";
import { apiFetch } from "../api";

const BASE = "/api/auth/2fa/";

export default function TwoFASection() {
  const [status, setStatus] = useState(null);
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch(`${BASE}status/`)
      .then(setStatus)
      .catch(() => setStatus({ enabled: false }));
  }, []);

  const startSetup = () => {
    setBusy(true);
    setError("");
    setNotice("");

    apiFetch(`${BASE}setup/`, { method: "POST" })
      .then((data) => {
        setSetup(data);
        setStatus({ ...status, enabled: false });
      })
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  };

  const activate = (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");

    apiFetch(`${BASE}activate/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    })
      .then(() => {
        setStatus({ enabled: true });
        setSetup(null);
        setCode("");
        setNotice("Two-factor authentication is now active.");
      })
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  };

  const disable = (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");

    apiFetch(`${BASE}disable/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    })
      .then((data) => {
        setStatus(data);
        setPassword("");
        setNotice("Two-factor authentication disabled.");
      })
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  };

  if (status === null) return null;

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h3>Two-Factor Authentication</h3>
          <p>
            {status.enabled
              ? "Enabled — a code is required when signing in."
              : "Add an extra layer of security to your account."}
          </p>
        </div>
      </div>

      {notice && (
        <div className="state-card" style={{ marginBottom: 12 }}>{notice}</div>
      )}

      {error && (
        <div className="state-card error" style={{ marginBottom: 12 }}>{error}</div>
      )}

      {!status.enabled && !setup && (
        <button
          type="button"
          className="primary-button"
          onClick={startSetup}
          disabled={busy}
        >
          <ShieldCheck size={15} />
          Set up authenticator app
        </button>
      )}

      {setup && !status.enabled && (
        <form onSubmit={activate}>
          <p style={{ marginBottom: 8 }}>
            1. Add this secret to your authenticator app
            (Google Authenticator, Authy, etc.):
          </p>

          <p>
            <code style={{ fontSize: 16, letterSpacing: 1 }}>
              {setup.secret}
            </code>
          </p>

          <p style={{ margin: "10px 0", wordBreak: "break-all" }}>
            Or open this link:{" "}
            <a href={setup.otpauth_uri}>{setup.otpauth_uri.slice(0, 60)}…</a>
          </p>

          <p>2. Enter the current 6-digit code to confirm:</p>

          <div className="filter-row">
            <input
              inputMode="numeric"
              maxLength={6}
              placeholder="123456"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            <button className="primary-button" disabled={busy || code.length < 6}>
              Activate
            </button>
          </div>
        </form>
      )}

      {status.enabled && (
        <form onSubmit={disable}>
          <div className="filter-row">
            <input
              type="password"
              placeholder="Confirm your password to disable"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
            <button className="primary-button" disabled={busy}>
              <ShieldOff size={15} />
              Disable 2FA
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
