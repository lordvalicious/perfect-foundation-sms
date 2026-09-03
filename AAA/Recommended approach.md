# Recommended approach

Build this as a **modular monolith**: one application, one database, and clearly separated modules for accounts, academics, fees, grades, events, and reporting.

Do **not** begin with microservices, a mobile app, separate frontend/backend repositories, or multiple authentication systems. Those choices add complexity without helping your first release.

A beginner-friendly production stack would be:

| Layer             | Recommendation                                  |
| ----------------- | ----------------------------------------------- |
| Backend           | Python + Django 5.2 LTS                         |
| Frontend          | Django templates + Bootstrap                    |
| Database          | PostgreSQL                                      |
| Local development | Docker Compose                                  |
| Production server | Gunicorn or another production WSGI/ASGI server |
| File storage      | S3-compatible object storage                    |
| Email             | Transactional email provider                    |
| Background work   | Add Redis + Celery later                        |
| Deployment        | Managed application host + managed PostgreSQL   |
| Source control    | GitHub                                          |
| Testing           | Django’s built-in test framework or pytest      |

Django 5.2 is a long-term support release receiving security updates for at least three years from April 2025, making it a sensible, stable choice for a beginner building a serious application. Django also includes authentication, password handling, sessions, forms, database migrations, an ORM, permissions, and an internal administration panel. ([Django Project][1])

---

# 1. Define the product boundary

Your system should initially solve these problems:

1. Manage institutions, campuses and academic years.
2. Manage students, teachers and non-teaching staff.
3. Give each user an appropriate portal.
4. Generate and collect student fees.
5. Let teachers enter grades.
6. Publish grades to students.
7. Create and publish events.
8. Maintain an audit history of important actions.

Do not put everything an institution could ever need into version one.

## MVP features

Your first deployable release should include:

* Institution and campus setup
* Academic year and term setup
* Student, teacher and staff profiles
* User invitations and password resets
* Role-based dashboards
* Courses, classes and student enrolments
* Fee structures, invoices, payments and receipts
* Assessments, scores and published grades
* Events and targeted announcements
* Search, filtering and CSV exports
* Audit logs
* Responsive screens for phones and computers

## Later features

After the MVP works reliably, consider:

* Attendance
* Parent or guardian portal
* Admissions
* Timetables
* Payroll
* Staff attendance and leave
* Library
* Transport
* Hostel management
* Online learning content
* SMS and WhatsApp notifications
* Native mobile applications
* Advanced analytics

Keeping these out of the first version will substantially improve your chance of finishing the application.

---

# 2. Application architecture

```text
Students / Teachers / Staff / Administrators
                    |
                 HTTPS
                    |
             Django Application
        ┌───────────┼────────────┐
        |           |            |
   PostgreSQL   File Storage   Email Provider
        |
   Backups and reporting

Later additions:
- Payment gateway
- Redis
- Background task worker
- Monitoring and error tracking
```

Use Django templates for the user interface initially. You will not need a separate React, Vue or Next.js application for this project.

A separate frontend would require you to learn:

* API authentication
* Cross-origin request security
* API versioning
* Client-side state
* Two deployment pipelines
* Duplicate form validation
* More complicated error handling

You can add an API later if you build a mobile app or integrate with other systems.

---

# 3. Design the login portals correctly

You can display separate login pages:

```text
/student/login/
/teacher/login/
/staff/login/
/finance/login/
/management/login/
```

However, all of them should use the **same underlying user table, password system and session system**.

After login:

1. Authenticate the user.
2. Find their active institution membership.
3. Find their assigned roles.
4. Redirect them to the appropriate dashboard.
5. Check permissions again on every request.

For example:

```text
/student/dashboard/
/teacher/dashboard/
/staff/dashboard/
/finance/dashboard/
/management/dashboard/
```

The URL is only part of the user experience. It must not be the security mechanism. A student typing `/management/dashboard/` should receive a permission error even when logged in.

Django supports custom user models, authentication backends and custom permissions. Create your custom user model at the beginning of the project; changing it after many database migrations becomes much harder. ([Django Project][2])

## Users with multiple roles

A real institution may have users with several responsibilities:

* A teacher may also be a department head.
* An accountant may also be a staff member.
* An administrator may teach a course.
* One user may work at two campuses.

Therefore, avoid putting only one `role` field directly on the user.

Use this structure instead:

```text
User
  └── InstitutionMembership
          └── RoleAssignment
```

A user with several roles can choose a portal after login or switch roles from the navigation menu.

---

# 4. Roles and permissions

Start with these roles:

| Role                   | Main permissions                                             |
| ---------------------- | ------------------------------------------------------------ |
| Platform super admin   | Manage institutions and platform configuration               |
| Institution admin      | Manage the institution, users, academics and settings        |
| Academic administrator | Manage courses, classes, terms and grade publication         |
| Accountant             | Manage fee plans, invoices, payments and receipts            |
| Teacher                | View assigned classes and enter grades                       |
| Student                | View their own profile, fees, grades and events              |
| Staff member           | View their own profile and permitted operational information |

A teacher should only access students and courses assigned to that teacher. A student should only see that student’s records. An accountant should not be able to change grades.

Authentication answers **“Who is the user?”** Authorization answers **“What is this user allowed to do?”** OWASP recommends checking authorization for the specific object on every request rather than assuming access to one item permits access to all items of that type. ([OWASP Cheat Sheet Series][3])

---

# 5. Core database design

## Institution module

```text
Institution
- id
- name
- institution_type: school, college, university
- timezone
- currency
- address
- status

Campus
- institution
- name
- address
```

Add `institution_id` to every institution-owned table, even when you initially deploy for only one institution. This makes future multi-institution support much easier.

For a future software-as-a-service version, PostgreSQL row-security policies can provide an additional database-level tenant boundary, although you should first implement and thoroughly test application-level filtering. ([PostgreSQL][4])

## Accounts and people

```text
User
- email
- password
- first_name
- last_name
- is_active

InstitutionMembership
- user
- institution
- status

RoleAssignment
- membership
- role

StudentProfile
- membership
- admission_number
- admission_date
- date_of_birth
- status

TeacherProfile
- membership
- employee_number
- department
- joining_date
- status

StaffProfile
- membership
- employee_number
- designation
- department
- joining_date
- status
```

Keep login information in `User` and institution-specific information in profiles and memberships.

## Academic structure

Schools, colleges and universities use different terminology, so create flexible academic structures:

```text
AcademicYear
Term
Department
Program
Course
ClassSection
CourseOffering
Enrollment
TeacherAssignment
```

Example:

```text
Course: Mathematics
CourseOffering: Mathematics taught during Term 1
ClassSection: Grade 9-A
TeacherAssignment: Mr Ahmed teaches Mathematics to Grade 9-A
Enrollment: Student Sara belongs to Grade 9-A
```

A university can use `Program` for degrees and `CourseOffering` for semester courses, while a school can use sections and grade levels.

---

# 6. Fees management

Do not treat fees as one editable “paid/unpaid” field.

A proper workflow is:

```text
Fee plan
   ↓
Student invoice
   ↓
Invoice lines
   ↓
Payment
   ↓
Payment allocation
   ↓
Receipt
```

## Recommended fee tables

```text
FeeCategory
- Tuition
- Admission
- Examination
- Transport
- Laboratory

FeePlan
- institution
- academic_term
- applicable_program_or_class
- due_date

FeePlanLine
- fee_plan
- fee_category
- amount

Invoice
- student
- issue_date
- due_date
- status

InvoiceLine
- invoice
- description
- amount

Payment
- student
- payment_date
- method
- amount
- reference
- status

PaymentAllocation
- payment
- invoice
- amount

Discount
- student_or_invoice
- type
- amount
- reason

RefundOrReversal
- original_payment
- amount
- reason
```

## Important financial rules

* Store monetary amounts as integer minor units or exact decimal values, never floating-point values.
* Allow partial payments.
* Allow one payment to cover several invoices.
* Give every receipt a unique institution-specific number.
* Never silently delete completed payments.
* Correct mistakes through reversals or adjustment records.
* Record who entered, approved or reversed a payment.
* Use database transactions when creating payments and allocations.
* Keep invoice totals, payments and outstanding balances consistent.
* Support cash, bank transfer and online payment separately.

Start with manual cash and bank-transfer recording. Add online payment only after the rest of the fee system is reliable.

When integrating a payment provider, your server should confirm payment using signed webhooks rather than trusting the user’s browser. Stripe’s official documentation, for example, recommends monitoring payment completion through server-side webhooks. ([Stripe Docs][5])

Do not store card numbers or card security codes in your database.

---

# 7. Grade management

The grade workflow should be:

```text
Course offering
   ↓
Assessments created
   ↓
Teachers enter scores
   ↓
Academic review
   ↓
Grades published
   ↓
Students view results
```

## Grade tables

```text
Assessment
- course_offering
- title
- type
- maximum_score
- weight
- due_date
- status

StudentScore
- assessment
- student
- score
- absent
- exempt
- entered_by
- entered_at

GradeScale
- minimum_percentage
- maximum_percentage
- letter_grade
- grade_point

FinalGrade
- student
- course_offering
- calculated_percentage
- letter_grade
- status: draft, approved, published
- published_at

GradeAmendment
- final_grade
- previous_value
- new_value
- reason
- approved_by
```

## Grade rules

* Assessment weights for a course should total 100%.
* Absence must be stored separately from a score of zero.
* Draft grades should not appear in the student portal.
* Teachers should only enter scores for assigned course offerings.
* Published grades should be locked.
* Changes to published grades should require an amendment reason.
* Every change should be traceable.
* Different institutions may have different grading scales.

Example calculation:

```text
Quiz:       15/20 × 20% = 15%
Assignment: 40/50 × 30% = 24%
Exam:       72/100 × 50% = 36%

Final percentage = 75%
```

Do grade calculations on the server, not only in browser JavaScript.

---

# 8. Events management

Events should support more than just a title and date.

```text
Event
- institution
- campus
- title
- description
- start_datetime
- end_datetime
- location
- status: draft, published, cancelled
- created_by

EventAudience
- event
- audience_type
- role, class, department or program

EventRSVP
- event
- user
- response

EventAttachment
- event
- file
```

Examples of audiences:

* Everyone
* Students only
* Teachers only
* Grade 10 students
* Computer Science department
* One university program
* One campus

Always store event time zones correctly. Your institution setting should define the default timezone.

Reminders can initially be sent immediately through email. Later, use a background worker for scheduled reminders.

---

# 9. Suggested Django project structure

```text
school_management/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── institutions/
│   ├── people/
│   ├── academics/
│   ├── fees/
│   ├── grades/
│   ├── events/
│   ├── notifications/
│   └── audit/
│
├── templates/
├── static/
├── media/
├── tests/
├── manage.py
├── compose.yaml
├── Dockerfile
├── requirements.txt
└── .env.example
```

Each app should own its models, forms, views, services, URLs and tests.

Avoid one enormous `models.py` or one giant “core” application.

---

# 10. Step-by-step implementation roadmap

## Milestone 1: Write the rules before coding

Create a small requirements document containing:

* Roles
* Permissions
* Institution terminology
* Fee workflow
* Grade workflow
* Event audiences
* What is explicitly excluded from version one

Also sketch the main screens on paper or in a simple design tool.

**Completion condition:** You can explain who performs each action and who can see its result.

## Milestone 2: Set up the project

Install:

* Python
* Git
* Docker Desktop
* A code editor
* PostgreSQL through Docker

Create the repository, Django project, environment settings and a basic automated test workflow.

Docker Compose is useful here because the web application and PostgreSQL can be defined and started together using one configuration file. Docker documents Compose for development, testing, staging and production-style environments. ([Docker Documentation][6])

**Completion condition:** A fresh computer can clone the repository and start the application using documented commands.

## Milestone 3: Build authentication first

Implement:

* Custom user model
* Institution memberships
* Roles
* Login
* Logout
* Password reset
* Dashboard redirection
* Permission helpers
* Institution filtering

Django does not provide login brute-force rate limiting by default, so add throttling before production. ([Django Project][2])

**Completion condition:** Each role signs in and sees only its own dashboard.

## Milestone 4: Build institution and people management

Implement:

* Institution
* Campus
* Departments
* Student profiles
* Teacher profiles
* Staff profiles
* Search
* Status changes
* CSV import

Do not permanently delete people when they leave. Mark them inactive or archived.

**Completion condition:** An administrator can create and manage all user types.

## Milestone 5: Build academics

Implement:

* Academic years
* Terms
* Programs
* Classes and sections
* Courses
* Course offerings
* Teacher assignments
* Student enrolments

**Completion condition:** The system knows which students and teachers belong to each active class or course.

## Milestone 6: Build fees

Implement in this order:

1. Fee categories
2. Fee plans
3. Invoice generation
4. Invoice details
5. Manual payment recording
6. Payment allocation
7. Receipt generation
8. Outstanding-balance reports
9. Discounts and reversals

Do not add a payment gateway yet.

**Completion condition:** An accountant can issue an invoice, record a partial payment and produce the correct receipt and balance.

## Milestone 7: Build grades

Implement:

1. Grade scales
2. Assessments
3. Score entry
4. Automatic calculations
5. Review and approval
6. Publishing
7. Student result view
8. Amendments

**Completion condition:** A teacher can grade assigned students, but students cannot see results before publication.

## Milestone 8: Build events

Implement:

* Draft events
* Audience selection
* Publishing
* Calendar and list views
* RSVP
* Cancellation
* Basic email notices

**Completion condition:** Only targeted users see each event.

## Milestone 9: Audit, reporting and exports

Audit at least:

* Login successes and failures
* User creation and deactivation
* Permission changes
* Invoice creation
* Payment entry and reversal
* Grade changes and publication
* Data exports
* Institution-setting changes

OWASP recommends logging authentication and authorization failures, administrative actions, access to sensitive data and data exports. Logs should capture who did what, where and when. ([OWASP Cheat Sheet Series][7])

**Completion condition:** Administrators can investigate important changes without directly querying the database.

## Milestone 10: Testing and production hardening

Add tests for:

* Student A cannot see Student B’s data.
* Teacher A cannot edit Teacher B’s course.
* An accountant cannot change grades.
* A teacher cannot publish grades without permission.
* Duplicate payment callbacks do not create duplicate payments.
* Partial payments calculate correctly.
* Reversals restore balances correctly.
* Grade weight totals are validated.
* Archived users cannot log in.
* Users from Institution A cannot access Institution B.

---

# 11. Deployment design

Maintain three environments:

```text
Local development
Staging
Production
```

## Production components

```text
Web application container
Managed PostgreSQL database
Managed object storage
Email provider
HTTPS domain
Automated database backups
Error monitoring
Central application logs
Uptime monitoring
```

For your first deployment, use a managed application platform rather than manually configuring a complex cloud network. Choose one that supports:

* Docker
* Managed PostgreSQL
* Environment variables
* HTTPS
* Scheduled jobs
* Persistent object storage or external S3 storage
* Deployment from GitHub
* Backups
* A data centre reasonably close to your users

## Deployment checklist

Before going live:

* Set `DEBUG = False`.
* Store secrets in environment variables.
* Use HTTPS.
* Configure secure cookies.
* Set allowed hosts.
* Use a production WSGI or ASGI server.
* Run database migrations.
* Run automated tests.
* Run `python manage.py check --deploy`.
* Configure backups.
* Test restoring a backup.
* Create an administrator account securely.
* Configure email delivery.
* Add error reporting.
* Add login throttling.
* Remove sample data.

Django explicitly states that its development `runserver` is not suitable for production and recommends running its deployment checks, protecting secret keys, disabling debug mode and configuring backups. ([Django Project][8])

---

# 12. Security requirements

Because student, employee, financial and academic information is sensitive, security must be part of the initial design.

Use these rules:

* Deny access unless explicitly permitted.
* Verify institution ownership on every database query.
* Verify object-level permissions on every request.
* Require MFA for institution administrators and finance users.
* Use generic login and password-reset responses.
* Throttle repeated login attempts.
* Use CSRF protection.
* Use secure HTTP-only session cookies.
* Re-authenticate before especially sensitive actions.
* Scan and restrict uploaded files.
* Never expose private uploads using predictable public URLs.
* Do not log passwords, reset tokens, card details or confidential documents.
* Audit changes to fees and published grades.
* Encrypt connections with HTTPS.
* Back up the database and uploaded files.
* Define data-retention and account-deletion procedures.

OWASP recommends generic authentication errors to prevent account discovery, secure sessions, login throttling and additional authentication for sensitive actions. ([OWASP Cheat Sheet Series][9])

---

# 13. Screens for the first release

## Management portal

* Dashboard
* Students
* Teachers
* Staff
* Classes and courses
* Academic years and terms
* Roles and permissions
* Reports
* Audit logs
* Institution settings

## Finance portal

* Dashboard
* Fee plans
* Invoices
* Receive payment
* Receipts
* Outstanding balances
* Discounts
* Reversals
* Financial reports

## Teacher portal

* Dashboard
* Assigned classes
* Student lists
* Assessments
* Gradebook
* Events

## Student portal

* Dashboard
* Profile
* Courses
* Fee invoices
* Payment history
* Results
* Events
* Account settings

## Staff portal

* Dashboard
* Profile
* Department information
* Events
* Role-specific operational pages

---

# 14. Definition of a successful MVP

Your system is ready for its first real institution when:

* Every user has an institution membership and role.
* Data is isolated between institutions.
* Students cannot access one another’s records.
* Teachers can only grade assigned classes.
* Accountants can manage payments without grade access.
* Invoice balances remain correct after partial payments and reversals.
* Grades require publication before students can see them.
* Events reach the correct audiences.
* Important actions are audited.
* Automated permission and financial tests pass.
* The application runs over HTTPS.
* Production backups exist and have been restored successfully.
* A staging environment is available for testing releases.

The best first coding target is **authentication, institution membership and role permissions**. Every later module depends on getting that foundation right.

[1]: https://docs.djangoproject.com/en/5.2/releases/5.2/ "Django 5.2 release notes | Django documentation | Django"
[2]: https://docs.djangoproject.com/en/5.2/topics/auth/customizing/ "Customizing authentication in Django | Django documentation | Django"
[3]: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html "Authorization - OWASP Cheat Sheet Series"
[4]: https://www.postgresql.org/docs/17/ddl-rowsecurity.html?utm_source=chatgpt.com "PostgreSQL: Documentation: 17: 5.9. Row Security Policies"
[5]: https://docs.stripe.com/payments/payment-intents/verifying-status?utm_source=chatgpt.com "Payment status updates"
[6]: https://docs.docker.com/compose/?utm_source=chatgpt.com "Docker Compose"
[7]: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html "Logging - OWASP Cheat Sheet Series"
[8]: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/ "Deployment checklist | Django documentation | Django"
[9]: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html "Authentication - OWASP Cheat Sheet Series"

