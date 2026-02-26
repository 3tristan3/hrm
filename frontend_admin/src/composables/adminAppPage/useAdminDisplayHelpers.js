import { getInterviewStatusClass, getInterviewStatusText } from "../../utils/interviewStatus";
import {
  resolveOperationActionLabel,
  resolveOperationModuleLabel,
} from "../../constants/operationLog";

export function createAdminDisplayHelpers({
  regions,
  operationLogMeta,
  interviewMeta,
}) {
  const regionName = (id) => regions.value.find((region) => region.id === id)?.name || "-";
  const operationModuleLabel = (value) =>
    resolveOperationModuleLabel(value, operationLogMeta.module_labels);
  const operationActionLabel = (value) =>
    resolveOperationActionLabel(value, operationLogMeta.action_labels);
  const operationResultLabel = (value) =>
    operationLogMeta.result_labels?.[value] || value || "-";
  const operationResultClass = (value) =>
    value === "failed" ? "chip-reject" : "chip-pass";
  const interviewStatusClass = (item) => getInterviewStatusClass(item, interviewMeta);
  const interviewStatusText = (item) => getInterviewStatusText(item, interviewMeta);

  const formatTime = (value) => {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "-";
    return date.toLocaleString();
  };

  const canScheduleInterview = (item) =>
    !(
      item.status === interviewMeta.status_completed &&
      interviewMeta.final_results.includes(item.result || "")
    );

  const scheduleActionLabel = (item) => {
    if (!canScheduleInterview(item)) return "不可安排";
    return item.interview_at ? "改期安排" : "安排面试";
  };

  return {
    regionName,
    operationModuleLabel,
    operationActionLabel,
    operationResultLabel,
    operationResultClass,
    interviewStatusClass,
    interviewStatusText,
    formatTime,
    canScheduleInterview,
    scheduleActionLabel,
  };
}
