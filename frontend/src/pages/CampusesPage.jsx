import { Building2, BookOpen, Users, LayoutGrid } from "lucide-react";
import { useApiList } from "./useApiList";
import {
  PageHeader,
  PanelHeader,
  StateArea,
  EmptyState,
  StatusBadge,
} from "./ui";

const API_URL = "/api/schools/campuses/";

export default function CampusesPage() {
  const { rows, count, loading, error, refresh } =
    useApiList(API_URL);

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Campuses"
        title="Campuses"
        subtitle="View all campuses and their statistics."
      />

      <div className="panel">
        <PanelHeader
          title="Campus List"
          subtitle="campuses found"
          count={count}
        />

        <StateArea
          loading={loading}
          error={error}
          onRetry={() => refresh(new URLSearchParams())}
        >
          {rows.length === 0 ? (
            <EmptyState
              icon={Building2}
              title="No campuses found"
              message="No campuses have been created yet."
            />
          ) : (
            <div className="campuses-grid">
              {rows.map((campus) => (
                <div className="campus-card" key={campus.id}>
                  <div className="campus-card-head">
                    <div className="campus-card-icon">
                      <Building2 size={22} />
                    </div>

                    <div>
                      <strong>{campus.name}</strong>

                      <span>
                        {[campus.city, campus.address]
                          .filter(Boolean)
                          .join(", ") || "—"}
                      </span>
                    </div>

                    <StatusBadge status={campus.status} />
                  </div>

                  <div className="campus-stats">
                    <div>
                      <Users size={17} />
                      <strong>
                        {campus.student_count ?? 0}
                      </strong>
                      <span>Students</span>
                    </div>

                    <div>
                      <BookOpen size={17} />
                      <strong>
                        {campus.class_count ?? 0}
                      </strong>
                      <span>Classes</span>
                    </div>

                    <div>
                      <LayoutGrid size={17} />
                      <strong>
                        {campus.section_count ?? 0}
                      </strong>
                      <span>Sections</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </StateArea>
      </div>
    </section>
  );
}
