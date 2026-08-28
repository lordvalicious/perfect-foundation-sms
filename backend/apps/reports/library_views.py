"""Library Reports."""

from decimal import Decimal
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum, Avg, Max, Min
from django.utils import timezone
from rest_framework.response import Response

from apps.accounts.access import apply_campus_scope
from apps.accounts.permissions import IsAccountantRole
from apps.reports.base_views import AggregateReportView, BaseReportView
from apps.reports.utils import quantize, to_csv


class LibraryInventoryReportView(AggregateReportView):
    """Book inventory report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "library_inventory"
    model = "apps.library.models.Book"

    def get_base_queryset(self, request):
        from apps.library.models import Book
        return Book.objects.filter(status="active").select_related("campus", "category").prefetch_related("copies")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "campus_id")

        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category_id=category)

        return queryset

    def get_summary(self, queryset, request):
        total_books = queryset.count()
        total_copies = sum(b.copies.count() for b in queryset)
        available_copies = sum(b.copies.filter(status="available").count() for b in queryset)

        by_category = queryset.values("category__name").annotate(
            books=Count("id"),
            copies=Sum("copies__id"),
        )

        return {
            "total_books": total_books,
            "total_copies": total_copies,
            "available_copies": available_copies,
            "issued_copies": total_copies - available_copies,
            "by_category": list(by_category),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for book in queryset:
            copies = book.copies.all()
            total = copies.count()
            available = copies.filter(status="available").count()
            issued = copies.filter(status="issued").count()
            overdue = copies.filter(status="overdue").count()

            rows.append({
                "title": book.title,
                "author": book.author,
                "isbn": book.isbn,
                "category": book.category.name if book.category else "-",
                "campus": book.campus.name if book.campus else "-",
                "total_copies": total,
                "available": available,
                "issued": issued,
                "overdue": overdue,
                "publisher": book.publisher or "-",
                "year": book.publication_year or "-",
            })
        return rows


class AvailableBooksReportView(AggregateReportView):
    """Available books report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "library_available"
    model = "apps.library.models.BookCopy"

    def get_base_queryset(self, request):
        from apps.library.models import BookCopy
        return BookCopy.objects.filter(status="available").select_related("book__category", "book__campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "book__campus_id")
        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        by_category = queryset.values("book__category__name").annotate(count=Count("id"))
        by_campus = queryset.values("book__campus__name").annotate(count=Count("id"))

        return {
            "total_available": total,
            "by_category": list(by_category),
            "by_campus": list(by_campus),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for copy in queryset:
            rows.append({
                "title": copy.book.title,
                "author": copy.book.author,
                "isbn": copy.book.isbn,
                "category": copy.book.category.name if copy.book.category else "-",
                "campus": copy.book.campus.name if copy.book.campus else "-",
                "accession_number": copy.accession_number,
                "location": copy.location or "-",
            })
        return rows


class IssuedBooksReportView(AggregateReportView):
    """Currently issued books report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "library_issued"
    model = "apps.library.models.BookIssue"

    def get_base_queryset(self, request):
        from apps.library.models import BookIssue
        return BookIssue.objects.filter(status__in=["issued", "overdue"]).select_related(
            "book_copy__book__category", "book_copy__book__campus", "student", "teacher"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "book_copy__book__campus_id")

        today = timezone.now().date()
        overdue_only = request.query_params.get("overdue_only")
        if overdue_only == "true":
            queryset = queryset.filter(Q(status="overdue") | Q(status="issued", due_date__lt=today))

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        overdue = queryset.filter(Q(status="overdue") | Q(status="issued", due_date__lt=timezone.now().date())).count()

        return {
            "total_issued": total,
            "overdue": overdue,
            "not_overdue": total - overdue,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        today = timezone.now().date()
        for issue in queryset:
            is_overdue = issue.status == "overdue" or (issue.status == "issued" and issue.due_date < today)
            days_overdue = (today - issue.due_date).days if is_overdue else 0

            borrower = issue.student.full_name if issue.student else (issue.teacher.full_name if issue.teacher else "-")
            borrower_type = "Student" if issue.student else ("Teacher" if issue.teacher else "-")

            rows.append({
                "title": issue.book_copy.book.title,
                "author": issue.book_copy.book.author,
                "accession_number": issue.book_copy.accession_number,
                "borrower": borrower,
                "borrower_type": borrower_type,
                "borrower_admission": issue.student.admission_number if issue.student else "-",
                "issue_date": issue.issue_date,
                "due_date": issue.due_date,
                "days_overdue": days_overdue,
                "fine": quantize(issue.fine) if issue.fine else "0.00",
                "status": issue.get_status_display(),
            })
        return rows


class ReturnedBooksReportView(AggregateReportView):
    """Returned books report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "library_returned"
    model = "apps.library.models.BookIssue"

    def get_base_queryset(self, request):
        from apps.library.models import BookIssue
        return BookIssue.objects.filter(status="returned").select_related(
            "book_copy__book__category", "book_copy__book__campus", "student", "teacher"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "book_copy__book__campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(return_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(return_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        late_returns = queryset.filter(return_date__gt=F("due_date")).count() if hasattr(F, '__call__') else 0

        return {
            "total_returned": total,
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for issue in queryset:
            was_late = issue.return_date > issue.due_date
            days_late = (issue.return_date - issue.due_date).days if was_late else 0

            borrower = issue.student.full_name if issue.student else (issue.teacher.full_name if issue.teacher else "-")

            rows.append({
                "title": issue.book_copy.book.title,
                "author": issue.book_copy.book.author,
                "borrower": borrower,
                "issue_date": issue.issue_date,
                "due_date": issue.due_date,
                "return_date": issue.return_date,
                "days_late": days_late,
                "fine": quantize(issue.fine) if issue.fine else "0.00",
            })
        return rows


class OverdueBooksReportView(AggregateReportView):
    """Overdue books report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "library_overdue"
    model = "apps.library.models.BookIssue"

    def get_base_queryset(self, request):
        from apps.library.models import BookIssue
        today = timezone.now().date()
        return BookIssue.objects.filter(
            Q(status="overdue") | Q(status="issued", due_date__lt=today)
        ).select_related(
            "book_copy__book__category", "book_copy__book__campus", "student", "teacher"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "book_copy__book__campus_id")
        return queryset

    def get_summary(self, queryset, request):
        total = queryset.count()
        total_fines = sum(Decimal(str(i.fine)) for i in queryset if i.fine)

        return {
            "total_overdue": total,
            "total_fines": quantize(total_fines),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        today = timezone.now().date()
        for issue in queryset:
            days_overdue = (today - issue.due_date).days
            borrower = issue.student.full_name if issue.student else (issue.teacher.full_name if issue.teacher else "-")
            borrower_type = "Student" if issue.student else ("Teacher" if issue.teacher else "-")

            rows.append({
                "title": issue.book_copy.book.title,
                "author": issue.book_copy.book.author,
                "accession_number": issue.book_copy.accession_number,
                "borrower": borrower,
                "borrower_type": borrower_type,
                "issue_date": issue.issue_date,
                "due_date": issue.due_date,
                "days_overdue": days_overdue,
                "fine": quantize(issue.fine) if issue.fine else "0.00",
                "status": issue.get_status_display(),
            })
        return rows


class LibraryFinesReportView(AggregateReportView):
    """Library fines report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "library_fines"
    model = "apps.library.models.BookIssue"

    def get_base_queryset(self, request):
        from apps.library.models import BookIssue
        return BookIssue.objects.filter(fine__gt=0).select_related(
            "book_copy__book", "student", "teacher"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "book_copy__book__campus_id")

        status = request.query_params.get("status")
        if status == "paid":
            queryset = queryset.filter(fine_paid=True)
        elif status == "unpaid":
            queryset = queryset.filter(fine_paid=False)

        return queryset

    def get_summary(self, queryset, request):
        total_fines = sum(Decimal(str(i.fine)) for i in queryset if i.fine)
        paid_fines = sum(Decimal(str(i.fine)) for i in queryset if i.fine and i.fine_paid)
        unpaid_fines = total_fines - paid_fines

        return {
            "total_fines": quantize(total_fines),
            "paid_fines": quantize(paid_fines),
            "unpaid_fines": quantize(unpaid_fines),
            "total_records": queryset.count(),
        }

    def get_detail_rows(self, queryset, request):
        rows = []
        for issue in queryset:
            borrower = issue.student.full_name if issue.student else (issue.teacher.full_name if issue.teacher else "-")
            borrower_type = "Student" if issue.student else ("Teacher" if issue.teacher else "-")

            rows.append({
                "title": issue.book_copy.book.title,
                "borrower": borrower,
                "borrower_type": borrower_type,
                "due_date": issue.due_date,
                "return_date": issue.return_date,
                "fine": quantize(issue.fine),
                "paid": "Yes" if issue.fine_paid else "No",
                "status": issue.get_status_display(),
            })
        return rows


class LibraryActivitySummaryReportView(AggregateReportView):
    """Library activity summary."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "library_activity_summary"
    model = "apps.library.models.BookIssue"

    def get_base_queryset(self, request):
        from apps.library.models import BookIssue
        return BookIssue.objects.select_related(
            "book_copy__book", "student", "teacher", "book_copy__book__campus"
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "book_copy__book__campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        total_issues = queryset.count()
        returned = queryset.filter(status="returned").count()
        active = queryset.filter(status__in=["issued", "overdue"]).count()
        overdue = queryset.filter(status="overdue").count()

        fines_outstanding = sum(Decimal(str(i.fine)) for i in queryset if i.fine and not i.fine_paid)
        fines_collected = sum(Decimal(str(i.fine)) for i in queryset if i.fine and i.fine_paid)

        return {
            "total_issues": total_issues,
            "returned": returned,
            "active_issues": active,
            "marked_overdue": overdue,
            "fines_outstanding": quantize(fines_outstanding),
            "fines_collected": quantize(fines_collected),
        }

    def get_detail_rows(self, queryset, request):
        # Most borrowed books
        books = {}
        for issue in queryset:
            title = issue.book_copy.book.title
            if title not in books:
                books[title] = {"title": title, "issues": 0, "currently_out": 0}
            books[title]["issues"] += 1
            if issue.status in ["issued", "overdue"]:
                books[title]["currently_out"] += 1

        most_borrowed = sorted(books.values(), key=lambda x: x["issues"], reverse=True)[:15]

        return {"most_borrowed": most_borrowed}


class MostBorrowedBooksReportView(AggregateReportView):
    """Most borrowed books report."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "library_most_borrowed"
    model = "apps.library.models.BookIssue"

    def get_base_queryset(self, request):
        from apps.library.models import BookIssue
        return BookIssue.objects.select_related("book_copy__book", "book_copy__book__campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = apply_campus_scope(queryset, request, "book_copy__book__campus_id")

        date_from = request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)

        date_to = request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)

        return queryset

    def get_summary(self, queryset, request):
        return {"period": f"{request.query_params.get('date_from')} to {request.query_params.get('date_to')}"}

    def get_detail_rows(self, queryset, request):
        books = {}
        for issue in queryset:
            title = issue.book_copy.book.title
            if title not in books:
                books[title] = {
                    "title": title,
                    "author": issue.book_copy.book.author,
                    "category": issue.book_copy.book.category.name if issue.book_copy.book.category else "-",
                    "issues": 0,
                    "currently_out": 0,
                }
            books[title]["issues"] += 1
            if issue.status in ["issued", "overdue"]:
                books[title]["currently_out"] += 1

        rows = sorted(books.values(), key=lambda x: x["issues"], reverse=True)
        return rows[:50]


class StudentBorrowingHistoryReportView(BaseReportView):
    """Student borrowing history."""

    permission_classes = [IsAccountantRole]
    report_definition_key = "library_student_history"
    model = "apps.library.models.BookIssue"

    def get_base_queryset(self, request):
        from apps.library.models import BookIssue
        return BookIssue.objects.select_related("book_copy__book", "student", "book_copy__book__campus")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        student_id = request.query_params.get("student")
        if not student_id:
            return queryset.none()
        queryset = queryset.filter(student_id=student_id)
        queryset = apply_campus_scope(queryset, request, "book_copy__book__campus_id")
        return queryset.order_by("-issue_date")

    def get(self, request):
        queryset = self.get_queryset(request)
        student_id = request.query_params.get("student")

        if not student_id:
            return Response({"detail": "Student ID required"}, status=400)

        from apps.students.models import Student
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found"}, status=404)

        rows = []
        for issue in queryset:
            rows.append({
                "title": issue.book_copy.book.title,
                "author": issue.book_copy.book.author,
                "issue_date": issue.issue_date,
                "due_date": issue.due_date,
                "return_date": issue.return_date,
                "status": issue.get_status_display(),
                "fine": quantize(issue.fine) if issue.fine else "0.00",
            })

        return Response({
            "student": {
                "admission_number": student.admission_number,
                "name": student.full_name,
            },
            "history": rows,
        })


class TeacherBorrowingHistoryReportView(StudentBorrowingHistoryReportView):
    """Teacher borrowing history."""
    report_definition_key = "library_teacher_history"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        teacher_id = request.query_params.get("teacher")
        if not teacher_id:
            return queryset.none()
        queryset = queryset.filter(teacher_id=teacher_id)
        queryset = apply_campus_scope(queryset, request, "book_copy__book__campus_id")
        return queryset.order_by("-issue_date")

    def get(self, request):
        queryset = self.get_queryset(request)
        teacher_id = request.query_params.get("teacher")

        if not teacher_id:
            return Response({"detail": "Teacher ID required"}, status=400)

        from apps.teachers.models import Teacher
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return Response({"detail": "Teacher not found"}, status=404)

        rows = []
        for issue in queryset:
            rows.append({
                "title": issue.book_copy.book.title,
                "author": issue.book_copy.book.author,
                "issue_date": issue.issue_date,
                "due_date": issue.due_date,
                "return_date": issue.return_date,
                "status": issue.get_status_display(),
                "fine": quantize(issue.fine) if issue.fine else "0.00",
            })

        return Response({
            "teacher": {
                "employee_number": teacher.employee_number,
                "name": teacher.full_name,
            },
            "history": rows,
        })