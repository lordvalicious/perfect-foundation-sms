# Harden 2FA backup-code storage: add a per-code salt (HMAC keyed by
# SECRET_KEY) instead of a bare SHA-256 digest. Legacy rows keep an
# empty salt and are still verified via the legacy path.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_create_frostfire_superadmin"),
    ]

    operations = [
        migrations.AddField(
            model_name="twofabackupcode",
            name="salt",
            field=models.CharField(
                default="",
                max_length=64,
                blank=True,
            ),
        ),
    ]