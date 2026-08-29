from django.apps import AppConfig


class WhiteLabelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.white_label"
    verbose_name = "White Label / SaaS"