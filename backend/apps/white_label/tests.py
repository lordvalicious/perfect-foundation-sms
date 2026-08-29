from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import InstitutionMembership, Role, RoleAssignment, User
from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, School, Section, Subject, SubjectOffering
from apps.students.models import Enrollment, Guardian, Student
from apps.teachers.models import Teacher, TeacherAssignment
from apps.transport.models import Route, RouteStop, TransportAssignment

from .models import WhiteLabelBranding, SchoolSettings, DomainMapping, WhiteLabelAuditLog


class WhiteLabelTestCase(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="White Label School")
        self.campus = Campus.objects.create(school=self.school, name="Main Campus")
        self.unit = AcademicUnit.objects.create(campus=self.campus, name="Primary")
        self.class_obj = Class.objects.create(unit=self.unit, name="Grade 7")
        self.section = Section.objects.create(class_obj=self.class_obj, name="A")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        )
        self.subject = Subject.objects.create(name="English", code="ENG-WL", institution=self.school)
        # SubjectOffering created only when needed by specific tests

        guardian = Guardian.objects.create(
            name="Parent", relationship="Father", phone="03000000000"
        )
        self.student = Student.objects.create(
            admission_number="ADM-WL-001",
            first_name="Ali",
            gender="male",
            guardian=guardian,
        )
        Enrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            section=self.section,
        )

        self.teacher_user = User.objects.create_user(
            username="teacher_wl", email="teacher_wl@test.edu", password="TestPass123!"
        )
        membership = InstitutionMembership.objects.create(user=self.teacher_user, institution=self.school)
        RoleAssignment.objects.create(membership=membership, role=Role.TEACHER)
        self.teacher = Teacher.objects.create(
            employee_number="T-WL-001",
            first_name="Ayesha",
            last_name="Khan",
            gender="female",
            user=self.teacher_user,
            membership=membership,
            institution=self.school,
        )
        TeacherAssignment.objects.create(
            teacher=self.teacher,
            campus=self.campus,
            class_obj=self.class_obj,
            section=self.section,
            subject=self.subject,
            academic_year=self.year,
            role="class_teacher",
            status="active",
        )

        self.parent_user = User.objects.create_user(
            username="parent_wl", email="parent_wl@test.edu", password="TestPass123!"
        )
        membership = InstitutionMembership.objects.create(user=self.parent_user, institution=self.school)
        RoleAssignment.objects.create(membership=membership, role=Role.PARENT)
        self.guardian = Guardian.objects.create(
            name="Parent Guardian", relationship="Father", phone="03000000000", user=self.parent_user
        )
        self.child = Student.objects.create(
            admission_number="ADM-C-001",
            first_name="Child",
            gender="female",
            guardian=self.guardian,
        )
        Enrollment.objects.create(
            student=self.child,
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            section=self.section,
        )

    def _make_user(self, username, role):
        user = User.objects.create_user(
            username=username, email=f"{username}@test.edu", password="TestPass123!"
        )
        membership = InstitutionMembership.objects.create(user=user, institution=self.school)
        RoleAssignment.objects.create(membership=membership, role=role)
        return user

    def _authed_client(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client


class WhiteLabelBrandingTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Branding School")
        self.branding = WhiteLabelBranding.objects.create(
            school=self.school,
            primary_color="#FF0000",
            secondary_color="#00FF00",
            accent_color="#0000FF",
            login_title="Custom Login",
            login_subtitle="Custom subtitle",
            subdomain="custom",
            maintenance_mode=True,
            maintenance_message="Under maintenance",
        )

    def test_branding_creation(self):
        self.assertEqual(self.branding.school, self.school)
        self.assertEqual(self.branding.primary_color, "#FF0000")
        self.assertEqual(self.branding.login_title, "Custom Login")
        self.assertEqual(self.branding.subdomain, "custom")
        self.assertTrue(self.branding.maintenance_mode)

    def test_css_variables_generation(self):
        css_vars = self.branding.css_variables
        self.assertEqual(css_vars["--color-primary"], "#FF0000")
        self.assertEqual(css_vars["--color-secondary"], "#00FF00")
        self.assertEqual(css_vars["--color-accent"], "#0000FF")
        self.assertIn("--font-family", css_vars)
        self.assertIn("--font-size-base", css_vars)
        self.assertIn("--border-radius-md", css_vars)
        self.assertIn("--spacing-unit", css_vars)

    def test_to_dict_serialization(self):
        data = self.branding.to_dict()
        self.assertEqual(data["id"], self.branding.id)
        self.assertEqual(data["colors"]["primary"], "#FF0000")
        self.assertEqual(data["typography"]["font_family"], "Inter, system-ui, sans-serif")
        self.assertEqual(data["border_radius"]["md"], 8)
        self.assertEqual(data["spacing_unit"], 4)
        self.assertEqual(data["login"]["title"], "Custom Login")
        self.assertEqual(data["seo"]["meta_title"], "")

    def test_subdomain_auto_generation(self):
        school = School.objects.create(name="Auto Subdomain School")
        branding = WhiteLabelBranding.objects.create(
            school=school,
            primary_color="#123456",
        )
        self.assertIsNotNone(branding.subdomain)
        self.assertTrue(branding.subdomain.startswith("auto-subdomain-school"))

    def test_subdomain_uniqueness(self):
        """Test that subdomain must be unique across all schools."""
        # Create a fresh school for the first branding
        school1 = School.objects.create(name="School One")
        WhiteLabelBranding.objects.create(school=school1, subdomain="unique-sub")
        
        # Create second school and try to use same subdomain - should fail on subdomain uniqueness
        school2 = School.objects.create(name="Another School")
        with self.assertRaises(IntegrityError):
            WhiteLabelBranding.objects.create(school=school2, subdomain="unique-sub")


class SchoolSettingsTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Settings School")

    def test_settings_creation(self):
        settings = SchoolSettings.objects.create(
            school=self.school,
            enabled_modules=["students", "fees", "attendance"],
            default_language="ur",
            default_timezone="Asia/Karachi",
            fee_grace_days=10,
        )
        self.assertEqual(settings.enabled_modules, ["students", "fees", "attendance"])
        self.assertEqual(settings.default_language, "ur")
        self.assertEqual(settings.default_timezone, "Asia/Karachi")
        self.assertEqual(settings.fee_grace_days, 10)

    def test_default_values(self):
        settings = SchoolSettings.objects.create(school=self.school)
        self.assertEqual(settings.default_language, "en")
        self.assertEqual(settings.default_timezone, "UTC")
        self.assertEqual(settings.date_format, "DD/MM/YYYY")
        self.assertEqual(settings.time_format, "12h")
        self.assertEqual(settings.first_day_of_week, 0)
        self.assertEqual(settings.fee_grace_days, 5)
        self.assertEqual(settings.fee_late_fee_percent, 0)
        self.assertEqual(settings.fee_late_fee_flat, 0)


class DomainMappingTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Domain School")

    def test_domain_mapping_creation(self):
        mapping = DomainMapping.objects.create(
            school=self.school,
            domain="school.example.com",
            is_primary=True,
            is_verified=True,
            ssl_enabled=True,
        )
        self.assertEqual(mapping.domain, "school.example.com")
        self.assertTrue(mapping.is_primary)
        self.assertTrue(mapping.is_verified)
        self.assertTrue(mapping.ssl_enabled)

    def test_subdomain_mapping(self):
        mapping = DomainMapping.objects.create(
            school=self.school,
            domain="sunrise",
            is_primary=True,
        )
        self.assertEqual(mapping.domain, "sunrise")
        self.assertTrue(mapping.is_primary)

    def test_unique_domain_constraint(self):
        DomainMapping.objects.create(school=self.school, domain="unique.example.com", is_primary=True)
        with self.assertRaises(Exception):
            DomainMapping.objects.create(school=self.school, domain="unique.example.com", is_primary=False)


class WhiteLabelAPITests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="API School")
        self.campus = Campus.objects.create(school=self.school, name="Main Campus")
        self.unit = AcademicUnit.objects.create(campus=self.campus, name="Primary")
        self.class_obj = Class.objects.create(unit=self.unit, name="Grade 1")
        self.section = Section.objects.create(class_obj=self.class_obj, name="A")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        )
        self.subject = Subject.objects.create(name="English", code="ENG-API", institution=self.school)
        SubjectOffering.objects.create(
            subject=self.subject,
            class_obj=self.class_obj,
            academic_year=self.year,
        )

        self.user = User.objects.create_superuser(
            username="apiuser", email="api@test.edu", password="TestPass123!"
        )
        membership = InstitutionMembership.objects.create(user=self.user, institution=self.school)
        RoleAssignment.objects.create(membership=membership, role=Role.SUPER_ADMIN)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_branding_creates_default(self):
        resp = self.client.get(reverse("white-label-branding"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("id", resp.data)
        self.assertEqual(resp.data["school_id"], self.school.id)
        self.assertEqual(resp.data["primary_color"], "#2563EB")  # default

    def test_update_branding(self):
        # First create branding
        WhiteLabelBranding.objects.create(school=self.school, primary_color="#000000")
        
        resp = self.client.put(
            reverse("white-label-branding"),
            {"primary_color": "#FF5733", "login_title": "Updated Login"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["primary_color"], "#FF5733")
        self.assertEqual(resp.data["login_title"], "Updated Login")

    def test_branding_css_variables_endpoint(self):
        WhiteLabelBranding.objects.create(
            school=self.school,
            primary_color="#123456",
            secondary_color="#654321",
        )
        resp = self.client.get(reverse("white-label-css-variables"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["css_variables"]["--color-primary"], "#123456")
        self.assertEqual(resp.data["css_variables"]["--color-secondary"], "#654321")

    def test_school_branding_config_endpoint(self):
        WhiteLabelBranding.objects.create(
            school=self.school,
            primary_color="#ABCDEF",
            login_title="Config Test",
            subdomain="config-test",
        )
        resp = self.client.get(reverse("white-label-config"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["colors"]["primary"], "#ABCDEF")
        self.assertEqual(resp.data["login"]["title"], "Config Test")
        self.assertEqual(resp.data["subdomain"], "config-test")

    def test_theme_preview_endpoint(self):
        WhiteLabelBranding.objects.create(
            school=self.school,
            primary_color="#111111",
            login_title="Preview Test",
        )
        resp = self.client.get(reverse("white-label-theme-preview"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["login_title"], "Preview Test")
        self.assertEqual(resp.data["css_variables"]["--color-primary"], "#111111")

    def test_school_settings_get(self):
        resp = self.client.get(reverse("white-label-settings"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["school_id"], self.school.id)
        self.assertEqual(resp.data["default_language"], "en")

    def test_school_settings_update(self):
        # First create settings object
        SchoolSettings.objects.create(school=self.school, fee_grace_days=5)
        
        resp = self.client.put(
            reverse("white-label-settings"),
            {
                "default_language": "ur",
                "fee_grace_days": 15,
                "enabled_modules": ["students", "fees"],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["default_language"], "ur")
        self.assertEqual(resp.data["fee_grace_days"], 15)
        self.assertEqual(resp.data["enabled_modules"], ["students", "fees"])

    def test_branding_public_endpoint(self):
        WhiteLabelBranding.objects.create(
            school=self.school,
            subdomain="public-test",
            primary_color="#FEDCBA",
            login_title="Public Login",
        )
        resp = self.client.get(reverse("white-label-public", kwargs={"subdomain": "public-test"}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["subdomain"], "public-test")
        self.assertEqual(resp.data["colors"]["primary"], "#FEDCBA")
        self.assertEqual(resp.data["login"]["title"], "Public Login")

    def test_branding_public_not_found(self):
        resp = self.client.get(reverse("white-label-public", kwargs={"subdomain": "nonexistent"}))
        self.assertEqual(resp.status_code, 404)

    def test_domain_mapping_crud(self):
        # Use a unique domain prefix to avoid conflicts with other tests
        unique_prefix = f"test-{self.school.id}-"
        
        # List
        resp = self.client.get(reverse("domain-mapping-list"))
        self.assertEqual(resp.status_code, 200)
        # Filter to only our test domains (paginated response has 'results' key)
        test_domains = [d for d in resp.data.get("results", []) if d["domain"].startswith("test-")]
        self.assertEqual(len(test_domains), 0)
        
        # Create
        resp = self.client.post(
            reverse("domain-mapping-list"),
            {"domain": f"{unique_prefix}school.example.com", "is_primary": True},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["domain"], f"{unique_prefix}school.example.com")
        self.assertTrue(resp.data["is_primary"])
        domain_id = resp.data["id"]
        
        # List again
        resp = self.client.get(reverse("domain-mapping-list"))
        test_domains = [d for d in resp.data.get("results", []) if d["domain"].startswith("test-")]
        self.assertEqual(len(test_domains), 1)
        
        # Detail
        resp = self.client.get(reverse("domain-mapping-detail", kwargs={"pk": domain_id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["domain"], f"{unique_prefix}school.example.com")
        
        # Update
        resp = self.client.put(
            reverse("domain-mapping-detail", kwargs={"pk": domain_id}),
            {"domain": f"{unique_prefix}school2.example.com", "is_primary": False},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["domain"], f"{unique_prefix}school2.example.com")
        self.assertFalse(resp.data["is_primary"])
        
        # Delete
        resp = self.client.delete(reverse("domain-mapping-detail", kwargs={"pk": domain_id}))
        self.assertEqual(resp.status_code, 204)
        
        # List should be empty
        resp = self.client.get(reverse("domain-mapping-list"))
        test_domains = [d for d in resp.data.get("results", []) if d["domain"].startswith(unique_prefix)]
        self.assertEqual(len(test_domains), 0)

    def test_duplicate_domain_rejected(self):
        DomainMapping.objects.create(school=self.school, domain="dup.example.com", is_primary=True)
        resp = self.client.post(
            reverse("domain-mapping-list"),
            {"domain": "dup.example.com", "is_primary": False},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)


class WhiteLabelAuditLogTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Audit School")
        self.user = User.objects.create_user(
            username="audituser", email="audit@test.edu", password="TestPass123!"
        )
        membership = InstitutionMembership.objects.create(user=self.user, institution=self.school)
        RoleAssignment.objects.create(membership=membership, role=Role.ADMIN)

    def test_audit_log_creation(self):
        log = WhiteLabelAuditLog.objects.create(
            school=self.school,
            user=self.user,
            action="update",
            model_name="WhiteLabelBranding",
            object_id="1",
            object_repr="Branding for Audit School",
            changes={"primary_color": {"old": "#000000", "new": "#FF0000"}},
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )
        self.assertEqual(log.school, self.school)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, "update")
        self.assertEqual(log.changes["primary_color"]["new"], "#FF0000")


class WhiteLabelIntegrationTests(TestCase):
    """Integration tests for white-label with other modules."""

    def setUp(self):
        self.school = School.objects.create(name="Integration School")
        self.campus = Campus.objects.create(school=self.school, name="Main Campus")
        self.unit = AcademicUnit.objects.create(campus=self.campus, name="Primary")
        self.class_obj = Class.objects.create(unit=self.unit, name="Grade 1")
        self.section = Section.objects.create(class_obj=self.class_obj, name="A")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 7, 31),
        )
        self.subject = Subject.objects.create(name="English", code="ENG-INT", institution=self.school)
        SubjectOffering.objects.create(
            subject=self.subject,
            class_obj=self.class_obj,
            academic_year=self.year,
        )

        guardian = Guardian.objects.create(name="Parent", relationship="Father", phone="03000000000")
        self.student = Student.objects.create(
            admission_number="ADM-INT-001", first_name="Ali", gender="male", guardian=guardian
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            academic_year=self.year,
            campus=self.campus,
            class_obj=self.class_obj,
            section=self.section,
        )

    def test_branding_in_invoice_pdf(self):
        """Test that invoice PDF uses school branding."""
        from apps.finance.pdf import payment_receipt_pdf
        from apps.finance.models import FeeCategory, Invoice, InvoiceItem, Payment

        WhiteLabelBranding.objects.create(
            school=self.school,
            primary_color="#FF0000",
            document_header_text="Custom Invoice Header",
        )

        invoice = Invoice.objects.create(
            invoice_number="INV-WL-001",
            student=self.student,
            enrollment=self.enrollment,
            academic_year=self.year,
            issue_date=date.today(),
            due_date=date.today(),
            status="issued",
        )
        InvoiceItem.objects.create(
            invoice=invoice, category=FeeCategory.objects.create(name="Tuition"),
            description="Tuition", amount=Decimal("1000.00")
        )
        payment = Payment.objects.create(
            receipt_number="RCPT-001",
            invoice=invoice,
            amount=Decimal("1000.00"),
            payment_date=date.today(),
        )

        # Should not raise
        pdf_bytes = payment_receipt_pdf(payment)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_branding_in_receipt_html(self):
        """Test that receipt HTML includes branding."""
        from apps.finance.views import PaymentReceiptHTMLView
        from apps.finance.models import FeeCategory, Invoice, InvoiceItem, Payment
        from django.test import RequestFactory

        WhiteLabelBranding.objects.create(
            school=self.school,
            primary_color="#00FF00",
            login_title="Branded Receipt",
            receipt_show_qr=True,
        )

        invoice = Invoice.objects.create(
            invoice_number="INV-HTML-001",
            student=self.student,
            enrollment=self.enrollment,
            academic_year=self.year,
            issue_date=date.today(),
            due_date=date.today(),
            status="paid",
        )
        InvoiceItem.objects.create(
            invoice=invoice, category=FeeCategory.objects.create(name="Tuition"),
            description="Tuition", amount=Decimal("500.00")
        )
        payment = Payment.objects.create(
            receipt_number="RCPT-HTML-001",
            invoice=invoice,
            amount=Decimal("500.00"),
            payment_date=date.today(),
            payment_method="cash",
        )

        factory = RequestFactory()
        request = factory.get(f"/api/finance/payments/{payment.pk}/receipt/")
        request.user = User.objects.create_superuser(username="test", email="test@test.edu", password="pass")
        request.institution = self.school

        view = PaymentReceiptHTMLView()
        view.kwargs = {"pk": payment.pk}
        view.request = request
        response = view.get(request, **view.kwargs)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("School", content)
        self.assertIn("RCPT-HTML-001", content)