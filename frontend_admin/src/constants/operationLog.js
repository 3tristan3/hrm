// 操作日志常量与文案映射：提供模块/动作/结果标签兜底与元信息规范化能力。
const FALLBACK_OPERATION_MODULE_LABELS = Object.freeze({
  applications: "应聘记录",
  interviews: "拟面试",
  talent: "人才库",
  jobs: "岗位管理",
  accounts: "账号管理",
});

const FALLBACK_OPERATION_ACTION_LABELS = Object.freeze({
  ADD_TO_INTERVIEW_POOL: "加入拟面试人员",
  BATCH_ADD_TO_INTERVIEW_POOL: "批量加入拟面试人员",
  ADD_TO_TALENT_POOL: "加入人才库",
  BATCH_ADD_TO_TALENT_POOL: "批量加入人才库",
  SCHEDULE_INTERVIEW: "安排面试",
  RESCHEDULE_INTERVIEW: "改期安排",
  CANCEL_INTERVIEW_SCHEDULE: "取消面试",
  SAVE_INTERVIEW_RESULT: "记录面试结果",
  REMOVE_FROM_INTERVIEW_POOL: "移出拟面试",
  BATCH_REMOVE_FROM_INTERVIEW_POOL: "批量移出拟面试",
  MOVE_TALENT_TO_INTERVIEW: "加入拟面试人员",
  BATCH_MOVE_TALENT_TO_INTERVIEW: "批量加入拟面试人员",
  CONFIRM_HIRE: "确认入职",
  BATCH_CONFIRM_HIRE: "批量确认入职",
  DELETE_JOB: "删除岗位",
  BATCH_DEACTIVATE_JOB: "批量下架岗位",
  BATCH_ACTIVATE_JOB: "批量上架岗位",
  BATCH_DELETE_JOB: "批量删除岗位",
  RESET_USER_PASSWORD: "重置密码",
  DELETE_USER: "删除账号",
});

export const DEFAULT_OPERATION_LOG_META = Object.freeze({
  module_labels: FALLBACK_OPERATION_MODULE_LABELS,
  action_labels: FALLBACK_OPERATION_ACTION_LABELS,
  result_labels: {
    success: "成功",
    failed: "失败",
  },
  page_size_options: [20, 30, 50, 100],
  default_recent_days: 90,
  pagination_mode: "cursor",
});

const toPlainObject = (value) =>
  value && typeof value === "object" && !Array.isArray(value) ? value : {};

export const normalizeOperationLogMeta = (payload = {}) => {
  const source = payload && typeof payload === "object" ? payload : {};
  const options = Array.isArray(source.page_size_options)
    ? source.page_size_options
        .map((item) => Number(item))
        .filter((item, index, arr) => Number.isFinite(item) && item > 0 && arr.indexOf(item) === index)
        .sort((a, b) => a - b)
    : [];
  return {
    module_labels: {
      ...DEFAULT_OPERATION_LOG_META.module_labels,
      ...toPlainObject(source.module_labels),
    },
    action_labels: {
      ...DEFAULT_OPERATION_LOG_META.action_labels,
      ...toPlainObject(source.action_labels),
    },
    result_labels: {
      ...DEFAULT_OPERATION_LOG_META.result_labels,
      ...toPlainObject(source.result_labels),
    },
    page_size_options:
      options.length > 0 ? options : [...DEFAULT_OPERATION_LOG_META.page_size_options],
    default_recent_days: Number(source.default_recent_days) > 0
      ? Number(source.default_recent_days)
      : DEFAULT_OPERATION_LOG_META.default_recent_days,
    pagination_mode: source.pagination_mode || DEFAULT_OPERATION_LOG_META.pagination_mode,
  };
};

export const resolveOperationModuleLabel = (value, moduleLabels = {}) =>
  moduleLabels?.[value] || value || "-";

export const resolveOperationActionLabel = (value, actionLabels = {}) =>
  actionLabels?.[value] || value || "-";

export const buildOperationModuleOptions = (logs = [], moduleLabels = {}) => {
  const options = Object.entries(moduleLabels).map(([value, label]) => ({
    value,
    label,
  }));
  const seen = new Set(options.map((item) => item.value));
  logs.forEach((item) => {
    const value = String(item?.module || "").trim();
    if (!value || seen.has(value)) return;
    seen.add(value);
    options.push({ value, label: resolveOperationModuleLabel(value, moduleLabels) });
  });
  return options.sort((a, b) => a.label.localeCompare(b.label, "zh-Hans-CN"));
};
