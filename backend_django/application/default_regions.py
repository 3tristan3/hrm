"""系统默认地区配置与幂等初始化工具。"""
from application.models import Region

DEFAULT_REGIONS = (
    {"name": "北京总部", "code": "beijing", "order": 1},
    {"name": "东营管理区", "code": "dongying", "order": 2},
    {"name": "聊城管理区", "code": "liaocheng", "order": 3},
)


def ensure_default_regions():
    """确保系统默认地区存在，按编码幂等更新并返回映射。"""
    region_map = {}
    for item in DEFAULT_REGIONS:
        region, _ = Region.objects.update_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "is_active": True,
                "order": item["order"],
            },
        )
        region_map[item["code"]] = region
    return region_map
