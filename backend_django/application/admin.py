"""Django Admin 注册与展示配置：用于后台查看和维护核心业务模型。"""
from django.contrib import admin

from .models import (
    Application,
    ApplicationAttachment,
    InterviewCandidate,
    InterviewRoundRecord,
    Job,
    Region,
    RegionField,
    UserProfile,
)

admin.site.site_header = "应聘信息管理后台"
admin.site.site_title = "应聘填报后台"
admin.site.index_title = "数据管理"


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "order")
    search_fields = ("name", "code")
    readonly_fields = ("name", "code", "is_active", "order")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RegionField)
class RegionFieldAdmin(admin.ModelAdmin):
    list_display = ("label", "key", "region", "field_type", "required", "order")
    list_filter = ("region",)
    readonly_fields = ("label", "key", "region", "field_type", "required", "options", "order")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "region", "salary", "education", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("region",)
    search_fields = ("title",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "region", "job", "created_at")
    list_filter = ("region", "job")
    search_fields = ("name", "phone", "email")


@admin.register(ApplicationAttachment)
class ApplicationAttachmentAdmin(admin.ModelAdmin):
    list_display = ("application", "category", "file", "created_at")
    list_filter = ("category",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "region", "can_view_all", "created_at")
    list_filter = ("region", "can_view_all")


@admin.register(InterviewCandidate)
class InterviewCandidateAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "interview_round",
        "interview_at",
        "interviewer",
        "interview_location",
        "result",
        "score",
        "status",
        "updated_at",
    )
    list_filter = ("status", "interview_round")
    search_fields = ("application__name", "application__phone", "interviewer")


@admin.register(InterviewRoundRecord)
class InterviewRoundRecordAdmin(admin.ModelAdmin):
    list_display = (
        "candidate",
        "round_no",
        "interview_at",
        "interviewer",
        "score",
        "result",
        "created_at",
    )
    list_filter = ("round_no", "result")
    search_fields = ("candidate__application__name", "candidate__application__phone", "interviewer")
