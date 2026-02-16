import { cursorFromLink } from "../../api/client";

export const useAdminApplicationActions = ({
  selectedApplicationIds,
  selectedInterviewIds,
  selectedPassedIds,
  selectedTalentIds,
  activeTab,
  dataLoaded,
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
}) => {
  const refreshInterviewModules = async ({ forcePassed = false, forceTalent = false } = {}) => {
    await loadInterviewCandidates(true);
    if (forcePassed || dataLoaded.passed) {
      await loadPassedCandidates(true);
    }
    if (forceTalent || dataLoaded.talent) {
      await loadTalentPoolCandidates(true);
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
    await loadInterviewCandidates(true);
    resetInterviewFilters();
    notifySuccess("拟面试人员列表已刷新");
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
    await runWithConfirm({
      confirm: {
        title: "确认入职",
        content: `确认将已选 ${selectedPassedIds.value.length} 人标记为已录用吗？`,
        confirmText: "确认入职",
        type: "default",
      },
      action: async () => {
        const result = await interviewApi.batchConfirmHires(selectedPassedIds.value);
        const parts = [];
        if (result.confirmed) parts.push(`确认 ${result.confirmed} 人`);
        if (result.already_confirmed) parts.push(`已确认 ${result.already_confirmed} 人`);
        notifySuccess(parts.length ? `操作完成：${parts.join("，")}` : "操作完成");
        selectedPassedIds.value = [];
        await loadPassedCandidates(true, passedPagination.page || 1);
      },
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
    changePassedPage,
    changeTalentPage,
    changeOperationLogPage,
    changeOperationLogPageSize,
    refreshPassedCandidates,
    confirmSelectedPassedHires,
    refreshTalentPoolCandidates,
    searchOperationLogs,
    refreshOperationLogs,
    refreshInterviewModules,
    batchRemoveInterviewCandidates,
    removeInterviewCandidate,
  };
};
