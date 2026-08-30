# Add the org_admin / head_office / librarian roles to the shared role enum.
# Additive only: existing role values are untouched.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0015_twofabackupcode_salt"),
    ]

    operations = [
        migrations.AlterField(
            model_name="roleassignment",
            name="role",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("super_admin", "Platform Super Admin"),
                    ("admin", "Institution Admin"),
                    ("org_admin", "Organization Administrator"),
                    ("head_office", "Head Office"),
                    ("principal", "Principal"),
                    ("vice_principal", "Vice Principal"),
                    ("campus_admin", "Campus Administrator"),
                    ("academic", "Academic Administrator"),
                    ("accountant", "Accountant"),
                    ("hr", "HR / Staff Officer"),
                    ("receptionist", "Receptionist"),
                    ("librarian", "Librarian"),
                    ("guard", "Security Guard"),
                    ("teacher", "Teacher"),
                    ("parent", "Parent / Guardian"),
                    ("student", "Student"),
                    ("staff", "Staff Member"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="rolepermission",
            name="role",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("super_admin", "Platform Super Admin"),
                    ("admin", "Institution Admin"),
                    ("org_admin", "Organization Administrator"),
                    ("head_office", "Head Office"),
                    ("principal", "Principal"),
                    ("vice_principal", "Vice Principal"),
                    ("campus_admin", "Campus Administrator"),
                    ("academic", "Academic Administrator"),
                    ("accountant", "Accountant"),
                    ("hr", "HR / Staff Officer"),
                    ("receptionist", "Receptionist"),
                    ("librarian", "Librarian"),
                    ("guard", "Security Guard"),
                    ("teacher", "Teacher"),
                    ("parent", "Parent / Guardian"),
                    ("student", "Student"),
                    ("staff", "Staff Member"),
                ],
            ),
        ),
    ]