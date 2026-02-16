"""application 应用配置：声明 Django 应用元信息与默认主键类型。"""
from django.apps import AppConfig


class ApplicationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "application"
