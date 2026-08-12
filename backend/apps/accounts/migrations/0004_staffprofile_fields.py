from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_staffprofile_photo_user_photo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staffprofile',
            name='user',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='staff_profile',
                to='accounts.user',
            ),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='first_name',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='last_name',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='gender',
            field=models.CharField(
                choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
                default='other',
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='phone',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='email',
            field=models.EmailField(blank=True),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='campus',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AlterModelOptions(
            name='staffprofile',
            options={'ordering': ['first_name', 'last_name']},
        ),
    ]
