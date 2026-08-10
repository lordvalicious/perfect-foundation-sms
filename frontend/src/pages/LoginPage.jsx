import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, LogIn } from "lucide-react";
import { useAuth } from "../auth";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSubmitting(true);
    setError("");

    try {
      await login(identifier, password);
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
        <div className="login-emblem">
          <ShieldCheck size={30} />
        </div>

        <h1>Perfect Foundation</h1>

        <p className="login-subtitle">
          School Management Portal
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
              placeholder="admin"
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
