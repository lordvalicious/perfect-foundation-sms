from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0002_alter_auditlog_action"),
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
                    ("invoice", "Invoice"),
                    ("export", "Export"),
                    ("other", "Other"),
                ],
                max_length=30,
            ),
        ),
    ]
