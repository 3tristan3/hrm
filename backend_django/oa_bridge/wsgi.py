"""WSGI 部署入口，用于生产环境加载 Django 应用。"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oa_bridge.settings")

application = get_wsgi_application()
