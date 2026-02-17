"""部署初始化命令：确保系统默认地区存在。"""
from django.core.management.base import BaseCommand

from application.default_regions import DEFAULT_REGIONS, ensure_default_regions


class Command(BaseCommand):
    help = "Ensure default regions exist (beijing, dongying, liaocheng)."

    def handle(self, *args, **options):
        region_map = ensure_default_regions()
        ordered_codes = [item["code"] for item in DEFAULT_REGIONS]
        self.stdout.write(
            self.style.SUCCESS(
                "Default regions ensured: " + ", ".join(code for code in ordered_codes if code in region_map)
            )
        )
