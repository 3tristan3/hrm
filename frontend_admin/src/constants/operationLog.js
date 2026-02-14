export const DEFAULT_OPERATION_LOG_META = Object.freeze({
  module_labels: {},
  action_labels: {},
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
    module_labels: toPlainObject(source.module_labels),
    action_labels: toPlainObject(source.action_labels),
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
