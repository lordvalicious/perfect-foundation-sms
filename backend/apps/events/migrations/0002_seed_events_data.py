from datetime import timedelta
from django.utils import timezone
from django.db import migrations


def seed_events(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    School = apps.get_model("schools", "School")
    Campus = apps.get_model("schools", "Campus")
    Event = apps.get_model("events", "Event")
    EventAudience = apps.get_model("events", "EventAudience")
    EventRSVP = apps.get_model("events", "EventRSVP")

    if Event.objects.exists():
        return

    school = School.objects.first()
    if not school:
        return
    campus = Campus.objects.first()
    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not admin_user:
        return

    now = timezone.now()

    events_data = [
        {
            "title": "Parent-Teacher Meeting",
            "description": "Quarterly meeting between parents and teachers to discuss student progress and areas of improvement.",
            "location": "School Auditorium",
            "start_datetime": now + timedelta(days=21),
            "end_datetime": now + timedelta(days=21, hours=4),
            "status": "published",
            "audiences": [{"audience_type": "everyone"}],
        },
        {
            "title": "Annual Sports Day",
            "description": "Inter-class sports competition including track events, cricket, football, and relay races.",
            "location": "School Sports Ground",
            "start_datetime": now + timedelta(days=55),
            "end_datetime": now + timedelta(days=55, hours=6),
            "status": "published",
            "audiences": [{"audience_type": "students"}, {"audience_type": "teachers"}],
        },
        {
            "title": "Science Exhibition 2025",
            "description": "Students will showcase science projects and experiments. Parents and guests are welcome to attend.",
            "location": "School Science Lab Block",
            "start_datetime": now + timedelta(days=40),
            "end_datetime": now + timedelta(days=40, hours=3),
            "status": "published",
            "audiences": [{"audience_type": "everyone"}],
        },
        {
            "title": "Staff Training Workshop",
            "description": "Mandatory training workshop on new digital assessment tools and modern teaching methodologies.",
            "location": "Conference Room",
            "start_datetime": now + timedelta(days=14),
            "end_datetime": now + timedelta(days=15),
            "status": "published",
            "audiences": [{"audience_type": "teachers"}, {"audience_type": "staff"}],
        },
        {
            "title": "Annual Day Celebration",
            "description": "Annual cultural celebration with performances by students. Chief guest: renowned educationist.",
            "location": "School Auditorium",
            "start_datetime": now + timedelta(days=90),
            "end_datetime": now + timedelta(days=90, hours=5),
            "status": "draft",
            "audiences": [{"audience_type": "everyone"}],
        },
        {
            "title": "Career Counseling Session",
            "description": "Guidance session for Class 10 and 12 students about career options and university admissions.",
            "location": "Lecture Hall",
            "start_datetime": now + timedelta(days=30),
            "end_datetime": now + timedelta(days=30, hours=2),
            "status": "published",
            "audiences": [{"audience_type": "students"}],
        },
        {
            "title": "PTA Meeting",
            "description": "Parent-Teacher Association monthly meeting to discuss school improvement initiatives.",
            "location": "Conference Room",
            "start_datetime": now + timedelta(days=7),
            "end_datetime": now + timedelta(days=7, hours=1, minutes=30),
            "status": "published",
            "audiences": [{"audience_type": "role", "role": "parent"}],
        },
    ]

    all_users = list(User.objects.filter(is_active=True)[:10])

    for ed in events_data:
        audiences_data = ed.pop("audiences")
        event = Event.objects.create(school=school, campus=campus, created_by=admin_user, **ed)
        for aud in audiences_data:
            EventAudience.objects.create(event=event, **aud)

        rsvp_users = all_users[:5] if ed["status"] == "published" else []
        for i, u in enumerate(rsvp_users):
            response = "yes" if i < 3 else ("maybe" if i == 3 else "no")
            EventRSVP.objects.create(event=event, user=u, response=response)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("schools", "0001_initial"),
        ("events", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(seed_events, migrations.RunPython.noop),
    ]
