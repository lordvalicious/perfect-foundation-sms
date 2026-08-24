import {
  School as SchoolIcon,
  Building2,
  LayoutGrid,
  Layers,
  BookOpen,
  CalendarRange,
  Boxes,
  Users,
} from "lucide-react";
import { useApiList } from "./useApiList";
import {
  PageHeader,
  PanelHeader,
  StateArea,
  EmptyState,
  StatusBadge,
} from "./ui";
import { formatDate } from "./format";

const SCHOOLS_API_URL = "/api/schools/schools/";
const CAMPUSES_API_URL = "/api/schools/campuses/";
const UNITS_API_URL = "/api/schools/units/";
const CLASSES_API_URL = "/api/schools/classes/";
const SECTIONS_API_URL = "/api/schools/sections/";
const YEARS_API_URL = "/api/schools/academic-years/";
const TERMS_API_URL = "/api/schools/terms/";
const SUBJECTS_API_URL = "/api/schools/subjects/";
const OFFERINGS_API_URL = "/api/schools/offerings/";

import TwoFASection from "./TwoFASection";

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">
        <Icon size={20} />
      </div>

      <div className="stat-info">
        <span>{label}</span>

        <strong>{value}</strong>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const schools = useApiList(SCHOOLS_API_URL);
  const campuses = useApiList(CAMPUSES_API_URL);
  const units = useApiList(UNITS_API_URL);
  const classes = useApiList(CLASSES_API_URL);
  const sections = useApiList(SECTIONS_API_URL);
  const years = useApiList(YEARS_API_URL);
  const terms = useApiList(TERMS_API_URL);
  const subjects = useApiList(SUBJECTS_API_URL);
  const offerings = useApiList(OFFERINGS_API_URL);

  const school = schools.rows[0];
  const activeYear = years.rows.find(
    (year) => year.status === "active"
  );

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Settings"
        title="Settings"
        subtitle="System configuration and academic structure."
      />

      <TwoFASection />

      <div className="stats-grid">
        <StatCard
          icon={SchoolIcon}
          label="Schools"
          value={schools.count || 0}
        />

        <StatCard
          icon={Building2}
          label="Campuses"
          value={campuses.count || 0}
        />

        <StatCard
          icon={LayoutGrid}
          label="Classes"
          value={classes.count || 0}
        />

        <StatCard
          icon={Layers}
          label="Sections"
          value={sections.count || 0}
        />

        <StatCard
          icon={BookOpen}
          label="Subjects"
          value={subjects.count || 0}
        />

        <StatCard
          icon={CalendarRange}
          label="Academic Years"
          value={years.count || 0}
        />

        <StatCard
          icon={Boxes}
          label="Units"
          value={units.count || 0}
        />

        <StatCard
          icon={Users}
          label="Offerings"
          value={offerings.count || 0}
        />
      </div>

      <div className="panel">
        <PanelHeader
          title="School Profile"
          subtitle="schools configured"
          count={schools.count}
        />

        <StateArea loading={schools.loading} error={schools.error}>
          {!school ? (
            <EmptyState
              icon={SchoolIcon}
              title="No school configured"
              message="No school record has been created yet."
            />
          ) : (
            <div className="overview-list">
              <div>
                <span>School Name</span>

                <strong>{school.name || "—"}</strong>
              </div>

              <div>
                <span>City</span>

                <strong>{school.city || "—"}</strong>
              </div>

              <div>
                <span>Address</span>

                <strong>{school.address || "—"}</strong>
              </div>

              <div>
                <span>Campuses</span>

                <strong>{school.campus_count ?? 0}</strong>
              </div>

              <div>
                <span>Status</span>

                <StatusBadge status={school.status} />
              </div>

              <div>
                <span>Active Academic Year</span>

                <strong>{activeYear ? activeYear.name : "—"}</strong>
              </div>
            </div>
          )}
        </StateArea>
      </div>

      <div className="panel">
        <PanelHeader
          title="Academic Years"
          subtitle="years configured"
          count={years.count}
        />

        <StateArea loading={years.loading} error={years.error}>
          {years.rows.length === 0 ? (
            <EmptyState
              icon={CalendarRange}
              title="No academic years"
              message="No academic years have been created yet."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>YEAR</th>
                    <th>SCHOOL</th>
                    <th>START</th>
                    <th>END</th>
                    <th>STATUS</th>
                  </tr>
                </thead>

                <tbody>
                  {years.rows.map((year) => (
                    <tr key={year.id}>
                      <td>
                        <strong>{year.name || "—"}</strong>
                      </td>

                      <td>{year.school_name || "—"}</td>

                      <td>{formatDate(year.start_date)}</td>

                      <td>{formatDate(year.end_date)}</td>

                      <td>
                        <StatusBadge status={year.status} />
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
          title="Terms"
          subtitle="terms configured"
          count={terms.count}
        />

        <StateArea loading={terms.loading} error={terms.error}>
          {terms.rows.length === 0 ? (
            <EmptyState
              icon={CalendarRange}
              title="No terms"
              message="No terms have been created yet."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>TERM</th>
                    <th>ACADEMIC YEAR</th>
                    <th>START</th>
                    <th>END</th>
                  </tr>
                </thead>

                <tbody>
                  {terms.rows.map((term) => (
                    <tr key={term.id}>
                      <td>
                        <strong>{term.name || "—"}</strong>
                      </td>

                      <td>{term.academic_year_name || "—"}</td>

                      <td>{formatDate(term.start_date)}</td>

                      <td>{formatDate(term.end_date)}</td>
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
          title="Classes"
          subtitle="classes configured"
          count={classes.count}
        />

        <StateArea loading={classes.loading} error={classes.error}>
          {classes.rows.length === 0 ? (
            <EmptyState
              icon={LayoutGrid}
              title="No classes"
              message="No classes have been created yet."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>CLASS</th>
                    <th>CAMPUS</th>
                    <th>UNIT</th>
                    <th>SECTIONS</th>
                    <th>STATUS</th>
                  </tr>
                </thead>

                <tbody>
                  {classes.rows.map((classObj) => (
                    <tr key={classObj.id}>
                      <td>
                        <strong>{classObj.name || "—"}</strong>

                        {classObj.level !== null &&
                          classObj.level !== undefined && (
                            <span className="cell-sub">
                              Level {classObj.level}
                            </span>
                          )}
                      </td>

                      <td>{classObj.campus_name || "—"}</td>

                      <td>{classObj.unit_name || "—"}</td>

                      <td>{classObj.section_count ?? 0}</td>

                      <td>
                        <StatusBadge status={classObj.status} />
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
          title="Sections"
          subtitle="sections configured"
          count={sections.count}
        />

        <StateArea loading={sections.loading} error={sections.error}>
          {sections.rows.length === 0 ? (
            <EmptyState
              icon={Layers}
              title="No sections"
              message="No sections have been created yet."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>SECTION</th>
                    <th>CLASS</th>
                    <th>CAMPUS</th>
                    <th>CAPACITY</th>
                    <th>STATUS</th>
                  </tr>
                </thead>

                <tbody>
                  {sections.rows.map((section) => (
                    <tr key={section.id}>
                      <td>
                        <strong>{section.name || "—"}</strong>
                      </td>

                      <td>{section.class_name || "—"}</td>

                      <td>{section.campus_name || "—"}</td>

                      <td>{section.capacity ?? "—"}</td>

                      <td>
                        <StatusBadge status={section.status} />
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
          title="Subjects"
          subtitle="subjects configured"
          count={subjects.count}
        />

        <StateArea loading={subjects.loading} error={subjects.error}>
          {subjects.rows.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="No subjects"
              message="No subjects have been created yet."
            />
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>CODE</th>
                    <th>SUBJECT</th>
                    <th>TYPE</th>
                    <th>PRACTICAL</th>
                    <th>STATUS</th>
                  </tr>
                </thead>

                <tbody>
                  {subjects.rows.map((subject) => (
                    <tr key={subject.id}>
                      <td>
                        <strong>{subject.code || "—"}</strong>
                      </td>

                      <td>{subject.name || "—"}</td>

                      <td>{subject.subject_type || "—"}</td>

                      <td>{subject.practical_required ? "Yes" : "No"}</td>

                      <td>
                        <StatusBadge status={subject.status} />
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
