from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("application", "0006_interviewcandidate"),
    ]

    operations = [
        migrations.AddField(
            model_name="interviewcandidate",
            name="interview_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="面试时间"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="interview_location",
            field=models.CharField(blank=True, default="", max_length=200, verbose_name="面试地点"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="interview_round",
            field=models.PositiveSmallIntegerField(default=1, verbose_name="面试轮次"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="interviewer",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="面试官"),
        ),
    ]

