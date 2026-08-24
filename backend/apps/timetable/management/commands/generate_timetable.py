"""Generate a weekly timetable for a campus.

    python manage.py generate_timetable --campus "Junior Campus" --lessons 5
"""

from django.core.management.base import BaseCommand, CommandError

from apps.schools.models import AcademicYear, Campus
from apps.timetable.generator import generate_timetable


class Command(BaseCommand):
    help = (
        "Auto-generate conflict-free weekly timetable entries from "
        "existing teacher assignments. Replaces current entries for "
        "the campus unless --no-replace is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--campus",
            required=True,
            help="Campus id or exact name.",
        )
        parser.add_argument(
            "--academic-year",
            type=int,
            default=None,
            help="AcademicYear id (default: latest active).",
        )
        parser.add_argument(
            "--lessons",
            type=int,
            default=5,
            help="Weekly periods per subject per section (default 5).",
        )
        parser.add_argument(
            "--days",
            default="monday,tuesday,wednesday,thursday,friday",
            help="Comma-separated teaching days.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Random seed for reproducible layouts.",
        )
        parser.add_argument(
            "--no-replace",
            action="store_true",
            help="Keep existing entries instead of replacing them.",
        )

    def handle(self, *args, **options):
        campus_raw = options["campus"]

        campus = None

        if str(campus_raw).isdigit():
            campus = Campus.objects.filter(pk=campus_raw).first()

        if campus is None:
            campus = Campus.objects.filter(
                name__iexact=str(campus_raw)
            ).first()

        if campus is None:
            raise CommandError(f"Campus '{campus_raw}' not found.")

        if options["academic_year"]:
            year = AcademicYear.objects.filter(
                pk=options["academic_year"]
            ).first()
        else:
            year = (
                AcademicYear.objects.filter(
                    school=campus.school, status="active"
                ).order_by("-start_date").first()
            or AcademicYear.objects.filter(
                school=campus.school
            ).order_by("-start_date").first()
        )

        if year is None:
            raise CommandError("No academic year found for this school.")

        days = [d.strip().lower() for d in options["days"].split(",") if d.strip()]

        try:
            stats = generate_timetable(
                campus=campus,
                academic_year=year,
                lessons_per_subject=options["lessons"],
                days=days,
                replace=not options["no_replace"],
                seed=options["seed"],
            )
        except ValueError as exc:
            raise CommandError(str(exc))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTimetable generated for {campus.name} ({year.name})"
            )
        )
        self.stdout.write(f"  Sections covered : {stats['sections']}/{stats['sections_total']}")
        self.stdout.write(f"  Entries created  : {stats['created']}")
        self.stdout.write(f"  Unplaced lessons : {stats['unplaced_count']}")

        for row in stats["unplaced"][:10]:
            self.stdout.write(
                self.style.WARNING(
                    f"    {row['section']} - {row['subject']}: {row['reason']}"
                )
            )
