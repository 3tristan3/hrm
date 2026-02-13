"""apps 文件，实现对应模块能力。"""
from django.apps import AppConfig


class ApplicationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "application"
