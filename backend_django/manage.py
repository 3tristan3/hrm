#!/usr/bin/env python
"""Django 项目管理入口，提供运行服务、迁移、测试等命令。"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oa_bridge.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
