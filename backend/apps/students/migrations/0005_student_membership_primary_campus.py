from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("students", "0004_guardian_user_studentdocument"), ("accounts", "0007_staffprofile_membership_primary_campus"), ("schools", "0006_school_institution_settings")]
    operations = [
        migrations.AddField(model_name="student", name="membership", field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="student_profile", to="accounts.institutionmembership")),
        migrations.AddField(model_name="student", name="primary_campus", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="primary_students", to="schools.campus")),
    ]
