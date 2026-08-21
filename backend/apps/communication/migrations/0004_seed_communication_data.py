from django.db import migrations


def seed_communication(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    School = apps.get_model("schools", "School")
    Campus = apps.get_model("schools", "Campus")
    Announcement = apps.get_model("communication", "Announcement")
    Message = apps.get_model("communication", "Message")
    Notification = apps.get_model("communication", "Notification")

    if Announcement.objects.exists():
        return

    school = School.objects.first()
    if not school:
        return
    campus = Campus.objects.first()
    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not admin_user:
        return

    users = list(User.objects.filter(is_active=True)[:10])
    if len(users) < 2:
        return

    announcements_data = [
        {
            "title": "Parent-Teacher Meeting Scheduled",
            "message": "A parent-teacher meeting has been scheduled for Saturday, September 13, 2025 from 9:00 AM to 1:00 PM. All parents are requested to attend.",
            "category": "announcement",
            "status": "published",
            "audience_roles": ["parent", "teacher"],
            "created_by": admin_user,
        },
        {
            "title": "Mid-Term Examination Schedule Released",
            "message": "The mid-term examination schedule for all classes has been released. Students should check the notice board for their individual timetables. Exams will begin from September 22, 2025.",
            "category": "announcement",
            "status": "published",
            "audience_roles": ["student", "teacher"],
            "created_by": admin_user,
        },
        {
            "title": "Annual Sports Day Notice",
            "message": "The annual sports day will be held on October 15, 2025. Students interested in participating should register with their PE teacher before October 1.",
            "category": "notice",
            "status": "published",
            "audience_roles": ["student"],
            "created_by": admin_user,
        },
        {
            "title": "Library Book Return Reminder",
            "message": "All students with pending library books are requested to return them by September 10, 2025. Overdue fines will be applied after the deadline.",
            "category": "notice",
            "status": "published",
            "audience_roles": ["student", "parent"],
            "created_by": admin_user,
        },
        {
            "title": "Holiday Notice - Eid Milad un-Nabi",
            "message": "The school will remain closed on September 17, 2025 on account of Eid Milad un-Nabi. Regular classes will resume on September 18.",
            "category": "announcement",
            "status": "published",
            "audience_roles": [],
            "created_by": admin_user,
        },
        {
            "title": "Fee Submission Deadline Extended",
            "message": "The deadline for Q1 fee submission has been extended to September 20, 2025. A late fee of Rs. 500 will be charged after this date.",
            "category": "notice",
            "status": "published",
            "audience_roles": ["parent"],
            "created_by": admin_user,
        },
        {
            "title": "Science Exhibition Preparations",
            "message": "All science teachers are requested to submit their exhibition project proposals by September 5, 2025. The exhibition will be held in the school auditorium.",
            "category": "announcement",
            "status": "draft",
            "audience_roles": ["teacher"],
            "created_by": admin_user,
        },
    ]

    for a in announcements_data:
        Announcement.objects.create(**a)

    message_data = [
        {"sender": users[0], "recipient": users[1], "subject": "Regarding Fee Structure", "body": "Could you please share the updated fee structure for the upcoming term?", "is_read": True},
        {"sender": users[1], "recipient": users[0], "subject": "Re: Regarding Fee Structure", "body": "The updated fee structure has been emailed to you. Please check your inbox.", "is_read": True},
        {"sender": users[0], "recipient": users[2], "subject": "Transport Route Inquiry", "body": "I wanted to ask about the bus route timings for Route A.", "is_read": False},
        {"sender": users[3], "recipient": users[1], "subject": "Student Progress Report", "body": "When will the progress reports be available for review?", "is_read": True},
        {"sender": users[1], "recipient": users[3], "subject": "Re: Student Progress Report", "body": "Progress reports will be shared after the parent-teacher meeting.", "is_read": False},
        {"sender": users[4], "recipient": users[0], "subject": "Library Membership", "body": "How can I get a library membership card for my child?", "is_read": True},
    ]

    for m in message_data:
        Message.objects.create(**m)

    notification_data = [
        {"recipient": users[0], "title": "Fee Payment Received", "message": "Your payment of Rs. 45,000 for Q1 fees has been received successfully.", "notification_type": "payment", "is_read": True},
        {"recipient": users[1], "title": "Exam Results Published", "message": "Monthly test results for Class 10 have been published. Please check.", "notification_type": "result", "is_read": False},
        {"recipient": users[2], "title": "Attendance Alert", "message": "Your child was marked absent today. Please contact the school if this is an error.", "notification_type": "attendance", "is_read": False},
        {"recipient": users[0], "title": "New Announcement", "message": "A new announcement has been posted: Parent-Teacher Meeting Scheduled", "notification_type": "announcement", "is_read": True},
        {"recipient": users[3], "title": "System Maintenance", "message": "The student portal will be under maintenance on September 8 from 2:00 AM to 5:00 AM.", "notification_type": "system", "is_read": False},
        {"recipient": users[1], "title": "Fee Payment Reminder", "message": "This is a reminder that Q1 fee payment is due by September 20, 2025.", "notification_type": "payment", "is_read": False},
        {"recipient": users[0], "title": "Holiday Upcoming", "message": "School will remain closed on September 17 for Eid Milad un-Nabi.", "notification_type": "announcement", "is_read": True},
        {"recipient": users[4], "title": "Book Overdue Notice", "message": "You have 2 overdue library books. Please return them to avoid fines.", "notification_type": "system", "is_read": False},
    ]

    for n in notification_data:
        Notification.objects.create(**n)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("schools", "0001_initial"),
        ("communication", "0003_notificationpreference_smslog"),
    ]
    operations = [
        migrations.RunPython(seed_communication, migrations.RunPython.noop),
    ]
