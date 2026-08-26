"""Email broadcast + log views. Mirrors the SMS views' targeting."""

import time

from django.contrib.auth import get_user_model
from django.core.mail import get_connection
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.access import is_global
from apps.students.models import Student

from .email_service import email_configured, send_email_message
from .models import EmailLog

User = get_user_model()


def _resolve_user_ids(role, campus_id):
    qs = User.objects.filter(memberships__status="active").distinct()

    if role == "all":
        return list(qs.values_list("id", flat=True))

    if role == "parent":
        users = User.objects.filter(guardian_profile__isnull=False)

        if campus_id:
            student_ids = Student.objects.filter(
                enrollment__campus_id=campus_id,
                enrollment__status="active",
            ).values_list("id", flat=True)
            users = users.filter(
                guardian_profile__students__id__in=student_ids
            )

        return list(users.values_list("id", flat=True))

    if role == "student":
        users = qs.filter(student_profile__isnull=False)

        if campus_id:
            users = users.filter(
                student_profile__enrollment__campus_id=campus_id,
                student_profile__enrollment__status="active",
            )

        return list(users.values_list("id", flat=True))

    if role == "teacher":
        users = qs.filter(teacher_profile__isnull=False)

        if campus_id:
            users = users.filter(
                teacher_profile__primary_campus_id=campus_id
            )

        return list(users.values_list("id", flat=True))

    return []


class EmailBroadcastView(APIView):
    """POST to send an email to selected recipients.

    Body mirrors the SMS broadcast:
        subject: str (required)
        message: str (required)
        recipient_ids: list[int] (optional) - specific user ids
        role: str (optional) - all | parent | student | teacher
        campus_id: int (optional)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"configured": email_configured()})

    def post(self, request):
        user = request.user

        if not is_global(user):
            return Response(
                {"detail": "Only admin users can send email."},
                status=status.HTTP_403_FORBIDDEN,
            )

        subject = (request.data.get("subject") or "").strip()
        message = (request.data.get("message") or "").strip()

        if not subject or not message:
            return Response(
                {"detail": "Subject and message are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipient_ids = request.data.get("recipient_ids") or []
        role = (request.data.get("role") or "").strip()
        campus_id = request.data.get("campus_id")

        if recipient_ids:
            target_users = User.objects.filter(id__in=recipient_ids)
        elif role:
            ids = _resolve_user_ids(role, campus_id)
            target_users = User.objects.filter(id__in=ids)
        else:
            return Response(
                {
                    "detail": (
                        "Provide recipient_ids or a role "
                        "(all/parent/student/teacher)."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        emails = set()

        for value in target_users.exclude(email="").values_list(
            "email", flat=True
        ):
            emails.add(value.strip())

        # Guardians of the targeted students also receive a copy.
        if role in ("parent", "all"):
            guardian_emails = User.objects.filter(
                guardian_profile_id__isnull=False
            ).values_list("email", flat=True)

            for value in guardian_emails:
                if value and value.strip():
                    emails.add(value.strip())

        if not emails:
            return Response(
                {"detail": "No recipients with email addresses found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sent = 0
        failed = 0
        skipped = 0

        # One shared SMTP session + a hard time budget so the request
        # always answers with JSON inside the serverless time limit.
        deadline = time.monotonic() + 8.0
        connection = None

        if email_configured():
            connection = get_connection(fail_silently=False, timeout=10)

        for email in sorted(emails):
            if time.monotonic() > deadline:
                skipped += 1
                ok, err = False, "Skipped: time budget reached, send again."
            else:
                ok, err = send_email_message(
                    email, subject, message, connection=connection
                )

            EmailLog.objects.create(
                recipient_email=email,
                subject=subject,
                body=message,
                status="sent" if ok else "failed",
                error=err or "",
                sent_by=user,
            )

            if ok:
                sent += 1
            else:
                failed += 1

        return Response({
            "sent": sent,
            "failed": failed,
            "skipped": skipped,
            "total_recipients": len(emails),
            "configured": True,
        })


class EmailLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = EmailLog.objects.all()[:200]
        data = [
            {
                "id": log.id,
                "recipient_email": log.recipient_email,
                "subject": log.subject,
                "status": log.status,
                "error": log.error,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
        return Response(data)
