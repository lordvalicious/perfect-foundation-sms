import { useEffect, useState } from "react";
import {
  BadgeCheck,
  BookOpen,
  Briefcase,
  Building2,
  CalendarDays,
  CheckCircle2,
  GraduationCap,
  Layers,
  Mail,
  MapPin,
  Phone,
  School,
  User,
  Users,
  X,
} from "lucide-react";

import { StatusBadge } from "./ui";
import { formatDate } from "./format";

const ROLE_LABELS = {
  super_admin: "Super Admin",
  admin: "Admin",
  principal: "Principal",
  academic: "Academic Administrator",
  accountant: "Accountant",
  teacher: "Teacher",
  student: "Student",
  staff: "Staff Member",
};

function roleLabel(role) {
  if (!role) {
    return null;
  }

  return (
    ROLE_LABELS[role] ||
    role
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
  );
}

function initials(name) {
  return (name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}

function DetailRow({ icon: Icon, label, value }) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  return (
    <div className="profile-row">
      <div className="profile-row-label">
        <Icon size={16} />
        <span>{label}</span>
      </div>

      <div className="profile-row-value">{value}</div>
    </div>
  );
}

function ProfileHero({ photoUrl, name, badges }) {
  return (
    <div className="profile-hero">
      <div className="profile-avatar">
        {photoUrl ? (
          <img src={photoUrl} alt={name} />
        ) : (
          <span>{initials(name)}</span>
        )}
      </div>

      <div className="profile-hero-info">
        <h3>{name}</h3>

        {badges.length > 0 && (
          <div className="profile-badges">
            {badges.map((badge) => (
              <span key={badge} className="profile-badge">
                {badge}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ProfileModal({ type, id, onClose }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState(null);
  const [account, setAccount] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError("");

      try {
        if (type === "teacher") {
          const res = await fetch(`/api/teachers/${id}/`, {
            credentials: "include",
          });

          if (!res.ok) {
            throw new Error("Could not load teacher profile.");
          }

          const data = await res.json();

          if (!cancelled) {
            setProfile({ ...data, kind: "teacher" });
          }
        } else if (type === "student") {
          const res = await fetch(`/api/students/${id}/`, {
            credentials: "include",
          });

          if (!res.ok) {
            throw new Error("Could not load student profile.");
          }

          const data = await res.json();

          if (!cancelled) {
            setProfile({ ...data, kind: "student" });
          }
        } else {
          const res = await fetch(`/api/auth/users/${id}/`, {
            credentials: "include",
          });

          if (!res.ok) {
            throw new Error("Could not load profile.");
          }

          const data = await res.json();

          if (!cancelled) {
            setAccount(data);
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [type, id]);

  const profileName =
    profile?.full_name || profile?.first_name || account?.full_name || "";

  const name = profile ? profileName : profileName || account?.username;

  const roleBadges = [];
  if (profile?.kind === "teacher") {
    roleBadges.push("Teacher");

    if (profile.employee_number) {
      roleBadges.push(profile.employee_number);
    }
  } else if (profile?.kind === "student") {
    roleBadges.push("Student");

    if (profile.admission_number) {
      roleBadges.push(profile.admission_number);
    }
  } else if (account?.primary_role) {
    roleBadges.push(roleLabel(account.primary_role));

    if (account.staff_profile?.employee_number) {
      roleBadges.push(account.staff_profile.employee_number);
    }
  }

  return (
    <div
      className="modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="modal profile-modal">
        <div className="modal-header">
          <div>
            <h3>Profile</h3>

            <p>
              {profile?.kind === "teacher"
                ? "Teacher profile"
                : profile?.kind === "student"
                ? "Student profile"
                : "Staff / User profile"}
            </p>
          </div>

          <button
            className="modal-close"
            onClick={onClose}
            aria-label="Close profile"
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="state-card">Loading profile...</div>
          )}

          {!loading && error && (
            <div className="state-card error">
              <strong>Unable to load profile.</strong>
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && (
            <>
              <ProfileHero
                photoUrl={profile?.photo_url || account?.photo_url}
                name={name}
                badges={roleBadges}
              />

              <div className="profile-sections">
                <div className="panel profile-section">
                  <h4>
                    <User size={16} />
                    Personal Details
                  </h4>

                  <DetailRow
                    icon={Mail}
                    label="Email"
                    value={profile?.email || account?.email}
                  />

                  <DetailRow
                    icon={Phone}
                    label="Phone"
                    value={profile?.phone || account?.phone}
                  />

                  <DetailRow
                    icon={CalendarDays}
                    label="Date of Birth"
                    value={formatDate(profile?.date_of_birth)}
                  />

                  <DetailRow
                    icon={Users}
                    label="Gender"
                    value={
                      profile?.gender
                        ? profile.gender.charAt(0).toUpperCase() +
                          profile.gender.slice(1)
                        : undefined
                    }
                  />

                  <DetailRow
                    icon={MapPin}
                    label="Address"
                    value={profile?.address}
                  />
                </div>

                <div className="panel profile-section">
                  <h4>
                    <Briefcase size={16} />
                    Role &amp; Organization
                  </h4>

                  {profile?.kind === "teacher" && (
                    <>
                      <DetailRow
                        icon={Building2}
                        label="Campus"
                        value={profile.campus_name}
                      />

                      <DetailRow
                        icon={BadgeCheck}
                        label="Designation"
                        value={profile.designation}
                      />

                      <DetailRow
                        icon={CalendarDays}
                        label="Joined"
                        value={formatDate(profile.joining_date)}
                      />

                      <DetailRow
                        icon={CheckCircle2}
                        label="Status"
                        value={<StatusBadge status={profile.status} />}
                      />
                    </>
                  )}

                  {profile?.kind === "student" && (
                    <>
                      <DetailRow
                        icon={School}
                        label="Campus"
                        value={profile.current_enrollment?.campus_name}
                      />

                      <DetailRow
                        icon={BookOpen}
                        label="Class"
                        value={profile.current_enrollment?.class_name}
                      />

                      <DetailRow
                        icon={Layers}
                        label="Section"
                        value={profile.current_enrollment?.section_name}
                      />

                      <DetailRow
                        icon={CalendarDays}
                        label="Academic Year"
                        value={profile.current_enrollment?.academic_year_name}
                      />

                      <DetailRow
                        icon={CalendarDays}
                        label="Admitted"
                        value={formatDate(profile.admission_date)}
                      />

                      <DetailRow
                        icon={CheckCircle2}
                        label="Status"
                        value={<StatusBadge status={profile.status} />}
                      />
                    </>
                  )}

                  {!profile && account && (
                    <>
                      <DetailRow
                        icon={Building2}
                        label="Institution"
                        value={account.primary_institution}
                      />

                      <DetailRow
                        icon={BadgeCheck}
                        label="Role"
                        value={roleLabel(account.primary_role)}
                      />

                      {account.staff_profile && (
                        <>
                          <DetailRow
                            icon={BadgeCheck}
                            label="Designation"
                            value={account.staff_profile.designation}
                          />

                          <DetailRow
                            icon={Building2}
                            label="Department"
                            value={account.staff_profile.department}
                          />

                          <DetailRow
                            icon={CalendarDays}
                            label="Joined"
                            value={formatDate(
                              account.staff_profile.joining_date
                            )}
                          />

                          <DetailRow
                            icon={CheckCircle2}
                            label="Status"
                            value={
                              <StatusBadge
                                status={account.staff_profile.status}
                              />
                            }
                          />
                        </>
                      )}
                    </>
                  )}
                </div>
              </div>

              {profile?.kind === "teacher" && (
                <div className="panel profile-section">
                  <h4>
                    <GraduationCap size={16} />
                    Class Teacher
                  </h4>

                  {profile.class_teacher_classes.length === 0 ? (
                    <p className="profile-empty">
                      Not assigned as a class teacher.
                    </p>
                  ) : (
                    <div className="profile-list">
                      {profile.class_teacher_classes.map((item) => (
                        <div key={item.id} className="profile-list-item">
                          <span className="profile-list-title">
                            {item.class_name} — {item.section_name}
                          </span>

                          <span className="profile-list-meta">
                            {item.campus_name} · {item.academic_year_name} ·{" "}
                            {item.student_count} students
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {profile?.kind === "student" && (
                <>
                  <div className="panel profile-section">
                    <h4>
                      <Users size={16} />
                      Guardian
                    </h4>

                    {!profile.guardian_details ? (
                      <p className="profile-empty">
                        No guardian on record.
                      </p>
                    ) : (
                      <>
                        <DetailRow
                          icon={User}
                          label="Name"
                          value={profile.guardian_details.name}
                        />

                        <DetailRow
                          icon={Users}
                          label="Relationship"
                          value={profile.guardian_details.relationship}
                        />

                        <DetailRow
                          icon={Phone}
                          label="Phone"
                          value={profile.guardian_details.phone}
                        />

                        <DetailRow
                          icon={Phone}
                          label="Alternate Phone"
                          value={profile.guardian_details.alternate_phone}
                        />

                        <DetailRow
                          icon={Mail}
                          label="Email"
                          value={profile.guardian_details.email}
                        />
                      </>
                    )}
                  </div>

                  <div className="panel profile-section">
                    <h4>
                      <BookOpen size={16} />
                      Enrollment History
                    </h4>

                    {profile.enrollments.length === 0 ? (
                      <p className="profile-empty">
                        No enrollments on record.
                      </p>
                    ) : (
                      <div className="profile-list">
                        {profile.enrollments.map((item) => (
                          <div
                            key={item.id}
                            className="profile-list-item"
                          >
                            <span className="profile-list-title">
                              {item.class_name} — {item.section_name}
                            </span>

                            <span className="profile-list-meta">
                              {item.campus_name} · {item.academic_year_name}
                            </span>

                            <StatusBadge status={item.status} />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}

              {!profile && account && (
                <div className="panel profile-section">
                  <h4>
                    <Building2 size={16} />
                    Memberships
                  </h4>

                  {account.memberships.length === 0 ? (
                    <p className="profile-empty">
                      Not a member of any institution yet.
                    </p>
                  ) : (
                    <div className="profile-list">
                      {account.memberships.map((membership) => (
                        <div
                          key={membership.id}
                          className="profile-list-item"
                        >
                          <span className="profile-list-title">
                            {membership.institution_name}
                          </span>

                          <span className="profile-list-meta">
                            Joined {formatDate(membership.joined_at)}
                          </span>

                          <StatusBadge status={membership.status} />

                          <div className="profile-list-roles">
                            {membership.roles.map((role) => (
                              <span
                                key={role.role}
                                className="role-chip"
                              >
                                {role.role_label}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
