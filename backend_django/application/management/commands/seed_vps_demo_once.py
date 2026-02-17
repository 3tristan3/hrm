"""VPS 演示数据初始化：只执行一次，生成 5 个岗位 + 20 条应聘记录。"""
import random
import string
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from application.default_regions import ensure_default_regions
from application.models import Application, Job, OperationLog, OperationLogArchive

SEED_ACTION = "SEED_DEMO_VPS_ONCE"
SEED_KEY = "vps_demo_seed_20260217"


class Command(BaseCommand):
    help = "Seed realistic demo data once: 5 jobs and 20 applications."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=20, help="How many applications to create.")
        parser.add_argument("--job-count", type=int, default=5, help="How many jobs to prepare.")

    def handle(self, *args, **options):
        count = max(int(options.get("count") or 20), 1)
        job_count = max(int(options.get("job_count") or 5), 1)

        if self._already_seeded():
            self.stdout.write(self.style.WARNING("检测到该演示数据已初始化，已跳过（只执行一次）。"))
            return

        region_map = ensure_default_regions()
        job_blueprints = self._job_blueprints()[:job_count]
        if not job_blueprints:
            self.stdout.write(self.style.ERROR("岗位配置为空，已终止。"))
            return

        rng = random.SystemRandom()
        created_job_ids = []
        created_application_ids = []

        with transaction.atomic():
            jobs = []
            for idx, blueprint in enumerate(job_blueprints, start=1):
                region = region_map[blueprint["region_code"]]
                job, _ = Job.objects.update_or_create(
                    region=region,
                    title=blueprint["title"],
                    defaults={
                        "description": blueprint["description"],
                        "salary": blueprint["salary"],
                        "education": blueprint["education"],
                        "is_active": True,
                        "is_deleted": False,
                        "deleted_at": None,
                        "order": idx,
                    },
                )
                jobs.append(job)
                created_job_ids.append(job.id)

            profiles = self._candidate_profiles()
            selected_profiles = [rng.choice(profiles) for _ in range(count)]
            for profile in selected_profiles:
                job = rng.choice(jobs)
                app = self._create_application(profile, job, rng)
                created_application_ids.append(app.id)

            self._write_seed_marker(
                jobs=jobs,
                created_job_ids=created_job_ids,
                created_application_ids=created_application_ids,
                count=count,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"演示数据初始化完成：岗位 {len(created_job_ids)} 个，应聘记录 {len(created_application_ids)} 条。"
            )
        )

    def _already_seeded(self):
        if OperationLog.objects.filter(action=SEED_ACTION, details__seed_key=SEED_KEY).exists():
            return True
        if OperationLogArchive.objects.filter(action=SEED_ACTION, details__seed_key=SEED_KEY).exists():
            return True
        return False

    def _job_blueprints(self):
        return [
            {
                "title": "化工装置操作员",
                "region_code": "dongying",
                "salary": "7000-9000元/月",
                "education": "中专/大专",
                "description": "负责装置巡检、参数记录、现场阀门切换与交接班，执行工艺与安全规程。",
            },
            {
                "title": "DCS中控操作员",
                "region_code": "dongying",
                "salary": "8000-11000元/月",
                "education": "大专及以上",
                "description": "负责中控画面监盘、报警处置、生产数据追踪与班组工况汇报。",
            },
            {
                "title": "设备点检技术员",
                "region_code": "liaocheng",
                "salary": "6500-9000元/月",
                "education": "大专及以上",
                "description": "负责机泵、换热器及管线点检，跟踪缺陷闭环并协助检修计划落实。",
            },
            {
                "title": "安全环保专员",
                "region_code": "beijing",
                "salary": "9000-13000元/月",
                "education": "本科及以上",
                "description": "负责作业票审查、风险辨识、环保台账管理与日常安全培训组织。",
            },
            {
                "title": "仓储发运专员",
                "region_code": "liaocheng",
                "salary": "6000-8500元/月",
                "education": "中专/大专",
                "description": "负责危化品出入库、发运计划执行、库存盘点与装卸现场安全监督。",
            },
        ]

    def _candidate_profiles(self):
        return [
            {"name": "王浩然", "gender": "男", "birth_year": 1997, "major": "应用化工技术", "education": "大专", "native": "山东东营"},
            {"name": "李佳宁", "gender": "女", "birth_year": 1999, "major": "化学工程与工艺", "education": "本科", "native": "山东聊城"},
            {"name": "张宇航", "gender": "男", "birth_year": 1995, "major": "过程装备与控制工程", "education": "本科", "native": "河南濮阳"},
            {"name": "刘雨桐", "gender": "女", "birth_year": 2000, "major": "环境工程", "education": "本科", "native": "山东滨州"},
            {"name": "陈博文", "gender": "男", "birth_year": 1996, "major": "工业分析技术", "education": "大专", "native": "河北沧州"},
            {"name": "杨欣怡", "gender": "女", "birth_year": 1998, "major": "安全工程", "education": "本科", "native": "山东德州"},
            {"name": "赵梓轩", "gender": "男", "birth_year": 1994, "major": "机械设计制造及其自动化", "education": "大专", "native": "山东淄博"},
            {"name": "黄若涵", "gender": "女", "birth_year": 1997, "major": "应用化学", "education": "本科", "native": "山东济南"},
            {"name": "周子墨", "gender": "男", "birth_year": 1993, "major": "电气自动化技术", "education": "大专", "native": "山东青岛"},
            {"name": "吴梦洁", "gender": "女", "birth_year": 1996, "major": "材料化学", "education": "本科", "native": "山东东营"},
            {"name": "徐景程", "gender": "男", "birth_year": 1998, "major": "化工安全技术", "education": "大专", "native": "山东聊城"},
            {"name": "孙嘉豪", "gender": "男", "birth_year": 1999, "major": "机电一体化技术", "education": "大专", "native": "山东潍坊"},
            {"name": "郑可馨", "gender": "女", "birth_year": 2001, "major": "物流管理", "education": "大专", "native": "山东烟台"},
            {"name": "冯晨曦", "gender": "男", "birth_year": 1995, "major": "环境监测与治理技术", "education": "大专", "native": "河北衡水"},
            {"name": "朱思远", "gender": "男", "birth_year": 1992, "major": "化工机械", "education": "中专", "native": "山东菏泽"},
            {"name": "马诗涵", "gender": "女", "birth_year": 1998, "major": "安全技术与管理", "education": "本科", "native": "山东临沂"},
            {"name": "高明轩", "gender": "男", "birth_year": 1996, "major": "应用化学", "education": "本科", "native": "山东泰安"},
            {"name": "胡雅雯", "gender": "女", "birth_year": 2000, "major": "化工过程自动化", "education": "大专", "native": "山东聊城"},
            {"name": "林志恒", "gender": "男", "birth_year": 1997, "major": "过程控制", "education": "本科", "native": "山东东营"},
            {"name": "郭雨晨", "gender": "女", "birth_year": 1999, "major": "工业工程", "education": "本科", "native": "山东德州"},
            {"name": "何振宇", "gender": "男", "birth_year": 1994, "major": "化工工艺", "education": "大专", "native": "河南新乡"},
            {"name": "罗子萱", "gender": "女", "birth_year": 2001, "major": "环境科学", "education": "本科", "native": "山东滨州"},
            {"name": "宋文昊", "gender": "男", "birth_year": 1995, "major": "机械电子工程", "education": "本科", "native": "山东济宁"},
            {"name": "唐雨泽", "gender": "男", "birth_year": 1998, "major": "化学工程", "education": "本科", "native": "山东青岛"},
        ]

    def _create_application(self, profile, job, rng):
        today = date.today()
        birth_month_num = rng.randint(1, 12)
        birth_day_num = rng.randint(1, 28)
        born = date(profile["birth_year"], birth_month_num, birth_day_num)
        birth_month = date(profile["birth_year"], birth_month_num, 1)
        age = self._calc_age(born, today)

        edu_start_year = profile["birth_year"] + 18
        edu_end_year = edu_start_year + (4 if profile["education"] == "本科" else 3)
        education_history = [
            {
                "school": rng.choice(
                    [
                        "山东化工职业学院",
                        "齐鲁工业大学",
                        "山东理工大学",
                        "青岛科技大学",
                        "山东科技大学",
                    ]
                ),
                "major": profile["major"],
                "degree": profile["education"],
                "start": f"{edu_start_year}-09",
                "end": f"{edu_end_year}-06",
            }
        ]

        work_history = self._build_work_history(rng, edu_end_year)
        family_members = self._build_family_members(rng)

        phone = self._unique_phone()
        emergency_phone = self._unique_phone()
        id_number = self._unique_id_number(born)
        name = profile["name"]
        first_py = self._name_prefix(name)
        wechat = f"{first_py}{rng.randint(1000, 9999)}"

        return Application.objects.create(
            region=job.region,
            job=job,
            name=name,
            recruit_type=rng.choice(["社招", "社招", "校招"]),
            apply_region=job.region.name,
            age=age,
            gender=profile["gender"],
            phone=phone,
            email=f"{first_py}{rng.randint(10, 99)}@example.com",
            apply_company=rng.choice(["华东化工集团", "齐安新材料", "鲁新化工股份"]) + rng.choice(["东营基地", "聊城基地", "总部"]),
            available_date=today + timedelta(days=rng.randint(5, 45)),
            expected_salary=rng.choice(["6500-8000", "7000-9000", "8000-10000", "9000-12000"]),
            recruitment_source=rng.choice(["招聘网站", "内部推荐", "线下招聘会", "人才市场"]),
            referrer_name=rng.choice(["", "张主管", "李班长", "王经理"]),
            referrer_relation=rng.choice(["", "同事", "同学", "亲友"]),
            referrer_company=rng.choice(["", "华东化工集团", "齐安新材料"]),
            marital_status=rng.choice(["未婚", "已婚"]),
            birth_month=birth_month,
            height_cm=rng.randint(158, 186),
            weight_kg=rng.randint(48, 88),
            health_status=rng.choice(["健康", "良好", "无职业禁忌病史"]),
            graduate_school=education_history[0]["school"],
            graduation_date=date(edu_end_year, 6, 1),
            major=profile["major"],
            title_cert=rng.choice(["危化品从业证", "低压电工证", "叉车证", ""]),
            education_level=profile["education"],
            education_period=f"{edu_start_year}-09 - {edu_end_year}-06",
            diploma_number=f"DIP{rng.randint(100000, 999999)}",
            political_status=rng.choice(["群众", "共青团员", "中共党员"]),
            ethnicity="汉族",
            hukou_type=rng.choice(["城镇户口", "农业户口"]),
            native_place=profile["native"],
            hukou_address=profile["native"] + "市",
            current_address=rng.choice(["东营市开发区化工路88号", "聊城市高新区产业园9号", "北京市朝阳区科创路16号"]),
            id_number=id_number,
            qq=str(rng.randint(10000000, 999999999)),
            wechat=wechat,
            emergency_name=rng.choice(["父亲", "母亲", "配偶"]),
            emergency_phone=emergency_phone,
            hobbies=rng.choice(["跑步、阅读", "羽毛球、摄影", "健身、旅行", "篮球、音乐"]),
            self_evaluation=rng.choice(
                [
                    "具备化工生产现场经验，执行力强，能够适应倒班。",
                    "熟悉安全操作规程，责任心强，具备团队协作意识。",
                    "学习能力较强，能够快速掌握装置工况与应急处置流程。",
                ]
            ),
            education_history=education_history,
            work_history=work_history,
            family_members=family_members,
            extra_fields={},
        )

    def _calc_age(self, born, today):
        age = today.year - born.year
        if (today.month, today.day) < (born.month, born.day):
            age -= 1
        return max(age, 18)

    def _build_work_history(self, rng, edu_end_year):
        company_pool = ["万润化工", "恒信新材料", "海岳精细化工", "齐安能源", "华泰化工"]
        position_pool = ["外操", "内操", "巡检员", "中控操作员", "点检员"]
        record_count = rng.choice([1, 2, 2, 3])
        rows = []
        start_year = max(edu_end_year, date.today().year - 8)
        for idx in range(record_count):
            sy = start_year + idx
            ey = min(sy + rng.choice([1, 2, 2, 3]), date.today().year - 1)
            rows.append(
                {
                    "company": rng.choice(company_pool),
                    "position": rng.choice(position_pool),
                    "start": f"{sy}-{rng.randint(1, 12):02d}",
                    "end": f"{ey}-{rng.randint(1, 12):02d}",
                }
            )
        return rows

    def _build_family_members(self, rng):
        return [
            {
                "name": rng.choice(["王建国", "李国强", "张卫东", "陈志刚"]),
                "relation": "父母",
                "age": rng.randint(50, 64),
                "company": rng.choice(["退休", "个体经营", "物流公司", "物业公司"]),
                "position": rng.choice(["退休", "职工", "店主"]),
                "phone": self._phone_like(),
            },
            {
                "name": rng.choice(["刘芳", "王丽", "李娜", "赵敏"]),
                "relation": rng.choice(["配偶", "父母"]),
                "age": rng.randint(26, 58),
                "company": rng.choice(["商贸公司", "医院", "学校", "个体经营"]),
                "position": rng.choice(["职员", "教师", "护士", "经营者"]),
                "phone": self._phone_like(),
            },
        ]

    def _unique_phone(self):
        prefixes = ["130", "131", "132", "133", "135", "136", "137", "138", "139", "150", "151", "152", "157", "158", "159", "186", "187", "188"]
        for _ in range(100):
            phone = f"{random.choice(prefixes)}{random.randint(10000000, 99999999)}"
            if not Application.objects.filter(phone=phone).exists():
                return phone
        return f"139{random.randint(10000000, 99999999)}"

    def _phone_like(self):
        prefixes = ["130", "131", "132", "133", "135", "136", "137", "138", "139", "150", "151", "152", "157", "158", "159", "186", "187", "188"]
        return f"{random.choice(prefixes)}{random.randint(10000000, 99999999)}"

    def _unique_id_number(self, born):
        area_codes = ["370502", "371502", "370105", "371102", "130983", "410900"]
        check_chars = string.digits + "X"
        birthday = born.strftime("%Y%m%d")
        for _ in range(100):
            candidate = f"{random.choice(area_codes)}{birthday}{random.randint(100, 999)}{random.choice(check_chars)}"
            if not Application.objects.filter(id_number=candidate).exists():
                return candidate
        return f"370502{birthday}123X"

    def _name_prefix(self, name):
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
            "郑": "zheng",
            "冯": "feng",
            "朱": "zhu",
            "马": "ma",
            "高": "gao",
            "胡": "hu",
            "林": "lin",
            "郭": "guo",
            "何": "he",
            "罗": "luo",
            "宋": "song",
            "唐": "tang",
        }
        return table.get(name[0], "hr")

    def _write_seed_marker(self, jobs, created_job_ids, created_application_ids, count):
        User = get_user_model()
        operator = User.objects.filter(is_superuser=True).order_by("id").first()
        primary_region = jobs[0].region if jobs else None
        OperationLog.objects.create(
            operator=operator,
            operator_username=getattr(operator, "username", ""),
            operator_role="superuser" if getattr(operator, "is_superuser", False) else "",
            operator_region_name=getattr(primary_region, "name", "") if primary_region else "",
            region=primary_region,
            module="system",
            action=SEED_ACTION,
            target_type="seed",
            target_label="VPS 演示数据",
            result=OperationLog.RESULT_SUCCESS,
            summary=f"初始化演示数据：岗位{len(created_job_ids)}个，应聘{count}条",
            details={
                "seed_key": SEED_KEY,
                "jobs": created_job_ids,
                "applications": created_application_ids,
                "count": count,
                "seeded_at": timezone.now().isoformat(),
            },
        )
