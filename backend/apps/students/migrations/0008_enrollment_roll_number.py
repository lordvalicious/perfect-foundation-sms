from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0007_studentleaverequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="enrollment",
            name="roll_number",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]