import { useCallback, useEffect, useMemo, useState } from "react";
import { GraduationCap, LogOut, RotateCcw, UserCheck } from "lucide-react";
import { apiFetch, authHeaders } from "../api";
import { StateArea, EmptyState, StatusBadge } from "./ui";

/* =============================================================================
   StudentLifecyclePanel — student lifecycle operations built against the
   backend business rules (/api/students). Never re-implements promotion,
   transfer or graduation logic — those live in Developer 1's progression
   services.
   ========================================================================== */

function endpointParams() {
  return { credentials: "include" };
}

function normalizePayload(data) {
  return (data && data.results) || [];
}

const CAN_MANAGE = ["super_admin", "admin", "principal", "academic"];
const CAN_REVIEW = ["super_admin", "admin", "principal", "vice_principal", "campus_admin", "academic"];

const ACTION_LABELS = {
  promotion: "Promotion",
  demotion: "Demotion",
  class_transfer: "Class transfer",
  section_transfer: "Section transfer",
  campus_transfer: "Campus transfer",
};

export { CAN_MANAGE, CAN_REVIEW };

function smallFormRow() {
  return { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 };
}

export default function StudentLifecyclePanel({
  studentId,
  studentName,
  currentCampusId = null,
  runId,
  hasRole,
  onChanged,
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [campusTransfers, setCampusTransfers] = useState([]);
  const [sectionTransfers, setSectionTransfers] = useState([]);
  const [reference, setReference] = useState({ years: [], campuses: [], classes: [], sections: [] });
  const [notice, setNotice] = useState("");
  const [busyAction, setBusyAction] = useState("");
  const [modal, setModal] = useState(null);

  const canManage = hasRole(CAN_MANAGE);
  const canReview = hasRole(CAN_REVIEW);

  const loadHistory = useCallback(() => {
    const params = new URLSearchParams({ student: String(studentId) });
    return fetch(`/api/students/progression/?${params.toString()}`, endpointParams())
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setHistory(Array.isArray(data) ? data : []))
      .catch(() => setHistory([]));
  }, [studentId]);

  const loadTransfers = useCallback(() => {
    const p = new URLSearchParams({ student: String(studentId) });
    const opts = endpointParams();
    return Promise.all([
      fetch(`/api/students/campus-transfers/?${p.toString()}`, opts).then((r) =>
        r.ok ? r.json() : { results: [] }
      ),
      fetch(`/api/students/section-transfers/?${p.toString()}`, opts).then((r) =>
        r.ok ? r.json() : { results: [] }
      ),
    ])
      .then(([campus, section]) => {
        setCampusTransfers(normalizePayload(campus));
        setSectionTransfers(normalizePayload(section));
      })
      .catch(() => {
        setCampusTransfers([]);
        setSectionTransfers([]);
      });
  }, [studentId]);

  const loadReference = useCallback(() => {
    const opts = endpointParams();
    const toList = (r) => (r.ok ? r.json() : { results: [] });
    return Promise.all([
      fetch("/api/schools/academic-years/", opts).then(toList),
      fetch("/api/schools/campuses/", opts).then(toList),
      fetch("/api/schools/classes/", opts).then(toList),
      fetch("/api/schools/sections/", opts).then(toList),
    ])
      .then(([years, campuses, classes, sections]) => {
        setReference({
          years: normalizePayload(years),
          campuses: normalizePayload(campuses),
          classes: normalizePayload(classes),
          sections: normalizePayload(sections),
        });
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");
    Promise.all([loadHistory(), loadTransfers(), loadReference()])
      .catch((err) => {
        if (alive) setError(err.message || "Unable to load lifecycle data.");
      })
      .finally(() => {
        if (alive) {
          setLoading(false);
        }
      });
    return () => {
      alive = false;
    };
  }, [loadHistory, loadTransfers, loadReference, runId]);

  const runAction = (key, promise, successMessage) => {
    setBusyAction(key);
    setNotice("");
    return promise
      .then(() => {
        setNotice(successMessage);
        return Promise.all([loadHistory(), loadTransfers()]);
      })
      .catch((err) => {
        setNotice(err.message || "Action failed.");
      })
      .finally(() => setBusyAction(""));
  };

  const bodyOf = (form) => {
    const body = {
      from_academic_year: Number(form.from_academic_year) || null,
      to_academic_year: Number(form.to_academic_year) || null,
      to_class: Number(form.to_class) || null,
      to_section: Number(form.to_section) || null,
      to_campus: Number(form.to_campus) || null,
      reason: form.reason || "",
      effective_date: form.effective_date || null,
    };
    if (body.to_academic_year === null) delete body.to_academic_year;
    if (body.to_class === null) delete body.to_class;
    if (body.to_section === null) delete body.to_section;
    if (body.to_campus === null) delete body.to_campus;
    if (!body.reason) delete body.reason;
    if (!body.effective_date) delete body.effective_date;
    return body;
  };

  /* -------- Promotion modal -------- */
  const promoteNow = (form) => {
    bodyOf(form);
    return runAction(
      "promote",
      apiFetch(`/api/students/promotions/${studentId}/`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(bodyOf(form)),
      }),
      "Student promoted / transferred."
    );
  };

  /* -------- Campus transfer modal -------- */
  const requestCampusTransfer = (form) =>
    runAction(
      "campus",
      apiFetch("/api/students/campus-transfers/", {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          student: studentId,
          from_campus: Number(form.from_campus) || null,
          to_campus: Number(form.to_campus) || null,
          academic_year: Number(form.academic_year) || null,
          effective_date: form.effective_date || null,
          reason: form.reason || "",
        }),
      }),
      "Campus transfer request created."
    );

  /* -------- Section transfer modal -------- */
  const requestSectionTransfer = (form) =>
    runAction(
      "section",
      apiFetch("/api/students/section-transfers/", {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          student: studentId,
          transfer_type: form.transfer_type || "section",
          from_section: Number(form.from_section) || null,
          to_section: Number(form.to_section) || null,
          academic_year: Number(form.academic_year) || null,
          effective_date: form.effective_date || null,
          reason: form.reason || "",
        }),
      }),
      "Section/class transfer request created."
    );

  /* -------- Status transitions -------- */
  const withdraw = () => {
    if (typeof window !== "undefined" && !window.confirm(`Withdraw ${studentName}? Their enrollment will be closed.`)) {
      return;
    }
    runAction(
      "withdraw",
      apiFetch(`/api/students/${studentId}/withdraw/`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({}),
      }),
      "Student marked as withdrawn."
    );
  };

  const graduate = () => {
    if (typeof window !== "undefined" && !window.confirm(`Graduate ${studentName}? This creates an alumni record.`)) {
      return;
    }
    runAction(
      "graduate",
      apiFetch(`/api/students/${studentId}/graduate/`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({}),
      }),
      "Student graduated and archived to alumni."
    );
  };

  const activate = () =>
    runAction(
      "activate",
      apiFetch(`/api/students/${studentId}/activate/`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({}),
      }),
      "Student activated."
    );

  const transferStatusAction = (kind, transfer, action, label) => {
    const base = kind === "campus" ? `/api/students/campus-transfers/${transfer.id}` : `/api/students/section-transfers/${transfer.id}`;
    const bound = { base };

    return (
      <button
        type="button"
        className="secondary-button secondary-button-sm"
        disabled={busyAction === label}
        onClick={() =>
          runAction(
            label,
            apiFetch(`${bound.base}/${action}/`, {
              method: "POST",
              headers: authHeaders({ "Content-Type": "application/json" }),
              body: JSON.stringify({}),
            }),
            `${transfer.student_name}: ${label}`
          )
        }
      >
        {label}
      </button>
    );
  };

  const workflowButtons = (kind, transfer) => {
    if (!canReview) return null;
    const buttons = [];
    if (transfer.status === "requested") {
      buttons.push(
        transferStatusAction(kind, transfer, "approve", "Approve"),
        transferStatusAction(kind, transfer, "reject", "Reject")
      );
    }
    if (transfer.status === "approved") {
      buttons.push(transferStatusAction(kind, transfer, "complete", "Complete"));
      buttons.push(transferStatusAction(kind, transfer, "cancel", "Cancel"));
    }
    if (transfer.status === "completed" && kind === "campus") {
      buttons.push(transferStatusAction(kind, transfer, "reverse", "Reverse"));
    }
    return buttons;
  };

  const referenceReady = useMemo(
    () => reference.years.length > 0 && reference.campuses.length > 0,
    [reference]
  );

  const sectionsForClass = (classId) =>
    reference.sections.filter((s) => Number(s.class_obj) === Number(classId));

  const currentCampusOptions = useMemo(
    () => reference.campuses.filter((c) => (currentCampusId ? Number(c.id) !== Number(currentCampusId) : true)),
    [reference.campuses, currentCampusId]
  );

  const currentSectionOptions = useMemo(() => {
    if (currentCampusId) return [];
    return reference.sections.filter((s) => { const c = s.class_obj; return true; });
  }, [reference.sections, currentCampusId]);

  return (
    <div>
      <StateArea
        loading={loading}
        error={error}
        onRetry={() => {
          setLoading(true);
          loadHistory().then(loadTransfers);
        }}
      >
        {notice && <div className="notice" style={{ marginBottom: 12 }}>{notice}</div>}

        {/* Action launchers */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 18 }}>
          {canManage && (
            <>
              <button type="button" className="secondary-button" onClick={() => setModal("promote")}>Promote / Transfer</button>
              <button type="button" className="secondary-button" onClick={() => setModal("campus")}>Request Campus Transfer</button>
              <button type="button" className="secondary-button" onClick={() => setModal("section")}>Request Section / Class Transfer</button>
            </>
          )}
          {canReview && (
            <>
              <button type="button" className="secondary-button" onClick={withdraw}>
                <LogOut size={14} /> Withdraw
              </button>
              <button type="button" className="secondary-button" onClick={graduate}>
                <GraduationCap size={14} /> Graduate
              </button>
              <button type="button" className="secondary-button" onClick={activate}>
                <RotateCcw size={14} /> Reactivate
              </button>
            </>
          )}
          {!canManage && !canReview && (
            <p className="muted">You do not have permission to change this student's lifecycle.</p>
          )}
        </div>

        {/* Promote modal */}
        {modal === "promote" && (
          <LifecycleModal
            title={`Promote / Transfer ${studentName}`}
            onClose={() => setModal(null)}
            onSubmit={(form) => promoteNow(form).then(() => setModal(null))}
            busy={busyAction === "promote"}
          >
            <p className="hint">Promotion uses the school's progression rules. Same-year moves are transfers; cross-year moves are promotions/demotions.</p>
            <FormField label="From academic year *">
              <select name="from_academic_year" defaultValue={reference.years.find((y) => y.status === "active")?.id || ""}>
                {reference.years.map((y) => (
                  <option key={y.id} value={y.id}>{y.name}</option>
                ))}
              </select>
            </FormField>
            <div style={smallFormRow()}>
              <FormField label="To academic year">
                <select name="to_academic_year" defaultValue="">
                  <option value="">— Keep current year (transfer) —</option>
                  {reference.years.map((y) => (
                    <option key={y.id} value={y.id}>{y.name}</option>
                  ))}
                </select>
              </FormField>
              <FormField label="To campus">
                <select name="to_campus" defaultValue="">
                  <option value="">— Keep current —</option>
                  {currentCampusOptions.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </FormField>
            </div>
            <FormField label="To class">
              <select name="to_class" defaultValue="">
                <option value="">— Keep current —</option>
                {reference.classes.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </FormField>
            <FormField label="To section">
              <select name="to_section" defaultValue="">
                <option value="">— Keep current —</option>
                {reference.sections.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </FormField>
            <div style={smallFormRow()}>
              <FormField label="Effective date">
                <input type="date" name="effective_date" />
              </FormField>
              <FormField label="Reason">
                <input type="text" name="reason" placeholder="Optional reason" />
              </FormField>
            </div>
          </LifecycleModal>
        )}

        {/* Campus transfer modal */}
        {modal === "campus" && (
          <LifecycleModal
            title={`Request campus transfer (${studentName})`}
            onClose={() => setModal(null)}
            onSubmit={(form) => requestCampusTransfer(form).then(() => setModal(null))}
            busy={busyAction === "campus"}
          >
            <div style={smallFormRow()}>
              <FormField label="From campus">
                <select name="from_campus" defaultValue={currentCampusId || ""}>
                  <option value="">— Select —</option>
                  {reference.campuses.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </FormField>
              <FormField label="To campus *">
                <select name="to_campus" defaultValue="">
                  <option value="">— Select —</option>
                  {currentCampusOptions.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </FormField>
            </div>
            <FormField label="Academic year *">
              <select name="academic_year" defaultValue={reference.years.find((y) => y.status === "active")?.id || ""}>
                {reference.years.map((y) => (
                  <option key={y.id} value={y.id}>{y.name}</option>
                ))}
              </select>
            </FormField>
            <div style={smallFormRow()}>
              <FormField label="Effective date">
                <input type="date" name="effective_date" />
              </FormField>
              <FormField label="Reason">
                <input type="text" name="reason" placeholder="Optional reason" />
              </FormField>
            </div>
          </LifecycleModal>
        )}

        {/* Section transfer modal */}
        {modal === "section" && (
          <LifecycleModal
            title={`Request section/class transfer (${studentName})`}
            onClose={() => setModal(null)}
            onSubmit={(form) => requestSectionTransfer(form).then(() => setModal(null))}
            busy={busyAction === "section"}
          >
            <FormField label="Transfer type *">
              <select name="transfer_type" defaultValue="section">
                <option value="section">Section change</option>
                <option value="class">Class change</option>
              </select>
            </FormField>
            <FormField label="To section *">
              <select name="to_section" defaultValue="">
                <option value="">— Select —</option>
                {reference.sections.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </FormField>
            <FormField label="Academic year *">
              <select name="academic_year" defaultValue={reference.years.find((y) => y.status === "active")?.id || ""}>
                {reference.years.map((y) => (
                  <option key={y.id} value={y.id}>{y.name}</option>
                ))}
              </select>
            </FormField>
            <div style={smallFormRow()}>
              <FormField label="Effective date">
                <input type="date" name="effective_date" />
              </FormField>
              <FormField label="Reason">
                <input type="text" name="reason" placeholder="Optional reason" />
              </FormField>
            </div>
          </LifecycleModal>
        )}

        {/* Open transfer requests */}
        <PanelHeader title="Open Transfer Requests" fill />
        {(campusTransfers.length === 0 && sectionTransfers.length === 0) ? (
          <EmptyState icon={UserCheck} title="No pending transfers" message="Requests from this student will appear here." />
        ) : (
          <>
            {campusTransfers.length > 0 && (
              <div className="table-wrapper" style={{ marginBottom: 14 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>TYPE</th><th>FROM → TO</th><th>YEAR</th><th>EFFECTIVE</th><th>STATUS</th><th>ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {campusTransfers.map((t) => (
                      <tr key={t.id}>
                        <td>Campus</td>
                        <td>{t.from_campus_name || "—"} → {t.to_campus_name || "—"}</td>
                        <td>{t.academic_year_name || "—"}</td>
                        <td>{t.effective_date || "—"}</td>
                        <td><StatusBadge status={t.status} /></td>
                        <td className="row-actions">{workflowButtons("campus", t)} {t.reversal_reason && ` · ${t.reversal_reason}`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {sectionTransfers.length > 0 && (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>TYPE</th><th>FROM → TO</th><th>YEAR</th><th>EFFECTIVE</th><th>STATUS</th><th>ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sectionTransfers.map((t) => (
                      <tr key={t.id}>
                        <td>{t.transfer_type === "class" ? "Class" : "Section"}</td>
                        <td>{(t.from_class_name || "") + (t.from_section_name ? ` ${t.from_section_name}` : "") || "—"} → {(t.to_class_name || "") + (t.to_section_name ? ` ${t.to_section_name}` : "") || "—"}</td>
                        <td>{t.academic_year_name || "—"}</td>
                        <td>{t.effective_date || "—"}</td>
                        <td><StatusBadge status={t.status} /></td>
                        <td className="row-actions">{workflowButtons("section", t)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {/* Progression history */}
        <PanelHeader title="Academic Progression" count={history.length ? `${history.length} records` : null} />
        {history.length === 0 ? (
          <EmptyState icon={GraduationCap} title="No progression history" message="Promotions, demotions and transfers will be logged here." />
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ACTION</th><th>FROM</th><th>TO</th><th>EFFECTIVE</th><th>REASON</th><th>BY</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id}>
                    <td>{ACTION_LABELS[h.action] || h.action_display || h.action}</td>
                    <td>{(h.from_academic_year_name || "")}{(h.from_class_name ? ` · ${h.from_class_name}` : "")}{(h.from_section_name ? ` ${h.from_section_name}` : "")}</td>
                    <td>{(h.to_academic_year_name || "—")}{(h.to_class_name ? ` · ${h.to_class_name}` : "")}{(h.to_section_name ? ` ${h.to_section_name}` : "")}</td>
                    <td>{h.effective_date || h.created_at?.slice(0, 10) || "—"}</td>
                    <td>{h.reason || "—"}</td>
                    <td>{h.performed_by_name || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </StateArea>
      {!referenceReady && !loading && (
        <p className="muted">Reference data unavailable — promotion/transfer forms may be limited.</p>
      )}
    </div>
  );
}

/* =============================================================================
   Small internal building blocks
   ========================================================================== */

function FormField({ label, children }) {
  return (
    <label className="form-field" style={{ display: "block", marginBottom: 10 }}>
      <span className="field-label">{label}</span>
      {children}
    </label>
  );
}

function PanelHeader({ title, count, fill }) {
  return (
    <div className="teacher-list-header" style={fill ? { marginTop: 10 } : undefined}>
      <div>
        <h3>{title}</h3>
        {typeof count === "string" && <p>{count}</p>}
      </div>
    </div>
  );
}

function LifecycleModal({ title, onClose, onSubmit, busy, children }) {
  const [form, setForm] = useState({});
  const set = (name) => (e) => setForm((f) => ({ ...f, [name]: e.target.value }));

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 560 }}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button type="button" className="icon-button" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          {ReactChildren({ target: children, set, form })}
        </div>
        <div className="modal-footer">
          <button type="button" className="secondary-button" onClick={onClose}>Cancel</button>
          <button
            type="button"
            className="primary-button"
            disabled={busy}
            onClick={() => onSubmit(form)}
          >
            {busy ? "Saving..." : "Submit"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ReactChildren({ target, set, form }) {
  return (
    <>
      {(Array.isArray(target) ? target : [target]).map((child, i) => {
        if (child && typeof child === "object" && child.type === FormField) {
          const props = { ...child.props };
          const input = props.children;
          if (input && typeof input.type === "string" && input.props && input.props.name) {
            props.children = {
              ...input,
              props: {
                ...input.props,
                value: form[input.props.name] || input.props.defaultValue || "",
                onChange: set(input.props.name),
              },
            };
          }
          return <FormField key={i} {...props} />;
        }
        if (child && typeof child === "object" && child.props) {
          return (
            <div key={i} style={child.props.style}>
              {ReactChildren({ target: child.props.children, set, form })}
            </div>
          );
        }
        return child;
      })}
    </>
  );
}
