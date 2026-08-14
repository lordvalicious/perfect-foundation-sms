import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.finance.models import FeeStructure
from apps.schools.models import AcademicYear, Campus, Class

ay = AcademicYear.objects.get(name="2026-2027")
print("=== CAMPUSES / CLASSES / STRUCTURE COVERAGE ===")
for campus in Campus.objects.order_by("id"):
    classes = Class.objects.filter(unit__campus=campus).order_by("id")
    print(f"{campus.name}: {classes.count()} classes")
    for cls in classes:
        cats = list(
            FeeStructure.objects.filter(
                campus=campus, class_obj=cls, academic_year=ay
            ).values_list("category__name", "amount")
        )
        label = ", ".join(f"{n}={a}" for n, a in cats) if cats else "NO STRUCTURE"
        print(f"   {cls.name}: {label}")

print("=== ACADEMIC YEARS ===")
for y in AcademicYear.objects.all():
    print(f"  {y.id}: {y.name} active={y.is_current}")
