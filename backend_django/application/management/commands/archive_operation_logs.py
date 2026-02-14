"""归档历史操作日志到冷表，降低主日志表体积。"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from application.models import OperationLog, OperationLogArchive


class Command(BaseCommand):
    help = "将超过指定天数的操作日志归档到 operation_log_archive 表"

    def add_arguments(self, parser):
        parser.add_argument(
            "--before-days",
            type=int,
            default=180,
            help="归档多少天之前的日志（默认 180）",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="单批处理数量（默认 1000）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅输出预估数量，不执行写入/删除",
        )

    def handle(self, *args, **options):
        before_days = max(int(options["before_days"]), 1)
        batch_size = max(int(options["batch_size"]), 100)
        dry_run = bool(options["dry_run"])
        cutoff = timezone.now() - timedelta(days=before_days)

        queryset = OperationLog.objects.filter(created_at__lt=cutoff).order_by("id")
        total = queryset.count()
        self.stdout.write(
            self.style.NOTICE(
                f"准备归档 created_at < {cutoff.isoformat()} 的日志，共 {total} 条。"
            )
        )
        if total == 0:
            return
        if dry_run:
            self.stdout.write(self.style.WARNING("dry-run 模式，未执行归档。"))
            return

        processed = 0
        while True:
            batch = list(queryset[:batch_size])
            if not batch:
                break

            archive_rows = [
                OperationLogArchive(
                    source_log_id=item.id,
                    operator_username=item.operator_username,
                    operator_role=item.operator_role,
                    operator_region_name=item.operator_region_name,
                    module=item.module,
                    action=item.action,
                    target_type=item.target_type,
                    target_id=item.target_id,
                    target_label=item.target_label,
                    result=item.result,
                    summary=item.summary,
                    details=item.details or {},
                    request_id=item.request_id,
                    created_at=item.created_at,
                )
                for item in batch
            ]
            ids = [item.id for item in batch]
            with transaction.atomic():
                OperationLogArchive.objects.bulk_create(archive_rows, ignore_conflicts=True)
                OperationLog.objects.filter(id__in=ids).delete()
            processed += len(ids)
            self.stdout.write(f"已归档 {processed}/{total} 条")

        self.stdout.write(self.style.SUCCESS(f"归档完成，共处理 {processed} 条日志。"))
