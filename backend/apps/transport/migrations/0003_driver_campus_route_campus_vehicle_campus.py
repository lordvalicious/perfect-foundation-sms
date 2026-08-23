from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("schools", "0006_school_institution_settings"),
        ("transport", "0002_seed_transport_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="driver",
            name="campus",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="drivers",
                to="schools.campus",
            ),
        ),
        migrations.AddField(
            model_name="route",
            name="campus",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="transport_routes",
                to="schools.campus",
            ),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="campus",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="vehicles",
                to="schools.campus",
            ),
        ),
    ]