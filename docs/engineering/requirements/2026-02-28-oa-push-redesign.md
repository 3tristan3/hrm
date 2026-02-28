# OA 推送能力重构需求（2026-02-28）

## 1. 目标

- 在“确认入职”后触发 OA 流程创建（`doCreateRequest`）。
- 不调用 `regist`，仅使用已发放的 `appid`、`secrit`、`spk`。
- 支持字段映射配置化，便于后续扩展十多个字段（含简历模板字段）。
- 支持失败原因沉淀、自动重试、人工重发。
- 失败不阻断确认入职主流程。

## 2. 范围

### 2.1 范围内

- OA 鉴权：`applytoken` 获取 token。
- OA 业务调用：`/api/workflow/paService/doCreateRequest`。
- 推送字段映射：主表、明细、扩展参数配置化。
- 推送状态落库：成功、失败、重试次数、失败原因、OA 返回信息。
- 重发能力：单条手动重发 + 自动重试策略。

### 2.2 范围外

- `regist` 自动化。
- OA 审批结果回写本系统。
- 前端页面改造（本期先提供后端能力与接口）。

## 3. 核心约束

- 主流程优先：确认入职成功后，再执行 OA 推送；推送失败不回滚主流程。
- 幂等保护：同一候选人在同一模板版本下避免重复创建流程。
- 敏感信息不入库：`secrit`、`spk` 不写数据库，仅环境变量读取。
- 默认请求头 `Content-Type` 为 `application/x-www-form-urlencoded; charset=utf-8`，可配置切换。

## 4. 配置设计

## 4.1 基础配置（环境变量）

- `OA_PUSH_ENABLED`
- `OA_PUSH_BASE_URL`
- `OA_PUSH_APP_ID`
- `OA_PUSH_SECRIT`
- `OA_PUSH_SPK`
- `OA_PUSH_USER_ID`
- `OA_PUSH_WORKFLOW_ID`
- `OA_PUSH_TOKEN_TTL_SECONDS`
- `OA_PUSH_REQUEST_TIMEOUT_SECONDS`
- `OA_PUSH_REQUEST_NAME_TEMPLATE`
- `OA_PUSH_REQUEST_LEVEL`
- `OA_PUSH_REMARK_TEMPLATE`
- `OA_PUSH_CONTENT_TYPE`

## 4.2 字段映射配置（环境变量 JSON）

- `OA_PUSH_MAIN_FIELD_MAPPINGS`（主表映射）
- `OA_PUSH_DETAIL_DATA_TEMPLATE`（明细模板）
- `OA_PUSH_OTHER_PARAMS`（扩展参数）

`OA_PUSH_MAIN_FIELD_MAPPINGS` 推荐结构：

```json
[
  { "oa_field": "xm", "source": "application.name" },
  { "oa_field": "sjh", "source": "application.phone" },
  { "oa_field": "xl", "source": "application.education_level" },
  { "oa_field": "bz", "source": "candidate.note", "default": "" }
]
```

说明：

- `oa_field`：OA 表单字段名（数据库字段名）。
- `source`：系统内取值路径（支持 `application.*`、`candidate.*`、`constant.*`）。
- `default`：取值为空时默认值。

## 5. 数据模型扩展

在 `InterviewCandidate` 增加 OA 推送状态字段：

- `oa_push_status`：`idle/pending/success/failed`
- `oa_push_retry_count`
- `oa_push_last_attempt_at`
- `oa_push_success_at`
- `oa_push_request_id`
- `oa_push_error_code`
- `oa_push_error_message`
- `oa_push_oa_code`
- `oa_push_oa_message`
- `oa_push_payload_snapshot`（JSON）

## 6. 失败分类与重试策略

## 6.1 失败分类

- `OA_DISABLED`
- `OA_CONFIG_ERROR`
- `OA_PAYLOAD_INVALID`
- `OA_TOKEN_EXPIRED`
- `OA_AUTH_ERROR`
- `OA_PERMISSION_ERROR`
- `OA_PARAM_ERROR`
- `OA_SERVER_ERROR`
- `OA_NETWORK_ERROR`
- `OA_RUNTIME_ERROR`

## 6.2 自动重试策略

- 自动重试类型：`OA_TOKEN_EXPIRED`、`OA_SERVER_ERROR`、`OA_NETWORK_ERROR`。
- 最大重试次数：3（可配置）。
- 退避策略：立即一次（token 刷新），后续由人工重发或定时命令处理。

## 6.3 人工重发

- 新增后端接口：`POST /api/admin/passed-candidates/<id>/retry-oa-push/`
- 仅允许通过权限范围内账号操作。
- 重发后保留历史失败原因与次数。

## 7. 流程编排

1. 批量确认入职成功。
2. 遍历候选人调用 OA 推送服务。
3. 每个候选人独立更新 OA 推送状态，不相互影响。
4. 返回主流程成功结果，同时附带推送成功/失败统计。

## 8. 日志与可观测

- 操作日志新增动作：
  - `OA_PUSH_SUCCESS`
  - `OA_PUSH_FAILED`
  - `OA_PUSH_RETRY`
- 日志详情至少包含：
  - 候选人 ID
  - OA requestId（成功时）
  - error_code / error_message（失败时）
  - retry_count

## 9. 验收标准

- 开启 OA 推送后，确认入职可触发 OA 调用并落库状态。
- 关闭 OA 推送时，主流程正常，状态标记为 `OA_DISABLED`。
- 字段映射改动无需改代码，仅改配置可生效。
- 失败原因可查询且可人工重发。
- 重发成功后状态变更为 `success` 并记录 `oa_push_request_id`。

## 10. 迁移策略

- 无迁移，直接替换。
