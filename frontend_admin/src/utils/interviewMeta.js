// 面试元信息工具：提供默认枚举和后端返回值规范化逻辑。
export const defaultInterviewMeta = Object.freeze({
  status_pending: "待安排",
  status_scheduled: "已安排",
  status_completed: "已完成",
  result_pending: "待定",
  result_next_round: "进入下一轮",
  result_pass: "通过",
  result_reject: "淘汰",
  status_choices: [
    { value: "待安排", label: "待安排" },
    { value: "已安排", label: "已安排" },
    { value: "已完成", label: "已完成" },
  ],
  result_choices: [
    { value: "进入下一轮", label: "进入下一轮" },
    { value: "通过", label: "通过" },
    { value: "淘汰", label: "淘汰" },
    { value: "待定", label: "待定" },
  ],
  final_results: ["通过", "淘汰"],
  max_round: 3,
});

export const createInterviewMeta = (payload = {}) => {
  const merged = { ...defaultInterviewMeta, ...(payload || {}) };
  const maxRound = Number(merged.max_round);
  return {
    ...merged,
    status_choices:
      Array.isArray(merged.status_choices) && merged.status_choices.length
        ? merged.status_choices
        : defaultInterviewMeta.status_choices,
    result_choices:
      Array.isArray(merged.result_choices) && merged.result_choices.length
        ? merged.result_choices
        : defaultInterviewMeta.result_choices,
    final_results:
      Array.isArray(merged.final_results) && merged.final_results.length
        ? merged.final_results
        : defaultInterviewMeta.final_results,
    max_round:
      Number.isFinite(maxRound) && maxRound > 0
        ? Math.floor(maxRound)
        : defaultInterviewMeta.max_round,
  };
};
