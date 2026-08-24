from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0003_alter_auditlog_action"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("login", "Login"),
                    ("login_failed", "Login Failed"),
                    ("institution_switched", "Institution Switched"),
                    ("logout", "Logout"),
                    ("create", "Create"),
                    ("update", "Update"),
                    ("delete", "Delete"),
                    ("export", "Export"),
                    ("permission_change", "Permission Change"),
                    ("settings_change", "Settings Change"),
                    ("password_reset", "Password Reset"),
                    ("grade_publish", "Grade Publish"),
                    ("grade_amendment", "Grade Amendment"),
                    ("payment", "Payment"),
                    ("payment_reversal", "Payment Reversal"),
                    ("payment_refund", "Payment Refund"),
                    ("invoice", "Invoice"),
                    ("expense_posted", "Expense Posted"),
                    ("concession_approved", "Concession Approved"),
                    ("staff_leave_approved", "Staff Leave Approved"),
                    ("staff_leave_rejected", "Staff Leave Rejected"),
                    ("other", "Other"),
                ],
                max_length=30,
            ),
        ),
    ]
