from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("application", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("can_view_all", models.BooleanField(default=False, verbose_name="全局权限")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                (
                    "region",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="application.region", verbose_name="地区"),
                ),
                (
                    "user",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to="auth.user"),
                ),
            ],
            options={
                "verbose_name": "账号区域权限",
                "verbose_name_plural": "账号区域权限",
            },
        ),
    ]

