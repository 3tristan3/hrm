# 需求门禁模板

日期：2026-02-26
负责人：Codex
状态：已完成

## 1. 目标与成功标准
- 目标：
  - 执行生产清理 Phase2 Batch1：剥离上线无关的联调接口与造数/重置命令，同时保证主业务与部署启动不受影响。
- 成功标准：
  - 删除 `mock-oa` 路由与对应视图导出，后端其余 API 与测试通过。
  - 删除 `reset_app_data`、`seed_operator_applications`、`seed_vps_demo_once` 三个管理命令及根目录 `seed_demo_once.sh`。
  - 保持 `deploy.sh`、`docker-compose.yml`、`backend_django/entrypoint.sh` 无改动。
  - 通过后端测试与双前端构建验证。

## 2. 功能边界
- 范围内：
  - 移除联调接口：`POST /api/application/mock-oa/`。
  - 移除开发/演示造数与重置命令文件。
  - 更新相关环境示例注释与清理文档状态。
- 范围外：
  - 不调整业务流程、权限、数据模型。
  - 不修改线上启动链路和容器编排逻辑。
  - 不处理 C 类历史兼容残留（`ApplicationForm.vue` / `vue.config.js` / `public/index.html`）。

## 3. 实施计划
1. 清理 `mock-oa` 视图、导出与 URL 映射。
2. 删除造数/重置命令与脚本，更新 `.env.example` 中联调提示。
3. 跑 `python manage.py test` 与前端 `npm run build` 回归。
4. 更新清理清单，标记 B 类第一批完成状态与后续批次建议。

## 4. 输出规范
- 改动文件：
  - `backend_django/application/api_views/public.py`
  - `backend_django/application/api_views/__init__.py`
  - `backend_django/application/urls.py`
  - `backend_django/application/management/commands/reset_app_data.py`（删除）
  - `backend_django/application/management/commands/seed_operator_applications.py`（删除）
  - `backend_django/application/management/commands/seed_vps_demo_once.py`（删除）
  - `seed_demo_once.sh`（删除）
  - `backend_django/.env.example`
  - `docs/engineering/cleanup/production-cleanup-inventory-2026-02-26.md`
  - `docs/engineering/requirements/2026-02-26-prod-cleanup-phase2-batch1.md`
- 行为/API 影响：
  - 移除联调接口 `POST /api/application/mock-oa/`。
  - 移除 3 个 CLI 管理命令与 1 个演示脚本。
- 测试/构建预期：
  - 后端测试通过。
  - `frontend_vue`、`frontend_admin` 构建通过。
- 交付形式：
  - 代码与文档变更 + 验证结果 + 最小提交建议。

## 5. 禁止越界规则
- 凡不在本文件范围内的事项，均记录为后续项；未经明确批准不得实现。
