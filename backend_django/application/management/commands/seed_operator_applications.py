"""测试数据填充命令：批量生成应聘记录及附件，便于本地联调与演示。"""
import random
import string
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from application.models import Application, Job, Region


class Command(BaseCommand):
    help = "Seed random complete applications for chemical plant operator jobs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=8,
            help="How many applications to create (default: 8)",
        )
        parser.add_argument(
            "--job-title",
            type=str,
            default="化工装置操作员",
            help="Job title to target/create (default: 化工装置操作员)",
        )
        parser.add_argument(
            "--region-code",
            type=str,
            default="",
            help="Optional region code. If omitted, uses the job's region or first active region.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        job_title = (options["job_title"] or "").strip()
        region_code = (options["region_code"] or "").strip()
        if count <= 0:
            raise CommandError("--count 必须大于 0")
        if not job_title:
            raise CommandError("--job-title 不能为空")

        region = self._resolve_region(region_code)
        job = self._resolve_or_create_job(job_title, region)

        created_ids = []
        with transaction.atomic():
            for _ in range(count):
                app = self._build_random_application(job)
                created_ids.append(app.id)

        self.stdout.write(
            self.style.SUCCESS(
                f"已新增 {len(created_ids)} 条「{job.title}」应聘记录，ID: {created_ids}"
            )
        )

    def _resolve_region(self, region_code):
        if region_code:
            region = Region.objects.filter(code=region_code).first()
            if not region:
                raise CommandError(f"地区不存在: {region_code}")
            return region
        region = Region.objects.filter(is_active=True).order_by("order", "id").first()
        if not region:
            raise CommandError("没有可用地区，请先初始化地区与岗位数据")
        return region

    def _resolve_or_create_job(self, job_title, fallback_region):
        job = (
            Job.objects.filter(title=job_title, is_active=True)
            .select_related("region")
            .order_by("order", "id")
            .first()
        )
        if job:
            return job

        # Fallback: contains match.
        fuzzy = (
            Job.objects.filter(title__icontains=job_title, is_active=True)
            .select_related("region")
            .order_by("order", "id")
            .first()
        )
        if fuzzy:
            return fuzzy

        return Job.objects.create(
            region=fallback_region,
            title=job_title,
            description="负责化工装置巡检、操作、参数记录与安全执行。",
            salary="7k-11k",
            education="中专/大专",
            is_active=True,
            order=999,
        )

    def _build_random_application(self, job):
        region = job.region
        today = date.today()
        rng = random.SystemRandom()

        gender = rng.choice(["男", "女"])
        surname = rng.choice(
            [
                "王",
                "李",
                "张",
                "刘",
                "陈",
                "杨",
                "赵",
                "黄",
                "周",
                "吴",
                "徐",
                "孙",
            ]
        )
        given = rng.choice(
            [
                "浩然",
                "梓轩",
                "宇航",
                "嘉豪",
                "子墨",
                "欣怡",
                "雨桐",
                "若涵",
                "梦洁",
                "佳宁",
                "博文",
                "景程",
            ]
        )
        name = f"{surname}{given}"

        birth_year = rng.randint(today.year - 36, today.year - 21)
        birth_month_num = rng.randint(1, 12)
        birth_day = rng.randint(1, 28)
        birth_full_date = date(birth_year, birth_month_num, birth_day)
        birth_month = date(birth_year, birth_month_num, 1)
        age = self._calc_age(birth_full_date, today)

        education_level = rng.choice(["中专", "大专", "本科"])
        edu_start_year = birth_year + 18
        edu_end_year = edu_start_year + rng.choice([3, 4])
        edu_start = f"{edu_start_year}-09"
        edu_end = f"{edu_end_year}-06"
        graduation_date = date(edu_end_year, 6, 1)
        education_period = f"{edu_start} - {edu_end}"

        phone = self._unique_phone()
        emergency_phone = self._unique_phone()
        id_number = self._unique_id_number(birth_full_date)
        qq = str(rng.randint(10000000, 999999999))
        wechat = f"{self._pinyin_stub(name)}{rng.randint(1000, 9999)}"

        company = rng.choice(
            [
                "华东化工集团",
                "中汇精细化工",
                "鲁新石化材料",
                "安泰能源化工",
                "海润新材料",
            ]
        )
        apply_company = f"{company}{rng.choice(['一厂', '二厂', '生产基地'])}"
        apply_region = rng.choice([region.name, "厂区A", "厂区B", "综合装置区"])

        major = rng.choice(["化学工程与工艺", "应用化工技术", "工业分析技术", "过程装备"])
        graduate_school = rng.choice(
            [
                "山东化工职业学院",
                "青岛职业技术学院",
                "齐鲁工业大学",
                "山东理工大学",
                "济南职业学院",
            ]
        )

        work_history = self._random_work_history(edu_end_year, today.year - 1)
        education_history = [
            {
                "school": graduate_school,
                "major": major,
                "degree": education_level,
                "start": edu_start,
                "end": edu_end,
            }
        ]
        family_members = self._random_family_members()

        required_extra = self._build_region_extra_fields(region, rng)

        return Application.objects.create(
            region=region,
            job=job,
            name=name,
            recruit_type=rng.choice(["社招", "校招"]),
            apply_region=apply_region,
            age=age,
            gender=gender,
            phone=phone,
            email=f"{self._pinyin_stub(name)}{rng.randint(10, 99)}@example.com",
            apply_company=apply_company,
            available_date=today + timedelta(days=rng.randint(7, 45)),
            expected_salary=rng.choice(["6k-8k", "7k-10k", "8k-12k"]),
            recruitment_source=rng.choice(
                ["招聘网站", "贵公司人员介绍", "行政单位人员介绍", "其他", "公司内岗位调整"]
            ),
            referrer_name=rng.choice(["", "张师傅", "李经理", "王主管"]),
            referrer_relation=rng.choice(["", "同事", "同学", "亲友"]),
            referrer_company=rng.choice(["", company, "外部推荐"]),
            marital_status=rng.choice(["未婚", "已婚"]),
            birth_month=birth_month,
            height_cm=rng.randint(158, 186),
            weight_kg=rng.randint(50, 88),
            health_status=rng.choice(["良好", "健康", "无慢性病史"]),
            graduate_school=graduate_school,
            graduation_date=graduation_date,
            major=major,
            title_cert=rng.choice(["危化品从业证", "特种设备操作证", ""]),
            education_level=education_level,
            education_period=education_period,
            diploma_number=f"DIP{rng.randint(100000, 999999)}",
            political_status=rng.choice(["群众", "共青团员", "中共党员"]),
            ethnicity="汉族",
            hukou_type=rng.choice(["城镇户口", "农业户口"]),
            native_place=rng.choice(["山东东营", "山东聊城", "山东淄博", "河北沧州", "河南濮阳"]),
            hukou_address=rng.choice(
                ["山东省东营市东营区", "山东省聊城市东昌府区", "山东省滨州市", "河北省沧州市"]
            ),
            current_address=rng.choice(
                ["东营市开发区化工路88号", "聊城市高新区产业园9号", "青岛市黄岛区海滨路66号"]
            ),
            id_number=id_number,
            qq=qq,
            wechat=wechat,
            emergency_name=rng.choice(["父亲", "母亲", "配偶"]),
            emergency_phone=emergency_phone,
            hobbies=rng.choice(["阅读、跑步", "篮球、钓鱼", "旅行、摄影", "健身、音乐"]),
            self_evaluation=rng.choice(
                [
                    "执行力强，熟悉化工安全规范，能适应倒班。",
                    "责任心强，具备DCS基础操作经验。",
                    "学习能力强，具备团队协作意识和现场应急处理能力。",
                ]
            ),
            education_history=education_history,
            work_history=work_history,
            family_members=family_members,
            extra_fields=required_extra,
        )

    def _calc_age(self, born, today):
        age = today.year - born.year
        if (today.month, today.day) < (born.month, born.day):
            age -= 1
        return max(age, 18)

    def _unique_phone(self):
        prefixes = ["130", "131", "132", "133", "135", "136", "137", "138", "139", "150", "151", "152", "157", "158", "159", "186", "187", "188"]
        for _ in range(50):
            phone = f"{random.choice(prefixes)}{random.randint(10000000, 99999999)}"
            if not Application.objects.filter(phone=phone).exists():
                return phone
        return f"139{random.randint(10000000, 99999999)}"

    def _unique_id_number(self, birth_full_date):
        area_codes = ["370502", "371502", "370105", "371102", "130983", "410900"]
        check_chars = string.digits + "X"
        for _ in range(50):
            area = random.choice(area_codes)
            birthday = birth_full_date.strftime("%Y%m%d")
            seq = f"{random.randint(100, 999)}"
            candidate = f"{area}{birthday}{seq}{random.choice(check_chars)}"
            if not Application.objects.filter(id_number=candidate).exists():
                return candidate
        return f"370502{birth_full_date.strftime('%Y%m%d')}123X"

    def _pinyin_stub(self, name):
        # Keep it lightweight: deterministic Latin fallback for handles/email prefix.
        table = {
            "王": "wang",
            "李": "li",
            "张": "zhang",
            "刘": "liu",
            "陈": "chen",
            "杨": "yang",
            "赵": "zhao",
            "黄": "huang",
            "周": "zhou",
            "吴": "wu",
            "徐": "xu",
            "孙": "sun",
        }
        first = table.get(name[0], "hr")
        return first

    def _random_work_history(self, start_year, max_end_year):
        rng = random.SystemRandom()
        company_pool = [
            "万润化工",
            "恒信新材料",
            "海岳精细化工",
            "齐安能源",
            "华泰化工",
        ]
        position_pool = ["操作员", "外操", "内操", "班组长助理", "巡检员"]
        records = []
        cur_start_year = max(start_year, max_end_year - 8)
        count = rng.choice([1, 2, 2, 3])
        for idx in range(count):
            sy = cur_start_year + idx
            ey = min(sy + rng.choice([1, 2, 3]), max_end_year)
            if ey < sy:
                ey = sy
            records.append(
                {
                    "company": rng.choice(company_pool),
                    "position": rng.choice(position_pool),
                    "start": f"{sy}-{rng.randint(1, 12):02d}",
                    "end": f"{ey}-{rng.randint(1, 12):02d}",
                }
            )
        return records

    def _random_family_members(self):
        rng = random.SystemRandom()
        return [
            {
                "name": rng.choice(["张建国", "李国强", "王志刚", "陈卫东"]),
                "relation": "父母",
                "age": rng.randint(48, 62),
                "company": rng.choice(["个体", "退休", "物流公司", "物业公司"]),
                "position": rng.choice(["职工", "店主", "退休"]),
                "phone": self._phone_like(),
            },
            {
                "name": rng.choice(["刘芳", "王丽", "李娜", "赵敏"]),
                "relation": rng.choice(["配偶", "父母"]),
                "age": rng.randint(25, 58),
                "company": rng.choice(["商贸公司", "医院", "学校", "个体经营"]),
                "position": rng.choice(["职员", "教师", "护士", "经营者"]),
                "phone": self._phone_like(),
            },
        ]

    def _phone_like(self):
        prefixes = ["130", "131", "132", "133", "135", "136", "137", "138", "139", "150", "151", "152", "157", "158", "159", "186", "187", "188"]
        return f"{random.choice(prefixes)}{random.randint(10000000, 99999999)}"

    def _build_region_extra_fields(self, region, rng):
        result = {}
        for field in region.fields.all():
            if field.field_type == "number":
                result[field.key] = rng.randint(1, 100)
                continue
            if field.field_type == "date":
                year = rng.randint(date.today().year - 5, date.today().year)
                result[field.key] = f"{year}-{rng.randint(1, 12):02d}"
                continue
            if field.field_type == "select":
                options = field.options if isinstance(field.options, list) else []
                if options:
                    result[field.key] = str(rng.choice(options))
                else:
                    result[field.key] = "测试选项"
                continue
            # text / fallback
            result[field.key] = f"测试-{field.label}-{rng.randint(10, 99)}"
        return result
