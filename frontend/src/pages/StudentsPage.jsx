import { useState, useRef, useEffect } from "react";
import { Search, Building2 } from "lucide-react";
import { useAuth } from "../auth";
import { useLang } from "../i18n";
import ProfileModal from "./ProfileModal";

const STUDENTS_API_URL = "/api/students/";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }

  return null;
}

function authHeaders(extra = {}) {
  const csrfToken = getCookie("csrftoken");

  return {
    ...extra,
    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
  };
}

function StudentsPage() {
  const { t } = useLang();
  const { hasRole } = useAuth();
  const campusSectionRefs = useRef({});

  const isStudentSelf =
    hasRole(["student"]) &&
    !hasRole([
      "super_admin",
      "admin",
      "principal",
      "academic",
      "accountant",
      "teacher",
      "staff",
    ]);

  const canManage = hasRole([
    "super_admin",
    "admin",
    "principal",
    "academic",
  ]);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [gender, setGender] = useState("");
  const [status, setStatus] = useState("");

  const [section, setSection] = useState("");
  const [campusOptions, setCampusOptions] = useState([]);
  const [sectionOptions, setSectionOptions] = useState([]);

  const [campusData, setCampusData] = useState({});

  const [showForm, setShowForm] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [saving, setSaving] = useState(false);

  const [profileView, setProfileView] = useState(null);

  const emptyForm = {
    admission_number: "",
    first_name: "",
    middle_name: "",
    last_name: "",
    gender: "",
    date_of_birth: "",
    phone: "",
    address: "",
    status: "active",
    admission_date: "",
    guardian_name: "",
    guardian_relationship: "",
    guardian_phone: "",
    guardian_alternate_phone: "",
    guardian_email: "",
    guardian_address: "",
  };

  const [form, setForm] = useState(emptyForm);
  const [photoFile, setPhotoFile] = useState(null);

  const [myProfile, setMyProfile] = useState(null);
  const [myProfileLoading, setMyProfileLoading] = useState(
    isStudentSelf
  );

  const buildStudentParams = (campusId, pageNumber) => {
    const params = new URLSearchParams();

    params.append("campus", campusId);
    params.append("page", pageNumber);

    if (search.trim()) {
      params.append("search", search.trim());
    }

    if (gender) {
      params.append("gender", gender);
    }

    if (status) {
      params.append("status", status);
    }

    if (section) {
      params.append("section", section);
    }

    return params;
  };

  const fetchCampusStudents = (campusId, pageNumber = 1) => {
    const params = buildStudentParams(campusId, pageNumber);

    setCampusData((prev) => ({
      ...prev,
      [campusId]: { ...(prev[campusId] || {}), loading: true },
    }));

    return fetch(`${STUDENTS_API_URL}?${params.toString()}`, {
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load students.");
        }

        return response.json();
      })
      .then((data) => {
        setCampusData((prev) => ({
          ...prev,
          [campusId]: {
            students: data.results || [],
            count: data.count || 0,
            page: pageNumber,
            next: data.next,
            previous: data.previous,
            loaded: true,
            loading: false,
            error: "",
          },
        }));
      })
      .catch((err) => {
        setCampusData((prev) => ({
          ...prev,
          [campusId]: {
            ...(prev[campusId] || {}),
            loaded: true,
            loading: false,
            error: err.message,
          },
        }));
      });
  };

  const fetchAllCampuses = (pageNumber = 1) => {
    campusOptions.forEach((campus) => {
      fetchCampusStudents(campus.id, pageNumber);
    });
  };

  useEffect(() => {
    if (isStudentSelf) {
      fetch("/api/students/me/", { credentials: "include" })
        .then((response) => {
          if (!response.ok) {
            throw new Error("No student profile linked.");
          }

          return response.json();
        })
        .then((data) => {
          setMyProfile(data);
          setError("");
        })
        .catch((err) => {
          setError(err.message);
        })
        .finally(() => {
          setMyProfileLoading(false);
        });

      return;
    }

    const loadCampusStudents = (campus, pageNumber) => {
      const params = new URLSearchParams();

      params.append("campus", campus.id);
      params.append("page", pageNumber);

      fetch(`${STUDENTS_API_URL}?${params.toString()}`, {
        credentials: "include",
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to load students.");
          }

          return response.json();
        })
        .then((data) => {
          setCampusData((prev) => ({
            ...prev,
            [campus.id]: {
              students: data.results || [],
              count: data.count || 0,
              page: pageNumber,
              next: data.next,
              previous: data.previous,
              loaded: true,
              loading: false,
              error: "",
            },
          }));
        })
        .catch((err) => {
          setCampusData((prev) => ({
            ...prev,
            [campus.id]: {
              ...(prev[campus.id] || {}),
              loaded: true,
              loading: false,
              error: err.message,
            },
          }));
        });
    };

    fetch("/api/schools/campuses/", {
      credentials: "include",
    })
      .then((response) =>
        response.ok ? response.json() : []
      )
      .then((data) => {
        const campuses = Array.isArray(data) ? data : [];

        setCampusOptions(campuses);

        campuses.forEach((campus) => {
          loadCampusStudents(campus, 1);
        });
      })
      .catch(() => {});

    fetch("/api/schools/sections/", {
      credentials: "include",
    })
      .then((response) =>
        response.ok ? response.json() : []
      )
      .then((data) =>
        setSectionOptions(
          Array.isArray(data) ? data : []
        )
      )
      .catch(() => {});
  }, [isStudentSelf]);

  const viewCampusStudents = (campusId) => {
    campusSectionRefs.current[campusId]?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const handleSectionChange = (value) => {
    setSection(value);

    setTimeout(() => {
      fetchAllCampuses(1);
    }, 0);
  };

  const handleSearch = (event) => {
    event.preventDefault();
    fetchAllCampuses(1);
  };

  const clearFilters = () => {
    setSearch("");
    setGender("");
    setStatus("");
    setSection("");

    setTimeout(() => {
      fetchAllCampuses(1);
    }, 0);
  };

  /* --------------------------
     FORM HANDLING
  -------------------------- */

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handlePhoto = (event) => {
    setPhotoFile(event.target.files[0] || null);
  };

  const openAddStudent = () => {
    setEditingStudent(null);
    setPhotoFile(null);
    setForm(emptyForm);
    setShowForm(true);
  };

  const openEditStudent = (student) => {
    setEditingStudent(student);
    setPhotoFile(null);

    setForm({
      admission_number: student.admission_number || "",
      first_name: student.first_name || "",
      middle_name: student.middle_name || "",
      last_name: student.last_name || "",
      gender: student.gender || "",
      date_of_birth: student.date_of_birth || "",
      phone: student.phone || "",
      address: student.address || "",
      status: student.status || "active",
      admission_date: student.admission_date || "",
      guardian_name:
        student.guardian_details?.name || "",
      guardian_relationship:
        student.guardian_details?.relationship || "",
      guardian_phone:
        student.guardian_details?.phone || "",
      guardian_alternate_phone:
        student.guardian_details?.alternate_phone || "",
      guardian_email:
        student.guardian_details?.email || "",
      guardian_address:
        student.guardian_details?.address || "",
    });

    setShowForm(true);
  };

  const closeForm = () => {
    if (saving) return;

    setShowForm(false);
    setEditingStudent(null);
    setPhotoFile(null);
    setForm(emptyForm);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSaving(true);
    setError("");

    try {
      const isEditing = Boolean(editingStudent);

      const url = isEditing
        ? `${STUDENTS_API_URL}${editingStudent.id}/`
        : STUDENTS_API_URL;

      const body = new FormData();

      for (const [key, value] of Object.entries(form)) {
        body.append(key, value === "" ? "" : value);
      }

      if (photoFile) {
        body.append("photo", photoFile);
      }

      const response = await fetch(url, {
        method: isEditing ? "PUT" : "POST",
        credentials: "include",
        headers: authHeaders(),
        body,
      });

      const responseText = await response.text();

      let data = {};

      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch {
        data = {};
      }

      if (!response.ok) {
        let message = "Unable to save student.";

        if (data && typeof data === "object") {
          message = Object.entries(data)
            .map(([field, value]) => {
              const text = Array.isArray(value)
                ? value.join(", ")
                : String(value);

              return `${field}: ${text}`;
            })
            .join(" | ");
        }

        if (
          !message ||
          message === "Unable to save student."
        ) {
          message =
            responseText ||
            `Request failed (${response.status})`;
        }

        throw new Error(message);
      }

      closeForm();
      await fetchAllCampuses(1);

      if (isStudentSelf) {
        fetch("/api/students/me/", {
          credentials: "include",
        })
          .then((response) => response.json())
          .then((profile) => setMyProfile(profile))
          .catch(() => {});
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (student) => {
    const confirmed = window.confirm(
      `Delete student "${student.full_name || student.admission_number}"? ` +
        "This cannot be undone."
    );

    if (!confirmed) return;

    setSaving(true);
    setError("");

    try {
      const response = await fetch(
        `${STUDENTS_API_URL}${student.id}/`,
        {
          method: "DELETE",
          credentials: "include",
          headers: authHeaders(),
        }
      );

      if (!response.ok) {
        throw new Error("Unable to delete student.");
      }

      const campusId = student.current_enrollment?.campus_id;

      if (campusId) {
        const entry = campusData[campusId] || {};
        await fetchCampusStudents(campusId, entry.page || 1);
      } else {
        await fetchAllCampuses(1);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  /* --------------------------
     STUDENT SELF PROFILE
  -------------------------- */

  if (isStudentSelf) {
    return (
      <section className="content">
        <div className="page-header">
          <div>
            <div className="breadcrumb">Home / My Profile</div>
            <h2>My Profile</h2>

            <p className="subtitle">
              Your student information at Perfect Foundation
              School.
            </p>
          </div>
        </div>

        {myProfileLoading && (
          <div className="state-card">
            Loading your profile...
          </div>
        )}

        {!myProfileLoading && error && (
          <div className="state-card error">
            <strong>Unable to load your profile.</strong>
            <span>{error}</span>
          </div>
        )}

        {!myProfileLoading && !error && myProfile && (
          <div className="profile-grid">
            <div className="panel profile-card">
              {myProfile.photo_url ? (
                <img
                  className="profile-photo"
                  src={myProfile.photo_url}
                  alt={myProfile.full_name}
                />
              ) : (
                <div className="profile-photo placeholder">
                  {(myProfile.full_name || "S")
                    .charAt(0)
                    .toUpperCase()}
                </div>
              )}

              <h3>{myProfile.full_name}</h3>
              <span className="status-badge active">
                {myProfile.status}
              </span>

              <p className="muted">
                {myProfile.admission_number}
              </p>

              <div className="profile-detail">
                <strong>Date of Birth</strong>
                <span>{myProfile.date_of_birth || "—"}</span>
              </div>

              <div className="profile-detail">
                <strong>Gender</strong>
                <span>
                  {myProfile.gender
                    ? myProfile.gender.charAt(0).toUpperCase() +
                      myProfile.gender.slice(1)
                    : "—"}
                </span>
              </div>

              <div className="profile-detail">
                <strong>Phone</strong>
                <span>{myProfile.phone || "—"}</span>
              </div>

              <div className="profile-detail">
                <strong>Address</strong>
                <span>{myProfile.address || "—"}</span>
              </div>
            </div>

            <div className="profile-grid-main">
              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h3>Guardian</h3>
                    <p>Contact information of your guardian</p>
                  </div>
                </div>

                <div className="overview-list">
                  <div>
                    <span>Name</span>
                    <strong>
                      {myProfile.guardian_details?.name || "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Relationship</span>
                    <strong>
                      {myProfile.guardian_details?.relationship ||
                        "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Phone</span>
                    <strong>
                      {myProfile.guardian_details?.phone || "—"}
                    </strong>
                  </div>
                  <div>
                    <span>Email</span>
                    <strong>
                      {myProfile.guardian_details?.email || "—"}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <div>
                    <h3>Enrollments</h3>
                    <p>Classes you are enrolled in</p>
                  </div>
                </div>

                {(myProfile.enrollments || []).length === 0 ? (
                  <div className="state-card">
                    No enrollments found.
                  </div>
                ) : (
                  <div className="table-wrapper">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>ACADEMIC YEAR</th>
                          <th>CLASS</th>
                          <th>SECTION</th>
                          <th>STATUS</th>
                        </tr>
                      </thead>

                      <tbody>
                        {myProfile.enrollments.map(
                          (enrollment) => (
                            <tr key={enrollment.id}>
                              <td>
                                {enrollment.academic_year_name}
                              </td>
                              <td>
                                <strong>
                                  {enrollment.class_name}
                                </strong>
                              </td>
                              <td>{enrollment.section_name}</td>
                              <td>
                                <span
                                  className={`status-badge ${
                                    enrollment.status === "active"
                                      ? "active"
                                      : "inactive"
                                  }`}
                                >
                                  {enrollment.status}
                                </span>
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </section>
    );
  }

  /* --------------------------
     ADMIN / TEACHER LIST VIEW
  -------------------------- */

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <div className="breadcrumb">{t("Home / Students")}</div>

          <h2>{t("Students")}</h2>

          <p className="subtitle">
            {t("Manage students enrolled at Perfect Foundation School.")}
          </p>
        </div>

        {canManage && (
          <button
            className="primary-button"
            onClick={openAddStudent}
          >
            {t("+ Add Student")}
          </button>
        )}
      </div>

      {/* Campus overview */}
      {campusOptions.length > 0 && (
        <div className="campus-cards">
          {campusOptions.map((item) => (
            <div key={item.id} className="campus-card">
              <div className="campus-card-header">
                <Building2 size={20} />
                <strong>{item.name}</strong>
              </div>

              <p className="campus-card-sub">
                {[item.city, item.address]
                  .filter(Boolean)
                  .join(", ") || "Perfect Foundation School"}
              </p>

              <div className="campus-card-stats">
                <div>
                  <span>{item.student_count || 0}</span>
                  <small>Students</small>
                </div>

                <div>
                  <span>{item.class_count || 0}</span>
                  <small>Classes</small>
                </div>

                <div>
                  <span>{item.section_count || 0}</span>
                  <small>Sections</small>
                </div>
              </div>

              <button
                className="primary-button campus-card-button"
                onClick={() => viewCampusStudents(item.id)}
              >
                View All Students
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="panel students-filters">
        <form onSubmit={handleSearch}>
          <div className="filter-row">
            <div className="filter-search">
              <Search size={18} />

              <input
                type="text"
                placeholder={t("Search by name, admission number or phone...")}
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />
            </div>

            <select
              value={gender}
              onChange={(event) => {
                setGender(event.target.value);
                setTimeout(() => {
                  fetchAllCampuses(1);
                }, 0);
              }}
            >
              <option value="">All genders</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>

            <select
              value={section}
              onChange={(event) =>
                handleSectionChange(event.target.value)
              }
            >
              <option value="">All sections</option>

              {sectionOptions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.class_name} - {item.name}
                </option>
              ))}
            </select>

            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setTimeout(() => {
                  fetchAllCampuses(1);
                }, 0);
              }}
            >
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>

            <button type="submit" className="primary-button">
              Search
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={clearFilters}
            >
              Clear
            </button>
          </div>
        </form>
      </div>

      {/* Student lists by campus */}
      {campusOptions.length === 0 ? (
        <div className="state-card">
          No campuses found.
        </div>
      ) : (
        <div className="campus-student-lists">
          {campusOptions.map((campus) => {
            const data =
              campusData[campus.id] || {
                students: [],
                count: 0,
                page: 1,
                next: null,
                previous: null,
                loading: true,
                error: "",
              };

            const campusTotalPages = Math.max(
              1,
              Math.ceil(data.count / 20)
            );

            return (
              <div
                key={campus.id}
                className="panel campus-student-list"
                ref={(el) => {
                  campusSectionRefs.current[campus.id] = el;
                }}
              >
                <div className="panel-header">
                  <div>
                    <h3>{campus.name}</h3>

                    <p>
                      {data.count.toLocaleString()} students
                      found
                    </p>
                  </div>
                </div>

                {data.loading && (
                  <div className="state-card">
                    Loading students...
                  </div>
                )}

                {!data.loading && data.error && (
                  <div className="state-card error">
                    <strong>
                      Unable to load students.
                    </strong>

                    <span>
                      Make sure Django is running at
                      127.0.0.1:8000.
                    </span>

                    <code>{data.error}</code>
                  </div>
                )}

                {!data.loading && !data.error && (
                  <>
                    {data.students.length === 0 ? (
                      <div className="state-card">
                        No students found.
                      </div>
                    ) : (
                      <div className="students-table-wrapper">
                        <table className="data-table">
                          <thead>
                            <tr>
                  <th>{t("Student")}</th>
                  <th>{t("Admission No.")}</th>
                  <th>{t("Class")}</th>
                  <th>{t("Section")}</th>
                  <th>{t("Date of Birth")}</th>
                  <th>{t("Gender")}</th>
                  <th>{t("Guardian")}</th>
                  <th>{t("Phone")}</th>
                  <th>{t("Status")}</th>
                              <th></th>
                            </tr>
                          </thead>

                          <tbody>
                            {data.students.map((student) => (
                              <tr key={student.id}>
                                <td>
                                  <div className="student-name-cell">
                                    {student.photo_url ? (
                                      <img
                                        className="table-photo"
                                        src={student.photo_url}
                                        alt={student.full_name}
                                      />
                                    ) : (
                                      <div className="table-avatar">
                                        {(
                                          student.full_name ||
                                          "S"
                                        )
                                          .charAt(0)
                                          .toUpperCase()}
                                      </div>
                                    )}

                                    <strong>
                                      {student.full_name ||
                                        `${student.first_name ||
                                          ""} ${
                                          student.middle_name ||
                                          ""
                                        } ${
                                          student.last_name ||
                                          ""
                                        }`.trim()}
                                    </strong>
                                  </div>
                                </td>

                                <td>
                                  <strong>
                                    {student.admission_number}
                                  </strong>
                                </td>

                                <td>
                                  {student.current_enrollment
                                    ?.class_name || "—"}
                                </td>

                                <td>
                                  {student.current_enrollment
                                    ?.section_name || "—"}
                                </td>

                                <td>
                                  {student.date_of_birth ||
                                    "—"}
                                </td>

                                <td>
                                  {student.gender
                                    ? student.gender
                                        .charAt(0)
                                        .toUpperCase() +
                                      student.gender.slice(1)
                                    : "—"}
                                </td>

                                <td>
                                  {student.guardian_details
                                    ?.name || "—"}
                                </td>

                                <td>{student.phone || "—"}</td>

                                <td>
                                  <span
                                    className={`status-badge ${
                                      student.status ===
                                      "active"
                                        ? "active"
                                        : "inactive"
                                    }`}
                                  >
                                    {student.status || "—"}
                                  </span>
                                </td>

                                <td>
                                  <button
                                    className="table-action"
                                    onClick={() =>
                                      setProfileView({
                                        type: "student",
                                        id: student.id,
                                      })
                                    }
                                  >
                                    View Profile
                                  </button>

                                  {canManage && (
                                    <>
                                      <button
                                        className="table-action"
                                        onClick={() =>
                                          openEditStudent(
                                            student
                                          )
                                        }
                                      >
                                        Edit
                                      </button>

                                      <button
                                        className="table-action danger"
                                        onClick={() =>
                                          handleDelete(student)
                                        }
                                      >
                                        Delete
                                      </button>
                                    </>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {data.count > 0 && (
                      <div className="pagination">
                        <button
                          disabled={!data.previous}
                          onClick={() =>
                            fetchCampusStudents(
                              campus.id,
                              data.page - 1
                            )
                          }
                        >
                          Previous
                        </button>

                        <span>
                          Page {data.page} of{" "}
                          {campusTotalPages}
                        </span>

                        <button
                          disabled={!data.next}
                          onClick={() =>
                            fetchCampusStudents(
                              campus.id,
                              data.page + 1
                            )
                          }
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add / Edit Student Modal */}
      {showForm && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeForm();
            }
          }}
        >
          <div className="teacher-modal student-modal">
            <div className="modal-header">
              <div>
                <h3>
                  {editingStudent
                    ? "Edit Student"
                    : "Add Student"}
                </h3>

                <p>
                  {editingStudent
                    ? "Update student information."
                    : "Create a new student profile."}
                </p>
              </div>

              <button
                className="modal-close"
                onClick={closeForm}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-section">
                <h4>Personal Information</h4>

                <div className="form-grid">
                  <label>
                    Admission Number
                    <input
                      name="admission_number"
                      value={form.admission_number}
                      onChange={handleChange}
                      placeholder="PF-ST-0001"
                      required
                    />
                  </label>

                  <label>
                    Gender
                    <select
                      name="gender"
                      value={form.gender}
                      onChange={handleChange}
                      required
                    >
                      <option value="">Select gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </label>

                  <label>
                    First Name
                    <input
                      name="first_name"
                      value={form.first_name}
                      onChange={handleChange}
                      placeholder="First name"
                      required
                    />
                  </label>

                  <label>
                    Middle Name
                    <input
                      name="middle_name"
                      value={form.middle_name}
                      onChange={handleChange}
                      placeholder="Middle name"
                    />
                  </label>

                  <label>
                    Last Name
                    <input
                      name="last_name"
                      value={form.last_name}
                      onChange={handleChange}
                      placeholder="Last name"
                    />
                  </label>

                  <label>
                    Date of Birth
                    <input
                      type="date"
                      name="date_of_birth"
                      value={form.date_of_birth}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Admission Date
                    <input
                      type="date"
                      name="admission_date"
                      value={form.admission_date}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Status
                    <select
                      name="status"
                      value={form.status}
                      onChange={handleChange}
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="graduated">
                        Graduated
                      </option>
                      <option value="withdrawn">
                        Withdrawn
                      </option>
                    </select>
                  </label>

                  <label>
                    Photo
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handlePhoto}
                    />
                  </label>

                  {photoFile && (
                    <div className="photo-preview">
                      <img
                        src={URL.createObjectURL(photoFile)}
                        alt="preview"
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="form-section">
                <h4>Contact Information</h4>

                <div className="form-grid">
                  <label>
                    Phone
                    <input
                      name="phone"
                      value={form.phone}
                      onChange={handleChange}
                      placeholder="03XX-XXXXXXX"
                    />
                  </label>

                  <label>
                    Address
                    <input
                      name="address"
                      value={form.address}
                      onChange={handleChange}
                      placeholder="Home address"
                    />
                  </label>
                </div>
              </div>

              <div className="form-section">
                <h4>Guardian Information</h4>

                <div className="form-grid">
                  <label>
                    Guardian Name
                    <input
                      name="guardian_name"
                      value={form.guardian_name}
                      onChange={handleChange}
                      placeholder="Full name"
                      required={!editingStudent}
                    />
                  </label>

                  <label>
                    Relationship
                    <input
                      name="guardian_relationship"
                      value={form.guardian_relationship}
                      onChange={handleChange}
                      placeholder="e.g. Father, Mother"
                      required={!editingStudent}
                    />
                  </label>

                  <label>
                    Guardian Phone
                    <input
                      name="guardian_phone"
                      value={form.guardian_phone}
                      onChange={handleChange}
                      placeholder="03XX-XXXXXXX"
                      required={!editingStudent}
                    />
                  </label>

                  <label>
                    Alternate Phone
                    <input
                      name="guardian_alternate_phone"
                      value={form.guardian_alternate_phone}
                      onChange={handleChange}
                      placeholder="Alternate phone"
                    />
                  </label>

                  <label>
                    Guardian Email
                    <input
                      type="email"
                      name="guardian_email"
                      value={form.guardian_email}
                      onChange={handleChange}
                      placeholder="guardian@example.com"
                    />
                  </label>

                  <label>
                    Guardian Address
                    <input
                      name="guardian_address"
                      value={form.guardian_address}
                      onChange={handleChange}
                      placeholder="Guardian address"
                    />
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeForm}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : editingStudent
                    ? "Save Changes"
                    : "Add Student"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {profileView && (
        <ProfileModal
          type={profileView.type}
          id={profileView.id}
          onClose={() => setProfileView(null)}
        />
      )}
    </section>
  );
}

export default StudentsPage;
