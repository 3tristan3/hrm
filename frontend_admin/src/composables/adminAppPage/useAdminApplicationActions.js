import { cursorFromLink } from "../../api/client";
import {
  OFFER_STATUS,
  OFFER_STATUS_LABELS,
  canModifyOfferStatus,
  resolveOfferStatus,
} from "../../utils/offerStatusTransition";

export const useAdminApplicationActions = ({
  selectedApplicationIds,
  selectedInterviewIds,
  selectedPassedIds,
  selectedTalentIds,
  passedCandidates,
  activeTab,
  dataLoaded,
  interviewPagination,
  passedPagination,
  talentPagination,
  operationLogPagination,
  operationLogPageCursorMap,
  runWithConfirm,
  interviewApi,
  loadApplications,
  loadInterviewCandidates,
  loadPassedCandidates,
  loadTalentPoolCandidates,
  loadOperationLogs,
  resetInterviewFilters,
  resetPassedFilters,
  resetTalentFilters,
  resetOperationLogPageState,
  notifySuccess,
  notifyError,
}) => {
  const refreshInterviewModules = async ({ forcePassed = false, forceTalent = false } = {}) => {
    await loadInterviewCandidates(true, interviewPagination.page || 1);
    if (forcePassed || dataLoaded.passed) {
      await loadPassedCandidates(true, passedPagination.page || 1);
    }
    if (forceTalent || dataLoaded.talent) {
      await loadTalentPoolCandidates(true, talentPagination.page || 1);
    }
  };

  const isApplicationSelected = (applicationId) =>
    selectedApplicationIds.value.includes(applicationId);

  const getApplicationGroupIds = (items) =>
    (Array.isArray(items) ? items : [])
      .map((item) => item?.id)
      .filter((id) => typeof id === "number");

  const isApplicationGroupFullySelected = (items) => {
    const groupIds = getApplicationGroupIds(items);
    return (
      groupIds.length > 0 &&
      groupIds.every((id) => selectedApplicationIds.value.includes(id))
    );
  };

  const toggleApplicationGroupSelection = (items) => {
    const groupIds = getApplicationGroupIds(items);
    if (!groupIds.length) return;

    if (isApplicationGroupFullySelected(items)) {
      const groupSet = new Set(groupIds);
      selectedApplicationIds.value = selectedApplicationIds.value.filter(
        (id) => !groupSet.has(id)
      );
      return;
    }

    const merged = new Set([...selectedApplicationIds.value, ...groupIds]);
    selectedApplicationIds.value = Array.from(merged);
  };

  const toggleApplicationSelection = (applicationId) => {
    if (isApplicationSelected(applicationId)) {
      selectedApplicationIds.value = selectedApplicationIds.value.filter(
        (id) => id !== applicationId
      );
      return;
    }
    selectedApplicationIds.value = [...selectedApplicationIds.value, applicationId];
  };

  const addSelectedToInterviewPool = async () => {
    if (!selectedApplicationIds.value.length) return;
    await runWithConfirm({
      confirm: {
        title: "加入拟面试人员",
        content: `确认将已选 ${selectedApplicationIds.value.length} 人加入拟面试人员吗？`,
        confirmText: "加入",
        type: "default",
      },
      action: async () => {
        const result = await interviewApi.batchAddFromApplications(selectedApplicationIds.value);
        const parts = [];
        if (result.added) parts.push(`新增 ${result.added} 人`);
        if (result.existing) parts.push(`已存在 ${result.existing} 人`);
        notifySuccess(parts.length ? `操作完成：${parts.join("，")}` : "操作完成");
        selectedApplicationIds.value = [];
        await Promise.all([loadApplications(true), loadInterviewCandidates(true)]);
        activeTab.value = "interviews";
      },
    });
  };

  const addSelectedToTalentPool = async () => {
    if (!selectedApplicationIds.value.length) return;
    await runWithConfirm({
      confirm: {
        title: "加入人才库",
        content: `确认将已选 ${selectedApplicationIds.value.length} 人加入人才库吗？加入后将标记为“简历初筛未通过”，并从应聘记录中移除。`,
        confirmText: "确认加入",
        type: "danger",
      },
      action: async () => {
        const result = await interviewApi.batchAddToTalentPool(selectedApplicationIds.value);
        const parts = [];
        if (result.moved) parts.push(`加入 ${result.moved} 人`);
        if (result.existing) parts.push(`已在人才库 ${result.existing} 人`);
        if (result.blocked) parts.push(`已通过未处理 ${result.blocked} 人`);
        notifySuccess(parts.length ? `操作完成：${parts.join("，")}` : "操作完成");
        selectedApplicationIds.value = [];
        await loadApplications(true);
        if (dataLoaded.interviews) {
          await loadInterviewCandidates(true);
        }
        if (dataLoaded.talent) {
          await loadTalentPoolCandidates(true, 1);
        } else {
          dataLoaded.talent = false;
        }
      },
    });
  };

  const addSelectedTalentToInterviewPool = async () => {
    if (!selectedTalentIds.value.length) return;
    await runWithConfirm({
      confirm: {
        title: "加入拟面试人员",
        content: `确认将已选 ${selectedTalentIds.value.length} 人加入拟面试人员吗？加入后将从人才库移除。`,
        confirmText: "确认加入",
        type: "default",
      },
      action: async () => {
        const result = await interviewApi.batchMoveTalentToInterview(selectedTalentIds.value);
        selectedTalentIds.value = [];
        await Promise.all([loadTalentPoolCandidates(true, 1), loadInterviewCandidates(true)]);
        if (dataLoaded.applications) {
          await loadApplications(true);
        }
        notifySuccess(`已加入拟面试人员 ${result.moved || 0} 人`);
      },
    });
  };

  const refreshInterviewCandidates = async () => {
    await loadInterviewCandidates(true, 1);
    selectedInterviewIds.value = [];
    resetInterviewFilters();
    notifySuccess("拟面试人员列表已刷新");
  };

  const changeInterviewPage = async (nextPage) => {
    const page = Math.max(Number(nextPage || 1), 1);
    if (page === interviewPagination.page) return;
    await loadInterviewCandidates(true, page);
  };

  const changePassedPage = async (nextPage) => {
    const page = Math.max(Number(nextPage || 1), 1);
    if (page === passedPagination.page) return;
    await loadPassedCandidates(true, page);
  };

  const changeTalentPage = async (nextPage) => {
    const page = Math.max(Number(nextPage || 1), 1);
    if (page === talentPagination.page) return;
    await loadTalentPoolCandidates(true, page);
  };

  const changeInterviewPageSize = async (nextPageSize) => {
    const pageSize = Number(nextPageSize || interviewPagination.pageSize);
    if (!Number.isFinite(pageSize) || pageSize <= 0) return;
    if (pageSize === Number(interviewPagination.pageSize)) return;
    interviewPagination.pageSize = pageSize;
    await loadInterviewCandidates(true, 1);
    selectedInterviewIds.value = [];
  };

  const changePassedPageSize = async (nextPageSize) => {
    const pageSize = Number(nextPageSize || passedPagination.pageSize);
    if (!Number.isFinite(pageSize) || pageSize <= 0) return;
    if (pageSize === Number(passedPagination.pageSize)) return;
    passedPagination.pageSize = pageSize;
    await loadPassedCandidates(true, 1);
    selectedPassedIds.value = [];
  };

  const changeTalentPageSize = async (nextPageSize) => {
    const pageSize = Number(nextPageSize || talentPagination.pageSize);
    if (!Number.isFinite(pageSize) || pageSize <= 0) return;
    if (pageSize === Number(talentPagination.pageSize)) return;
    talentPagination.pageSize = pageSize;
    await loadTalentPoolCandidates(true, 1);
    selectedTalentIds.value = [];
  };

  const changeOperationLogPage = async (target) => {
    if (target === "next") {
      if (!operationLogPagination.next) return;
      await loadOperationLogs(
        true,
        cursorFromLink(operationLogPagination.next),
        operationLogPagination.page + 1
      );
      return;
    }
    if (target === "previous") {
      if (!operationLogPagination.previous) return;
      await loadOperationLogs(
        true,
        cursorFromLink(operationLogPagination.previous),
        Math.max(operationLogPagination.page - 1, 1)
      );
      return;
    }
    const targetPage = Math.max(Number(target || 1), 1);
    if (!Number.isFinite(targetPage) || targetPage === operationLogPagination.page) return;
    const targetCursor = operationLogPageCursorMap.value[targetPage];
    if (targetPage !== 1 && typeof targetCursor !== "string") return;
    await loadOperationLogs(true, targetPage === 1 ? "" : targetCursor, targetPage);
  };

  const changeOperationLogPageSize = async (nextPageSize) => {
    const pageSize = Number(nextPageSize || operationLogPagination.pageSize);
    if (!Number.isFinite(pageSize) || pageSize <= 0) return;
    if (pageSize === Number(operationLogPagination.pageSize)) return;
    operationLogPagination.pageSize = pageSize;
    resetOperationLogPageState();
    await loadOperationLogs(true, "", 1);
  };

  const refreshPassedCandidates = async () => {
    await loadPassedCandidates(true, 1);
    selectedPassedIds.value = [];
    resetPassedFilters();
    notifySuccess("面试通过人员列表已刷新");
  };

  const confirmSelectedPassedHires = async () => {
    if (!selectedPassedIds.value.length) return;
    const passedList = Array.isArray(passedCandidates?.value) ? passedCandidates.value : [];
    const selectedCandidateMap = new Map(
      passedList
        .filter((item) => selectedPassedIds.value.includes(item?.id))
        .map((item) => [item.id, item])
    );
    const pendingIds = selectedPassedIds.value.filter((candidateId) => {
      const target = selectedCandidateMap.get(candidateId);
      if (!target) return false;
      return resolveOfferStatus(target) === OFFER_STATUS.PENDING;
    });
    const ignoredCount = selectedPassedIds.value.length - pendingIds.length;
    if (!pendingIds.length) {
      notifyError("仅支持对“待发offer”状态候选人执行发放offer");
      return;
    }
    await runWithConfirm({
      confirm: {
        title: "发放offer",
        content: `确认向已选 ${pendingIds.length} 人发放offer吗？`,
        confirmText: "发放offer",
        type: "default",
      },
      action: async () => {
        const result = await interviewApi.batchConfirmHires(pendingIds);
        const parts = [];
        if (result.confirmed) parts.push(`发放 ${result.confirmed} 人`);
        if (result.already_confirmed) parts.push(`已发 ${result.already_confirmed} 人`);
        if (ignoredCount > 0) parts.push(`跳过 ${ignoredCount} 人`);
        notifySuccess(parts.length ? `操作完成：${parts.join("，")}` : "操作完成");
        selectedPassedIds.value = [];
        await loadPassedCandidates(true, passedPagination.page || 1);
      },
    });
  };

  const confirmSelectedPassedOnboard = async () => {
    if (!selectedPassedIds.value.length) return;
    const passedList = Array.isArray(passedCandidates?.value) ? passedCandidates.value : [];
    const selectedCandidateMap = new Map(
      passedList
        .filter((item) => selectedPassedIds.value.includes(item?.id))
        .map((item) => [item.id, item])
    );
    const pendingOnboardIds = selectedPassedIds.value.filter((candidateId) => {
      const target = selectedCandidateMap.get(candidateId);
      if (!target) return false;
      return resolveOfferStatus(target) === OFFER_STATUS.PENDING_ONBOARD;
    });
    const ignoredCount = selectedPassedIds.value.length - pendingOnboardIds.length;
    if (!pendingOnboardIds.length) {
      notifyError("仅支持对“待确认入职”状态候选人执行确认入职");
      return;
    }
    await runWithConfirm({
      confirm: {
        title: "确认入职",
        content: `确认将已选 ${pendingOnboardIds.length} 人标记为“已确认入职”吗？`,
        confirmText: "确认入职",
        type: "default",
      },
      action: async () => {
        const result = await interviewApi.batchConfirmOnboard(pendingOnboardIds);
        const parts = [];
        if (result.confirmed) parts.push(`确认 ${result.confirmed} 人`);
        if (ignoredCount > 0) parts.push(`跳过 ${ignoredCount} 人`);
        notifySuccess(parts.length ? `操作完成：${parts.join("，")}` : "操作完成");
        selectedPassedIds.value = [];
        await loadPassedCandidates(true, passedPagination.page || 1);
      },
    });
  };

  const changePassedCandidateStatus = async ({ item, nextStatus }) => {
    const candidateId = Number(item?.id || 0);
    const statusValue = String(nextStatus || "").trim();
    if (!Number.isFinite(candidateId) || candidateId <= 0 || !statusValue) return;
    if (!canModifyOfferStatus(item)) {
      notifyError("仅支持对“已发offer/待确认入职/拒绝offer”状态候选人修改后续状态");
      return;
    }
    const allowedTargetStatuses = new Set([
      OFFER_STATUS.REJECTED,
      OFFER_STATUS.PENDING_ONBOARD,
    ]);
    if (!allowedTargetStatuses.has(statusValue)) {
      notifyError("仅支持修改为“拒绝offer”或“待确认入职”");
      return;
    }
    if (statusValue === resolveOfferStatus(item)) {
      return;
    }
    const statusLabel = OFFER_STATUS_LABELS[statusValue] || statusValue;
    await runWithConfirm({
      confirm: {
        title: "修改状态",
        content: `确认将「${item?.name || "该候选人"}」状态改为“${statusLabel}”吗？`,
        confirmText: "确认修改",
        type: "danger",
      },
      action: async () => {
        const result = await interviewApi.updatePassedCandidateOfferStatus(candidateId, {
          offer_status: statusValue,
        });
        notifySuccess(result?.message || `状态已更新为${statusLabel}`);
        selectedPassedIds.value = selectedPassedIds.value.filter((id) => id !== candidateId);
        await loadPassedCandidates(true, passedPagination.page || 1);
      },
      onActionError: notifyError,
    });
  };

  const refreshTalentPoolCandidates = async () => {
    await loadTalentPoolCandidates(true, 1);
    selectedTalentIds.value = [];
    resetTalentFilters();
    notifySuccess("人才库列表已刷新");
  };

  const searchOperationLogs = async () => {
    resetOperationLogPageState();
    await loadOperationLogs(true, "", 1);
  };

  const refreshOperationLogs = async () => {
    resetOperationLogPageState();
    await loadOperationLogs(true, "", 1);
    notifySuccess("操作日志已刷新");
  };

  const batchRemoveInterviewCandidates = async () => {
    if (!selectedInterviewIds.value.length) return;
    await runWithConfirm({
      confirm: {
        title: "批量移出拟面试人员",
        content: `确认移出已选 ${selectedInterviewIds.value.length} 人吗？`,
        confirmText: "移出",
        type: "danger",
      },
      action: async () => {
        const result = await interviewApi.batchRemoveCandidates(selectedInterviewIds.value);
        selectedInterviewIds.value = [];
        await refreshInterviewModules();
        notifySuccess(`已移出 ${result.removed || 0} 人`);
      },
    });
  };

  const removeInterviewCandidate = async (item) => {
    await runWithConfirm({
      confirm: {
        title: "移出拟面试人员",
        content: `确认将「${item.name || "该应聘者"}」移出拟面试人员吗？`,
        confirmText: "移出",
        type: "danger",
      },
      action: async () => {
        await interviewApi.removeCandidate(item.id);
        selectedInterviewIds.value = selectedInterviewIds.value.filter((id) => id !== item.id);
        notifySuccess("已移出拟面试人员");
        await refreshInterviewModules();
      },
    });
  };

  return {
    isApplicationSelected,
    getApplicationGroupIds,
    isApplicationGroupFullySelected,
    toggleApplicationGroupSelection,
    toggleApplicationSelection,
    addSelectedToInterviewPool,
    addSelectedToTalentPool,
    addSelectedTalentToInterviewPool,
    refreshInterviewCandidates,
    changeInterviewPage,
    changePassedPage,
    changeTalentPage,
    changeInterviewPageSize,
    changePassedPageSize,
    changeTalentPageSize,
    changeOperationLogPage,
    changeOperationLogPageSize,
    refreshPassedCandidates,
    confirmSelectedPassedHires,
    confirmSelectedPassedOnboard,
    changePassedCandidateStatus,
    refreshTalentPoolCandidates,
    searchOperationLogs,
    refreshOperationLogs,
    refreshInterviewModules,
    batchRemoveInterviewCandidates,
    removeInterviewCandidate,
  };
};
