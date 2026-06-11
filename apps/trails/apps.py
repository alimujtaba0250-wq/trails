# AppConfig for the trails application

from django.apps import AppConfig


class TrailsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trails"
    label = "trails"
