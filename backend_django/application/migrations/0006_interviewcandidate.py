from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("application", "0005_application_wechat"),
    ]

    operations = [
        migrations.CreateModel(
            name="InterviewCandidate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("待安排", "待安排"),
                            ("已安排", "已安排"),
                            ("已完成", "已完成"),
                        ],
                        default="待安排",
                        max_length=20,
                        verbose_name="面试状态",
                    ),
                ),
                ("note", models.TextField(blank=True, default="", verbose_name="备注")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "application",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interview_candidate",
                        to="application.application",
                        verbose_name="应聘记录",
                    ),
                ),
            ],
            options={
                "verbose_name": "拟面试人员",
                "verbose_name_plural": "拟面试人员",
                "ordering": ["-created_at", "id"],
            },
        ),
    ]
