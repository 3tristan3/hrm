"""业务数据模型定义，包含应聘记录、拟面试人员与轮次快照等核心实体。"""
import secrets

from django.db import models


def generate_attachment_token() -> str:
    return secrets.token_urlsafe(24)


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
    is_deleted = models.BooleanField("逻辑删除", default=False)
    deleted_at = models.DateTimeField("删除时间", null=True, blank=True)
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
    attachment_token = models.CharField(
        "附件令牌",
        max_length=48,
        db_index=True,
        default=generate_attachment_token,
        editable=False,
    )
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


class InterviewCandidate(models.Model):
    """拟面试池记录：保存当前轮次、当前安排和当前结果。"""

    STATUS_PENDING = "待安排"
    STATUS_SCHEDULED = "已安排"
    STATUS_COMPLETED = "已完成"

    STATUS_CHOICES = [
        (STATUS_PENDING, "待安排"),
        (STATUS_SCHEDULED, "已安排"),
        (STATUS_COMPLETED, "已完成"),
    ]

    RESULT_PENDING = "待定"
    RESULT_NEXT_ROUND = "进入下一轮"
    RESULT_PASS = "通过"
    RESULT_REJECT = "淘汰"
    RESULT_CHOICES = [
        (RESULT_PENDING, "待定"),
        (RESULT_NEXT_ROUND, "进入下一轮"),
        (RESULT_PASS, "通过"),
        (RESULT_REJECT, "淘汰"),
    ]

    SMS_STATUS_IDLE = "idle"
    SMS_STATUS_SENDING = "sending"
    SMS_STATUS_SUCCESS = "success"
    SMS_STATUS_FAILED = "failed"
    SMS_STATUS_CHOICES = [
        (SMS_STATUS_IDLE, "未发送"),
        (SMS_STATUS_SENDING, "发送中"),
        (SMS_STATUS_SUCCESS, "发送成功"),
        (SMS_STATUS_FAILED, "发送失败"),
    ]
    OA_PUSH_STATUS_IDLE = "idle"
    OA_PUSH_STATUS_PENDING = "pending"
    OA_PUSH_STATUS_SUCCESS = "success"
    OA_PUSH_STATUS_FAILED = "failed"
    OA_PUSH_STATUS_CHOICES = [
        (OA_PUSH_STATUS_IDLE, "未推送"),
        (OA_PUSH_STATUS_PENDING, "推送中"),
        (OA_PUSH_STATUS_SUCCESS, "推送成功"),
        (OA_PUSH_STATUS_FAILED, "推送失败"),
    ]
    OFFER_STATUS_PENDING = "pending_hire"
    OFFER_STATUS_ISSUED = "offer_issued"
    OFFER_STATUS_CONFIRMED = "confirmed_hire"
    OFFER_STATUS_REJECTED = "offer_rejected"
    OFFER_STATUS_CHOICES = [
        (OFFER_STATUS_PENDING, "待发offer"),
        (OFFER_STATUS_ISSUED, "已发offer"),
        (OFFER_STATUS_CONFIRMED, "待确认入职"),
        (OFFER_STATUS_REJECTED, "拒绝offer"),
    ]

    application = models.OneToOneField(
        Application,
        related_name="interview_candidate",
        on_delete=models.CASCADE,
        verbose_name="应聘记录",
    )
    status = models.CharField(
        "面试状态", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    interview_round = models.PositiveSmallIntegerField("面试轮次", default=1)
    interview_at = models.DateTimeField("面试时间", null=True, blank=True)
    interviewer = models.CharField("面试官", max_length=100, blank=True, default="")
    interviewers = models.JSONField("面试官列表", default=list, blank=True)
    interview_location = models.CharField("面试地点", max_length=200, blank=True, default="")
    result = models.CharField("面试结果", max_length=20, choices=RESULT_CHOICES, blank=True, default="")
    score = models.PositiveSmallIntegerField("面试评分", null=True, blank=True)
    interviewer_scores = models.JSONField("面试官评分明细", default=list, blank=True)
    result_note = models.TextField("结果评语", blank=True, default="")
    result_at = models.DateTimeField("结果记录时间", null=True, blank=True)
    is_hired = models.BooleanField("已确认入职", default=False)
    hired_at = models.DateTimeField("确认入职时间", null=True, blank=True)
    offer_status = models.CharField(
        "Offer状态",
        max_length=30,
        choices=OFFER_STATUS_CHOICES,
        default=OFFER_STATUS_PENDING,
    )
    note = models.TextField("备注", blank=True, default="")
    sms_status = models.CharField(
        "短信状态",
        max_length=20,
        choices=SMS_STATUS_CHOICES,
        default=SMS_STATUS_IDLE,
    )
    sms_retry_count = models.PositiveSmallIntegerField("短信重试次数", default=0)
    sms_last_attempt_at = models.DateTimeField("短信最近尝试时间", null=True, blank=True)
    sms_sent_at = models.DateTimeField("短信发送成功时间", null=True, blank=True)
    sms_updated_at = models.DateTimeField("短信状态更新时间", null=True, blank=True)
    sms_error = models.TextField("短信失败原因", blank=True, default="")
    sms_provider_code = models.CharField("短信供应商状态码", max_length=50, blank=True, default="")
    sms_provider_message = models.CharField("短信供应商返回信息", max_length=255, blank=True, default="")
    sms_message_id = models.CharField("短信消息ID", max_length=100, blank=True, default="")
    oa_push_status = models.CharField(
        "OA推送状态",
        max_length=20,
        choices=OA_PUSH_STATUS_CHOICES,
        default=OA_PUSH_STATUS_IDLE,
    )
    oa_push_retry_count = models.PositiveSmallIntegerField("OA推送重试次数", default=0)
    oa_push_last_attempt_at = models.DateTimeField("OA推送最近尝试时间", null=True, blank=True)
    oa_push_success_at = models.DateTimeField("OA推送成功时间", null=True, blank=True)
    oa_push_request_id = models.CharField("OA流程请求ID", max_length=64, blank=True, default="")
    oa_push_error_code = models.CharField("OA推送错误码", max_length=50, blank=True, default="")
    oa_push_error_message = models.TextField("OA推送失败原因", blank=True, default="")
    oa_push_oa_code = models.CharField("OA返回码", max_length=50, blank=True, default="")
    oa_push_oa_message = models.CharField("OA返回信息", max_length=255, blank=True, default="")
    oa_push_payload_snapshot = models.JSONField("OA推送请求快照", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-created_at", "id"]
        verbose_name = "拟面试人员"
        verbose_name_plural = "拟面试人员"

    def __str__(self):
        return f"{self.application.name}-{self.application.job.title}"


class InterviewRoundRecord(models.Model):
    """轮次快照：每轮结果落盘，支持通过人员多轮信息展示。"""

    candidate = models.ForeignKey(
        InterviewCandidate,
        related_name="round_records",
        on_delete=models.CASCADE,
        verbose_name="拟面试人员",
    )
    round_no = models.PositiveSmallIntegerField("面试轮次")
    interview_at = models.DateTimeField("面试时间", null=True, blank=True)
    interviewer = models.CharField("面试官", max_length=100, blank=True, default="")
    interviewers = models.JSONField("面试官列表", default=list, blank=True)
    score = models.PositiveSmallIntegerField("面试评分", null=True, blank=True)
    interviewer_scores = models.JSONField("面试官评分明细", default=list, blank=True)
    result = models.CharField(
        "面试结果",
        max_length=20,
        choices=InterviewCandidate.RESULT_CHOICES,
        blank=True,
        default="",
    )
    result_note = models.TextField("结果评语", blank=True, default="")
    created_at = models.DateTimeField("记录时间", auto_now_add=True)

    class Meta:
        ordering = ["round_no", "id"]
        verbose_name = "面试轮次记录"
        verbose_name_plural = "面试轮次记录"
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "round_no"], name="uniq_interview_candidate_round_no"
            )
        ]

    def __str__(self):
        return f"{self.candidate.application.name}-第{self.round_no}轮"


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


class OperationLog(models.Model):
    """管理端操作审计日志。"""

    RESULT_SUCCESS = "success"
    RESULT_FAILED = "failed"
    RESULT_CHOICES = [
        (RESULT_SUCCESS, "成功"),
        (RESULT_FAILED, "失败"),
    ]

    operator = models.ForeignKey(
        "auth.User",
        related_name="operation_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="操作人",
    )
    operator_username = models.CharField("操作账号", max_length=150, blank=True, default="")
    operator_role = models.CharField("操作角色", max_length=50, blank=True, default="")
    operator_region_name = models.CharField("操作地区", max_length=50, blank=True, default="")
    region = models.ForeignKey(
        Region,
        related_name="operation_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="所属地区",
    )
    module = models.CharField("模块", max_length=50)
    action = models.CharField("动作", max_length=80)
    target_type = models.CharField("对象类型", max_length=50, blank=True, default="")
    target_id = models.PositiveIntegerField("对象ID", null=True, blank=True)
    target_label = models.CharField("对象名称", max_length=200, blank=True, default="")
    application = models.ForeignKey(
        Application,
        related_name="operation_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联应聘记录",
    )
    interview_candidate = models.ForeignKey(
        InterviewCandidate,
        related_name="operation_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联拟面试记录",
    )
    result = models.CharField("结果", max_length=20, choices=RESULT_CHOICES, default=RESULT_SUCCESS)
    summary = models.CharField("摘要", max_length=255, blank=True, default="")
    details = models.JSONField("详情", default=dict, blank=True)
    request_id = models.CharField("请求链路ID", max_length=64, blank=True, default="")
    created_at = models.DateTimeField("记录时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"
        indexes = [
            models.Index(fields=["created_at"], name="oplog_created"),
            models.Index(fields=["module", "action"], name="oplog_mod_act"),
            models.Index(fields=["result"], name="oplog_result"),
            models.Index(fields=["operator_username"], name="oplog_operator"),
            models.Index(fields=["application"], name="oplog_app"),
            models.Index(fields=["region"], name="oplog_region"),
        ]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.operator_username} {self.action}"


class OperationLogArchive(models.Model):
    """历史操作日志归档（冷数据）。"""

    source_log_id = models.PositiveIntegerField("原日志ID", unique=True)
    operator_username = models.CharField("操作账号", max_length=150, blank=True, default="")
    operator_role = models.CharField("操作角色", max_length=50, blank=True, default="")
    operator_region_name = models.CharField("操作地区", max_length=50, blank=True, default="")
    module = models.CharField("模块", max_length=50)
    action = models.CharField("动作", max_length=80)
    target_type = models.CharField("对象类型", max_length=50, blank=True, default="")
    target_id = models.PositiveIntegerField("对象ID", null=True, blank=True)
    target_label = models.CharField("对象名称", max_length=200, blank=True, default="")
    result = models.CharField("结果", max_length=20, choices=OperationLog.RESULT_CHOICES, default=OperationLog.RESULT_SUCCESS)
    summary = models.CharField("摘要", max_length=255, blank=True, default="")
    details = models.JSONField("详情", default=dict, blank=True)
    request_id = models.CharField("请求链路ID", max_length=64, blank=True, default="")
    created_at = models.DateTimeField("记录时间")
    archived_at = models.DateTimeField("归档时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "操作日志归档"
        verbose_name_plural = "操作日志归档"

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.operator_username} {self.action}"
