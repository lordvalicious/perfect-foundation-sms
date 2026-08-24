from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.schools.models import Campus, Class, School, Section


class Message(models.Model):
    """A direct message between two users, with reply threading.

    ``parent`` links a reply to its root message. Deletes are soft per
    side (``sender_deleted`` / ``recipient_deleted``) so the other party
    keeps their copy of the conversation.
    """

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )

    sender = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )

    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="received_messages",
    )

    subject = models.CharField(max_length=200)

    body = models.TextField(blank=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
    )

    is_read = models.BooleanField(default=False)

    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    sent_at = models.DateTimeField(default=timezone.now)

    sender_deleted = models.BooleanField(default=False)

    recipient_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-sent_at"]

        indexes = [
            models.Index(
                fields=["recipient", "recipient_deleted", "is_read"],
                name="msg_recipient_box_idx",
            ),
            models.Index(
                fields=["sender", "sender_deleted"],
                name="msg_sender_box_idx",
            ),
            models.Index(
                fields=["parent"],
                name="msg_parent_idx",
            ),
        ]

    def __str__(self):
        return f"{self.sender_id} -> {self.recipient_id}: {self.subject}"


class Announcement(models.Model):
    """A notice or announcement targeted at a specific audience.

    ``audience_roles`` is a JSON list of role slugs (e.g.
    ``["parent", "teacher"]``). ``campus``/``class_obj``/``section``
    further narrow the audience. When left blank the announcement
    targets everyone with a matching role.
    """

    CATEGORY_CHOICES = [
        ("announcement", "Announcement"),
        ("notice", "Notice"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="announcements",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=200)
    message = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="announcement",
    )

    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
    )

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
    )

    audience_roles = models.JSONField(
        default=list,
        blank=True,
        help_text="Role slugs this announcement is for.",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_announcements",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.class_obj_id and self.campus_id:
            if self.class_obj.unit.campus_id != self.campus_id:
                raise ValidationError(
                    {"class_obj": "Class must belong to the selected campus."}
                )

        if self.section_id and self.class_obj_id:
            if self.section.class_obj_id != self.class_obj_id:
                raise ValidationError(
                    {"section": "Section must belong to the selected class."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()

        if (
            self.status == "published"
            and self.published_at is None
        ):
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def target_user_ids(self):
        """Resolve the user ids that should receive this announcement."""
        User = get_user_model()

        roles = self.audience_roles or []

        if self.class_obj_id:
            from apps.teachers.models import TeacherAssignment
            from apps.students.models import Enrollment

            enrollments = Enrollment.objects.filter(
                class_obj=self.class_obj,
                status="active",
            )

            if self.campus_id:
                enrollments = enrollments.filter(
                    campus_id=self.campus_id
                )

            if self.section_id:
                enrollments = enrollments.filter(
                    section_id=self.section_id
                )

            student_ids = list(
                enrollments.values_list("student_id", flat=True)
            )

            user_ids = set()

            if "student" in roles or not roles:
                user_ids.update(
                    User.objects.filter(
                        student_profile_id__in=student_ids
                    ).values_list("id", flat=True)
                )

            if "parent" in roles or not roles:
                from apps.students.models import Student

                guardian_ids = (
                    Student.objects
                    .filter(id__in=student_ids)
                    .values_list("guardian_id", flat=True)
                )

                user_ids.update(
                    User.objects.filter(
                        guardian_profile_id__in=guardian_ids
                    ).values_list("id", flat=True)
                )

            if "teacher" in roles or not roles:
                teacher_ids = (
                    TeacherAssignment.objects
                    .filter(
                        class_obj=self.class_obj,
                        status="active",
                    )
                    .values_list("teacher_id", flat=True)
                )

                user_ids.update(
                    User.objects.filter(
                        teacher_profile_id__in=teacher_ids
                    ).values_list("id", flat=True)
                )

            return list(user_ids)

        memberships = (
            User.objects
            .filter(memberships__status="active")
            .distinct()
        )

        if roles:
            from apps.accounts.models import RoleAssignment

            memberships = memberships.filter(
                role_assignments__role__in=roles
            )

        if self.campus_id:
            from apps.students.models import Enrollment

            enrollment_students = Enrollment.objects.filter(
                campus_id=self.campus_id,
                status="active",
            ).values_list("student_id", flat=True)

            student_user_ids = set(
                User.objects.filter(
                    student_profile_id__in=enrollment_students
                ).values_list("id", flat=True)
            )

            guardian_ids = (
                Enrollment.objects
                .filter(
                    campus_id=self.campus_id,
                    status="active",
                )
                .values_list("student__guardian_id", flat=True)
            )

            guardian_user_ids = set(
                User.objects.filter(
                    guardian_profile_id__in=guardian_ids
                ).values_list("id", flat=True)
            )

            return list(
                student_user_ids | guardian_user_ids
            )

        return list(
            memberships.values_list("id", flat=True)
        )

    def notify(self):
        """Create in-app notifications and send SMS to target users."""
        from .models import Notification, NotificationPreference

        user_ids = self.target_user_ids()

        existing = set(
            Notification.objects.filter(
                announcement=self,
            ).values_list("recipient_id", flat=True)
        )

        new_ids = [
            user_id
            for user_id in user_ids
            if user_id not in existing
        ]

        Notification.objects.bulk_create(
            [
                Notification(
                    recipient_id=user_id,
                    announcement=self,
                    title=self.title,
                    message=self.message,
                    notification_type="announcement",
                )
                for user_id in new_ids
            ]
        )

        sms_users = User.objects.filter(
            id__in=user_ids,
            notification_preferences__sms_enabled=True,
            notification_preferences__announcement_sms=True,
        ).values_list("id", "phone")

        from .sms import send_sms as _send_sms

        for uid, phone in sms_users:
            if phone and phone.strip():
                ok, err = _send_sms(phone, f"{self.title}\n\n{self.message}")
                SMSLog.objects.create(
                    recipient_id=uid,
                    phone_number=phone.strip(),
                    message=f"{self.title}\n\n{self.message}",
                    status="sent" if ok else "failed",
                    error=err or "",
                    announcement=self,
                )

        return len(new_ids)

    def __str__(self):
        return self.title


class Notification(models.Model):
    """A single in-app notification for one user."""

    TYPE_CHOICES = [
        ("announcement", "Announcement"),
        ("payment", "Payment"),
        ("result", "Result"),
        ("attendance", "Attendance"),
        ("system", "System"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="system",
    )

    link = models.CharField(max_length=255, blank=True)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["recipient", "is_read"],
                name="notif_recipient_read_idx",
            )
        ]

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"


class SMSLog(models.Model):
    """Log of every SMS sent through the system."""

    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="sms_logs_tenant",
        null=True,
        blank=True,
    )

    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_logs",
    )

    phone_number = models.CharField(max_length=20)

    message = models.TextField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="queued",
    )

    error = models.TextField(blank=True)

    sent_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_sms_logs",
    )

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_logs",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["status"],
                name="sms_status_idx",
            ),
            models.Index(
                fields=["recipient"],
                name="sms_recipient_idx",
            ),
        ]

    def __str__(self):
        return f"SMS to {self.phone_number}: {self.message[:40]}"


class NotificationPreference(models.Model):
    """Per-user notification channel preferences."""

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )

    sms_enabled = models.BooleanField(
        default=True,
        help_text="Receive SMS notifications.",
    )

    email_enabled = models.BooleanField(
        default=False,
        help_text="Receive email notifications.",
    )

    push_enabled = models.BooleanField(
        default=True,
        help_text="Receive in-app push notifications.",
    )

    attendance_alerts = models.BooleanField(
        default=True,
        help_text="SMS on attendance absence.",
    )

    payment_reminders = models.BooleanField(
        default=True,
        help_text="SMS on fee payment reminders.",
    )

    result_notifications = models.BooleanField(
        default=True,
        help_text="SMS when exam results are published.",
    )

    announcement_sms = models.BooleanField(
        default=True,
        help_text="SMS for important announcements.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification prefs for {self.user.username}"


class MessageTemplate(models.Model):
    CHANNEL_CHOICES = [
        ("sms", "SMS"),
        ("email", "Email"),
        ("both", "Both"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="message_templates",
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=200)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default="sms")
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"

    def render(self, context=None):
        text = self.body
        if context:
            for key, value in context.items():
                text = text.replace("{" + key + "}", str(value))
        return text