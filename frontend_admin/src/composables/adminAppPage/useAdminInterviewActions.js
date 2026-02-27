import { toDateTimeLocal } from "../../utils/detailFormatters";

const normalizeInterviewerNames = (values = []) => {
  const normalized = [];
  const seen = new Set();
  (values || []).forEach((raw) => {
    const name = String(raw || "").trim();
    if (!name || seen.has(name)) return;
    seen.add(name);
    normalized.push(name);
  });
  return normalized;
};

const splitLegacyInterviewer = (text) => {
  let raw = String(text || "").trim();
  if (!raw) return [];
  ["、", "，", ";", "；", "/", "|"].forEach((separator) => {
    raw = raw.replaceAll(separator, ",");
  });
  return normalizeInterviewerNames(raw.split(","));
};

const toScheduleInterviewerRows = (item = {}) => {
  const names = normalizeInterviewerNames(item.interviewers || []);
  if (names.length) return names;
  const legacy = splitLegacyInterviewer(item.interviewer);
  if (legacy.length) return legacy;
  return [""];
};

const toResultScoreRows = (item = {}) => {
  const rows = Array.isArray(item.interviewer_scores)
    ? item.interviewer_scores
        .map((row) => ({
          interviewer: String(row?.interviewer || "").trim(),
          score: row?.score ?? null,
        }))
        .filter((row) => row.interviewer)
    : [];
  if (rows.length) return rows;
  const names = normalizeInterviewerNames(item.interviewers || []);
  if (names.length) {
    if (names.length === 1 && item.score !== null && item.score !== undefined) {
      return [{ interviewer: names[0], score: item.score }];
    }
    return names.map((name) => ({ interviewer: name, score: null }));
  }
  const legacyNames = splitLegacyInterviewer(item.interviewer);
  if (legacyNames.length) {
    if (legacyNames.length === 1 && item.score !== null && item.score !== undefined) {
      return [{ interviewer: legacyNames[0], score: item.score }];
    }
    return legacyNames.map((name) => ({ interviewer: name, score: null }));
  }
  return [{ interviewer: "", score: null }];
};

const normalizeResultScoreRows = (rows = []) => {
  const normalized = [];
  const seen = new Set();
  for (const row of rows || []) {
    const interviewer = String(row?.interviewer || "").trim();
    const hasName = Boolean(interviewer);
    const hasScore = !(row?.score === null || row?.score === undefined || row?.score === "");
    if (!hasName && !hasScore) continue;
    if (!hasName || !hasScore) {
      return { ok: false, message: "请完整填写面试官与评分" };
    }
    const score = Number(row.score);
    if (!Number.isInteger(score) || score < 0 || score > 100) {
      return { ok: false, message: "评分需为 0-100 的整数" };
    }
    if (seen.has(interviewer)) {
      return { ok: false, message: "面试官姓名不能重复" };
    }
    seen.add(interviewer);
    normalized.push({ interviewer, score });
  }
  if (!normalized.length) {
    return { ok: false, message: "请至少填写一位面试官评分" };
  }
  return { ok: true, rows: normalized };
};

export const useAdminInterviewActions = ({
  interviewScheduleForm,
  interviewResultForm,
  interviewMeta,
  activeApplication,
  applicationDetailLoading,
  interviewScheduleHasExisting,
  showInterviewScheduleForm,
  showInterviewResultForm,
  scheduleSaving,
  resultSaving,
  toastRef,
  interviewApi,
  loadInterviewCandidates,
  refreshInterviewModules,
  dataLoaded,
  notifySuccess,
  notifyError,
  runWithConfirm,
  resetInterviewScheduleForm,
  resetInterviewResultForm,
}) => {
  // 打开安排面试弹窗：自动推导当前应安排轮次（仅展示）
  const openInterviewSchedule = (item) => {
    activeApplication.value = null;
    applicationDetailLoading.value = false;
    interviewScheduleHasExisting.value = Boolean(
      item.interview_at || item.status === interviewMeta.status_scheduled
    );
    const currentRound = Math.max(Number(item.interview_round || 1), 1);
    const autoRound =
      item.interview_at || item.status === interviewMeta.status_scheduled
        ? currentRound
        : item.status === interviewMeta.status_completed ||
            (item.status === interviewMeta.status_pending &&
              item.result === interviewMeta.result_next_round)
          ? Math.min(currentRound + 1, interviewMeta.max_round)
          : currentRound;
    Object.assign(interviewScheduleForm, {
      id: item.id,
      name: item.name || "",
      phone: item.phone || "",
      job_title: item.job_title || "",
      interview_round: autoRound,
      interview_at: toDateTimeLocal(item.interview_at),
      interviewer: item.interviewer || "",
      interviewers: toScheduleInterviewerRows(item),
      interview_location: item.interview_location || "",
      note: item.note || "",
      send_sms: false,
    });
    showInterviewScheduleForm.value = true;
  };

  // 关闭安排弹窗并清理临时状态
  const closeInterviewSchedule = () => {
    showInterviewScheduleForm.value = false;
    interviewScheduleHasExisting.value = false;
    scheduleSaving.value = false;
    resetInterviewScheduleForm();
  };

  // 打开结果录入弹窗，带入当前轮次与历史评分
  const openInterviewResult = (item) => {
    Object.assign(interviewResultForm, {
      id: item.id,
      name: item.name || "",
      interview_round: item.interview_round || 1,
      status: item.status || "",
      result: interviewMeta.result_next_round,
      score: item.score ?? null,
      interviewer_scores: toResultScoreRows(item),
      result_note: item.result_note || "",
    });
    showInterviewResultForm.value = true;
  };

  // 关闭结果弹窗并重置表单
  const closeInterviewResult = () => {
    showInterviewResultForm.value = false;
    resultSaving.value = false;
    resetInterviewResultForm();
  };

  // 保存安排：做前端基础校验后提交后端状态机
  const saveInterviewSchedule = async () => {
    if (!interviewScheduleForm.id) return;
    if (!interviewScheduleForm.interview_at) {
      toastRef.value?.show("请填写面试时间", "error");
      return;
    }
    const interviewTime = new Date(interviewScheduleForm.interview_at);
    if (Number.isNaN(interviewTime.getTime())) {
      toastRef.value?.show("面试时间格式不正确", "error");
      return;
    }
    if (interviewTime.getTime() <= Date.now()) {
      toastRef.value?.show("面试时间不能早于当前时间", "error");
      return;
    }
    scheduleSaving.value = true;
    try {
      const shouldSendSms = Boolean(interviewScheduleForm.send_sms);
      const hasStructuredInterviewerRows = Array.isArray(interviewScheduleForm.interviewers);
      const interviewerNames = normalizeInterviewerNames(
        hasStructuredInterviewerRows ? interviewScheduleForm.interviewers : []
      );
      const fallbackInterviewerNames = interviewerNames.length
        ? interviewerNames
        : hasStructuredInterviewerRows
          ? []
          : splitLegacyInterviewer(interviewScheduleForm.interviewer);
      const result = await interviewApi.scheduleCandidate(interviewScheduleForm.id, {
        interview_at: interviewScheduleForm.interview_at,
        interviewer: fallbackInterviewerNames.join("、"),
        interviewers: fallbackInterviewerNames,
        interview_location: interviewScheduleForm.interview_location,
        note: interviewScheduleForm.note,
        send_sms: shouldSendSms,
      });
      notifySuccess(result?.message || "面试安排已保存");
      closeInterviewSchedule();
      await loadInterviewCandidates(true);
    } catch (err) {
      notifyError(err);
    } finally {
      scheduleSaving.value = false;
    }
  };

  const retryInterviewSms = async (item) => {
    const candidateId = Number(item?.id || 0);
    if (!Number.isFinite(candidateId) || candidateId <= 0) return;
    try {
      const result = await interviewApi.resendSms(candidateId);
      notifySuccess(result?.message || "短信重发已提交");
      await loadInterviewCandidates(true);
    } catch (err) {
      notifyError(err);
    }
  };

  // 取消当前已安排的面试（保留候选人在拟面试池）
  const cancelInterviewSchedule = async ({ id, name }) => {
    const { done } = await runWithConfirm({
      confirm: {
        title: "取消面试安排",
        content: `确认取消「${name || "该候选人"}」当前面试安排吗？`,
        confirmText: "取消安排",
        type: "danger",
      },
      action: async () => {
        await interviewApi.cancelSchedule(id);
        notifySuccess("已取消面试安排");
        await loadInterviewCandidates(true);
      },
    });
    return done;
  };

  // 从安排弹窗内触发取消安排
  const cancelInterviewScheduleFromForm = async () => {
    if (!interviewScheduleForm.id) return;
    const done = await cancelInterviewSchedule({
      id: interviewScheduleForm.id,
      name: interviewScheduleForm.name,
    });
    if (done) closeInterviewSchedule();
  };

  // 保存结果：支持进入下一轮/通过/淘汰，并按需刷新通过列表与人才库
  const saveInterviewResult = async () => {
    if (!interviewResultForm.id) return;
    const scoreRowsResult = normalizeResultScoreRows(interviewResultForm.interviewer_scores);
    if (!scoreRowsResult.ok) {
      toastRef.value?.show(scoreRowsResult.message, "error");
      return;
    }
    const interviewerScores = scoreRowsResult.rows;
    resultSaving.value = true;
    try {
      const payload = {
        result: interviewResultForm.result,
        result_note: interviewResultForm.result_note,
        interviewer_scores: interviewerScores,
        score: interviewerScores.length === 1 ? interviewerScores[0].score : null,
      };
      await interviewApi.saveResult(interviewResultForm.id, payload);
      const shouldRefreshPassed =
        dataLoaded.passed || interviewResultForm.result === interviewMeta.result_pass;
      const shouldRefreshTalent =
        dataLoaded.talent || interviewResultForm.result === interviewMeta.result_reject;
      notifySuccess("面试结果已保存");
      closeInterviewResult();
      await refreshInterviewModules({
        forcePassed: shouldRefreshPassed,
        forceTalent: shouldRefreshTalent,
      });
    } catch (err) {
      notifyError(err);
    } finally {
      resultSaving.value = false;
    }
  };

  return {
    openInterviewSchedule,
    closeInterviewSchedule,
    openInterviewResult,
    closeInterviewResult,
    saveInterviewSchedule,
    retryInterviewSms,
    cancelInterviewSchedule,
    cancelInterviewScheduleFromForm,
    saveInterviewResult,
  };
};
