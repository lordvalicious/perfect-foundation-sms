from datetime import date, timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Role, StaffProfile
from apps.accounts.test_access import make_user
from apps.schools.models import (
    AcademicUnit,
    AcademicYear,
    Campus,
    Class,
    School,
    Section,
)
from apps.students.models import Enrollment, Guardian, Student

from .models import (
    EmailLog,
    Notification,
    NotificationDispatch,
    NotificationPreference,
    QueuedNotification,
    SMSLog,
)

from . import notification_queue


def _sms_item(phone="03000000001"):
    return notification_queue.enqueue(
        "sms",
        kind="test_kind",
        reference="ref-1",
        to_address=phone,
        body="Hello parent",
    )


class NotificationQueueTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Queue School")

    def test_enqueue_creates_queued_row(self):
        item = _sms_item()
        self.assertIsNotNone(item)
        self.assertEqual(item.status, "queued")
        self.assertEqual(item.channel, "sms")
        self.assertEqual(item.attempts, 0)
        self.assertEqual(item.max_attempts, 3)

    def test_enqueue_dedupes_open_row(self):
        first = _sms_item()
        second = _sms_item()
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(QueuedNotification.objects.count(), 1)

    def test_enqueue_dedupes_against_dispatch_ledger(self):
        NotificationDispatch.objects.create(
            kind="test_kind",
            reference="ref-1",
            channel="sms",
            recipient="03000000001",
        )
        self.assertIsNone(_sms_item())

    def test_unknown_channel_rejected(self):
        with self.assertRaises(ValueError):
            notification_queue.enqueue("carrier_pigeon", body="hi")

    def test_process_delivers_sms_writes_log_and_dispatch(self):
        item = _sms_item()
        summary = notification_queue.process_due_notifications()

        self.assertEqual(summary["sent"], 1)
        item.refresh_from_db()
        self.assertEqual(item.status, "sent")
        self.assertIsNotNone(item.processed_at)

        log = SMSLog.objects.get()
        self.assertEqual(log.phone_number, "03000000001")
        self.assertEqual(log.status, "sent")

        self.assertTrue(
            NotificationDispatch.objects.filter(
                kind="test_kind",
                reference="ref-1",
                channel="sms",
            ).exists()
        )

    def test_process_skips_future_scheduled_items(self):
        item = _sms_item()
        item.scheduled_at = timezone.now() + timedelta(hours=2)
        item.next_attempt_at = timezone.now() + timedelta(hours=2)
        item.save()

        summary = notification_queue.process_due_notifications()

        self.assertEqual(summary["processed"], 0)
        item.refresh_from_db()
        self.assertEqual(item.status, "queued")

    def test_process_retries_then_fails_permanently(self):
        item = notification_queue.enqueue(
            "sms",
            to_address="03000000002",
            body="Retry me",
            max_attempts=2,
        )
        self.assertIsNotNone(item)

        with mock.patch(
            "apps.communication.notification_queue.deliver_sms",
            return_value=(False, "provider down"),
        ):
            first = notification_queue.process_due_notifications()

        self.assertEqual(first["failed"], 1)
        item.refresh_from_db()
        self.assertEqual(item.status, "queued")
        self.assertEqual(item.attempts, 1)
        self.assertGreater(item.next_attempt_at, timezone.now())

        # Force the retry to run now.
        item.next_attempt_at = timezone.now() - timedelta(minutes=1)
        item.save(update_fields=["next_attempt_at", "updated_at"])

        with mock.patch(
            "apps.communication.notification_queue.deliver_sms",
            return_value=(False, "provider down"),
        ):
            second = notification_queue.process_due_notifications()

        self.assertEqual(second["permanent_failures"], 1)
        item.refresh_from_db()
        self.assertEqual(item.status, "failed")
        self.assertEqual(item.attempts, 2)
        self.assertEqual(item.last_error, "provider down")

    def test_process_delivers_in_app_notification(self):
        user = make_user("parent-one", Role.PARENT, self.school)
        guardian = Guardian.objects.create(
            user=user,
            name="Parent One",
            relationship="Mother",
            phone="03000000003",
        )
        item = notification_queue.enqueue(
            "in_app",
            kind="system",
            recipient=user,
            subject="Welcome",
            body="Have a nice day",
            institution=self.school,
        )
        self.assertIsNotNone(item)

        summary = notification_queue.process_due_notifications()

        self.assertEqual(summary["sent"], 1)
        note = Notification.objects.get(recipient=user)
        self.assertEqual(note.title, "Welcome")
        self.assertEqual(note.notification_type, "system")
        self.assertEqual(note.institution, self.school)
        # guarding guardian.user link consistency
        self.assertEqual(guardian.user, user)

    def test_send_now_sent(self):
        outcome, error = notification_queue.send_now(
            "sms",
            kind="hot",
            reference="r-sent",
            to_address="03000000004",
            body="Instant",
        )
        self.assertEqual(outcome, "sent")
        self.assertEqual(error, "")
        self.assertEqual(SMSLog.objects.filter(status="sent").count(), 1)

    def test_send_now_skipped_when_already_dispatched(self):
        NotificationDispatch.objects.create(
            kind="hot",
            reference="r-skip",
            channel="sms",
            recipient="03000000005",
        )
        outcome, error = notification_queue.send_now(
            "sms",
            kind="hot",
            reference="r-skip",
            to_address="03000000005",
            body="Dup",
        )
        self.assertEqual(outcome, "skipped")
        self.assertEqual(QueuedNotification.objects.count(), 0)

    def test_send_now_failed_records_and_retries(self):
        with mock.patch(
            "apps.communication.notification_queue.deliver_email",
            return_value=(False, "smtp down"),
        ):
            outcome, error = notification_queue.send_now(
                "email",
                to_address="parent@test.edu",
                subject="Hi",
                body="Hello",
            )
        self.assertEqual(outcome, "failed")
        self.assertEqual(error, "smtp down")
        self.assertEqual(EmailLog.objects.filter(status="failed").count(), 1)
        item = QueuedNotification.objects.get()
        self.assertEqual(item.attempts, 1)
        self.assertEqual(item.status, "queued")

    def test_send_now_in_app_creates_notification(self):
        user = make_user("parent-two", Role.PARENT, self.school)
        notification_queue.send_now(
            "in_app",
            kind="system",
            recipient=user,
            subject="Hello",
            body="World",
        )
        self.assertTrue(Notification.objects.filter(recipient=user).exists())

    def test_retry_failed_requeues(self):
        item = _sms_item()
        item.status = "failed"
        item.last_error = "boom"
        item.save()

        count = notification_queue.retry_failed()

        self.assertEqual(count, 1)
        item.refresh_from_db()
        self.assertEqual(item.status, "queued")
        self.assertEqual(item.last_error, "")

    def test_queue_status_breakdown(self):
        _sms_item()
        summary = notification_queue.queue_status()
        self.assertEqual(summary["queued"], 1)
        self.assertEqual(summary["sent"], 0)
        self.assertEqual(summary["due_now"], 1)


class ProcessNotificationsCronTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Cron School")
        self.user = make_user("cron-user", Role.TEACHER, self.school)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _enqueue_sms(self):
        notification_queue.enqueue(
            "sms",
            to_address="03000000006",
            body="Cron send",
        )

    def test_cron_requires_secret_for_non_global_user(self):
        self._enqueue_sms()
        with mock.patch.dict("os.environ", {"CRON_SECRET": "swordfish"}):
            response = self.client.get(
                "/api/communication/cron/process-notifications/"
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cron_with_secret_processes_due(self):
        self._enqueue_sms()
        with mock.patch.dict("os.environ", {"CRON_SECRET": "swordfish"}):
            response = self.client.get(
                "/api/communication/cron/process-notifications/",
                HTTP_AUTHORIZATION="Bearer swordfish",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["sent"], 1)
        self.assertEqual(data["queue"]["queued"], 0)

    def test_global_user_may_run_without_secret(self):
        super_admin = make_user(
            "root-cron", Role.SUPER_ADMIN, self.school
        )
        self.client.force_authenticate(super_admin)
        self._enqueue_sms()

        response = self.client.get(
            "/api/communication/cron/process-notifications/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["sent"], 1)


class ResultPublishedNotificationTests(TestCase):
    def _build_fixture(self):
        school = School.objects.create(name="Results School")
        campus = Campus.objects.create(school=school, name="Main")
        unit = AcademicUnit.objects.create(campus=campus, name="Primary")
        class_obj = Class.objects.create(unit=unit, name="Grade 1")
        section = Section.objects.create(class_obj=class_obj, name="A")
        year = AcademicYear.objects.create(
            school=school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        )

        from apps.exams.models import Exam

        exam = Exam.objects.create(
            name="Annual",
            exam_type="annual",
            academic_year=year,
            campus=campus,
            class_obj=class_obj,
            start_date=date(2027, 3, 1),
            end_date=date(2027, 3, 5),
        )

        guardian_user = make_user("rp-guardian", Role.PARENT, school)
        guardian = Guardian.objects.create(
            user=guardian_user,
            name="Guardian",
            relationship="Father",
            phone="03000000007",
            email="guardian@test.edu",
        )
        student = Student.objects.create(
            admission_number="ADM-RP-001",
            first_name="Rita",
            last_name="Rao",
            gender="female",
            primary_campus=campus,
            guardian=guardian,
        )
        Enrollment.objects.create(
            student=student,
            academic_year=year,
            campus=campus,
            class_obj=class_obj,
            section=section,
        )

        from apps.reportcards.models import ReportCard

        return school, guardian_user, student, exam, ReportCard

    def _clear_email_contacts(self, student):
        guardian = student.guardian
        guardian.email = ""
        guardian.save()
        if guardian.user:
            guardian.user.email = ""
            guardian.user.save()

    def test_publish_enqueues_result_sms_for_guardian(self):
        school, guardian_user, student, exam, ReportCard = (
            self._build_fixture()
        )
        self._clear_email_contacts(student)
        card = ReportCard.objects.create(student=student, exam=exam)

        card.publish(user=guardian_user)

        items = QueuedNotification.objects.filter(kind="result_published")
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().channel, "sms")
        self.assertEqual(items.first().to_address, "03000000007")
        self.assertEqual(
            items.first().reference,
            f"result:{card.pk}",
        )

    def test_publish_enqueues_email_when_enabled(self):
        school, guardian_user, student, exam, ReportCard = (
            self._build_fixture()
        )
        NotificationPreference.objects.create(
            user=guardian_user,
            email_enabled=True,
        )
        card = ReportCard.objects.create(student=student, exam=exam)

        card.publish(user=guardian_user)

        channels = set(
            QueuedNotification.objects.filter(
                kind="result_published"
            ).values_list("channel", flat=True)
        )
        self.assertEqual(
            channels,
            {"sms", "email"},
        )

    def test_publish_honors_disabled_result_preference(self):
        school, guardian_user, student, exam, ReportCard = (
            self._build_fixture()
        )
        NotificationPreference.objects.create(
            user=guardian_user,
            result_notifications=False,
        )
        card = ReportCard.objects.create(student=student, exam=exam)

        card.publish(user=guardian_user)

        self.assertEqual(
            QueuedNotification.objects.filter(
                kind="result_published"
            ).count(),
            0,
        )

    def test_publish_without_guardian_phone_enqueues_nothing(self):
        school, guardian_user, student, exam, ReportCard = (
            self._build_fixture()
        )
        self._clear_email_contacts(student)
        student.guardian.phone = ""
        student.guardian.alternate_phone = ""
        student.guardian.save()
        card = ReportCard.objects.create(student=student, exam=exam)

        card.publish(user=guardian_user)

        self.assertEqual(
            QueuedNotification.objects.filter(
                kind="result_published"
            ).count(),
            0,
        )