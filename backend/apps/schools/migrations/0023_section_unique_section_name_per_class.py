from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0022_dedupe_sections'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='section',
            constraint=models.UniqueConstraint(fields=('class_obj', 'name'), name='unique_section_name_per_class'),
        ),
    ]
