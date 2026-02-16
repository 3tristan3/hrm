from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("application", "0004_application_apply_region_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="application",
            name="wechat",
            field=models.CharField("微信号", max_length=50, blank=True, default=""),
        ),
    ]
