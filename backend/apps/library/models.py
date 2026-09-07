from django.db import models

from apps.schools.models import Campus, School


class Book(models.Model):
    CATEGORY_CHOICES = [
        ("fiction", "Fiction"),
        ("non_fiction", "Non-Fiction"),
        ("textbook", "Textbook"),
        ("reference", "Reference"),
        ("science", "Science"),
        ("math", "Mathematics"),
        ("literature", "Literature"),
        ("history", "History"),
        ("geography", "Geography"),
        ("other", "Other"),
    ]

    institution = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="library_books_tenant",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_books",
    )
    author = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(
        max_length=32,
        blank=True,
    )
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.PositiveIntegerField(null=True, blank=True)
    category = models.CharField(
        max_length=32,
        choices=CATEGORY_CHOICES,
        default="other",
    )
    description = models.TextField(blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name_plural = "books"

    @property
    def available_copies(self):
        return self.copies.filter(status="available").count()

    @property
    def issued_copies(self):
        return self.copies.filter(status="issued").count()

    def __str__(self):
        return self.title


class BookCopy(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("issued", "Issued"),
        ("lost", "Lost"),
        ("damaged", "Damaged"),
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="copies",
    )
    barcode = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="available",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["barcode"]

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = f"{self.book.pk:04d}-{self.pk or ''}".rstrip("-")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book.title} ({self.barcode})"


class BookIssue(models.Model):
    STATUS_CHOICES = [
        ("issued", "Issued"),
        ("returned", "Returned"),
        ("overdue", "Overdue"),
    ]

    book_copy = models.ForeignKey(
        BookCopy,
        on_delete=models.CASCADE,
        related_name="issues",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="book_issues",
    )
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="book_issues",
    )
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fine = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="issued",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issue_date"]

    @property
    def borrower(self):
        if self.student_id:
            return self.student.full_name

        if self.teacher_id:
            return self.teacher.full_name

        return ""

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.student_id and self.teacher_id:
            raise ValidationError(
                "An issue must be assigned to either a student or a teacher, not both."
            )

        if not self.student_id and not self.teacher_id:
            raise ValidationError(
                "An issue must be assigned to a student or a teacher."
            )

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.pk is None:
            self.book_copy.status = "issued"
            self.book_copy.save(update_fields=["status"])

        super().save(*args, **kwargs)

    def return_copy(self, return_date=None):
        from django.utils import timezone

        self.return_date = return_date or timezone.localdate()
        self.status = "returned"
        self.book_copy.status = "available"
        self.book_copy.save(update_fields=["status"])
        self.save(update_fields=["return_date", "status"])

    def __str__(self):
        return f"{self.book_copy} -> {self.borrower}"


class BookReservation(models.Model):
    """Queue of patrons waiting for a book."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("available", "Available for Pickup"),
        ("fulfilled", "Fulfilled"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="book_reservations",
    )
    teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="book_reservations",
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="pending",
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    fulfilled_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fulfilled_reservations",
    )
    pickup_deadline = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["requested_at"]
        indexes = [
            models.Index(fields=["book", "status"]),
            models.Index(fields=["student", "status"]),
            models.Index(fields=["teacher", "status"]),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.student_id and self.teacher_id:
            raise ValidationError("Reservation must be for either a student or a teacher, not both.")
        if not self.student_id and not self.teacher_id:
            raise ValidationError("Reservation must be for a student or a teacher.")

    def __str__(self):
        borrower = ""
        if self.student_id:
            borrower = self.student.full_name
        elif self.teacher_id:
            borrower = self.teacher.full_name
        return f"{borrower} waiting for {self.book.title} [{self.status}]"

    @property
    def queue_position(self):
        """Return the position in queue (1-indexed)."""
        if self.status != "pending":
            return None
        return BookReservation.objects.filter(
            book=self.book,
            status="pending",
            requested_at__lt=self.requested_at,
        ).count() + 1

    def fulfill(self, user, pickup_hours=48):
        """Mark reservation as available for pickup."""
        from django.utils import timezone
        from datetime import timedelta

        self.status = "available"
        self.fulfilled_at = timezone.now()
        self.fulfilled_by = user
        self.pickup_deadline = timezone.now() + timedelta(hours=pickup_hours)
        self.save(update_fields=["status", "fulfilled_at", "fulfilled_by", "pickup_deadline"])

    def cancel(self):
        """Cancel the reservation."""
        self.status = "cancelled"
        self.save(update_fields=["status"])

    def expire(self):
        """Mark reservation as expired (pickup deadline passed)."""
        self.status = "expired"
        self.save(update_fields=["status"])
