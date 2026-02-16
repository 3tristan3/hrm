from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Region",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("code", models.CharField(max_length=50, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="Job",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("salary", models.CharField(blank=True, max_length=100)),
                ("education", models.CharField(blank=True, max_length=50)),
                ("is_active", models.BooleanField(default=True)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "region",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jobs", to="application.region"),
                ),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="RegionField",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=50)),
                ("label", models.CharField(max_length=50)),
                ("field_type", models.CharField(choices=[("text", "文本"), ("select", "下拉"), ("number", "数字"), ("date", "日期")], default="text", max_length=20)),
                ("required", models.BooleanField(default=False)),
                ("options", models.JSONField(blank=True, null=True)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "region",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fields", to="application.region"),
                ),
            ],
            options={"ordering": ["order", "id"], "unique_together": {("region", "key")}},
        ),
        migrations.CreateModel(
            name="Application",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50)),
                ("gender", models.CharField(max_length=20)),
                ("phone", models.CharField(max_length=20)),
                ("email", models.EmailField(max_length=254)),
                ("extra_fields", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "job",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="application.job"),
                ),
                (
                    "region",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="application.region"),
                ),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
    ]

