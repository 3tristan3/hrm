from django.db import models


class Region(models.Model):
    name = models.CharField("地区名称", max_length=50, unique=True)
    code = models.CharField("地区编码", max_length=50, unique=True)
    is_active = models.BooleanField("启用", default=True)
    order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "地区"
        verbose_name_plural = "地区"

    def __str__(self):
        return self.name


class RegionField(models.Model):
    TEXT = "text"
    SELECT = "select"
    NUMBER = "number"
    DATE = "date"

    FIELD_TYPES = [
        (TEXT, "文本"),
        (SELECT, "下拉"),
        (NUMBER, "数字"),
        (DATE, "日期"),
    ]

    region = models.ForeignKey(
        Region, related_name="fields", on_delete=models.CASCADE, verbose_name="地区"
    )
    key = models.CharField("字段编码", max_length=50)
    label = models.CharField("字段显示名", max_length=50)
    field_type = models.CharField(
        "类型", max_length=20, choices=FIELD_TYPES, default=TEXT
    )
    required = models.BooleanField("必填", default=False)
    options = models.JSONField("选项", blank=True, null=True)
    order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = ("region", "key")
        verbose_name = "地区字段"
        verbose_name_plural = "地区字段"

    def __str__(self):
        return f"{self.region.name}-{self.label}"


class Job(models.Model):
    region = models.ForeignKey(
        Region, related_name="jobs", on_delete=models.CASCADE, verbose_name="地区"
    )
    title = models.CharField("岗位名称", max_length=100)
    description = models.TextField("岗位描述", blank=True)
    salary = models.CharField("薪资范围", max_length=100, blank=True)
    education = models.CharField("学历要求", max_length=50, blank=True)
    is_active = models.BooleanField("启用", default=True)
    order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "岗位"
        verbose_name_plural = "岗位"

    def __str__(self):
        return self.title


class Application(models.Model):
    region = models.ForeignKey(Region, on_delete=models.PROTECT, verbose_name="地区")
    job = models.ForeignKey(Job, on_delete=models.PROTECT, verbose_name="岗位")
    name = models.CharField("姓名", max_length=50)
    recruit_type = models.CharField("招聘类型", max_length=20, blank=True, default="")
    apply_region = models.CharField("应聘区域", max_length=50, blank=True, default="")
    age = models.PositiveIntegerField("年龄", null=True, blank=True)
    gender = models.CharField("性别", max_length=20)
    phone = models.CharField("手机号", max_length=20)
    email = models.EmailField("邮箱", blank=True, default="")
    apply_company = models.CharField("应聘公司", max_length=200, blank=True, default="")
    available_date = models.DateField("能上岗日期", null=True, blank=True)
    expected_salary = models.CharField("期望薪资", max_length=100, blank=True, default="")
    recruitment_source = models.CharField("招聘来源", max_length=100, blank=True, default="")
    referrer_name = models.CharField("介绍人姓名", max_length=50, blank=True, default="")
    referrer_relation = models.CharField("介绍人关系", max_length=50, blank=True, default="")
    referrer_company = models.CharField("介绍人单位", max_length=200, blank=True, default="")
    marital_status = models.CharField("婚姻情况", max_length=20, blank=True, default="")
    birth_month = models.DateField("出生年月", null=True, blank=True)
    height_cm = models.PositiveIntegerField("身高(cm)", null=True, blank=True)
    weight_kg = models.PositiveIntegerField("体重(kg)", null=True, blank=True)
    health_status = models.CharField("健康情况", max_length=50, blank=True, default="")
    graduate_school = models.CharField("毕业院校", max_length=200, blank=True, default="")
    graduation_date = models.DateField("毕业时间", null=True, blank=True)
    major = models.CharField("专业", max_length=100, blank=True, default="")
    title_cert = models.CharField("职称证书", max_length=200, blank=True, default="")
    education_level = models.CharField("最高学历", max_length=50, blank=True, default="")
    education_period = models.CharField("最高学历起止时间", max_length=50, blank=True, default="")
    diploma_number = models.CharField("毕业证编号", max_length=100, blank=True, default="")
    political_status = models.CharField("政治面貌", max_length=50, blank=True, default="")
    ethnicity = models.CharField("民族", max_length=50, blank=True, default="")
    hukou_type = models.CharField("户口性质", max_length=50, blank=True, default="")
    native_place = models.CharField("籍贯", max_length=100, blank=True, default="")
    hukou_address = models.CharField("户口所在地", max_length=200, blank=True, default="")
    current_address = models.CharField("现住地址", max_length=200, blank=True, default="")
    id_number = models.CharField("身份证号", max_length=30, blank=True, default="")
    qq = models.CharField("QQ", max_length=30, blank=True, default="")
    wechat = models.CharField("微信号", max_length=50, blank=True, default="")
    emergency_name = models.CharField("紧急联系人姓名", max_length=50, blank=True, default="")
    emergency_phone = models.CharField("紧急联系人手机号", max_length=20, blank=True, default="")
    hobbies = models.TextField("兴趣爱好", blank=True, default="")
    self_evaluation = models.TextField("自我评价", blank=True, default="")
    education_history = models.JSONField("教育培训经历", default=list, blank=True)
    work_history = models.JSONField("工作经历", default=list, blank=True)
    family_members = models.JSONField("家庭成员", default=list, blank=True)
    extra_fields = models.JSONField("扩展字段", default=dict, blank=True)
    created_at = models.DateTimeField("提交时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]
        verbose_name = "应聘记录"
        verbose_name_plural = "应聘记录"

    def __str__(self):
        return f"{self.name}-{self.job.title}"


class ApplicationAttachment(models.Model):
    CATEGORY_CHOICES = [
        ("photo", "个人照片"),
        ("id_front", "身份证正面"),
        ("id_back", "身份证反面"),
        ("diploma", "毕业证"),
        ("degree", "学位证"),
        ("resume", "个人简历"),
        ("criminal", "无犯罪证明"),
        ("credit", "个人信用报告"),
        ("other", "其他相关附件"),
    ]

    application = models.ForeignKey(
        Application, related_name="attachments", on_delete=models.CASCADE
    )
    category = models.CharField("附件类型", max_length=30, choices=CATEGORY_CHOICES)
    file = models.FileField("文件", upload_to="attachments/%Y/%m/")
    created_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "id"]
        verbose_name = "附件"
        verbose_name_plural = "附件"

    def __str__(self):
        return f"{self.application.pk}-{self.category}"


class UserProfile(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="profile")
    region = models.ForeignKey(Region, on_delete=models.PROTECT, verbose_name="地区")
    can_view_all = models.BooleanField("全局权限", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "账号区域权限"
        verbose_name_plural = "账号区域权限"

    def __str__(self):
        return f"{self.user.username}-{self.region.name}"
