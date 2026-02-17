"""初始化管理员账号命令：按环境变量创建/更新系统管理员。"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from application.default_regions import DEFAULT_REGIONS
from application.models import Region, UserProfile


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = "Create or update the default admin account from environment variables."

    def handle(self, *args, **options):
        if not env_bool("AUTO_CREATE_ADMIN", False):
            self.stdout.write("AUTO_CREATE_ADMIN is disabled; skipping admin bootstrap.")
            return

        username = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
        password = os.getenv("ADMIN_PASSWORD", "").strip()
        if not password:
            self.stdout.write("ADMIN_PASSWORD is empty; skipping admin bootstrap.")
            return

        default_region_name_map = {item["code"]: item["name"] for item in DEFAULT_REGIONS}
        region_code = os.getenv("ADMIN_REGION_CODE", "beijing").strip() or "beijing"
        default_region_name = default_region_name_map.get(region_code, "北京总部")
        region_name = os.getenv("ADMIN_REGION_NAME", default_region_name).strip() or default_region_name
        can_view_all = env_bool("ADMIN_CAN_VIEW_ALL", True)
        reset_password = env_bool("ADMIN_RESET_PASSWORD", True)

        region = Region.objects.filter(code=region_code).first()
        if region is None:
            region = Region.objects.create(
                name=region_name,
                code=region_code,
                is_active=True,
                order=1,
            )

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_superuser": True,
                "is_staff": True,
                "is_active": True,
            },
        )

        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        if created or reset_password:
            user.set_password(password)
        user.save()

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "region": region,
                "can_view_all": can_view_all,
            },
        )

        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Admin user {action}: {username}"))
