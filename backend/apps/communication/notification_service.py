"""Automated parent notifications: fee reminders and absence alerts.

Both jobs are idempotent via NotificationDispatch — a guardian is
messaged once per reference (e.g. once per week per student for fee
reminders, once per day for an absence) no matter how often the cron
fires.
"""

from datetime import timedelta

from django.utils import timezone

FEE_REMINDER_MIN_DAYS = 3
FEE_REMINDER_REPEAT_DAYS = 7


def _school_branding_for(obj_school):
    """Return {'display', 'email_from_name', 'email_from_address'}."""
    from apps.schools.branding_context import get_school_branding

    if obj_school is None:
        return {
            "display": "School",
            "email_from_name": "",
            "email_from_address": "",
        }

    b = get_school_branding(obj_school)

    return {
        "display": b["short_name"] or b["name"],
        "email_from_name": b["email_from_name"] or b["name"],
        "email_from_address": b["email_from_address"],
    }
ABSENCE_ALERT_PREFIX = "[Absence]"


def _prefs_allow(user, flag):
    """Check a guardian's channel preference; default allow."""
    if user is None:
        return True

    prefs = getattr(user, "notification_preferences", None)

    if prefs is None:
        return True

    return bool(getattr(prefs, flag, True))


def _guardian_contacts(student):
    """Return ({'sms': [phones], 'email': [emails]}, pref_user)."""
    guardian = student.guardian

    phones = set()
    emails = set()

    if guardian is None:
        return {"sms": [], "email": []}, None

    for phone in (guardian.phone, guardian.alternate_phone):
        if phone and phone.strip():
            phones.add(phone.strip())

    user = getattr(guardian, "user", None)

    email = (getattr(guardian, "email", "") or "").strip()

    if email:
        emails.add(email)

    if user and (user.email or "").strip():
        emails.add(user.email.strip())

    return {"sms": list(phones), "email": list(emails)}, user


def _dispatch_exists(kind, reference, channel):
    from .models import NotificationDispatch

    return NotificationDispatch.objects.filter(
        kind=kind,
        reference=reference,
        channel=channel,
    ).exists()


def _record_dispatch(kind, reference, channel, recipient):
    from .models import NotificationDispatch

    NotificationDispatch.objects.create(
        kind=kind,
        reference=reference,
        channel=channel,
        recipient=recipient,
    )


def send_fee_reminders(
    min_days_overdue=FEE_REMINDER_MIN_DAYS,
    repeat_days=FEE_REMINDER_REPEAT_DAYS,
    dry_run=False,
):
    """Consolidated weekly reminder per student with overdue fees."""
    from apps.finance.models import Invoice
    from .email_service import send_email_message
    from .models import SMSLog
    from .sms import send_sms

    today = timezone.localdate()
    cutoff = today - timedelta(days=min_days_overdue)
    week_key = f"{today.isocalendar().year}-W{today.isocalendar().week:02d}"

    invoices = (
        Invoice.objects
        .filter(
            status__in=["issued", "partial", "overdue"],
            due_date__lt=cutoff,
        )
        .exclude(due_date__isnull=True)
        .prefetch_related(
            "items",
            "payments",
            "payments__refunds",
            "payments__reversals",
            "concessions",
        )
        .select_related("student", "student__guardian")
    )

    per_student = {}

    for invoice in invoices:
        balance = invoice.balance

        if balance <= 0:
            continue

        entry = per_student.get(invoice.student_id)

        if entry is None:
            per_student[invoice.student_id] = {
                "student": invoice.student,
                "total": balance,
                "oldest_due": invoice.due_date,
                "count": 1,
            }
        else:
            entry["total"] += balance
            entry["count"] += 1

            if invoice.due_date < entry["oldest_due"]:
                entry["oldest_due"] = invoice.due_date

    sent = {"sms": 0, "email": 0}
    skipped = 0
    failed = []
    preview = []

    for entry in sorted(
        per_student.values(),
        key=lambda item: -item["total"],
    ):
        student = entry["student"]
        reference = f"fee:{student.id}:{week_key}"

        contacts, pref_user = _guardian_contacts(student)

        campus = (
            student.enrollments.filter(status="active")
            .select_related("campus__school")
            .first()
        )
        school = campus.campus.school if campus else None
        brand = _school_branding_for(school)

        amount = int(entry["total"])
        sms_text = (
            f"[{brand['display']}] Fee reminder: Rs {amount:,} outstanding "
            f"for {student.full_name} "
            f"({entry['count']} invoice(s), oldest due "
            f"{entry['oldest_due']:%d %b}). Kindly clear at your earliest."
        )

        email_body = (
            f"Dear Guardian,\n\nThis is a reminder that outstanding "
            f"school fees for {student.full_name} currently total "
            f"Rs {amount:,} across {entry['count']} invoice(s), the "
            f"oldest due on {entry['oldest_due']:%d %B %Y}.\n\n"
            f"Please clear the dues at your earliest convenience.\n\n"
            f"- {brand['display']}"
        )

        if dry_run:
            preview.append({
                "student": student.full_name,
                "outstanding": str(entry["total"]),
                "sms_to": contacts["sms"],
                "email_to": contacts["email"],
            })
            continue

        # SMS channel
        if contacts["sms"] and _prefs_allow(pref_user, "payment_reminders"):
            phone = contacts["sms"][0]

            if not _dispatch_exists("fee_reminder", reference, "sms"):
                ok, err = send_sms(phone, sms_text)

                SMSLog.objects.create(
                    phone_number=phone,
                    message=sms_text,
                    status="sent" if ok else "failed",
                    error=err or "",
                )

                if ok:
                    _record_dispatch(
                        "fee_reminder", reference, "sms", phone
                    )
                    sent["sms"] += 1
                else:
                    failed.append(f"SMS {phone}: {err}")
            else:
                skipped += 1
        elif not contacts["sms"]:
            skipped += 1

        # Email channel
        email_target = contacts["email"][0] if contacts["email"] else ""

        if email_target and _prefs_allow(pref_user, "payment_reminders"):
            if not _dispatch_exists(
                "fee_reminder", reference, "email"
            ):
                from_name = brand["email_from_name"] or None
                from_address = brand["email_from_address"] or None

                ok, err = send_email_message(
                    email_target,
                    f"Fee reminder - {student.full_name}",
                    email_body,
                    from_name=from_name,
                    from_address=from_address,
                )

                from .models import EmailLog

                EmailLog.objects.create(
                    recipient_email=email_target,
                    subject=f"Fee reminder - {student.full_name}",
                    body=email_body,
                    status="sent" if ok else "failed",
                    error=err or "",
                )

                if ok:
                    _record_dispatch(
                        "fee_reminder", reference, "email", email_target
                    )
                    sent["email"] += 1
                else:
                    failed.append(f"Email {email_target}: {err}")
            else:
                skipped += 1

    result = {
        "students_with_dues": len(per_student),
        "sent": sent,
        "skipped_already_notified": skipped,
        "failed": failed[:10],
    }

    if dry_run:
        result["dry_run"] = True
        result["would_notify"] = preview[:25]

    return result


def send_absence_alerts(dry_run=False):
    """Same-day alert to guardians of students marked absent."""
    from apps.attendance.models import Attendance
    from .email_service import send_email_message
    from .models import SMSLog
    from .sms import send_sms

    today = timezone.localdate()
    reference_day = f"absence:{today.isoformat()}"

    absentees = (
        Attendance.objects
        .filter(date=today, status="absent")
        .select_related(
            "student", "student__guardian", "class_obj",
            "campus__school",
        )
    )

    sent = {"sms": 0, "email": 0}
    skipped = 0
    failed = []
    preview = []

    for record in absentees:
        student = record.student
        contacts, pref_user = _guardian_contacts(student)

        brand = _school_branding_for(record.campus.school)

        sms_text = (
            f"[{brand['display']}] Attendance notice: {student.full_name} "
            f"was marked ABSENT today ({today:%d %b}). If this is "
            f"unexpected, please contact the school office."
        )

        if dry_run:
            preview.append({
                "student": student.full_name,
                "class": record.class_obj.name,
                "sms_to": contacts["sms"],
            })
            continue

        if contacts["sms"] and _prefs_allow(pref_user, "attendance_alerts"):
            phone = contacts["sms"][0]

            if not _dispatch_exists(
                "absence_alert", reference_day, "sms"
            ):
                ok, err = send_sms(phone, sms_text)

                SMSLog.objects.create(
                    phone_number=phone,
                    message=sms_text,
                    status="sent" if ok else "failed",
                    error=err or "",
                )

                if ok:
                    _record_dispatch(
                        "absence_alert", reference_day, "sms", phone
                    )
                    sent["sms"] += 1
                else:
                    failed.append(f"SMS {phone}: {err}")
            else:
                skipped += 1
        elif not contacts["sms"]:
            skipped += 1

        email_target = contacts["email"][0] if contacts["email"] else ""

        if email_target and _prefs_allow(pref_user, "attendance_alerts"):
            ref = f"{reference_day}:email"

            if not _dispatch_exists("absence_alert", ref, "email"):
                from_name = brand["email_from_name"] or None
                from_address = brand["email_from_address"] or None

                ok, err = send_email_message(
                    email_target,
                    f"Absence notice - {student.full_name}",
                    sms_text,
                    from_name=from_name,
                    from_address=from_address,
                )

                from .models import EmailLog

                EmailLog.objects.create(
                    recipient_email=email_target,
                    subject=f"Absence notice - {student.full_name}",
                    body=sms_text,
                    status="sent" if ok else "failed",
                    error=err or "",
                )

                if ok:
                    _record_dispatch(
                        "absence_alert", ref, "email", email_target
                    )
                    sent["email"] += 1
                else:
                    failed.append(f"Email {email_target}: {err}")
            else:
                skipped += 1

    result = {
        "date": today.isoformat(),
        "absentees": len(absentees),
        "sent": sent,
        "skipped_already_notified": skipped,
        "failed": failed[:10],
    }

    if dry_run:
        result["dry_run"] = True
        result["would_notify"] = preview[:25]

    return result
