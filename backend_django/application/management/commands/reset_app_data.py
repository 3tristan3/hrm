"""数据重置命令：清理应聘、面试、日志等业务数据并保留基础配置。"""
from django.core.management.base import BaseCommand
from django.db import transaction

from application.models import (
    Application,
    ApplicationAttachment,
    Job,
    Region,
    RegionField,
    UserProfile,
)


class Command(BaseCommand):
    help = "Reset application data and seed fixed regions."

    def handle(self, *args, **options):
        fixed_regions = [
            {"name": "北京总部", "code": "beijing", "order": 1},
            {"name": "东营管理区", "code": "dongying", "order": 2},
            {"name": "聊城管理区", "code": "liaocheng", "order": 3},
        ]

        with transaction.atomic():
            # Ensure fixed regions exist first (for profile reassignment).
            region_map = {}
            for item in fixed_regions:
                region, _ = Region.objects.update_or_create(
                    code=item["code"],
                    defaults={
                        "name": item["name"],
                        "is_active": True,
                        "order": item["order"],
                    },
                )
                region_map[item["code"]] = region

            default_region = region_map["beijing"]

            # Re-assign profiles that are not in fixed regions.
            fixed_region_ids = {region.id for region in region_map.values()}
            profiles = UserProfile.objects.select_related("region")
            for profile in profiles:
                if profile.region_id not in fixed_region_ids:
                    profile.region = default_region
                    profile.can_view_all = profile.can_view_all and profile.user.is_superuser
                    profile.save(update_fields=["region", "can_view_all"])

            # Clear business data.
            ApplicationAttachment.objects.all().delete()
            Application.objects.all().delete()
            Job.objects.all().delete()
            RegionField.objects.all().delete()

            # Remove non-fixed regions.
            Region.objects.exclude(id__in=fixed_region_ids).delete()

        self.stdout.write(self.style.SUCCESS("已清空业务数据并重置地区为三大区域。"))
