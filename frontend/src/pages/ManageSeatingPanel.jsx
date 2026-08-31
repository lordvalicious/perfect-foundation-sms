import { useEffect, useState } from "react";
import { Armchair, Save, Wand2, AlertTriangle } from "lucide-react";
import { apiFetch } from "../api";
import { EmptyState, PanelHeader, StateArea } from "./ui";

const SECTIONS_URL = "/api/schools/sections/?page_size=500";
const STUDENTS_URL = "/api/students/?page_size=500";
const SEATING_URL = "/api/exams/seating/";
const SEATING_BULK_URL = "/api/exams/seating/bulk/";

function toList(data) {
  return Array.isArray(data) ? data : data.results || [];
}

export default function ManageSeatingPanel({ exam, onChanged }) {
  const [sections, setSections] = useState([]);
  const [selectedSection, setSelectedSection] = useState("");
  const [students, setStudents] = useState([]);
  const [existing, setExisting] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loadingSections, setLoadingSections] = useState(true);
  const [loadingRoster, setLoadingRoster] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [saveError, setSaveError] = useState("");

  const isLocked = exam.status === "completed";

  useEffect(() => {
    fetch(SECTIONS_URL, { credentials: "include" })
      .then((response) => (response.ok ? response.json() : []))
      .then((data) => {
        const all = toList(data);
        const classSections = all.filter(
          (section) => String(section.class_obj) === String(exam.class_obj)
        );
        setSections(classSections);
        if (classSections.length > 0) {
          setSelectedSection(String(classSections[0].id));
        }
      })
      .catch(() => setError("Failed to load sections."))
      .finally(() => setLoadingSections(false));
  }, [exam.id, exam.class_obj]);

  useEffect(() => {
    if (!selectedSection) {
      setStudents([]);
      setExisting([]);
      setAssignments([]);
      return undefined;
    }

    setLoadingRoster(true);
    setError("");
    setSaveMessage("");
    setSaveError("");

    const toListOrEmpty = (response) =>
      response.ok ? response.json() : [];

    Promise.all([
      fetch(
        `${STUDENTS_URL}&class_obj=${exam.class_obj}&section=${selectedSection}`,
        { credentials: "include" }
      ).then(toListOrEmpty),
      fetch(
        `${SEATING_URL}?exam=${exam.id}&section=${selectedSection}&page_size=500`,
        { credentials: "include" }
      ).then(toListOrEmpty),
    ])
      .then(([roster, seats]) => {
        const seatByStudent = new Map(
          toList(seats).map((seat) => [String(seat.student), seat])
        );

        setStudents(toList(roster));
        setExisting(toList(seats));
        setAssignments(
          toList(roster).map((student) => {
            const seat = seatByStudent.get(String(student.id));

            return {
              student_id: student.id,
              seat_number: seat ? String(seat.seat_number) : "",
              room: seat ? seat.room || "" : "",
              notes: seat ? seat.notes || "" : "",
            };
          })
        );
      })
      .catch(() => setError("Failed to load the seating roster."))
      .finally(() => setLoadingRoster(false));

    return undefined;
  }, [selectedSection, exam.id, exam.class_obj]);

  const setRow = (studentId, field, value) =>
    setAssignments((current) =>
      current.map((row) =>
        row.student_id === studentId ? { ...row, [field]: value } : row
      )
    );

  const assignSequential = () => {
    const used = new Set(
      assignments
        .map((row) => Number(row.seat_number))
        .filter((number) => Number.isFinite(number) && number > 0)
    );

    let next = 1;

    while (used.has(next)) {
      next += 1;
    }

    setAssignments((current) =>
      current.map((row) => {
        if (row.seat_number) {
          return row;
        }

        used.add(next);
        const value = next;

        next += 1;
        return { ...row, seat_number: String(value) };
      })
    );
  };

  const unseatedCount = assignments.filter((row) => !row.seat_number).length;

  const seatRowFor = (studentId) =>
    existing.find((seat) => String(seat.student) === String(studentId));

  const handleSave = async () => {
    setSaving(true);
    setSaveMessage("");
    setSaveError("");

    try {
      const items = assignments
        .filter((row) => row.seat_number && row.seat_number.trim())
        .map((row) => ({
          student: row.student_id,
          seat_number: row.seat_number.trim(),
          room: row.room.trim(),
          notes: row.notes.trim(),
        }));

      if (items.length === 0) {
        setSaveError(
          "Assign at least one seat before saving, or leave the section empty."
        );
        setSaving(false);
        return;
      }

      const removed = [];
      const kept = new Set(
        items
          .filter((item) => {
            const existingRow = seatRowFor(item.student);

            if (!existingRow) {
              return false;
            }

            if (
              String(existingRow.seat_number) === String(item.seat_number) &&
              (existingRow.room || "") === item.room &&
              (existingRow.notes || "") === item.notes
            ) {
              return true;
            }

            removed.push(existingRow.id);
            return false;
          })
          .map((item) => String(item.student))
      );

      const toDelete = [
        ...removed,
        ...existing
          .filter((seat) => !kept.has(String(seat.student)))
          .map((seat) => seat.id),
      ];

      for (const id of new Set(toDelete)) {
        await apiFetch(
          `${SEATING_URL}${id}/`,
          { method: "DELETE" },
          "Failed to clear a previous seat."
        );
      }

      const createItems = items.filter(
        (item) => !kept.has(String(item.student))
      );

      if (createItems.length > 0) {
        const result = await apiFetch(
          SEATING_BULK_URL,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              exam: exam.id,
              section: Number(selectedSection),
              items: createItems,
            }),
          },
          "Failed to save seating."
        );

        setSaveMessage(
          result.detail ||
            `${result.count || createItems.length} seats assigned.`
        );
      } else {
        setSaveMessage("Seating is already up to date.");
      }

      onChanged();
    } catch (err) {
      setSaveError(err.message || String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="panel">
      <PanelHeader
        title="Seating Arrangement"
        subtitle={`${assignments.length} students · ${unseatedCount} unseated`}
        action={
          !isLocked && (
            <div
              className="table-actions"
              style={{ gap: 8, display: "inline-flex" }}
            >
              <button
                type="button"
                className="secondary-button"
                onClick={assignSequential}
                disabled={loadingRoster || unseatedCount === 0}
              >
                <Wand2 size={16} />
                Assign sequential seats
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={handleSave}
                disabled={loadingRoster || saving}
              >
                <Save size={16} />
                {saving ? "Saving..." : "Save seating"}
              </button>
            </div>
          )
        }
      />

      {isLocked && (
        <div
          className="alert"
          style={{
            background: "var(--warning-soft)",
            border: "1px solid var(--warning)",
            color: "var(--warning)",
          }}
        >
          <AlertTriangle size={16} />
          Seating is locked because this exam is completed.
        </div>
      )}

      <div className="students-filters" style={{ padding: "12px 16px" }}>
        <div className="filter-row">
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <strong style={{ whiteSpace: "nowrap" }}>Section:</strong>
            <select
              value={selectedSection}
              onChange={(event) => setSelectedSection(event.target.value)}
              disabled={loadingSections}
            >
              {sections.map((section) => (
                <option key={section.id} value={section.id}>
                  {section.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <StateArea loading={loadingRoster} error={error} onRetry={() => {}}>
        {students.length === 0 ? (
          <EmptyState
            icon={Armchair}
            title="No students in this section"
            message="Choose another section or enroll students first."
          />
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>STUDENT</th>
                  <th>ADMISSION NO.</th>
                  <th style={{ width: 110 }}>SEAT NO.</th>
                  <th>ROOM</th>
                  {!isLocked && <th style={{ width: 140 }}>NOTES</th>}
                </tr>
              </thead>

              <tbody>
                {assignments.map((row) => {
                  const student = students.find(
                    (item) => item.id === row.student_id
                  );

                  return (
                    <tr key={row.student_id}>
                      <td>
                        <strong>{student?.full_name || "—"}</strong>
                      </td>

                      <td>{student?.admission_number || "—"}</td>

                      <td>
                        {isLocked ? (
                          row.seat_number || "—"
                        ) : (
                          <input
                            type="number"
                            min="1"
                            placeholder="Seat"
                            value={row.seat_number}
                            onChange={(event) =>
                              setRow(
                                row.student_id,
                                "seat_number",
                                event.target.value
                              )
                            }
                          />
                        )}
                      </td>

                      <td>
                        {isLocked ? (
                          row.room || "—"
                        ) : (
                          <input
                            type="text"
                            placeholder="Room"
                            value={row.room}
                            onChange={(event) =>
                              setRow(row.student_id, "room", event.target.value)
                            }
                          />
                        )}
                      </td>

                      {!isLocked && (
                        <td>
                          <input
                            type="text"
                            placeholder="Notes"
                            value={row.notes}
                            onChange={(event) =>
                              setRow(row.student_id, "notes", event.target.value)
                            }
                          />
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </StateArea>

      {saveMessage && (
        <div className="alert alert-success">{saveMessage}</div>
      )}

      {saveError && <div className="alert alert-error">{saveError}</div>}
    </div>
  );
}