# Generated migration to fix Campus DELETE 500 bug
# Changes AcademicCalendar.campus on_delete from PROTECT to SET_NULL

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0030_campus_campus_school_status_idx'),
    ]

    operations = [
        migrations.AlterField(
            model_name='academiccalendar',
            name='campus',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='calendar_events',
                to='schools.campus',
                verbose_name='Campus',
            ),
        ),
    ]