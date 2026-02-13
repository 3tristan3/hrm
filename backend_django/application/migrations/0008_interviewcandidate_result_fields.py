from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("application", "0007_interviewcandidate_schedule_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="interviewcandidate",
            name="result",
            field=models.CharField(
                blank=True,
                choices=[
                    ("待定", "待定"),
                    ("进入下一轮", "进入下一轮"),
                    ("通过", "通过"),
                    ("淘汰", "淘汰"),
                ],
                default="",
                max_length=20,
                verbose_name="面试结果",
            ),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="result_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="结果记录时间"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="result_note",
            field=models.TextField(blank=True, default="", verbose_name="结果评语"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="score",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="面试评分"),
        ),
    ]

