# Perfect Foundation School

# School Management System — Software Requirements Specification

**Project:** Generic School Management System
**Initial Case Study:** Perfect Foundation School
**Version:** 1.0
**Status:** Initial Requirements / Draft

---

# 1. Introduction

## 1.1 Purpose

The purpose of this project is to develop a generic School Management System based initially on the organizational and academic requirements of Perfect Foundation School.

The system will centralize the management of students, staff, campuses, classes, sections, subjects, examinations, marks, results, and other school operations.

Although Perfect Foundation School is the initial case study, the system should not be permanently hard-coded around its current structure. Important academic and administrative settings should be configurable so that the system can later be adapted to other schools.

## 1.2 Project Objectives

The main objectives are:

* Centralize school information.
* Manage multiple campuses/branches.
* Manage students and their academic history.
* Manage teachers and other staff.
* Manage classes and sections.
* Manage subjects.
* Manage examinations and tests.
* Record student marks.
* Calculate and maintain results.
* Support Grade 10 practical examinations.
* Provide role-based access to users.
* Reduce manual record keeping.
* Reduce calculation errors.
* Provide reports and useful school information.
* Keep the system flexible for future expansion.

---

# 2. Organization Structure

Perfect Foundation School consists of five branches/campuses.

The overall organization is controlled by the school owner.

Each campus has its own head/principal and supporting staff.

The organizational hierarchy is:

```text
Perfect Foundation School
│
└── Owner
    │
    ├── Junior Campus
    │   └── Principal/Head
    │
    ├── Girls Campus
    │   └── Principal/Head
    │
    ├── Boys Campus
    │   └── Principal/Head
    │
    ├── Haripur Campus
    │   ├── School 1
    │   └── School 2
    │
    └── Paris Road Campus
        └── Principal/Head
```

The system must support the management of multiple campuses under one school organization.

---

# 3. Campus Structure

## 3.1 Junior Campus

The Junior Campus currently contains:

| Class         | Sections |
| ------------- | -------: |
| Play Group    |        2 |
| Nursery       |        2 |
| Prep          |        2 |
| Grade/Class 1 |        2 |

The number of sections should remain configurable.

## 3.2 Girls Campus

The Girls Campus currently contains:

* Grade 2
* Grade 3
* Grade 4
* Grade 5
* Grade 6
* Grade 7
* Grade 8
* Grade 9
* Grade 10

## 3.3 Boys Campus

The Boys Campus currently contains:

* Grade 2
* Grade 3
* Grade 4
* Grade 5
* Grade 6
* Grade 7
* Grade 8
* Grade 9
* Grade 10

## 3.4 Haripur Campus

The Haripur Campus consists of two schools/academic units.

### Haripur School 1

* Play Group
* Nursery
* Prep
* Grade 1
* Grade 2
* Grade 3
* Grade 4
* Grade 5

### Haripur School 2

* Grade 6
* Grade 7
* Grade 8
* Grade 9
* Grade 10

## 3.5 Paris Road Campus

The Paris Road Campus currently contains:

* Play Group
* Nursery
* Prep
* Grade 1
* Grade 2
* Grade 3
* Grade 4
* Grade 5

---

# 4. Users and Roles

The system shall support different types of users.

## 4.1 Owner

The owner has organization-wide authority.

The owner should be able to:

* View all campuses.
* View school-wide information.
* Manage campuses.
* Manage high-level users and roles.
* View school-wide reports.
* Monitor academic information.
* Monitor financial information when the finance module is implemented.
* Configure system-level settings.

## 4.2 Principal / Head

Each campus shall have its own principal/head.

A principal should be able to:

* View information for their campus.
* Manage campus academic activities.
* View students.
* View teachers.
* Manage classes and sections where authorized.
* Review examination information.
* Review results.
* View campus reports.
* Manage or supervise campus staff.

A principal should not automatically have organization-wide access unless explicitly granted.

## 4.3 Vice Principal

A vice principal assists the principal.

The system should allow permissions such as:

* View students.
* View classes and sections.
* View teachers.
* Monitor academic activities.
* Review examination information.
* Review results.
* Perform administrative tasks assigned by the principal.

## 4.4 Management Staff

Management staff should have access to administrative functions according to their assigned permissions.

Their access should be configurable rather than permanently fixed.

## 4.5 Teacher

Teachers should be able to:

* View their assigned classes.
* View their assigned subjects.
* View their assigned sections.
* Enter marks where authorized.
* View relevant student information.
* View examination information.
* View relevant results.

Teachers should only access information allowed by their permissions and assignments.

## 4.6 Work Staff

Work staff may have limited access to administrative functions depending on their responsibilities.

## 4.7 Guard

Security guards should have limited system access.

Their permissions should be configurable if security-related functionality is introduced.

## 4.8 Student

Students should be able to access information assigned to their own account.

Potential student features include:

* View profile.
* View class and section.
* View subjects.
* View examination information.
* View results.

---

# 5. Student Management Requirements

The system shall maintain student records.

A student record should contain information such as:

* Student ID
* Admission number
* Name
* Date of birth
* Gender
* Admission date
* Current status
* Academic enrollment

The system shall associate students with:

* Campus
* Academic year
* Class
* Section

## 5.1 Student Academic History

The system should preserve historical enrollment information.

For example:

```text
2024–2025 → Grade 5 → Section A
2025–2026 → Grade 6 → Section B
2026–2027 → Grade 7 → Section A
```

Previous academic records should not be overwritten when a student is promoted.

---

# 6. Staff Management Requirements

The system shall maintain staff records.

Staff categories include:

* Principal/Head
* Vice Principal
* Management Staff
* Teacher
* Work Staff
* Guard

A staff member should have:

* Employee number
* Name
* Role
* Campus
* Joining date
* Status

The system should allow different roles to have different permissions.

---

# 7. Academic Management

The system shall manage the school's academic structure.

The academic structure should support:

```text
School
  ↓
Campus
  ↓
Academic Unit
  ↓
Class
  ↓
Section
```

## 7.1 Academic Year

The system shall support multiple academic years.

Each academic year should contain:

* Name
* Start date
* End date
* Status

Example:

```text
2026–2027
```

The system should preserve previous academic years.

## 7.2 Terms

The system should support academic terms.

Terms should be configurable because the exact structure may vary.

Each term should have:

* Name
* Start date
* End date
* Academic year

---

# 8. Class and Section Management

The system shall allow administrators to create and manage classes.

Examples include:

* Play Group
* Nursery
* Prep
* Grade 1
* Grade 2
* Grade 3
* Grade 4
* Grade 5
* Grade 6
* Grade 7
* Grade 8
* Grade 9
* Grade 10

Classes should not be hard-coded.

The administrator should be able to:

* Add a class.
* Rename a class.
* Deactivate a class.
* Assign classes to academic units.
* Create sections.

## 8.1 Sections

A class may have multiple sections.

Example:

```text
Grade 5
├── Section A
├── Section B
└── Section C
```

The number of sections must remain configurable.

---

# 9. Subject Management

The system shall maintain subjects.

The subjects currently identified for Perfect Foundation School include:

### General Subjects

* English
* Urdu
* Mathematics
* Science
* Islamiat
* Pakistan Studies
* Computer Science

### Senior / Specific Subjects

* Biology
* Chemistry
* Physics
* General Mathematics
* General Science
* Education
* Economics

The system should not assume that every subject applies to every class.

Subjects should be assignable to specific classes and academic years.

The system should support:

* Subject name
* Subject code
* Subject type
* Practical requirement
* Active/inactive status

---

# 10. Teacher Assignment

Teachers should be assignable to subjects and classes.

The system shall support:

```text
Teacher
   ↓
Subject Offering
   ↓
Class
   ↓
Section
```

Example:

```text
Teacher: Mr. Ahmed
Subject: Mathematics
Class: Grade 8
Section: A
Academic Year: 2026–2027
```

A teacher may teach:

* Multiple subjects.
* Multiple classes.
* Multiple sections.

Subject and teacher assignments should be stored separately from the teacher's personal profile.

---

# 11. Student Enrollment

Students shall be enrolled into a class and section for a particular academic year.

An enrollment should contain:

* Student
* Academic year
* Section
* Roll number
* Enrollment status

Example:

```text
Student: Ali
Academic Year: 2026–2027
Class: Grade 8
Section: B
Roll Number: 18
```

The system should preserve previous enrollments.

---

# 12. Examination Management

The school currently conducts multiple types of tests/examinations.

These include:

1. Monthly Tests
2. Class Tests
3. Mid-Term Examinations
4. Final Examinations

The system shall allow examination types to be configured.

## 12.1 Examination

An examination should contain:

* Examination name
* Examination type
* Academic year
* Term
* Start date
* End date
* Status

Example:

```text
Academic Year: 2026–2027
Examination: Mid-Term Examination
```

---

# 13. Examination Subjects

Each examination can contain multiple subjects.

For each examination subject, the system should store:

* Examination
* Subject
* Maximum marks
* Passing marks

Example:

```text
Mid-Term Examination
│
├── English → 100 marks
├── Urdu → 100 marks
├── Mathematics → 100 marks
└── Science → 100 marks
```

The actual marks should remain configurable.

---

# 14. Student Marks

The system shall record student marks for each examination subject.

The system should support:

* Obtained marks
* Maximum marks
* Absent status
* Remarks

Example:

```text
Student: Ali
Exam: Mid-Term
Subject: Mathematics
Maximum Marks: 100
Obtained Marks: 82
```

The system should prevent unauthorized users from changing marks.

---

# 15. Results

The system shall generate and maintain student results.

A result may contain:

* Student
* Academic year
* Examination
* Total marks
* Obtained marks
* Percentage
* Overall grade
* Status

Subject-level results should also be maintained.

Example:

```text
Student Result
│
├── English       78 / 100
├── Urdu          82 / 100
├── Mathematics   91 / 100
├── Science       85 / 100
└── Islamiat      88 / 100
```

The system should calculate percentages automatically according to configured rules.

---

# 16. Grading System

The grading system should be configurable.

The system should not permanently hard-code one grading scale.

A grade scale should contain ranges such as:

```text
Minimum Percentage
Maximum Percentage
Grade
Grade Point
```

Example structure:

```text
Grade Scale
│
├── 90–100 → A+
├── 80–89  → A
├── 70–79  → B
└── ...
```

The actual grading boundaries should be entered according to the school's approved grading policy.

---

# 17. Grade 10 Practical Examinations

Grade 10 students may have practical examinations at the end of the academic cycle.

The system shall support practical marks separately from theoretical marks.

Example:

```text
Grade 10
│
├── Theory
│    ├── Physics
│    ├── Chemistry
│    └── Biology
│
└── Practical
     ├── Physics
     ├── Chemistry
     └── Biology
```

The system should allow the school's approved rules to determine how practical and theoretical marks contribute to the final result.

---

# 18. Fee Management

A future fee module should support:

* Fee categories
* Fee schedules
* Student invoices
* Due dates
* Payments
* Receipts
* Outstanding balances
* Discounts
* Payment status

Possible fee categories include:

* Tuition
* Admission
* Examination
* Transport
* Laboratory
* Other charges

The exact fee structure has not yet been provided and should therefore remain configurable.

---

# 19. Attendance

Attendance should be designed as a future module.

Potential requirements include:

* Student attendance
* Teacher attendance
* Daily attendance
* Monthly attendance reports
* Present
* Absent
* Leave

The exact attendance process needs to be confirmed with the school.

---

# 20. Parent / Guardian Management

The system should be designed to support parent/guardian information.

Potential information includes:

* Parent/guardian name
* Relationship to student
* Phone number
* Address
* Email
* Emergency contact

A parent/guardian portal can be added as a future module.

---

# 21. Reports

The system should eventually provide reports such as:

### Student Reports

* Student profile
* Student academic history
* Enrollment report

### Academic Reports

* Class list
* Section list
* Subject list
* Teacher assignments

### Examination Reports

* Examination results
* Subject results
* Student marks
* Class performance
* Grade distribution

### Administrative Reports

* Staff list
* Campus information
* User activity

Financial reports can be added when the fee module is implemented.

---

# 22. Notifications and Announcements

A future notification module may allow authorized staff to publish:

* School announcements
* Examination notices
* Events
* Important dates
* Administrative messages

Notifications may later be delivered through:

* Web application
* Email
* SMS
* Other supported channels

---

# 23. Security Requirements

The system shall use authentication and authorization.

Users should only be able to access functionality permitted by their role.

Examples:

```text
Owner
   ↓
All campuses

Principal
   ↓
Own campus

Teacher
   ↓
Assigned classes/subjects

Student
   ↓
Own information
```

Passwords must not be stored as plain text.

The system should maintain secure authentication and authorization mechanisms.

---

# 24. Audit Requirements

Important actions should eventually be recorded.

Examples include:

* User login
* Creation of student records
* Modification of student information
* Mark entry
* Mark modification
* Result publication
* Fee payment
* Permission changes

Audit records should identify:

* User
* Action
* Date/time
* Relevant record
* Previous/new values where appropriate

---

# 25. Configurability Requirements

The system must remain generic.

The following should be configurable:

* School/campus structure
* Academic years
* Terms
* Academic units
* Classes
* Sections
* Subjects
* Teacher assignments
* Examination types
* Maximum marks
* Passing marks
* Grading scales
* Roles
* Permissions
* Fee categories
* Other future modules

The application should avoid hard-coded assumptions wherever a school-specific rule may change.

---

# 26. Non-Functional Requirements

## 26.1 Usability

The system should provide a clear and simple interface for administrators, teachers, and students.

## 26.2 Performance

The system should remain responsive when handling thousands of students and staff records.

The initial case study contains multiple campuses, more than 30 teachers per branch, and more than 500 students per branch, so the database must be designed to support growth.

## 26.3 Scalability

The system should allow:

* Additional campuses
* Additional students
* Additional teachers
* Additional classes
* Additional subjects
* Additional academic years

without requiring structural changes to the database.

## 26.4 Maintainability

The system should use a modular architecture so that modules can be developed and maintained independently.

## 26.5 Data Integrity

Relationships between students, enrollments, classes, subjects, examinations, marks, and results must maintain referential integrity.

## 26.6 Backup and Recovery

The database should support regular backups and recovery procedures.

---

# 27. Initial System Modules

The initial system should be divided into modules:

```text
School Management
│
├── Authentication & Users
├── Roles & Permissions
├── Campus Management
├── Staff Management
├── Student Management
├── Academic Management
├── Class & Section Management
├── Subject Management
├── Teacher Assignment
├── Examination Management
├── Marks Management
├── Results Management
└── Grading Management
```

Future modules:

```text
Future
│
├── Fees
├── Attendance
├── Parents/Guardians
├── Timetable
├── Events
├── Notifications
├── Library
├── Transport
├── Payroll
└── Admissions
```

---

# 28. Initial Development Priority

Development should follow dependencies rather than attempting to build every module simultaneously.

### Phase 1 — Foundation

* Project setup
* Authentication
* Users
* Roles
* Permissions
* School
* Campus

### Phase 2 — People

* Staff
* Teachers
* Students

### Phase 3 — Academics

* Academic years
* Terms
* Academic units
* Classes
* Sections
* Subjects
* Enrollment
* Teacher assignments

### Phase 4 — Examinations

* Examination types
* Examinations
* Examination subjects
* Student marks
* Practical marks

### Phase 5 — Results

* Grade scales
* Grade ranges
* Results
* Subject results
* Result publication

### Phase 6 — Future Modules

* Fees
* Attendance
* Parents
* Timetable
* Events
* Notifications
* Reports

---

# 29. Relationship With ERD

The requirements document is supported by the database ERD.

The initial ERD contains the major entities required for the academic system, including:

* School
* Campus
* Academic Unit
* User
* Role
* Staff
* Student
* Academic Year
* Term
* Class
* Section
* Enrollment
* Subject
* Subject Offering
* Teacher
* Teacher Assignment
* Student Subject
* Examination
* Examination Subject
* Student Mark
* Grade Scale
* Grade Range
* Result
* Result Subject
* Result Mark
* Practical Mark

The ERD should be reviewed against these requirements before database implementation begins.

---

# 30. Items Requiring Confirmation

The following information has not yet been finalized and should remain configurable until confirmed:

* Exact academic year dates
* Exact term structure
* Number of sections in Grades 2–10
* Exact student admission process
* Parent/guardian requirements
* Attendance process
* Exact fee structure
* Exact examination marks
* Exact passing marks
* Exact grading scale
* Exact practical marking scheme
* Promotion rules
* Exact permissions for each role
* Timetable requirements
* Reporting requirements
* Notification requirements

These items should not be hard-coded into the initial system.

---

# 31. Conclusion

The proposed School Management System will provide a centralized and configurable platform for managing Perfect Foundation School.

The system will initially focus on organization management, users, staff, students, academic structure, examinations, marks, grading, and results.

The architecture and database should remain flexible enough to support additional campuses, academic structures, examination systems, and future school-management modules.

The requirements will be reviewed and refined before implementation begins.
