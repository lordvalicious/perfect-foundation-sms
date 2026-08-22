from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.schools.models import AcademicUnit, AcademicYear, Campus, Class, School, Section
from apps.students.models import Enrollment, Guardian, Student

from .models import Account, Concession, Invoice, InvoiceItem, JournalEntry, JournalLine, Payment, PaymentRefund


class AccountingModelTests(TestCase):
	def setUp(self):
		self.school = School.objects.create(name="Test School")
		self.campus = Campus.objects.create(school=self.school, name="Main Campus")
		unit = AcademicUnit.objects.create(campus=self.campus, name="Primary")
		class_obj = Class.objects.create(unit=unit, name="Grade 1")
		section = Section.objects.create(class_obj=class_obj, name="A")
		year = AcademicYear.objects.create(
			school=self.school,
			name="2026-2027",
			start_date=date(2026, 8, 1),
			end_date=date(2027, 7, 31),
		)
		guardian = Guardian.objects.create(name="Parent", relationship="Father", phone="03000000000")
		student = Student.objects.create(admission_number="ADM-001", first_name="Ali", gender="male", guardian=guardian)
		self.enrollment = Enrollment.objects.create(
			student=student,
			academic_year=year,
			campus=self.campus,
			class_obj=class_obj,
			section=section,
		)
		self.category = __import__("apps.finance.models", fromlist=["FeeCategory"]).FeeCategory.objects.create(name="Tuition")
		self.invoice = Invoice.objects.create(
			invoice_number="INV-001",
			student=student,
			enrollment=self.enrollment,
			academic_year=year,
			issue_date=date.today(),
			due_date=date.today(),
		)
		InvoiceItem.objects.create(invoice=self.invoice, category=self.category, description="Tuition", amount=Decimal("1000.00"))

	def test_journal_line_requires_one_side(self):
		asset = Account.objects.create(institution=self.school, code="1000", name="Cash", account_type="asset")
		entry = JournalEntry.objects.create(institution=self.school, description="Test entry")
		line = JournalLine(entry=entry, account=asset)
		with self.assertRaises(ValidationError):
			line.full_clean()

	def test_journal_entry_balances(self):
		cash = Account.objects.create(institution=self.school, code="1000", name="Cash", account_type="asset")
		income = Account.objects.create(institution=self.school, code="4000", name="Tuition", account_type="income")
		entry = JournalEntry.objects.create(institution=self.school, description="Fee payment")
		JournalLine.objects.create(entry=entry, account=cash, debit=Decimal("1000.00"))
		JournalLine.objects.create(entry=entry, account=income, credit=Decimal("1000.00"))
		self.assertTrue(entry.is_balanced)
		self.assertEqual(entry.total_debit, entry.total_credit)

	def test_approved_concession_reduces_invoice_total(self):
		Concession.objects.create(invoice=self.invoice, amount=Decimal("200.00"), reason="Scholarship", status="approved")
		self.assertEqual(self.invoice.total_amount, Decimal("800.00"))

	def test_refund_cannot_exceed_payment(self):
		payment = Payment.objects.create(
			receipt_number="RCPT-001",
			invoice=self.invoice,
			amount=Decimal("500.00"),
			payment_date=date.today(),
		)
		refund = PaymentRefund(payment=payment, amount=Decimal("600.00"), reason="Duplicate payment")
		with self.assertRaises(ValidationError):
			refund.full_clean()
