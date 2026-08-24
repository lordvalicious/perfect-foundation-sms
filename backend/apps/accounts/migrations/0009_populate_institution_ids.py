"""Populate institution_id for all models that received it in the prior migration.

The derivation strategy (in priority order):
1. Direct campus FK  → campus.school_id
2. Direct academic_year FK → academic_year.school_id
3. Membership FK → membership.institution_id
4. Linked model that already has institution (e.g. Student via guardian or membership)
5. Fallback: first active School (for truly standalone reference data like GradeScale)
"""

from django.db import migrations


def populate_institution_field(apps, schema_editor, model_name, app_label, derive_fn, fallback=True):
    """Run a bulk UPDATE ... SET institution_id = <derived> for rows where institution IS NULL."""
    Model = apps.get_model(app_label, model_name)
    db_alias = schema_editor.connection.alias

    # Skip if model has no institution field (defensive)
    institution_field = None
    for f in Model._meta.get_fields():
        if getattr(f, "name", None) == "institution":
            institution_field = f
            break
    if institution_field is None:
        return

    qs = Model.objects.using(db_alias).filter(institution__isnull=True)
    total = qs.count()
    if total == 0:
        return

    updated = 0
    for obj in qs.iterator(chunk_size=500):
        new_id = derive_fn(obj)
        if new_id is not None:
            Model.objects.using(db_alias).filter(pk=obj.pk).update(institution_id=new_id)
            updated += 1

    if fallback and updated < total:
        School = apps.get_model("schools", "School")
        default_school = School.objects.using(db_alias).order_by("pk").first()
        if default_school is not None:
            remaining = Model.objects.using(db_alias).filter(institution__isnull=True)
            remaining.update(institution_id=default_school.pk)
            updated += remaining.count()

    print(f"  {app_label}.{model_name}: {updated}/{total} rows populated")


def forwards(apps, schema_editor):
    School = apps.get_model("schools", "School")
    db_alias = schema_editor.connection.alias

    # Ensure at least one school exists
    if School.objects.using(db_alias).count() == 0:
        School.objects.using(db_alias).create(name="Default Institution")

    # -----------------------------------------------------------------------
    # schools app
    # -----------------------------------------------------------------------
    print("Populating schools app...")

    def derive_subject(obj):
        return None  # Standalone; will be handled by fallback

    populate_institution_field(apps, schema_editor, "Subject", "schools", derive_subject)

    # -----------------------------------------------------------------------
    # students app
    # -----------------------------------------------------------------------
    print("Populating students app...")

    def derive_student(obj):
        if obj.primary_campus_id:
            return obj.primary_campus.school_id
        if obj.membership_id:
            return obj.membership.institution_id
        if obj.user_id:
            membership = getattr(obj.user, "memberships", None)
            if membership:
                m = membership.filter(status="active").first()
                if m:
                    return m.institution_id
        return None

    def derive_guardian(obj):
        # Derive from linked students
        if obj.user_id:
            membership = getattr(obj.user, "memberships", None)
            if membership:
                m = membership.filter(status="active").first()
                if m:
                    return m.institution_id
        return None

    def derive_admission_application(obj):
        if obj.campus_id:
            return obj.campus.school_id
        return None

    def derive_student_document(obj):
        if obj.student_id:
            return obj.student.institution_id
        return None

    def derive_student_leave(obj):
        if obj.student_id:
            return obj.student.institution_id
        return None

    def derive_lifecycle_event(obj):
        if obj.student_id:
            return obj.student.institution_id
        if obj.from_campus_id:
            return obj.from_campus.school_id
        if obj.to_campus_id:
            return obj.to_campus.school_id
        return None

    populate_institution_field(apps, schema_editor, "Guardian", "students", derive_guardian)
    populate_institution_field(apps, schema_editor, "Student", "students", derive_student)
    populate_institution_field(apps, schema_editor, "AdmissionApplication", "students", derive_admission_application)
    populate_institution_field(apps, schema_editor, "StudentDocument", "students", derive_student_document)
    populate_institution_field(apps, schema_editor, "StudentLeaveRequest", "students", derive_student_leave)
    populate_institution_field(apps, schema_editor, "StudentLifecycleEvent", "students", derive_lifecycle_event)

    # -----------------------------------------------------------------------
    # teachers app
    # -----------------------------------------------------------------------
    print("Populating teachers app...")

    def derive_teacher(obj):
        if obj.membership_id:
            return obj.membership.institution_id
        if obj.user_id:
            membership = getattr(obj.user, "memberships", None)
            if membership:
                m = membership.filter(status="active").first()
                if m:
                    return m.institution_id
        return None

    populate_institution_field(apps, schema_editor, "Teacher", "teachers", derive_teacher)

    # -----------------------------------------------------------------------
    # accounts app (StaffProfile, StaffAttendance, StaffLeave)
    # -----------------------------------------------------------------------
    print("Populating accounts app...")

    def derive_staff_profile(obj):
        if obj.membership_id:
            return obj.membership.institution_id
        if obj.user_id:
            membership = getattr(obj.user, "memberships", None)
            if membership:
                m = membership.filter(status="active").first()
                if m:
                    return m.institution_id
        return None

    def derive_staff_attendance(obj):
        if obj.staff_id:
            return obj.staff.institution_id
        return None

    def derive_staff_leave(obj):
        if obj.staff_id:
            return obj.staff.institution_id
        return None

    populate_institution_field(apps, schema_editor, "StaffProfile", "accounts", derive_staff_profile)
    populate_institution_field(apps, schema_editor, "StaffAttendance", "accounts", derive_staff_attendance)
    populate_institution_field(apps, schema_editor, "StaffLeave", "accounts", derive_staff_leave)

    # -----------------------------------------------------------------------
    # finance app
    # -----------------------------------------------------------------------
    print("Populating finance app...")

    def derive_fee_category(obj):
        return None  # Standalone reference; fallback

    def derive_invoice(obj):
        if obj.enrollment_id:
            return obj.enrollment.campus.school_id
        if obj.student_id and obj.student.primary_campus_id:
            return obj.student.primary_campus.school_id
        return None

    def derive_payment(obj):
        if obj.invoice_id:
            return derive_invoice(obj.invoice)
        return None

    def derive_concession(obj):
        if obj.invoice_id:
            return derive_invoice(obj.invoice)
        return None

    def derive_payment_reversal(obj):
        if obj.payment_id:
            return derive_payment(obj.payment)
        return None

    def derive_payment_refund(obj):
        if obj.payment_id:
            return derive_payment(obj.payment)
        return None

    populate_institution_field(apps, schema_editor, "FeeCategory", "finance", derive_fee_category)
    populate_institution_field(apps, schema_editor, "Invoice", "finance", derive_invoice)
    populate_institution_field(apps, schema_editor, "Payment", "finance", derive_payment)
    populate_institution_field(apps, schema_editor, "Concession", "finance", derive_concession)
    populate_institution_field(apps, schema_editor, "PaymentReversal", "finance", derive_payment_reversal)
    populate_institution_field(apps, schema_editor, "PaymentRefund", "finance", derive_payment_refund)

    # -----------------------------------------------------------------------
    # library app
    # -----------------------------------------------------------------------
    print("Populating library app...")

    def derive_book(obj):
        if obj.campus_id:
            return obj.campus.school_id
        return None

    populate_institution_field(apps, schema_editor, "Book", "library", derive_book)

    # -----------------------------------------------------------------------
    # inventory app
    # -----------------------------------------------------------------------
    print("Populating inventory app...")

    def derive_asset_category(obj):
        return None  # Standalone reference; fallback

    def derive_supplier(obj):
        return None  # Standalone reference; fallback

    def derive_asset(obj):
        if obj.campus_id:
            return obj.campus.school_id
        return None

    populate_institution_field(apps, schema_editor, "AssetCategory", "inventory", derive_asset_category)
    populate_institution_field(apps, schema_editor, "Supplier", "inventory", derive_supplier)
    populate_institution_field(apps, schema_editor, "Asset", "inventory", derive_asset)

    # -----------------------------------------------------------------------
    # transport app
    # -----------------------------------------------------------------------
    print("Populating transport app...")

    def derive_vehicle(obj):
        if obj.campus_id:
            return obj.campus.school_id
        return None

    def derive_driver(obj):
        if obj.campus_id:
            return obj.campus.school_id
        return None

    def derive_route(obj):
        if obj.campus_id:
            return obj.campus.school_id
        return None

    populate_institution_field(apps, schema_editor, "Vehicle", "transport", derive_vehicle)
    populate_institution_field(apps, schema_editor, "Driver", "transport", derive_driver)
    populate_institution_field(apps, schema_editor, "Route", "transport", derive_route)

    # -----------------------------------------------------------------------
    # communication app
    # -----------------------------------------------------------------------
    print("Populating communication app...")

    def derive_message(obj):
        # Messages are between two users; use sender's institution
        if obj.sender_id:
            user = obj.sender
            membership = user.memberships.filter(status="active").first()
            if membership:
                return membership.institution_id
        return None

    def derive_announcement(obj):
        if obj.campus_id:
            return obj.campus.school_id
        return None

    def derive_notification(obj):
        return None  # Will be derived from announcement or fallback

    def derive_sms_log(obj):
        return None  # Will be derived from announcement or fallback

    def derive_message_template(obj):
        if obj.created_by_id:
            user = obj.created_by
            membership = user.memberships.filter(status="active").first()
            if membership:
                return membership.institution_id
        return None

    populate_institution_field(apps, schema_editor, "Message", "communication", derive_message)
    populate_institution_field(apps, schema_editor, "Announcement", "communication", derive_announcement)
    populate_institution_field(apps, schema_editor, "Notification", "communication", derive_notification)
    populate_institution_field(apps, schema_editor, "SMSLog", "communication", derive_sms_log)
    populate_institution_field(apps, schema_editor, "MessageTemplate", "communication", derive_message_template)

    # -----------------------------------------------------------------------
    # reportcards app
    # -----------------------------------------------------------------------
    print("Populating reportcards app...")

    def derive_grade_scale(obj):
        return None  # Standalone reference; fallback

    populate_institution_field(apps, schema_editor, "GradeScale", "reportcards", derive_grade_scale)

    # -----------------------------------------------------------------------
    # timetable app
    # -----------------------------------------------------------------------
    print("Populating timetable app...")

    def derive_period(obj):
        return None  # Standalone reference; fallback

    populate_institution_field(apps, schema_editor, "Period", "timetable", derive_period)

    # -----------------------------------------------------------------------
    # audit app
    # -----------------------------------------------------------------------
    print("Populating audit app...")

    def derive_audit_log(obj):
        if obj.user_id:
            user = obj.user
            membership = user.memberships.filter(status="active").first()
            if membership:
                return membership.institution_id
        return None

    populate_institution_field(apps, schema_editor, "AuditLog", "audit", derive_audit_log)


def backwards(apps, schema_editor):
    pass  # No reverse needed; institution FK stays nullable


class Migration(migrations.Migration):

    dependencies = [
        ("schools", "0008_add_institution_to_all_models"),
        ("students", "0009_add_institution_to_all_models"),
        ("teachers", "0007_add_institution_to_all_models"),
        ("accounts", "0008_add_institution_to_all_models"),
        ("finance", "0005_add_institution_to_all_models"),
        ("library", "0004_add_institution_to_all_models"),
        ("inventory", "0004_add_institution_to_all_models"),
        ("transport", "0004_add_institution_to_all_models"),
        ("communication", "0006_add_institution_to_all_models"),
        ("reportcards", "0004_add_institution_to_all_models"),
        ("timetable", "0002_add_institution_to_all_models"),
        ("audit", "0005_add_institution_to_all_models"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
