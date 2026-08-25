import { useCallback, useEffect, useRef, useState } from "react";
import { Palette, Save, Upload } from "lucide-react";
import { PageHeader, StateArea } from "./ui";

const BRANDING_URL = "/api/schools/branding/";

const DEFAULT_COLORS = {
  primary_color: "#1a73e8",
  secondary_color: "#34a853",
  accent_color: "#fbbc04",
};

export default function BrandingPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const fileInputRef = useRef(null);
  const faviconInputRef = useRef(null);

  const [form, setForm] = useState({
    school_name: "",
    short_name: "",
    motto: "",
    primary_color: DEFAULT_COLORS.primary_color,
    secondary_color: DEFAULT_COLORS.secondary_color,
    accent_color: DEFAULT_COLORS.accent_color,
    contact_email: "",
    contact_phone: "",
    contact_website: "",
    address_line: "",
    footer_text: "",
    currency: "PKR",
    timezone: "UTC",
    date_format: "dd-mm-yyyy",
    language: "en",
    working_days: ["mon", "tue", "wed", "thu", "fri"],
    email_from_name: "",
    email_from_address: "",
  });

  const [logoPreview, setLogoPreview] = useState(null);
  const [logoFile, setLogoFile] = useState(null);
  const [faviconFile, setFaviconFile] = useState(null);

  const fetchBranding = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(BRANDING_URL, { credentials: "include" });
      if (response.ok) {
        const data = await response.json();
        setForm({
          school_name: data.school_name || "",
          short_name: data.short_name || "",
          motto: data.motto || "",
          primary_color: data.primary_color || DEFAULT_COLORS.primary_color,
          secondary_color: data.secondary_color || DEFAULT_COLORS.secondary_color,
          accent_color: data.accent_color || DEFAULT_COLORS.accent_color,
          contact_email: data.contact_email || "",
          contact_phone: data.contact_phone || "",
          contact_website: data.contact_website || "",
          address_line: data.address_line || "",
          footer_text: data.footer_text || "",
          currency: data.currency || "PKR",
          timezone: data.timezone || "UTC",
          date_format: data.date_format || "dd-mm-yyyy",
          language: data.language || "en",
          working_days:
            data.working_days?.length > 0
              ? data.working_days
              : ["mon", "tue", "wed", "thu", "fri"],
          email_from_name: data.email_from_name || "",
          email_from_address: data.email_from_address || "",
        });
        if (data.logo_url) setLogoPreview(data.logo_url);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBranding();
  }, [fetchBranding]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((p) => ({ ...p, [name]: value }));
  };

  const handleLogoChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setLogoFile(file);
      const reader = new FileReader();
      reader.onload = (e) => setLogoPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const handleFaviconChange = (event) => {
    const file = event.target.files[0];
    if (file) setFaviconFile(file);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    const formData = new FormData();
    Object.entries(form).forEach(([key, value]) => {
      if (key === "working_days") {
        formData.append("working_days", JSON.stringify(value));
      } else {
        formData.append(key, value);
      }
    });
    if (logoFile) formData.append("logo", logoFile);
    if (faviconFile) formData.append("favicon", faviconFile);

    try {
      const csrfToken = document.cookie.split("; ")
        .find((c) => c.startsWith("csrftoken="))
        ?.split("=")[1] || "";

      const response = await fetch(BRANDING_URL, {
        method: "PUT",
        headers: { "X-CSRFToken": csrfToken },
        credentials: "include",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to save.");
      }

      setSuccess("Branding settings saved successfully.");
      setLogoFile(null);
      setFaviconFile(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Settings / Branding"
        title="School Branding"
        subtitle="Customize the look and feel of your school's identity."
      />

      <StateArea loading={loading}>
        <form onSubmit={handleSubmit}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            {/* Left: Branding */}
            <div>
              <div className="panel">
                <div className="teacher-list-header">
                  <h3>Identity</h3>
                </div>
                <div className="form-section">
                  <div className="form-grid">
                    <label>
                      School Name
                      <input name="school_name" value={form.school_name} onChange={handleChange} />
                    </label>
                    <label style={{ gridColumn: "1 / -1" }}>
                      Motto / Tagline
                      <input name="motto" value={form.motto} onChange={handleChange} placeholder="Excellence in Education" />
                    </label>
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="teacher-list-header">
                  <h3><Palette size={16} /> Colors</h3>
                </div>
                <div className="form-section">
                  <div className="form-grid">
                    <label>
                      Primary Color
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <input type="color" value={form.primary_color} onChange={(e) => setForm((p) => ({ ...p, primary_color: e.target.value }))} style={{ width: 40, height: 32, padding: 0, border: "none", cursor: "pointer" }} />
                        <input name="primary_color" value={form.primary_color} onChange={handleChange} style={{ flex: 1 }} />
                      </div>
                    </label>
                    <label>
                      Secondary Color
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <input type="color" value={form.secondary_color} onChange={(e) => setForm((p) => ({ ...p, secondary_color: e.target.value }))} style={{ width: 40, height: 32, padding: 0, border: "none", cursor: "pointer" }} />
                        <input name="secondary_color" value={form.secondary_color} onChange={handleChange} style={{ flex: 1 }} />
                      </div>
                    </label>
                    <label>
                      Accent Color
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <input type="color" value={form.accent_color} onChange={(e) => setForm((p) => ({ ...p, accent_color: e.target.value }))} style={{ width: 40, height: 32, padding: 0, border: "none", cursor: "pointer" }} />
                        <input name="accent_color" value={form.accent_color} onChange={handleChange} style={{ flex: 1 }} />
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="teacher-list-header">
                  <h3>Localization & Settings</h3>
                </div>
                <div className="form-section">
                  <div className="form-grid">
                    <label>
                      Short Name
                      <input name="short_name" value={form.short_name} onChange={handleChange} placeholder="e.g. PFS" />
                    </label>
                    <label>
                      Currency (3-letter)
                      <input name="currency" maxLength={3} value={form.currency} onChange={handleChange} placeholder="PKR" />
                    </label>
                    <label>
                      Timezone
                      <input name="timezone" value={form.timezone} onChange={handleChange} placeholder="Asia/Karachi" />
                    </label>
                    <label>
                      Date Format
                      <select name="date_format" value={form.date_format} onChange={handleChange}>
                        {["dd-mm-yyyy", "dd MMM yyyy", "mm/dd/yyyy", "yyyy-mm-dd"].map((f) => (
                          <option key={f} value={f}>{f}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Default Language
                      <select name="language" value={form.language} onChange={handleChange}>
                        <option value="en">English</option>
                        <option value="ur">اردو</option>
                      </select>
                    </label>
                    <label style={{ gridColumn: "1 / -1" }}>
                      Working Days
                      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", fontSize: 13 }}>
                        {[
                          ["mon", "Mon"], ["tue", "Tue"], ["wed", "Wed"],
                          ["thu", "Thu"], ["fri", "Fri"], ["sat", "Sat"], ["sun", "Sun"],
                        ].map(([key, label]) => (
                          <label key={key} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <input
                              type="checkbox"
                              checked={form.working_days.includes(key)}
                              onChange={(e) =>
                                setForm((p) => ({
                                  ...p,
                                  working_days: e.target.checked
                                    ? [...p.working_days, key]
                                    : p.working_days.filter((d) => d !== key),
                                }))
                              }
                            />
                            {label}
                          </label>
                        ))}
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="teacher-list-header">
                  <h3>White-Label Email Sender</h3>
                </div>
                <div className="form-section">
                  <div className="form-grid">
                    <label>
                      From Name (on outgoing emails)
                      <input name="email_from_name" value={form.email_from_name} onChange={handleChange}
                        placeholder={`e.g. ${form.school_name || "School"} Office`} />
                    </label>
                    <label>
                      From Address override
                      <input type="email" name="email_from_address" value={form.email_from_address} onChange={handleChange}
                        placeholder="no-reply@yourdomain.edu" />
                    </label>
                  </div>
                  <p style={{ fontSize: 12, color: "#888" }}>
                    Leave blank to use the platform default sender. Custom domains need SPF/DKIM verification with your email provider.
                  </p>
                </div>
              </div>

              <div className="panel">
                <div className="teacher-list-header">
                  <h3>Contact Information</h3>
                </div>
                <div className="form-section">
                  <div className="form-grid">
                    <label>
                      Email
                      <input type="email" name="contact_email" value={form.contact_email} onChange={handleChange} placeholder="info@school.com" />
                    </label>
                    <label>
                      Phone
                      <input name="contact_phone" value={form.contact_phone} onChange={handleChange} placeholder="+92 300 1234567" />
                    </label>
                    <label>
                      Website
                      <input name="contact_website" value={form.contact_website} onChange={handleChange} placeholder="https://school.com" />
                    </label>
                    <label style={{ gridColumn: "1 / -1" }}>
                      Address
                      <input name="address_line" value={form.address_line} onChange={handleChange} placeholder="123 Education Street, Lahore" />
                    </label>
                    <label style={{ gridColumn: "1 / -1" }}>
                      Footer Text
                      <input name="footer_text" value={form.footer_text} onChange={handleChange} placeholder="Text shown in report card footers" />
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Logo Upload + Preview */}
            <div>
              <div className="panel">
                <div className="teacher-list-header">
                  <h3>Logo</h3>
                </div>
                <div className="form-section">
                  <div style={{ textAlign: "center" }}>
                    {logoPreview ? (
                      <img src={logoPreview} alt="Logo preview" style={{ maxWidth: "100%", maxHeight: 200, borderRadius: 8, border: "1px solid #e0e0e0" }} />
                    ) : (
                      <div style={{ width: "100%", height: 150, border: "2px dashed #ccc", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", color: "#999" }}>
                        No logo uploaded
                      </div>
                    )}
                    <input type="file" ref={fileInputRef} onChange={handleLogoChange} accept="image/*" style={{ display: "none" }} />
                    <button type="button" className="secondary-button" style={{ marginTop: 12 }} onClick={() => fileInputRef.current?.click()}>
                      <Upload size={14} /> Upload Logo
                    </button>
                  </div>

                  <div style={{ marginTop: 16, textAlign: "center" }}>
                    <input type="file" ref={faviconInputRef} onChange={handleFaviconChange} accept="image/*" style={{ display: "none" }} />
                    <button type="button" className="secondary-button" onClick={() => faviconInputRef.current?.click()}>
                      <Upload size={14} /> Upload Favicon
                    </button>
                    {faviconFile && <span style={{ marginLeft: 8, fontSize: 12 }}>{faviconFile.name}</span>}
                  </div>
                </div>
              </div>

              {/* Live Preview */}
              <div className="panel">
                <div className="teacher-list-header">
                  <h3>Live Preview</h3>
                </div>
                <div className="form-section">
                  <div style={{ borderRadius: 8, overflow: "hidden", border: "1px solid #e0e0e0" }}>
                    {/* Preview header */}
                    <div style={{ background: form.primary_color, color: "#fff", padding: "12px 16px", display: "flex", alignItems: "center", gap: 12 }}>
                      {logoPreview ? (
                        <img src={logoPreview} alt="" style={{ height: 32, borderRadius: 4 }} />
                      ) : (
                        <div style={{ width: 32, height: 32, background: "rgba(255,255,255,0.2)", borderRadius: 4, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 14 }}>
                          {form.school_name ? form.school_name.charAt(0) : "S"}
                        </div>
                      )}
                      <div>
                        <strong style={{ fontSize: 14 }}>{form.school_name || "School Name"}</strong>
                        {form.motto && <div style={{ fontSize: 11, opacity: 0.8 }}>{form.motto}</div>}
                      </div>
                    </div>
                    {/* Preview content */}
                    <div style={{ padding: 16, background: "#f8f9fa" }}>
                      <div style={{ display: "flex", gap: 8 }}>
                        <div style={{ width: 8, borderRadius: 4, background: form.secondary_color }} />
                        <div style={{ width: 8, borderRadius: 4, background: form.accent_color }} />
                        <div style={{ width: 8, borderRadius: 4, background: form.primary_color }} />
                      </div>
                      <div style={{ marginTop: 12, fontSize: 12, color: "#666" }}>
                        {form.contact_email && <div>Email: {form.contact_email}</div>}
                        {form.contact_phone && <div>Phone: {form.contact_phone}</div>}
                        {form.contact_website && <div>Web: {form.contact_website}</div>}
                      </div>
                    </div>
                    {/* Preview footer */}
                    {form.footer_text && (
                      <div style={{ background: form.primary_color, color: "#fff", padding: "8px 16px", fontSize: 11, textAlign: "center" }}>
                        {form.footer_text}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {error && <div className="state-card error"><strong>{error}</strong></div>}
          {success && <div className="state-card success"><strong>{success}</strong></div>}

          <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
            <button type="submit" className="primary-button" disabled={saving}>
              <Save size={15} />
              {saving ? "Saving..." : "Save Branding"}
            </button>
          </div>
        </form>
      </StateArea>
    </section>
  );
}
