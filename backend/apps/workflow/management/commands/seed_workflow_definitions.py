"""Idempotent seeder for the default workflow definitions.

These are configuration rows (state machines + approval queues), not
sample data. They make the engine usable out of the box for the school's
common approval journeys.
"""

from django.core.management.base import BaseCommand

from apps.workflow.models import WorkflowDefinition

DEFAULT_DEFINITIONS = [
    {
        "slug": "students.admission.application",
        "name": "Student Admission Approval",
        "object_type": "students.admissionapplication",
        "approval_steps": ["receptionist", "academic", "admin"],
    },
    {
        "slug": "students.transfer.request",
        "name": "Student Transfer Approval",
        "object_type": "students.transferrequest",
        "approval_steps": ["academic", "admin"],
    },
    {
        "slug": "students.certificate.request",
        "name": "Certificate Issuance Approval",
        "object_type": "students.certificaterequest",
        "approval_steps": ["academic", "admin"],
    },
    {
        "slug": "hr.leave.request",
        "name": "Leave Request Approval",
        "object_type": "hr.leaverequest",
        "approval_steps": ["hr", "admin"],
    },
    {
        "slug": "hr.loan.request",
        "name": "Staff Loan Approval",
        "object_type": "hr.loanrequest",
        "approval_steps": ["hr", "admin"],
    },
    {
        "slug": "finance.expense.request",
        "name": "Expense Approval",
        "object_type": "finance.expenserequest",
        "approval_steps": ["accountant", "admin"],
    },
    {
        "slug": "finance.refund.request",
        "name": "Fee Refund Approval",
        "object_type": "finance.refundrequest",
        "approval_steps": ["accountant", "admin"],
    },
    {
        "slug": "finance.discount.request",
        "name": "Fee Discount / Waiver Approval",
        "object_type": "finance.discountrequest",
        "approval_steps": ["accountant", "admin"],
    },
    {
        "slug": "inventory.purchase.request",
        "name": "Purchase Order Approval",
        "object_type": "inventory.purchaserequest",
        "approval_steps": ["accountant", "admin"],
    },
    {
        "slug": "payroll.run.approval",
        "name": "Payroll Run Approval",
        "object_type": "payroll.payrollrun",
        "approval_steps": ["accountant", "admin"],
    },
    {
        "slug": "reportcards.result.approval",
        "name": "Report Card Result Approval",
        "object_type": "reportcards.reportcard",
        "approval_steps": ["academic", "principal"],
    },
]


def build_definition(spec):
    return {
        "states": ["draft", "pending_approval", "approved", "rejected", "cancelled"],
        "initial_state": "draft",
        "approval_steps": spec["approval_steps"],
        "transitions": {
            "submit": {"from": ["draft"], "to": "pending_approval"},
            "approve": {"from": ["pending_approval"], "to": "approved"},
            "reject": {"from": ["pending_approval"], "to": "rejected"},
            "cancel": {"from": ["draft", "pending_approval"], "to": "cancelled"},
            "restart": {"from": ["rejected"], "to": "draft"},
        },
    }


class Command(BaseCommand):
    help = "Seed (and refresh) the default workflow definitions."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for spec in DEFAULT_DEFINITIONS:
            payload = {
                "name": spec["name"],
                "object_type": spec["object_type"],
            }
            payload.update(build_definition(spec))

            definition, was_created = WorkflowDefinition.objects.update_or_create(
                object_type=spec["object_type"],
                slug=spec["slug"],
                defaults=payload,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"\nWorkflow definitions: {created} created, {updated} refreshed."))
        self.stdout.write(self.style.SUCCESS(f"Total active definitions: {WorkflowDefinition.objects.filter(is_active=True).count()}\n"))