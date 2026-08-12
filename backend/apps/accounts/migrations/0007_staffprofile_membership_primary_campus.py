from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0006_staffleave_staffattendance"), ("schools", "0006_school_institution_settings")]
    operations = [
        migrations.AddField(model_name="staffprofile", name="membership", field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="staff_profile_membership", to="accounts.institutionmembership")),
        migrations.AddField(model_name="staffprofile", name="primary_campus", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="primary_staff", to="schools.campus")),
    ]
