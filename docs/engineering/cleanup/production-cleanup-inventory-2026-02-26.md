# 生产无关项梳理清单（2026-02-26）

范围：用于“真正上线”场景的剥离评估。  
说明：按风险分级，不直接删除高风险项。

## A. 可立即清理（低风险，本地垃圾/缓存，已执行）

- `backend_django/db.sqlite3`（未跟踪）：本地 SQLite 文件，当前后端已强制 MySQL。（已清理）
- `backend_django/db_dev.sqlite3`（未跟踪）：本地 SQLite 文件。（已清理）
- `backend_django/db.sqlite3-journal`（未跟踪）：SQLite 日志文件。（已清理）
- `omp.cache`（未跟踪）：终端缓存文件。（已清理）
- `pwsh.21e75840-cbd8-47d1-bc50-21fdf6415da9.omp.cache`（未跟踪）：终端缓存文件。（已清理）
- `pwsh.c9886e5b-920c-4328-9d44-4c903bcb8184.omp.cache`（未跟踪）：终端缓存文件。（已清理）
- `frontend_admin/.tmp-dev.stdout.log`（未跟踪）：本地 dev 输出日志。（已清理）
- `frontend_admin/.tmp-dev.stderr.log`（未跟踪）：本地 dev 输出日志。（已清理）
- `.tmp-pydeps/`（未跟踪）：本地临时 Python 依赖目录。（已清理）

## B. 明确“开发/联调/演示”用途（生产可剥离，分批执行中）

- `backend_django/application/api_views/public.py` 的 `MockOAView` 与路由 `POST /api/application/mock-oa/`：
  - 用途：联调模拟。
  - 现状：前端未检索到调用。（Phase2 Batch1 已移除）
- `backend_django/.env.example` 中 `OA_API_URL=http://127.0.0.1:8000/api/application/mock-oa/` 注释：
  - 用途：本地联调提示，非生产配置。
  - 现状：已从环境示例中移除该提示。（Phase2 Batch1 已完成）
- `backend_django/application/management/commands/reset_app_data.py`：
  - 用途：开发环境重置业务数据。（Phase2 Batch1 已移除）
- `backend_django/application/management/commands/seed_operator_applications.py`：
  - 用途：测试造数。（Phase2 Batch1 已移除）
- `backend_django/application/management/commands/seed_vps_demo_once.py`：
  - 用途：演示环境一次性造数。（Phase2 Batch1 已移除）
- `seed_demo_once.sh`：
  - 用途：调用演示造数命令的便捷脚本。（Phase2 Batch1 已移除）
- `start_all.ps1`（本地未跟踪）：
  - 用途：本地一键启动（`.gitignore` 已忽略，不会进入线上提交）。

## C. 高概率历史兼容残留（建议单独确认后删）

- `frontend_vue/src/components/ApplicationForm.vue`（已跟踪）：
  - 代码注明“历史占位组件”，且当前未发现引用。
- `frontend_vue/vue.config.js`（已跟踪）：
  - 仅为 Vue CLI 兼容占位，当前构建走 Vite。
- `frontend_vue/public/index.html`（已跟踪）：
  - 当前入口使用根 `index.html`，该文件疑似历史残留。

## D. 不建议剥离（线上启动链路依赖）

- `backend_django/application/management/commands/ensure_default_regions.py`：
  - `entrypoint.sh`、`start_all.ps1` 使用。
- `backend_django/application/management/commands/ensure_admin_user.py`：
  - `entrypoint.sh`、`start_all.ps1` 使用。
- `backend_django/application/default_regions.py`：
  - `ensure_default_regions` 与多条初始化命令依赖。
- `deploy.sh`、`docker-compose.yml`、`backend_django/entrypoint.sh`：
  - 线上部署/启动主链路。

## E. 运行时无依赖的协作文件（可按团队策略决定是否保留）

- `docs/engineering/**`：
  - 用途：需求门禁、清理记录、工程工具说明。
  - 说明：对运行时无依赖，但对协作与审计有价值。
- `.claude/settings.local.json`：
  - 用途：本地智能体工具配置。
  - 建议：若目标是纯运行时仓库，可单独评估移除或改为本地忽略。

## 建议剥离顺序

1. A 类已完成：仅清理本地垃圾与缓存（不改业务代码）。
2. B 类 Phase2 Batch1 已完成：移除 `mock-oa` 与造数/重置命令。
3. 下一步做 B 类剩余项：仅保留本地自用脚本策略确认（如 `start_all.ps1` 是否继续本地保留）。
4. 最后做 C 类：删除历史兼容残留，并回归前端构建验证。
