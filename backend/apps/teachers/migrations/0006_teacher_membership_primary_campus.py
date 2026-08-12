from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("teachers", "0005_teacher_address_teacher_department_and_more"), ("accounts", "0007_staffprofile_membership_primary_campus"), ("schools", "0006_school_institution_settings")]
    operations = [
        migrations.AddField(model_name="teacher", name="membership", field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="teacher_profile", to="accounts.institutionmembership")),
        migrations.AddField(model_name="teacher", name="primary_campus", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="primary_teachers", to="schools.campus")),
    ]
