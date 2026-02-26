from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("application", "0014_interviewcandidate_hired_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="interviewcandidate",
            name="sms_error",
            field=models.TextField(blank=True, default="", verbose_name="短信失败原因"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="sms_last_attempt_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="短信最近尝试时间"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="sms_message_id",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="短信消息ID"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="sms_provider_code",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="短信供应商状态码"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="sms_provider_message",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="短信供应商返回信息"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="sms_retry_count",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="短信重试次数"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="sms_sent_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="短信发送成功时间"),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="sms_status",
            field=models.CharField(
                choices=[
                    ("idle", "未发送"),
                    ("sending", "发送中"),
                    ("success", "发送成功"),
                    ("failed", "发送失败"),
                ],
                default="idle",
                max_length=20,
                verbose_name="短信状态",
            ),
        ),
        migrations.AddField(
            model_name="interviewcandidate",
            name="sms_updated_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="短信状态更新时间"),
        ),
    ]
