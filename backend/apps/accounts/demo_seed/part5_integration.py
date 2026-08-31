"""Part 5 — Integration: portals, LMS, discipline, events, communications.

Creates (idempotently, scoped to DEMO-EDU / ctx.school / ctx.active_year):
- LMS courses, lessons, completions, quizzes, questions, quiz attempts
- Homework + submissions
- Discipline incidents + disciplinary actions
- Events + audiences + RSVPs
- Announcements + notifications
- Messages + SMS logs
- Support tickets
- Alumni profiles
- Campus transfers
- Student transfers
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

import apps.accounts.demo_seed.base as base
from apps.accounts.demo_seed.base import getc

CAMPUS_CODES = ["GVC", "CSC", "BFC", "KHC", "EXC"]


# ---------------------------------------------------------------------------
# LMS
# ---------------------------------------------------------------------------

def _seed_lms(ctx):
    ctx.log("Creating LMS courses, lessons, quizzes, completions...")
    from apps.lms.models import Course, Lesson, LessonCompletion, Quiz, Question, QuizAttempt
    from apps.teachers.models import Teacher
    from apps.students.models import Student
    from apps.schools.models import Subject

    teachers = list(Teacher.objects.filter(institution=ctx.school, primary_campus__isnull=False))
    subjects = list(Subject.objects.filter(institution=ctx.school))
    subj_map = {s.code: s for s in subjects}

    course_count = 0
    lesson_count = 0
    completion_count = 0
    quiz_count = 0

    sample_courses = [
        ("Mathematics Fundamentals", "MAT", "Core mathematics concepts"),
        ("English Communication", "ENG", "English language skills"),
        ("Science Explorations", "SCI", "General science topics"),
        ("Computer Basics", "COM", "Introduction to computers"),
        ("Urdu Language", "URD", "Urdu reading and writing"),
    ]

    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        campus_teachers = [t for t in teachers if t.primary_campus_id == campus.id]

        for title, subj_code, desc in sample_courses:
            teacher = campus_teachers[hash(title) % max(1, len(campus_teachers))] if campus_teachers else None
            subj = subj_map.get(subj_code)
            if not teacher:
                continue

            course, created = Course.objects.get_or_create(
                institution=ctx.school,
                title=f"{title} - {campus_code}",
                defaults={
                    "teacher": teacher,
                    "campus": campus,
                    "subject": subj,
                    "description": desc,
                    "is_published": True,
                },
            )
            if not created:
                continue
            course_count += 1
            ctx.count("lms_courses")

            # Lessons
            lesson_titles = ["Chapter 1: Introduction", "Chapter 2: Exercises", "Chapter 3: Review"]
            for j, ltitle in enumerate(lesson_titles):
                Lesson.objects.get_or_create(
                    course=course,
                    order=j + 1,
                    defaults={
                        "title": f"{title} - {ltitle}",
                        "content": f"Demo content for {ltitle} in {title}.",
                    },
                )
                lesson_count += 1
            ctx.count("lms_lessons", len(lesson_titles))

            # Quiz
            quiz, q_created = Quiz.objects.get_or_create(
                course=course,
                title=f"{title} Quiz",
                defaults={
                    "description": f"Quiz for {title}",
                    "is_published": True,
                    "due_date": date(2027, 3, 15),
                },
            )
            if q_created:
                quiz_count += 1
                for q_idx in range(3):
                    Question.objects.get_or_create(
                        quiz=quiz,
                        text=f"Question {q_idx + 1} for {title}?",
                        defaults={
                            "option_a": "Option A",
                            "option_b": "Option B",
                            "option_c": "Option C",
                            "option_d": "Option D",
                            "correct_option": "a",
                            "marks": 1,
                        },
                    )

            # Lesson completions (some students complete some lessons)
            lessons = list(Lesson.objects.filter(course=course))
            campus_students = list(
                Student.objects.filter(
                    institution=ctx.school,
                    primary_campus=campus,
                    status="active",
                )[:20]
            )
            for stu in campus_students[:10]:
                for lesson in lessons[:random.randint(0, len(lessons))]:
                    LessonCompletion.objects.get_or_create(
                        lesson=lesson,
                        student=stu,
                    )
                    completion_count += 1

            # Quiz attempts
            for stu in campus_students[:5]:
                QuizAttempt.objects.get_or_create(
                    quiz=quiz,
                    student=stu,
                    defaults={
                        "answers": {"1": "a", "2": "b", "3": "c"},
                        "score": Decimal(str(random.randint(1, 3))),
                        "total_marks": 3,
                    },
                )

    ctx.ok(f"Courses: {course_count}, Lessons: {lesson_count}, "
           f"Completions: {completion_count}, Quizzes: {quiz_count}")


# ---------------------------------------------------------------------------
# HOMEWORK
# ---------------------------------------------------------------------------

def _seed_homework(ctx):
    ctx.log("Creating homework and submissions...")
    from apps.homework.models import Homework, Submission
    from apps.teachers.models import Teacher
    from apps.students.models import Student
    from apps.schools.models import Subject

    teachers = list(Teacher.objects.filter(institution=ctx.school, primary_campus__isnull=False))
    subjects = list(Subject.objects.filter(institution=ctx.school))

    hw_count = 0
    sub_count = 0

    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        campus_teachers = [t for t in teachers if t.primary_campus_id == campus.id]

        for i in range(10):
            teacher = campus_teachers[i % max(1, len(campus_teachers))]
            # Find a class the teacher is assigned to
            cls_key = f"{campus_code}:Class {(i % 8) + 1}"
            cls = ctx.classes.get(cls_key)
            if not cls:
                continue
            section_key = f"{cls_key}:A"
            section = ctx.sections.get(section_key)
            subj = subjects[i % len(subjects)]

            assigned = date(2026, 9 + (i % 4), 1 + (i % 20))
            hw, created = Homework.objects.get_or_create(
                institution=ctx.school,
                teacher=teacher,
                campus=campus,
                class_obj=cls,
                defaults={
                    "section": section,
                    "subject": subj,
                    "title": f"Homework #{hw_count + 1} - {subj.name}",
                    "description": f"Complete exercises for chapter {i + 1}",
                    "assigned_date": assigned,
                    "due_date": assigned + timedelta(days=3),
                    "max_marks": 10,
                    "created_by": teacher.user,
                },
            )
            if not created:
                continue
            hw_count += 1
            ctx.count("homework")

            # Submissions from some students
            students = Student.objects.filter(
                institution=ctx.school,
                primary_campus=campus,
                enrollments__class_obj=cls,
                enrollments__academic_year=ctx.active_year,
                status="active",
            ).distinct()[:8]
            for stu in students:
                status = "submitted" if random.random() > 0.3 else "graded"
                marks = random.randint(5, 10) if status == "graded" else None
                Submission.objects.get_or_create(
                    homework=hw,
                    student=stu,
                    defaults={
                        "content": f"Demo submission by {stu.first_name}",
                        "status": status,
                        "marks_obtained": marks,
                    },
                )
                sub_count += 1

    ctx.ok(f"Homework: {hw_count}, Submissions: {sub_count}")


# ---------------------------------------------------------------------------
# DISCIPLINE
# ---------------------------------------------------------------------------

def _seed_discipline(ctx):
    ctx.log("Creating discipline incidents and actions...")
    from apps.discipline.models import Incident, DisciplinaryAction
    from apps.students.models import Student

    incidents_data = [
        ("Late Arrival", "minor", "Student arrived 15 minutes late"),
        ("Uniform Violation", "minor", "Not wearing proper school uniform"),
        ("Classroom Disruption", "moderate", "Disrupting class activities"),
        ("Academic Misconduct", "major", "Copying during examination"),
        ("Bullying Report", "major", "Reported by fellow student"),
        ("Homework Not Submitted", "minor", "Repeated failure to submit homework"),
        ("Property Damage", "moderate", "Broke classroom equipment"),
        ("Unauthorized Absence", "moderate", "Absent without prior notice"),
    ]

    statuses = ["open", "action_taken", "resolved"]
    action_types = ["verbal_warning", "written_warning", "detention", "parent_meeting", "counselling"]

    inc_count = 0
    action_count = 0
    students = list(Student.objects.filter(institution=ctx.school, status="active")[:40])

    for i, stu in enumerate(students):
        inc_data = incidents_data[i % len(incidents_data)]
        title, severity, desc = inc_data
        campus = stu.primary_campus

        inc, created = Incident.objects.get_or_create(
            institution=ctx.school,
            student=stu,
            title=f"{title} - Student {i + 1:03d}",
            defaults={
                "campus": campus,
                "reported_by": ctx.users.get("demo_superadmin"),
                "description": desc,
                "incident_date": date(2026, 9 + (i % 4), 1 + (i % 27)),
                "severity": severity,
                "status": statuses[i % len(statuses)],
                "parent_notified": random.random() > 0.5,
            },
        )
        if created:
            inc_count += 1
            ctx.count("discipline_incidents")

            if inc.status == "action_taken":
                action, a_created = DisciplinaryAction.objects.get_or_create(
                    incident=inc,
                    defaults={
                        "action_type": action_types[i % len(action_types)],
                        "details": f"Action taken for {title}",
                        "action_date": date(2026, 9 + (i % 4), 5 + (i % 20)),
                        "recorded_by": ctx.users.get("demo_superadmin"),
                    },
                )
                if a_created:
                    action_count += 1

    ctx.ok(f"Discipline incidents: {inc_count}, Actions: {action_count}")


# ---------------------------------------------------------------------------
# EVENTS
# ---------------------------------------------------------------------------

def _seed_events(ctx):
    ctx.log("Creating events, audiences, RSVPs...")
    from apps.events.models import Event, EventAudience, EventRSVP
    from apps.teachers.models import Teacher

    superuser = ctx.users.get("demo_superadmin")
    events_data = [
        ("Annual Sports Day", "2026-11-15", "2026-11-15", "Main Ground"),
        ("Science Exhibition", "2026-12-10", "2026-12-10", "Science Hall"),
        ("Parent-Teacher Meeting", "2026-10-25", "2026-10-25", "Main Hall"),
        ("Orientation Day", "2026-08-17", "2026-08-17", "Auditorium"),
        ("Annual Function", "2027-03-20", "2027-03-21", "Main Auditorium"),
        ("Workshop on Coding", "2026-11-05", "2026-11-05", "Computer Lab"),
        ("Field Trip - Museum", "2026-12-20", "2026-12-20", "National Museum"),
    ]

    ev_count = 0
    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        for title, start_str, end_str, loc in events_data:
            start = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=timezone.UTC)
            end = datetime.strptime(end_str, "%Y-%m-%d").replace(hour=16, tzinfo=timezone.UTC)
            ev, created = Event.objects.get_or_create(
                school=ctx.school,
                title=f"{title} - {campus_code}",
                defaults={
                    "campus": campus,
                    "description": f"Demo event: {title} at {campus.name}",
                    "location": loc,
                    "start_datetime": start,
                    "end_datetime": end,
                    "status": "published",
                    "created_by": superuser,
                },
            )
            if created:
                ev_count += 1
                ctx.count("events")

                EventAudience.objects.get_or_create(
                    event=ev,
                    audience_type="everyone",
                )

                # RSVPs from some teachers
                teachers = list(
                    Teacher.objects.filter(
                        institution=ctx.school, primary_campus=campus
                    )[:5]
                )
                for t in teachers:
                    EventRSVP.objects.get_or_create(
                        event=ev,
                        user=t.user,
                        defaults={"response": random.choice(["yes", "yes", "yes", "maybe"])},
                    )

    ctx.ok(f"Events: {ev_count}")


# ---------------------------------------------------------------------------
# ANNOUNCEMENTS + NOTIFICATIONS
# ---------------------------------------------------------------------------

def _seed_announcements(ctx):
    ctx.log("Creating announcements and notifications...")
    from apps.communication.models import Announcement, Notification
    from apps.students.models import Student

    superuser = ctx.users.get("demo_superadmin")
    announcements_data = [
        ("Fee Submission Reminder", "announcement", "All pending fees must be submitted by end of month."),
        ("Exam Schedule Released", "notice", "Mid-term examination schedule has been published."),
        ("Holiday Notice", "announcement", "School will remain closed on account of public holiday."),
        ("Parent Meeting", "notice", "Parent-teacher meeting scheduled for next week."),
        ("Sports Event", "announcement", "Annual sports day will be held next month."),
    ]

    ann_count = 0
    notif_count = 0

    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        for title, cat, msg in announcements_data:
            ann, created = Announcement.objects.get_or_create(
                institution=ctx.school,
                title=f"{title} - {campus_code}",
                message=msg,
                defaults={
                    "category": cat,
                    "campus": campus,
                    "status": "published",
                    "published_at": timezone.now(),
                    "created_by": superuser,
                    "audience_roles": ["student", "parent", "teacher"],
                },
            )
            if created:
                ann_count += 1
                ctx.count("announcements")

                # Notifications for some students
                students = Student.objects.filter(
                    institution=ctx.school,
                    primary_campus=campus,
                    status="active",
                )[:5]
                for stu in students:
                    if stu.user:
                        Notification.objects.get_or_create(
                            institution=ctx.school,
                            recipient=stu.user,
                            title=f"Announcement: {title}",
                            defaults={
                                "message": msg,
                                "notification_type": "announcement",
                                "announcement": ann,
                                "is_read": random.random() > 0.5,
                            },
                        )
                        notif_count += 1

    ctx.ok(f"Announcements: {ann_count}, Notifications: {notif_count}")


# ---------------------------------------------------------------------------
# MESSAGES
# ---------------------------------------------------------------------------

def _seed_messages(ctx):
    ctx.log("Creating messages and SMS logs...")
    from apps.communication.models import Message, SMSLog
    from apps.students.models import Student
    from apps.teachers.models import Teacher

    superuser = ctx.users.get("demo_superadmin")
    msg_count = 0
    sms_count = 0

    # Messages between parents and teachers
    for campus_code in CAMPUS_CODES[:2]:
        campus = ctx.campuses[campus_code]
        teachers = list(Teacher.objects.filter(
            institution=ctx.school, primary_campus=campus
        )[:3])
        students = list(Student.objects.filter(
            institution=ctx.school, primary_campus=campus,
            status="active",
        )[:5])

        for t in teachers:
            for stu in students:
                if stu.guardian and stu.guardian.user:
                    # Parent -> Teacher
                    Message.objects.get_or_create(
                        institution=ctx.school,
                        sender=stu.guardian.user,
                        recipient=t.user,
                        subject=f"Regarding {stu.first_name}",
                        defaults={
                            "body": f"Dear teacher, I want to discuss {stu.first_name}'s progress.",
                            "is_read": random.random() > 0.5,
                            "sent_at": timezone.now(),
                        },
                    )
                    msg_count += 1
                    # Teacher -> Parent (reply)
                    Message.objects.get_or_create(
                        institution=ctx.school,
                        sender=t.user,
                        recipient=stu.guardian.user,
                        subject=f"Re: Regarding {stu.first_name}",
                        defaults={
                            "body": f"Thank you for reaching out. {stu.first_name} is doing well.",
                            "is_read": True,
                            "sent_at": timezone.now(),
                        },
                    )
                    msg_count += 1

    # SMS logs
    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        for i in range(5):
            SMSLog.objects.get_or_create(
                institution=ctx.school,
                phone_number=f"0321{1000000 + i:07d}",
                message=f"Demo SMS notification {i + 1} from {campus.name}",
                defaults={
                    "status": "sent",
                    "sent_by": superuser,
                },
            )
            sms_count += 1

    ctx.ok(f"Messages: {msg_count}, SMS logs: {sms_count}")


# ---------------------------------------------------------------------------
# SUPPORT TICKETS
# ---------------------------------------------------------------------------

def _seed_helpdesk(ctx):
    ctx.log("Creating support tickets...")
    from apps.helpdesk.models import SupportTicket

    superuser = ctx.users.get("demo_superadmin")
    priorities = ["low", "medium", "high", "urgent"]
    statuses = ["open", "in_progress", "resolved", "closed"]
    categories_hint = ["Fees", "Login", "Academic", "Attendance", "Transport", "Technical"]

    tk_count = 0
    for campus_code in CAMPUS_CODES:
        campus = ctx.campuses[campus_code]
        for i in range(10):
            priority = priorities[i % len(priorities)]
            status = statuses[i % len(statuses)]
            tk, created = SupportTicket.objects.get_or_create(
                institution=ctx.school,
                subject=f"Ticket #{tk_count + 1} - {campus_code}",
                defaults={
                    "campus": campus,
                    "description": f"Demo support ticket {i + 1} from {campus.name}",
                    "priority": priority,
                    "status": status,
                    "created_by": superuser,
                    "assignee": superuser if status != "open" else None,
                    "resolution_notes": "Resolved" if status in ("resolved", "closed") else "",
                },
            )
            if created:
                tk_count += 1
                ctx.count("helpdesk_tickets")

    ctx.ok(f"Support tickets: {tk_count}")


# ---------------------------------------------------------------------------
# ALUMNI
# ---------------------------------------------------------------------------

def _seed_alumni(ctx):
    ctx.log("Creating alumni profiles...")
    from apps.alumni.models import AlumniProfile

    alumni_count = 0
    for i in range(50):
        campus_code = CAMPUS_CODES[i % 5]
        campus = ctx.campuses[campus_code]
        AlumniProfile.objects.get_or_create(
            institution=ctx.school,
            full_name=f"Alumni {i + 1:03d}",
            batch_year=2020 + (i % 6),
            defaults={
                "campus": campus,
                "email": f"alumni.{i + 1:03d}@example.test",
                "phone": f"0333{i:07d}",
                "occupation": random.choice(["Engineer", "Doctor", "Teacher", "Business", "Student"]),
                "city": random.choice(["Lahore", "Sialkot", "Islamabad", "Faisalabad", "Gujranwala"]),
                "is_active_member": random.random() > 0.3,
            },
        )
        alumni_count += 1
        ctx.count("alumni")

    ctx.ok(f"Alumni profiles: {alumni_count}")


# ---------------------------------------------------------------------------
# TRANSFERS
# ---------------------------------------------------------------------------

def _seed_transfers(ctx):
    ctx.log("Creating campus and student transfers...")
    from apps.students.models import CampusTransfer, Student
    from apps.accounts.models import StudentTransfer

    superuser = ctx.users.get("demo_superadmin")
    students = list(Student.objects.filter(institution=ctx.school, status="active")[:10])

    transfer_count = 0
    for i, stu in enumerate(students):
        from_ci = i % 5
        to_ci = (i + 1) % 5
        from_campus = ctx.campuses[CAMPUS_CODES[from_ci]]
        to_campus = ctx.campuses[CAMPUS_CODES[to_ci]]

        # Campus transfer in students app
        CampusTransfer.objects.get_or_create(
            student=stu,
            from_campus=from_campus,
            to_campus=to_campus,
            academic_year=ctx.active_year,
            defaults={
                "effective_date": date(2026, 12, 1),
                "reason": f"Demo transfer from {CAMPUS_CODES[from_ci]} to {CAMPUS_CODES[to_ci]}",
                "status": "completed" if i < 5 else "pending",
                "requested_by": superuser,
            },
        )
        transfer_count += 1

        # StudentTransfer in accounts app.
        # NOTE: StudentTransfer.objects is REPLACED at module level by a
        # TransferManager whose get_queryset() yields model=None (ERP bug).
        # Use _default_manager instead, which is the correctly-bound manager.
        StudentTransfer._default_manager.get_or_create(
            student=stu,
            from_campus=from_campus,
            to_campus=to_campus,
            defaults={
                "status": "approved" if i < 5 else "pending",
                "reason": f"Demo transfer: {CAMPUS_CODES[from_ci]} -> {CAMPUS_CODES[to_ci]}",
                "approved_by": superuser,
            },
        )

    ctx.ok(f"Transfers: {transfer_count}")
    ctx.count("transfers", transfer_count)


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

@transaction.atomic
def run(ctx):
    ctx.log("Part 5: integration (LMS, homework, discipline, events, comms, helpdesk, alumni, transfers).")
    base.base_users(ctx)
    _seed_lms(ctx)
    _seed_homework(ctx)
    _seed_discipline(ctx)
    _seed_events(ctx)
    _seed_announcements(ctx)
    _seed_messages(ctx)
    _seed_helpdesk(ctx)
    _seed_alumni(ctx)
    _seed_transfers(ctx)
    ctx.ok("Part 5 done.")
