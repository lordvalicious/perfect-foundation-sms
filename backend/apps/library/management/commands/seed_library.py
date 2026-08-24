import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.library.models import Book, BookCopy, BookIssue
from apps.schools.models import Campus
from apps.students.models import Enrollment
from apps.teachers.models import Teacher


class Command(BaseCommand):
    help = "Seed library with books, copies, and sample issues."

    BOOKS = [
        ("Islamic Studies Grade 5", "Maulana Abdul Karim", "textbook", "978-0-123456-01-1"),
        ("Mathematics Grade 6", "Dr. Aisha Khan", "textbook", "978-0-123456-02-8"),
        ("English Grammar Primer", "Sarah Williams", "textbook", "978-0-123456-03-5"),
        ("Pakistan Studies", "Prof. Tariq Rehman", "textbook", "978-0-123456-04-2"),
        ("General Science Grade 7", "Dr. Farooq Ahmed", "textbook", "978-0-123456-05-9"),
        ("Urdu Adab Anthology", "Mirza Ghalib", "literature", "978-0-123456-06-6"),
        ("The Quaid and Pakistan", "Stanley Wolpert", "history", "978-0-123456-07-3"),
        ("World Atlas for Students", "National Geographic", "geography", "978-0-123456-08-0"),
        ("Diary of a Young Girl", "Anne Frank", "fiction", "978-0-123456-09-7"),
        ("The Old Man and the Sea", "Ernest Hemingway", "fiction", "978-0-123456-10-3"),
        ("Animal Farm", "George Orwell", "fiction", "978-0-123456-11-0"),
        ("A Brief History of Time", "Stephen Hawking", "science", "978-0-123456-12-7"),
        ("Fundamentals of Physics", "Halliday & Resnick", "science", "978-0-123456-13-4"),
        ("Algebra for Beginners", "Schaum Series", "math", "978-0-123456-14-1"),
        ("Geometry Workbook", "Riaz Ahmad", "math", "978-0-123456-15-8"),
        ("Advanced English Composition", "John Seely", "reference", "978-0-123456-16-5"),
        ("Peer-e-Kamil", "UMERAH Ahmed", "fiction", "978-0-123456-17-2"),
        ("Seerat un Nabi", "Shibli Nomani", "non_fiction", "978-0-123456-18-9"),
        ("Chemistry Lab Manual", "Dr. Nasir Islam", "science", "978-0-123456-19-6"),
        ("计算机科学导论", "Ali Raza", "reference", "978-0-123456-20-2"),
        ("Hazaron Khwahishen", "Mirza Ghalib", "literature", "978-0-123456-21-9"),
        ("The White Tiger", "Aravind Adiga", "fiction", "978-0-123456-22-6"),
        ("Hamlet", "William Shakespeare", "literature", "978-0-123456-23-3"),
        ("Reasoning & Aptitude", "M.K. Pandey", "reference", "978-0-123456-24-0"),
        ("Geography of Pakistan", "Dr. Raza Khan", "geography", "978-0-123456-25-7"),
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\nSeeding library data...\n"))

        school = Campus.objects.values_list("school_id", flat=True).first()
        if not school:
            self.stderr.write(self.style.ERROR("No school found. Run seed setup first."))
            return

        campuses = list(Campus.objects.filter(status="active"))
        if not campuses:
            self.stderr.write(self.style.ERROR("No active campuses found."))
            return

        books_created = 0
        copies_created = 0
        issues_created = 0

        for title, author, category, isbn in self.BOOKS:
            book, created = Book.objects.get_or_create(
                isbn=isbn,
                defaults={
                    "title": title,
                    "author": author,
                    "category": category,
                    "publisher": "Pakistan Academy Press",
                    "publication_year": random.choice([2020, 2021, 2022, 2023, 2024, 2025]),
                    "total_copies": random.choice([3, 5, 8, 10]),
                    "description": f"{title} by {author}.",
                    "institution_id": school,
                },
            )
            if created:
                books_created += 1

            for i in range(book.total_copies):
                barcode = f"LIB-{book.pk:04d}-{i + 1:03d}"
                copy, copy_created = BookCopy.objects.get_or_create(
                    barcode=barcode,
                    defaults={
                        "book": book,
                        "status": "available",
                    },
                )
                if copy_created:
                    copies_created += 1

        for campus in campuses:
            campus_books = list(Book.objects.all())
            if not campus_books:
                continue

            enrollments = list(
                Enrollment.objects.filter(
                    campus=campus,
                    status="active",
                ).select_related("student")[:20]
            )

            teachers = list(
                Teacher.objects.filter(status="active")[:8]
            )

            available_copies = list(
                BookCopy.objects.filter(status="available")
            )

            if not available_copies:
                continue

            issue_copies = random.sample(
                available_copies,
                min(len(available_copies), random.randint(10, 20)),
            )

            for copy in issue_copies:
                if random.random() < 0.6 and enrollments:
                    borrower_type = "student"
                    borrower = random.choice(enrollments).student
                elif teachers:
                    borrower_type = "teacher"
                    borrower = random.choice(teachers)
                else:
                    continue

                days_ago = random.randint(1, 45)
                issue_date = date.today() - timedelta(days=days_ago)
                due_date = issue_date + timedelta(days=random.choice([7, 14, 21]))

                is_overdue = due_date < date.today() and random.random() < 0.3
                is_returned = not is_overdue and random.random() < 0.5

                issue, issue_created = BookIssue.objects.get_or_create(
                    book_copy=copy,
                    student=borrower if borrower_type == "student" else None,
                    teacher=borrower if borrower_type == "teacher" else None,
                    issue_date=issue_date,
                    defaults={
                        "due_date": due_date,
                        "return_date": (date.today() - timedelta(days=random.randint(1, 5))) if is_returned else None,
                        "fine": random.randint(50, 500) if is_overdue else 0,
                        "status": "returned" if is_returned else ("overdue" if is_overdue else "issued"),
                    },
                )
                if issue_created:
                    issues_created += 1

                    if is_returned:
                        copy.status = "available"
                        copy.save(update_fields=["status"])
                    else:
                        copy.status = "issued"
                        copy.save(update_fields=["status"])

        self.stdout.write(self.style.SUCCESS(f"Books created: {books_created}"))
        self.stdout.write(self.style.SUCCESS(f"Book copies created: {copies_created}"))
        self.stdout.write(self.style.SUCCESS(f"Book issues created: {issues_created}"))
        self.stdout.write(self.style.SUCCESS("\nLibrary seeding completed.\n"))
