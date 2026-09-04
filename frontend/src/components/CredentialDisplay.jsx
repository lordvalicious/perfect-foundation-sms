import { useState } from "react";
import { Check, Copy } from "lucide-react";

function CopyButton({ text, label }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const value = text || "";
    if (!value) return;

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = value;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard unavailable — nothing sensitive is logged */
    }
  };

  return (
    <button
      type="button"
      className="secondary-button"
      onClick={handleCopy}
      style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
      title={`Copy ${label}`}
    >
      {copied ? <Check size={14} /> : <Copy size={14} />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export function CredentialRow({ label, value }) {
  if (!value) return null;

  return (
    <div className="credential-row">
      <span>
        {label}: <strong>{value}</strong>
      </span>
      <CopyButton text={value} label={label} />
    </div>
  );
}

export default function CredentialDisplay({ username, password, name, note, onDismiss }) {
  if (!username && !password) return null;

  return (
    <div className="state-card success">
      <strong>
        {name ? `Login account created for ${name}.` : "User Created"}
      </strong>

      {username && <CredentialRow label="Username" value={username} />}

      {password && (
        <CredentialRow label="Temporary Password" value={password} />
      )}

      {note && <span>{note}</span>}

      <span>
        Share these credentials securely and remind the user to change their
        password after first login.
      </span>

      {onDismiss && (
        <button
          type="button"
          className="secondary-button"
          onClick={onDismiss}
          style={{ alignSelf: "center" }}
        >
          Got It
        </button>
      )}
    </div>
  );
}
