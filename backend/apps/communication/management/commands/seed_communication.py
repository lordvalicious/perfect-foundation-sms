import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.communication.models import (
    Announcement,
    Message,
    Notification,
    NotificationPreference,
    SMSLog,
)
from apps.schools.models import Campus, School


class Command(BaseCommand):
    help = "Seed communication data: messages, announcements, notifications, SMS logs."

    ANNOUNCEMENT_TITLES = [
        "Parent-Teacher Meeting Schedule",
        "Annual Sports Day Announcement",
        "Mid-Term Examination Timetable",
        "School Holiday Notice - Eid Milan",
        "Fee Submission Deadline Reminder",
        "Science Fair 2026 Registration Open",
        "New Library Hours Starting Next Week",
        "School Bus Route Changes",
        "Staff Training Workshop",
        "Annual Day Celebration",
        "Summer Camp Registration",
        "Staff Meeting Notice",
        "Inter-School Cricket Tournament",
        "Student Council Elections",
        "Independence Day Celebration",
    ]

    ANNOUNCEMENT_MESSAGES = [
        "Dear parents and students, please note the upcoming schedule changes. Contact the office for details.",
        "We are pleased to announce our annual event. All students are encouraged to participate.",
        "The examination schedule has been finalized. Please check the notice board for your individual timetables.",
        "School will remain closed on the announced date. Regular classes will resume the following day.",
        "All fee payments must be submitted before the deadline to avoid late charges.",
        "Registration for the science fair is now open. Students from grades 5-10 are eligible.",
        "The library will operate on extended hours during the examination period.",
        "Bus routes have been updated. Please verify your child's pickup and drop-off times.",
        "All staff members are required to attend the professional development workshop.",
        "This is a reminder about our upcoming cultural event. Volunteers needed!",
    ]

    MESSAGE_SUBJECTS = [
        "Query about exam schedule",
        "Fee payment confirmation",
        "Leave application",
        "Result inquiry",
        "Transport route query",
        "Library book extension",
        "PTM feedback",
        "Assignment submission",
        "Student progress update",
        "Meeting request",
    ]

    MESSAGE_BODIES = [
        "Dear Sir/Madam, I would like to inquire about the upcoming examination schedule.",
        "This is to confirm that the fee payment has been submitted via online transfer.",
        "I am writing to request leave for my child due to health reasons.",
        "Could you please share the latest exam results for the midterm examinations?",
        "I wanted to confirm the bus route and timing for the new academic session.",
        "Is it possible to extend the due date for the library book I borrowed?",
        "Thank you for organizing the parent-teacher meeting. The feedback was very helpful.",
        "I have completed the assignment and uploaded it to the portal.",
        "Could you provide an update on my child's academic progress this term?",
        "I would like to schedule a meeting with the class teacher next week.",
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\nSeeding communication data...\n"))

        school = School.objects.first()
        if not school:
            self.stderr.write(self.style.ERROR("No school found."))
            return

        users = list(User.objects.filter(memberships__status="active").distinct()[:30])
        if not users:
            self.stderr.write(self.style.ERROR("No active users found."))
            return

        campuses = list(Campus.objects.filter(status="active"))

        messages_created = 0
        announcements_created = 0
        notifications_created = 0
        prefs_created = 0
        sms_created = 0

        for i in range(20):
            sender = random.choice(users)
            recipient = random.choice([u for u in users if u.id != sender.id])

            msg, created = Message.objects.get_or_create(
                institution=school,
                sender=sender,
                recipient=recipient,
                subject=random.choice(self.MESSAGE_SUBJECTS),
                defaults={
                    "body": random.choice(self.MESSAGE_BODIES),
                    "is_read": random.choice([True, False, False]),
                    "sent_at": timezone.now() - timedelta(days=random.randint(0, 30)),
                },
            )
            if created:
                messages_created += 1

                if random.random() < 0.3:
                    Message.objects.create(
                        institution=school,
                        sender=recipient,
                        recipient=sender,
                        subject=f"Re: {msg.subject}",
                        body="Thank you for your message. We will get back to you shortly.",
                        parent=msg,
                        is_read=random.choice([True, False]),
                        sent_at=timezone.now() - timedelta(days=random.randint(0, 28)),
                    )

        for i, title in enumerate(self.ANNOUNCEMENT_TITLES):
            campus = random.choice(campuses) if campuses else None

            ann, created = Announcement.objects.get_or_create(
                institution=school,
                title=title,
                defaults={
                    "message": self.ANNOUNCEMENT_MESSAGES[i % len(self.ANNOUNCEMENT_MESSAGES)],
                    "category": random.choice(["announcement", "notice"]),
                    "campus": campus,
                    "audience_roles": random.choice([
                        ["parent"],
                        ["teacher"],
                        ["student"],
                        ["parent", "teacher"],
                        [],
                    ]),
                    "status": random.choice(["published", "published", "draft"]),
                    "created_by": random.choice(users),
                    "published_at": timezone.now() - timedelta(days=random.randint(0, 60)),
                },
            )
            if created:
                announcements_created += 1

                if ann.status == "published":
                    target_users = random.sample(users, min(len(users), random.randint(3, 8)))
                    for user in target_users:
                        Notification.objects.create(
                            institution=school,
                            recipient=user,
                            announcement=ann,
                            title=ann.title,
                            message=ann.message[:200],
                            notification_type="announcement",
                            is_read=random.choice([True, False, False]),
                        )
                        notifications_created += 1

                        if random.random() < 0.2:
                            SMSLog.objects.create(
                                institution=school,
                                recipient=user,
                                phone_number=f"03{random.randint(10, 49)}-{random.randint(1000000, 9999999)}",
                                message=f"{ann.title}: {ann.message[:100]}",
                                status=random.choice(["sent", "sent", "failed"]),
                                announcement=ann,
                            )
                            sms_created += 1

        for user in users:
            _, created = NotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    "sms_enabled": random.choice([True, True, False]),
                    "email_enabled": random.choice([True, False]),
                    "push_enabled": True,
                    "attendance_alerts": True,
                    "payment_reminders": True,
                    "result_notifications": True,
                    "announcement_sms": random.choice([True, True, False]),
                },
            )
            if created:
                prefs_created += 1

        self.stdout.write(self.style.SUCCESS(f"Messages created: {messages_created}"))
        self.stdout.write(self.style.SUCCESS(f"Announcements created: {announcements_created}"))
        self.stdout.write(self.style.SUCCESS(f"Notifications created: {notifications_created}"))
        self.stdout.write(self.style.SUCCESS(f"Notification preferences created: {prefs_created}"))
        self.stdout.write(self.style.SUCCESS(f"SMS logs created: {sms_created}"))
        self.stdout.write(self.style.SUCCESS("\nCommunication seeding completed.\n"))
