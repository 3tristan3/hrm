import { computed } from "vue";

const SMS_DEFAULT_FAIL_REASON = "短信网关返回失败（示例）";

const parseRetryCount = (value) => {
  const count = Number(value);
  if (!Number.isFinite(count) || count < 0) return 0;
  return Math.floor(count);
};

const normalizeSmsStatus = (value) => {
  const raw = String(value || "").trim();
  if (!raw) return "idle";
  const lowered = raw.toLowerCase();
  if (
    ["sending", "queued", "pending", "processing"].includes(lowered) ||
    raw.includes("发送中")
  ) {
    return "sending";
  }
  if (
    ["success", "sent", "delivered", "ok"].includes(lowered) ||
    raw.includes("成功")
  ) {
    return "success";
  }
  if (
    ["failed", "fail", "error", "rejected"].includes(lowered) ||
    raw.includes("失败")
  ) {
    return "failed";
  }
  return "idle";
};

const formatSmsScheduleTime = (value) => {
  if (!value) return "待定";
  const normalized = String(value).includes("T")
    ? String(value)
    : String(value).replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return String(value);
  const pad = (num) => String(num).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(
    date.getHours()
  )}:${pad(date.getMinutes())}`;
};

export const useInterviewSmsShell = ({ interviewScheduleForm, formatTime, emit }) => {
  const smsPreviewText = computed(() => {
    const name = interviewScheduleForm.name || "候选人";
    const round = interviewScheduleForm.interview_round || 1;
    const time = formatSmsScheduleTime(interviewScheduleForm.interview_at);
    const location = interviewScheduleForm.interview_location || "待补充";
    const note = interviewScheduleForm.note || "无";
    const jobTitle = interviewScheduleForm.job_title || "应聘岗位";
    return `【亚通集团面试通知】${name}，您好！您应聘的「${jobTitle}」已安排第${round}轮面试，时间：${time}，地点/链接：${location}，${note}。如需改期请及时联系。`;
  });

  const smsStatusShell = (item) => {
    const status = normalizeSmsStatus(
      item?.sms_status || item?.sms_send_status || item?.sms_delivery_status
    );
    const labelMap = {
      idle: "未发送",
      sending: "发送中",
      success: "发送成功",
      failed: "发送失败",
    };
    return {
      status,
      label: labelMap[status] || "未发送",
      phone: item?.phone || "",
      retryCount: parseRetryCount(item?.sms_retry_count ?? item?.sms_retry_times),
      updatedAt: item?.sms_updated_at || item?.sms_sent_at || item?.sms_last_attempt_at || "",
      error:
        status === "failed"
          ? item?.sms_error || item?.sms_last_error || SMS_DEFAULT_FAIL_REASON
          : "",
    };
  };

  const smsStatusTime = (item) => {
    const time = smsStatusShell(item).updatedAt;
    if (!time) return "暂无";
    return formatTime(time);
  };

  const smsCanRetry = (item) =>
    smsStatusShell(item).status === "failed" && Boolean(item?.id);

  const retrySms = (item) => {
    if (!smsCanRetry(item)) return;
    emit("retry-sms", item);
  };

  return {
    smsPreviewText,
    smsStatusShell,
    smsStatusTime,
    smsCanRetry,
    retrySms,
  };
};
