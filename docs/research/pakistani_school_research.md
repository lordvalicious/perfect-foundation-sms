# Pakistani School Management System — Research

## 1. Introduction

This research studies the academic and administrative structure of a Pakistani school and identifies the requirements for developing a generic School Management System.

The system will be designed as a flexible template rather than being permanently tied to one particular school or examination board.

## 2. Pakistani School Structure

### 2.1 Academic Year

Describe how the school organizes its academic year.

Questions to investigate:

* When does the academic year normally begin?
* When does it end?
* Is the year divided into terms, semesters, or other periods?
* Can the school configure its own academic calendar?

### 2.2 Classes

Identify the classes/levels used by the school.

Example:

* Playgroup
* Nursery
* Prep
* Grade 1
* Grade 2
* Grade 3
* ...
* Grade 10
* Grade 11
* Grade 12

The system should allow a school administrator to add, rename, or deactivate classes.

### 2.3 Sections

Investigate how classes are divided into sections.

Example:

Grade 5:

* Section A
* Section B
* Section C

The system should support multiple sections for the same class.

### 2.4 Subjects

Identify common subjects taught at different levels.

Examples may include:

* English
* Urdu
* Mathematics
* Science
* Islamiat
* Pakistan Studies
* Computer Science

The final subject list should be configurable because subjects can differ between schools and classes.

## 3. Students

Investigate the information normally maintained about students.

Possible information:

* Student name
* Admission number
* Date of birth
* Gender
* Admission date
* Class
* Section
* Academic year
* Contact information
* Student status

## 4. Teachers

Investigate teacher information and responsibilities.

Possible information:

* Teacher name
* Employee number
* Department
* Joining date
* Subjects taught
* Classes/sections assigned

## 5. Examinations

Investigate how examinations are organized.

Examples to investigate:

* Monthly tests
* Class tests
* Mid-term examinations
* Final examinations
* Practical examinations

Determine whether different examinations use different maximum marks, weights, or grading rules.

## 6. Results and Grading

Investigate:

* How marks are recorded
* Maximum marks
* Obtained marks
* Percentage calculation
* Grades
* Grade boundaries
* Subject-wise results
* Overall result
* Pass/fail status
* Result publication
* Student promotion

The system should allow grading rules to be configured rather than hard-coded.

## 7. Fees

Investigate common school fees and payment processes.

Possible categories:

* Tuition fee
* Admission fee
* Examination fee
* Transport fee
* Laboratory fee
* Other charges

Investigate:

* Fee schedules
* Student invoices
* Due dates
* Partial payments
* Receipts
* Outstanding balances
* Discounts

## 8. School Roles

Identify the users of the system.

Possible roles:

* School Administrator
* Teacher
* Student
* Accountant
* Staff Member

For each role, document what the user can view, create, edit, approve, and publish.

## 9. Current/Manual Process

Describe how schools may currently manage:

* Student records
* Attendance
* Classes
* Exams
* Results
* Fees
* Notices/events

Identify problems such as duplicate data, manual calculations, difficult record searching, and lack of centralized information.

## 10. Proposed School Management System

The proposed system will provide modules for:

* School management
* Student management
* Teacher management
* Class and section management
* Subject management
* Examination management
* Result management
* Fee management
* Events/announcements
* Reports

## 11. Generic/Configurable Features

The system should not assume one fixed school's rules.

The following should be configurable:

* Academic years
* Terms
* Classes
* Sections
* Subjects
* Examination types
* Grading scales
* Fee categories
* Fee structures
* User roles and permissions

## 12. Future Expansion

Potential future modules include:

* Attendance
* Parent/guardian portal
* Admissions
* Timetable
* Library
* Transport
* Hostel
* Payroll
* Online learning
* Notifications

## 13. Conclusion

The research will be used to design the database, ERD, system architecture, requirements, and implementation of the generic Pakistani School Management System.


VS Code
   ↓
pakistani_school_research.md
   ↓
Research + sources
   ↓
requirements.md
   ↓
ERD
   ↓
Use Case Diagram
   ↓
Architecture
   ↓
Django + PostgreSQL

