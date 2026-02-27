// 面试状态与结果文案规则：供拟面试/通过/人才库统一复用。

const toCnRound = (roundValue) => {
  const round = Math.max(Number(roundValue || 1), 1);
  const map = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"];
  if (round <= 10) return map[round];
  return String(round);
};

const roundFaceLabel = (item) => `${toCnRound(item?.interview_round)}面`;

const isDirectTalentReject = (item, interviewMeta = {}) => {
  if (!item) return false;
  const rejectValue = interviewMeta.result_reject || "淘汰";
  if (item.result !== rejectValue) return false;
  const hasRoundSnapshot = Boolean(item.first_round_at || item.second_round_at || item.third_round_at);
  const hasInterviewTrace = Boolean(item.interview_at || item.interviewer || item.interview_location);
  return !hasRoundSnapshot && !hasInterviewTrace;
};

export const getInterviewStatusClass = (item, interviewMeta = {}) => {
  if (item?.offer_status === "offer_rejected") return "chip-reject";
  if (item?.offer_status === "confirmed_hire") return "chip-hired";
  if (item?.offer_status === "pending_hire" && item?.result === interviewMeta.result_pass) {
    return "chip-pass";
  }
  if (item?.is_hired) return "chip-hired";
  if (item?.status === interviewMeta.status_scheduled) return "chip-scheduled";
  if (item?.result === interviewMeta.result_next_round || item?.result === interviewMeta.result_pass) {
    return "chip-pass";
  }
  if (item?.result === interviewMeta.result_reject) return "chip-reject";
  if (item?.result === interviewMeta.result_pending) return "chip-pending";
  return "chip-subtle";
};

export const getInterviewStatusText = (item, interviewMeta = {}) => {
  const statusPending = interviewMeta.status_pending || "待安排";
  const resultPending = interviewMeta.result_pending || "待定";
  const resultPass = interviewMeta.result_pass || "通过";
  const resultReject = interviewMeta.result_reject || "淘汰";
  const roundLabel = roundFaceLabel(item);

  if (item?.offer_status === "offer_rejected") return "拒绝offer";
  if (item?.offer_status === "confirmed_hire") return "确认入职";
  if (item?.offer_status === "pending_hire" && item?.result === interviewMeta.result_pass) {
    return "待确认入职";
  }
  if (item?.is_hired) return "确认入职";
  if (item?.status === interviewMeta.status_scheduled) return `已安排${roundLabel}`;
  if (item?.result === interviewMeta.result_pending) return `${roundLabel}${resultPending}`;
  if (item?.result === interviewMeta.result_next_round || item?.result === interviewMeta.result_pass) {
    return `${roundLabel}${resultPass}`;
  }
  if (isDirectTalentReject(item, interviewMeta)) return "简历初筛未通过";
  if (item?.result === interviewMeta.result_reject) return `${roundLabel}${resultReject}`;
  if (item?.status === statusPending) return `待安排${roundLabel}`;
  return item?.status || statusPending;
};
