// 管理后台主页面逻辑：状态管理、数据加载与业务动作。
import { onMounted, reactive, ref, watch } from "vue";
import { buildApiUrl, resolveAssetUrl } from "../config/runtime";
import { useConfirmAction } from "./useConfirmAction";
import { createInterviewApi } from "../api/interview";
import {
  createRequest,
  resolveErrorCodeMessage,
} from "../api/client";
import { getInterviewStatusClass, getInterviewStatusText } from "../utils/interviewStatus";
import { createInterviewMeta, defaultInterviewMeta } from "../utils/interviewMeta";
import {
  createPageState,
  resetPageState,
} from "../utils/pagination";
import { toDateTimeLocal } from "../utils/detailFormatters";
import {
  DEFAULT_OPERATION_LOG_META,
  normalizeOperationLogMeta,
  resolveOperationActionLabel,
  resolveOperationModuleLabel,
} from "../constants/operationLog";
import { useAdminDataLoaders } from "./adminAppPage/useAdminDataLoaders";
import { useAdminDerivedState } from "./adminAppPage/useAdminDerivedState";
import { useAdminApplicationActions } from "./adminAppPage/useAdminApplicationActions";
import { useAdminApplicationDetail } from "./adminAppPage/useAdminApplicationDetail";
import { useAdminSessionActions } from "./adminAppPage/useAdminSessionActions";

export const useAdminAppPage = () => {
  const toastRef = ref(null);
  const confirmRef = ref(null);

  // === 环境变量与基础配置 ===
  const adminBase = buildApiUrl("api/admin");
  const authBase = buildApiUrl("api/auth");
  const resolveMediaUrl = (url) => resolveAssetUrl(url);

  const resetOperationLogPageState = () => {
    resetPageState(operationLogPagination);
    operationLogPagination.cursor = "";
    operationLogPageCursorMap.value = { 1: "" };
  };

  // === 状态管理 ===
  const token = ref(localStorage.getItem("admin_token") || "");
  const currentUsername = ref(localStorage.getItem("admin_username") || "");
  const authMode = ref("login");
  const activeTab = ref("jobs");

  const tabs = [
    { key: "regions", label: "地区管理", adminOnly: true },
    { key: "jobs", label: "岗位管理", adminOnly: false },
    { key: "applications", label: "应聘记录", adminOnly: false },
    { key: "interviews", label: "拟面试人员", adminOnly: false },
    { key: "passed", label: "面试通过人员", adminOnly: false },
    { key: "talent", label: "人才库", adminOnly: false },
    { key: "operationLogs", label: "操作日志", adminOnly: false },
    { key: "accounts", label: "账号管理", adminOnly: true },
  ];

  const authForm = reactive({ username: "", password: "", region_id: "" });
  const jobForm = reactive({ id: null, region: "", title: "", description: "", salary: "", education: "", order: 0, is_active: true });
  const regionForm = reactive({ name: "", code: "", order: 0, is_active: true });
  const showRegionDeleteModal = ref(false);
  const regionDeleteSubmitting = ref(false);
  const regionDeletePassword = ref("");
  const pendingDeleteRegion = ref(null);
  const passwordForm = reactive({ user_id: "", password: "" });
  const selfPasswordForm = reactive({ old_password: "", new_password: "", confirm_password: "" });
  const selectedJobIds = ref([]);
  const selectedApplicationIds = ref([]);
  const selectedInterviewIds = ref([]);
  const selectedPassedIds = ref([]);
  const selectedTalentIds = ref([]);
  const jobFilters = reactive({ keyword: "" });
  const showJobForm = ref(false);
  const showInterviewScheduleForm = ref(false);
  const showInterviewResultForm = ref(false);
  const interviewScheduleHasExisting = ref(false);
  const scheduleSaving = ref(false);
  const resultSaving = ref(false);
  const interviewTimeSort = ref("none");
  const applicationFilters = reactive({ job: "all", region: "" });
  const interviewFilters = reactive({ job: "all", region: "", keyword: "" });
  const passedFilters = reactive({ job: "all", hire_status: "all" });
  const talentFilters = reactive({ job: "all" });
  const operationLogFilters = reactive({
    module: "",
    operator: "",
    date_from: "",
    date_to: "",
  });
  const interviewScheduleForm = reactive({
    id: null,
    name: "",
    interview_round: 1,
    interview_at: "",
    interviewer: "",
    interview_location: "",
    note: "",
  });
  const interviewResultForm = reactive({
    id: null,
    name: "",
    interview_round: 1,
    status: "",
    result: defaultInterviewMeta.result_next_round,
    score: null,
    result_note: "",
  });

  const publicRegions = ref([]);
  const regions = ref([]);
  const jobs = ref([]);
  const applications = ref([]);
  const interviewCandidates = ref([]);
  const passedCandidates = ref([]);
  const talentPoolCandidates = ref([]);
  const operationLogs = ref([]);
  const passedPagination = reactive(createPageState());
  const talentPagination = reactive(createPageState());
  const operationLogPagination = reactive({
    ...createPageState(),
    cursor: "",
  });
  const operationLogPageCursorMap = ref({ 1: "" });
  const interviewMeta = reactive(createInterviewMeta());
  const users = ref([]);
  const userProfile = reactive({ can_view_all: false, region_name: "", region_id: null, is_superuser: false });
  const activeApplication = ref(null);
  const applicationDetailLoading = ref(false);
  const applicationOperationLogs = ref([]);
  const applicationLogsLoading = ref(false);
  const operationLogsQueried = ref(false);
  const operationLogMeta = reactive({
    ...normalizeOperationLogMeta(DEFAULT_OPERATION_LOG_META),
    loaded: false,
  });
  const dataLoaded = reactive({ regions: false, jobs: false, applications: false, interviews: false, passed: false, talent: false, operationLogs: false, interviewMeta: false, users: false });
  const dataLoading = reactive({ regions: false, jobs: false, applications: false, interviews: false, passed: false, talent: false, operationLogs: false, interviewMeta: false, users: false });

  const {
    visibleTabs,
    interviewRoundHint,
    interviewResultOptions,
    currentTitle,
    userInitial,
    showRegionFilter,
    hasJobKeyword,
    filteredJobs,
    selectedJobStats,
    canBatchActivateJobs,
    canBatchDeactivateJobs,
    operationModuleOptions,
    operationLogSuccessCount,
    operationLogFailedCount,
    operationLogPageSizeOptions,
    operationLogKnownMaxPage,
    operationLogPageItems,
    jobCategories,
    filteredApplications,
    groupedApplications,
    interviewJobCategories,
    filteredInterviewCandidates,
    sortedInterviewCandidates,
    passedJobCategories,
    passedStatusOptions,
    filteredPassedCandidates,
    talentJobCategories,
    filteredTalentCandidates,
    selectedApplicationsCount,
    selectedJobsCount,
    isAllJobsSelected,
    selectedInterviewCount,
    isAllVisibleInterviewsSelected,
    isAllVisiblePassedSelected,
    selectedTalentCount,
    isAllVisibleTalentSelected,
  } = useAdminDerivedState({
    tabs,
    userProfile,
    interviewScheduleForm,
    interviewScheduleHasExisting,
    interviewMeta,
    activeTab,
    currentUsername,
    jobFilters,
    jobs,
    selectedJobIds,
    operationLogs,
    operationLogMeta,
    operationLogPageCursorMap,
    operationLogPagination,
    applications,
    applicationFilters,
    interviewCandidates,
    interviewFilters,
    interviewTimeSort,
    passedCandidates,
    passedFilters,
    talentPoolCandidates,
    talentFilters,
    selectedApplicationIds,
    selectedInterviewIds,
    selectedPassedIds,
    selectedTalentIds,
  });

  // === API 请求封装 ===
  const request = createRequest(() => token.value);
  const interviewApi = createInterviewApi({ adminBase, request });

  const notifyError = (err) => {
    console.error(err);
    const mapped = resolveErrorCodeMessage(
      typeof err?.code === "string" ? err.code : ""
    );
    toastRef.value?.show(mapped || err?.message || "操作失败", "error");
  };
  const notifySuccess = (msg) => {
    toastRef.value?.show(msg, 'success');
  };
  const { askConfirm, runWithConfirm } = useConfirmAction(confirmRef, {
    onError: notifyError,
    onSuccess: notifySuccess,
  });

  const {
    fetchPublicRegions,
    loadRegions,
    loadJobs,
    loadApplications,
    loadInterviewCandidates,
    loadInterviewMeta,
    loadPassedCandidates,
    loadTalentPoolCandidates,
    loadOperationLogMeta,
    loadOperationLogs,
    loadApplicationOperationLogs,
    loadUsers,
    ensureTabData,
    loadProfile,
  } = useAdminDataLoaders({
    buildApiUrl,
    request,
    adminBase,
    authBase,
    interviewApi,
    dataLoaded,
    dataLoading,
    publicRegions,
    regions,
    jobs,
    applications,
    interviewCandidates,
    passedCandidates,
    talentPoolCandidates,
    operationLogs,
    applicationOperationLogs,
    applicationLogsLoading,
    operationLogFilters,
    operationLogMeta,
    operationLogPagination,
    operationLogPageCursorMap,
    operationLogsQueried,
    users,
    userProfile,
    jobForm,
    activeTab,
    visibleTabs,
    token,
    selectedJobIds,
    selectedApplicationIds,
    selectedInterviewIds,
    selectedPassedIds,
    selectedTalentIds,
    applicationFilters,
    interviewFilters,
    passedFilters,
    talentFilters,
    interviewMeta,
    passedPagination,
    talentPagination,
    jobCategories,
    interviewJobCategories,
    passedJobCategories,
    talentJobCategories,
    operationLogPageSizeOptions,
    notifyError,
  });

  const { submitAuth, logout } = useAdminSessionActions({
    authMode,
    authForm,
    authBase,
    token,
    currentUsername,
    dataLoaded,
    dataLoading,
    passedPagination,
    talentPagination,
    operationLogPagination,
    operationLogs,
    selectedPassedIds,
    selectedTalentIds,
    regions,
    jobs,
    applications,
    interviewCandidates,
    passedCandidates,
    talentPoolCandidates,
    users,
    selectedApplicationIds,
    selectedInterviewIds,
    activeApplication,
    applicationDetailLoading,
    applicationOperationLogs,
    applicationLogsLoading,
    showInterviewScheduleForm,
    scheduleSaving,
    resetInterviewScheduleForm,
    showInterviewResultForm,
    resultSaving,
    resetInterviewResultForm,
    userProfile,
    activeTab,
    interviewMeta,
    fetchPublicRegions,
    loadProfile,
    ensureTabData,
    askConfirm,
    request,
    notifySuccess,
    notifyError,
    resetOperationLogPageState,
    resetJobFilters,
    resetApplicationFilters,
    resetInterviewFilters,
    resetPassedFilters,
    resetTalentFilters,
    resetOperationLogFilters,
    resetOperationLogMeta,
  });

  // === CRUD 操作 ===
  const regionName = (id) => regions.value.find(r => r.id === id)?.name || "-";
  const operationModuleLabel = (value) => resolveOperationModuleLabel(value, operationLogMeta.module_labels);
  const operationActionLabel = (value) => resolveOperationActionLabel(value, operationLogMeta.action_labels);
  const operationResultLabel = (value) =>
    operationLogMeta.result_labels?.[value] || value || "-";
  const operationResultClass = (value) => (value === "failed" ? "chip-reject" : "chip-pass");
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

  // 地区
  const resetRegionForm = () => {
    Object.assign(regionForm, { name: "", code: "", order: 0, is_active: true });
  };
  const saveRegion = async () => {
    const payload = {
      name: regionForm.name.trim(),
      code: regionForm.code.trim(),
      order: Number.isFinite(Number(regionForm.order)) ? Number(regionForm.order) : 0,
      is_active: Boolean(regionForm.is_active),
    };
    if (!payload.name || !payload.code) {
      toastRef.value?.show("请填写地区名称和地区编码", "error");
      return;
    }
    try {
      await request(`${adminBase}/regions/`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      notifySuccess("地区已新增");
      resetRegionForm();
      await loadRegions(true);
      if (dataLoaded.jobs) {
        await loadJobs(true);
      }
      publicRegions.value = [];
      await fetchPublicRegions();
    } catch (err) {
      notifyError(err);
    }
  };
  const openDeleteRegionModal = (item) => {
    pendingDeleteRegion.value = item;
    regionDeletePassword.value = "";
    regionDeleteSubmitting.value = false;
    showRegionDeleteModal.value = true;
  };
  const closeDeleteRegionModal = () => {
    showRegionDeleteModal.value = false;
    regionDeleteSubmitting.value = false;
    regionDeletePassword.value = "";
    pendingDeleteRegion.value = null;
  };
  const confirmDeleteRegion = async () => {
    const target = pendingDeleteRegion.value;
    if (!target) return;
    if (!regionDeletePassword.value.trim()) {
      toastRef.value?.show("请输入当前登录密码", "error");
      return;
    }
    regionDeleteSubmitting.value = true;
    try {
      await request(`${adminBase}/regions/${target.id}/`, {
        method: "DELETE",
        body: JSON.stringify({ password: regionDeletePassword.value }),
      });
      notifySuccess("地区已删除");
      closeDeleteRegionModal();
      await loadRegions(true);
      if (dataLoaded.jobs) {
        await loadJobs(true);
      }
      publicRegions.value = [];
      await fetchPublicRegions();
    } catch (err) {
      notifyError(err);
    } finally {
      regionDeleteSubmitting.value = false;
    }
  };

  // 岗位
  const resetJobForm = () => {
    Object.assign(jobForm, { id: null, region: "", title: "", description: "", salary: "", education: "", order: 0, is_active: true });
    if (!userProfile.can_view_all && userProfile.region_id) {
      jobForm.region = userProfile.region_id;
    }
  };
  const openNewJob = () => {
    resetJobForm();
    showJobForm.value = true;
  };
  const closeJobForm = () => {
    showJobForm.value = false;
    resetJobForm();
  };
  const editJob = (item) => {
    Object.assign(jobForm, item);
    showJobForm.value = true;
  };
  const deleteJob = async (id) => {
    await runWithConfirm({
      confirm: {
        title: "删除岗位",
        content: "此操作将永久删除该岗位及其关联数据，是否继续？",
        type: "danger",
      },
      action: async () => {
        await request(`${adminBase}/jobs/${id}/`, { method: "DELETE" });
        notifySuccess("删除成功");
        await loadJobs(true);
      },
    });
  };
  const batchUpdateJobsStatus = async (isActive) => {
    if (!selectedJobIds.value.length) return;
    const selectedSet = new Set(selectedJobIds.value);
    const targetJobIds = jobs.value
      .filter((item) => selectedSet.has(item.id) && item.is_active !== isActive)
      .map((item) => item.id);
    if (!targetJobIds.length) {
      toastRef.value?.show(isActive ? "所选岗位已全部上架" : "所选岗位已全部下架", "info");
      return;
    }

    const actionText = isActive ? "上架" : "下架";
    const title = isActive ? "批量上架岗位" : "批量下架岗位";
    const content = isActive
      ? `将上架已选中的 ${targetJobIds.length} 个岗位，上架后对应应聘记录将恢复可见，是否继续？`
      : `将下架已选中的 ${targetJobIds.length} 个岗位，下架后对应应聘记录将不再展示，是否继续？`;
    await runWithConfirm({
      confirm: {
        title,
        content,
        type: isActive ? "default" : "danger",
        confirmText: actionText,
      },
      action: async () => {
        const result = await request(`${adminBase}/jobs/batch-status/`, {
          method: "POST",
          body: JSON.stringify({ job_ids: targetJobIds, is_active: isActive }),
        });
        notifySuccess(`已${actionText} ${result.updated || 0} 个岗位`);
        await loadJobs(true);
        if (dataLoaded.applications) {
          await loadApplications(true);
        }
      },
    });
  };
  const batchActivateJobs = async () => {
    await batchUpdateJobsStatus(true);
  };
  const batchDeactivateJobs = async () => {
    await batchUpdateJobsStatus(false);
  };
  const batchDeleteJobs = async () => {
    if (!selectedJobIds.value.length) return;
    await runWithConfirm({
      confirm: {
        title: "批量删除岗位",
        content: `将删除已选中的 ${selectedJobIds.value.length} 个岗位，是否继续？`,
        type: "danger",
        confirmText: "删除",
      },
      action: async () => {
        const ids = [...selectedJobIds.value];
        const results = await Promise.allSettled(
          ids.map((targetId) => request(`${adminBase}/jobs/${targetId}/`, { method: "DELETE" }))
        );
        const success = results.filter((item) => item.status === "fulfilled").length;
        const fail = results.length - success;
        if (success) notifySuccess(`已删除 ${success} 个岗位`);
        if (fail) toastRef.value?.show(`${fail} 个岗位删除失败`, "error");
        await loadJobs(true);
      },
    });
  };
  const saveJob = async () => {
    const method = jobForm.id ? "PUT" : "POST";
    const url = jobForm.id ? `${adminBase}/jobs/${jobForm.id}/` : `${adminBase}/jobs/`;
    try {
      await request(url, { method, body: JSON.stringify(jobForm) });
      notifySuccess("保存成功");
      resetJobForm();
      showJobForm.value = false;
      await loadJobs(true);
    } catch (err) {
      notifyError(err);
    }
  };

  // 账号
  const resetUserPassword = async () => {
    const { user_id, password } = passwordForm;
    if (!user_id || !password) return;
    try {
      await request(`${adminBase}/users/${user_id}/password/`, {
        method: "POST",
        body: JSON.stringify({ password })
      });
      notifySuccess("密码已更新");
      passwordForm.user_id = "";
      passwordForm.password = "";
    } catch (err) {
      notifyError(err);
    }
  };

  const changeMyPassword = async () => {
    const { old_password, new_password, confirm_password } = selfPasswordForm;
    if (!old_password || !new_password || !confirm_password) return;
    if (new_password !== confirm_password) {
      toastRef.value?.show("两次输入的新密码不一致", "error");
      return;
    }
    try {
      const result = await request(`${authBase}/password/`, {
        method: "POST",
        body: JSON.stringify({ old_password, new_password })
      });
      if (result?.force_relogin) {
        notifySuccess(result?.message || "密码已更新，请重新登录");
        await logout(true);
        return;
      }
      notifySuccess(result?.message || "密码已更新");
      selfPasswordForm.old_password = "";
      selfPasswordForm.new_password = "";
      selfPasswordForm.confirm_password = "";
    } catch (err) {
      notifyError(err);
    }
  };

  const selectUserForReset = (item) => {
    passwordForm.user_id = item.id;
    passwordForm.password = "";
  };

  const deleteUser = async (item) => {
    await runWithConfirm({
      confirm: {
        title: "删除账号",
        content: `确定删除账号「${item.username}」吗？该操作不可恢复。`,
        type: "danger",
        confirmText: "删除",
      },
      action: async () => {
        await request(`${adminBase}/users/${item.id}/`, { method: "DELETE" });
        notifySuccess("账号已删除");
        await loadUsers(true);
      },
    });
  };

  const fetchApplications = async () => {
    const ok = await loadApplications(true);
    if (!ok) return;
    activeApplication.value = null;
    applicationDetailLoading.value = false;
    notifySuccess("数据已刷新");
  };

  const refreshApplications = async () => {
    await fetchApplications();
    resetApplicationFilters();
  };

  const fetchJobs = async () => {
    await loadJobs(true);
  };

  function resetJobFilters() {
    jobFilters.keyword = "";
  }

  function resetApplicationFilters() {
    applicationFilters.job = "all";
    applicationFilters.region = "";
  }

  function resetInterviewFilters() {
    interviewFilters.job = "all";
    interviewFilters.region = "";
    interviewFilters.keyword = "";
    interviewTimeSort.value = "none";
  }

  function resetPassedFilters() {
    passedFilters.job = "all";
    passedFilters.hire_status = "all";
  }

  function resetTalentFilters() {
    talentFilters.job = "all";
  }

  function resetOperationLogFilters() {
    operationLogFilters.module = "";
    operationLogFilters.operator = "";
    operationLogFilters.date_from = "";
    operationLogFilters.date_to = "";
  }

  function resetOperationLogMeta() {
    operationLogMeta.module_labels = { ...DEFAULT_OPERATION_LOG_META.module_labels };
    operationLogMeta.action_labels = { ...DEFAULT_OPERATION_LOG_META.action_labels };
    operationLogMeta.result_labels = { ...DEFAULT_OPERATION_LOG_META.result_labels };
    operationLogMeta.page_size_options = [...DEFAULT_OPERATION_LOG_META.page_size_options];
    operationLogMeta.default_recent_days = DEFAULT_OPERATION_LOG_META.default_recent_days;
    operationLogMeta.pagination_mode = DEFAULT_OPERATION_LOG_META.pagination_mode;
    operationLogMeta.loaded = false;
    operationLogsQueried.value = false;
  }

  // 面试时间排序在“升序/降序”间切换
  const toggleInterviewTimeSort = () => {
    interviewTimeSort.value = interviewTimeSort.value === "asc" ? "desc" : "asc";
  };

  function resetInterviewScheduleForm() {
    Object.assign(interviewScheduleForm, {
      id: null,
      name: "",
      interview_round: 1,
      interview_at: "",
      interviewer: "",
      interview_location: "",
      note: "",
    });
  }

  function resetInterviewResultForm() {
    Object.assign(interviewResultForm, {
      id: null,
      name: "",
      interview_round: 1,
      status: "",
      result: interviewMeta.result_next_round,
      score: null,
      result_note: "",
    });
  }

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
      interview_round: autoRound,
      interview_at: toDateTimeLocal(item.interview_at),
      interviewer: item.interviewer || "",
      interview_location: item.interview_location || "",
      note: item.note || "",
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
      await interviewApi.scheduleCandidate(interviewScheduleForm.id, {
        interview_at: interviewScheduleForm.interview_at,
        interviewer: interviewScheduleForm.interviewer,
        interview_location: interviewScheduleForm.interview_location,
        note: interviewScheduleForm.note,
      });
      notifySuccess("面试安排已保存");
      closeInterviewSchedule();
      await loadInterviewCandidates(true);
    } catch (err) {
      notifyError(err);
    } finally {
      scheduleSaving.value = false;
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
    if (interviewResultForm.score !== null && interviewResultForm.score !== "") {
      const score = Number(interviewResultForm.score);
      if (!Number.isInteger(score) || score < 0 || score > 100) {
        toastRef.value?.show("评分需为 0-100 的整数", "error");
        return;
      }
    }
    resultSaving.value = true;
    try {
      const payload = {
        result: interviewResultForm.result,
        result_note: interviewResultForm.result_note,
        score:
          interviewResultForm.score === null || interviewResultForm.score === ""
            ? null
            : Number(interviewResultForm.score),
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

  const {
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
  } = useAdminApplicationActions({
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
  });

  const {
    openApplicationFromInterview,
    openApplicationFromOutcome,
    openApplication,
    closeApplication,
    attachmentCardMeta,
    applicationAttachments,
    keyAttachmentCards,
    otherAttachmentFiles,
    openAttachment,
    detailSections,
  } = useAdminApplicationDetail({
    activeApplication,
    applicationDetailLoading,
    applicationOperationLogs,
    applicationLogsLoading,
    resolveMediaUrl,
    request,
    adminBase,
    loadApplicationOperationLogs,
    notifyError,
  });

  watch(
    () => activeTab.value,
    (tab) => {
      ensureTabData(tab);
    }
  );

  onMounted(async () => {
    if (!token.value) {
      await fetchPublicRegions();
      return;
    }
    try {
      await loadProfile();
      await ensureTabData(activeTab.value, true);
    } catch {
      await logout(true);
    }
  });

  return {
    toastRef,
    confirmRef,
    adminBase,
    authBase,
    resolveMediaUrl,
    resetOperationLogPageState,
    token,
    currentUsername,
    authMode,
    activeTab,
    tabs,
    authForm,
    jobForm,
    regionForm,
    showRegionDeleteModal,
    regionDeleteSubmitting,
    regionDeletePassword,
    pendingDeleteRegion,
    passwordForm,
    selfPasswordForm,
    selectedJobIds,
    selectedApplicationIds,
    selectedInterviewIds,
    selectedPassedIds,
    selectedTalentIds,
    jobFilters,
    showJobForm,
    showInterviewScheduleForm,
    showInterviewResultForm,
    interviewScheduleHasExisting,
    scheduleSaving,
    resultSaving,
    interviewTimeSort,
    applicationFilters,
    interviewFilters,
    passedFilters,
    talentFilters,
    operationLogFilters,
    interviewScheduleForm,
    interviewResultForm,
    publicRegions,
    regions,
    jobs,
    applications,
    interviewCandidates,
    passedCandidates,
    talentPoolCandidates,
    operationLogs,
    passedPagination,
    talentPagination,
    operationLogPagination,
    operationLogPageCursorMap,
    interviewMeta,
    users,
    userProfile,
    activeApplication,
    applicationDetailLoading,
    applicationOperationLogs,
    applicationLogsLoading,
    operationLogsQueried,
    operationLogMeta,
    dataLoaded,
    dataLoading,
    visibleTabs,
    interviewRoundHint,
    interviewResultOptions,
    currentTitle,
    userInitial,
    showRegionFilter,
    hasJobKeyword,
    filteredJobs,
    selectedJobStats,
    canBatchActivateJobs,
    canBatchDeactivateJobs,
    operationModuleOptions,
    operationLogSuccessCount,
    operationLogFailedCount,
    operationLogPageSizeOptions,
    operationLogKnownMaxPage,
    operationLogPageItems,
    jobCategories,
    filteredApplications,
    groupedApplications,
    interviewJobCategories,
    filteredInterviewCandidates,
    sortedInterviewCandidates,
    passedJobCategories,
    passedStatusOptions,
    filteredPassedCandidates,
    talentJobCategories,
    filteredTalentCandidates,
    selectedApplicationsCount,
    selectedJobsCount,
    isAllJobsSelected,
    selectedInterviewCount,
    isAllVisibleInterviewsSelected,
    isAllVisiblePassedSelected,
    selectedTalentCount,
    isAllVisibleTalentSelected,
    request,
    interviewApi,
    notifyError,
    notifySuccess,
    askConfirm,
    runWithConfirm,
    fetchPublicRegions,
    loadRegions,
    loadJobs,
    loadApplications,
    loadInterviewCandidates,
    loadInterviewMeta,
    loadPassedCandidates,
    loadTalentPoolCandidates,
    loadOperationLogMeta,
    loadOperationLogs,
    loadApplicationOperationLogs,
    loadUsers,
    ensureTabData,
    loadProfile,
    submitAuth,
    logout,
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
    resetRegionForm,
    saveRegion,
    openDeleteRegionModal,
    closeDeleteRegionModal,
    confirmDeleteRegion,
    resetJobForm,
    openNewJob,
    closeJobForm,
    editJob,
    deleteJob,
    batchUpdateJobsStatus,
    batchActivateJobs,
    batchDeactivateJobs,
    batchDeleteJobs,
    saveJob,
    resetUserPassword,
    changeMyPassword,
    selectUserForReset,
    deleteUser,
    fetchApplications,
    refreshApplications,
    fetchJobs,
    resetJobFilters,
    resetApplicationFilters,
    resetInterviewFilters,
    resetPassedFilters,
    resetTalentFilters,
    resetOperationLogFilters,
    resetOperationLogMeta,
    toggleInterviewTimeSort,
    resetInterviewScheduleForm,
    resetInterviewResultForm,
    openInterviewSchedule,
    closeInterviewSchedule,
    openInterviewResult,
    closeInterviewResult,
    saveInterviewSchedule,
    cancelInterviewSchedule,
    cancelInterviewScheduleFromForm,
    saveInterviewResult,
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
    openApplicationFromInterview,
    openApplicationFromOutcome,
    openApplication,
    closeApplication,
    attachmentCardMeta,
    applicationAttachments,
    keyAttachmentCards,
    otherAttachmentFiles,
    openAttachment,
    detailSections,
  };
};
