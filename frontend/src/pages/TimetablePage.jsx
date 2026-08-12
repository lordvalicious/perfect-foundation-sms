import { CalendarDays } from "lucide-react";
import { useApiList } from "./useApiList";
import { useAuth } from "../auth";
import {
  PageHeader,
  PanelHeader,
  StateArea,
  EmptyState,
  StatusBadge,
} from "./ui";

const PERIODS_API_URL = "/api/timetable/periods/";
const ENTRIES_API_URL = "/api/timetable/entries/";

export default function TimetablePage() {
  const periods = useApiList(PERIODS_API_URL);
  const entries = useApiList(ENTRIES_API_URL);
  const { user, hasRole } = useAuth();

  const isTeacher = hasRole(["teacher"]);

  const teacherName = user
    ? `${user.first_name || ""} ${user.last_name || ""}`.trim()
    : "";

  const pageTitle = isTeacher ? "My Timetable" : "Timetable";

  const pageSubtitle = isTeacher
    ? `Welcome, ${teacherName || "Teacher"}. This is your personal class schedule.`
    : "View class timetables and period schedules.";

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Timetable"
        title={pageTitle}
        subtitle={pageSubtitle}
      />

      <div className="panel">
        <PanelHeader
          title="Period Schedule"
          subtitle="periods configured"
          count={periods.count}
        />

        <StateArea loading={periods.loading} error={periods.error}>
          {periods.rows.length === 0 ? (
            <EmptyState
              icon={CalendarDays}
              title="No periods configured"
              message="No teaching periods have been configured yet."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>PERIOD</th>
                    <th>NUMBER</th>
                    <th>START</th>
                    <th>END</th>
                    <th>TYPE</th>
                    <th>STATUS</th>
                  </tr>
                </thead>

                <tbody>
                  {periods.rows.map((period) => (
                    <tr key={period.id}>
                      <td>
                        <strong>{period.name || "—"}</strong>
                      </td>

                      <td>#{period.number}</td>

                      <td>{period.start_time || "—"}</td>

                      <td>{period.end_time || "—"}</td>

                      <td>
                        {period.is_break ? "Break" : "Teaching"}
                      </td>

                      <td>
                        <StatusBadge
                          status={period.status}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </StateArea>
      </div>

      <div className="panel">
        <PanelHeader
          title="Timetable Entries"
          subtitle="entries found"
          count={entries.count}
        />

        <StateArea loading={entries.loading} error={entries.error}>
          {entries.rows.length === 0 ? (
            <EmptyState
              icon={CalendarDays}
              title="No timetable entries"
              message="No class timetable entries have been created yet."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>DAY</th>
                    <th>PERIOD</th>
                    <th>TIME</th>
                    <th>GRADE</th>
                    <th>SUBJECT</th>
                    <th>TEACHER</th>
                    <th>SECTION</th>
                    <th>ROOM</th>
                    <th>STATUS</th>
                  </tr>
                </thead>

                <tbody>
                  {entries.rows.map((entry) => (
                    <tr key={entry.id}>
                      <td>
                        <strong>{entry.day_display || "—"}</strong>
                      </td>

                      <td>
                        {entry.period_name || "—"} (
                        {entry.period_number || "—"})
                      </td>

                      <td>
                        {entry.start_time || "—"} –{" "}
                        {entry.end_time || "—"}
                      </td>

                      <td>
                        <span className="grade-badge">
                          {entry.class_name || "—"}
                        </span>
                      </td>

                      <td>
                        <strong>
                          {entry.subject_name || "—"}
                        </strong>

                        {entry.subject_code && (
                          <span className="cell-sub">
                            {entry.subject_code}
                          </span>
                        )}
                      </td>

                      <td>{entry.teacher_name || "—"}</td>

                      <td>{entry.section_name || "—"}</td>

                      <td>{entry.room || "—"}</td>

                      <td>
                        <StatusBadge
                          status={entry.status}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </StateArea>
      </div>
    </section>
  );
}
