import { createInterviewMeta } from "../../utils/interviewMeta";
import { LIST_PAGE_SIZE, resetPageState } from "../../utils/pagination";

export const useAdminSessionActions = ({
  authMode,
  authForm,
  authBase,
  token,
  currentUsername,
  dataLoaded,
  dataLoading,
  interviewPagination,
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
}) => {
  const submitAuth = async () => {
    try {
      const endpoint = authMode.value === "register" ? "register" : "login";
      const body = { username: authForm.username, password: authForm.password };
      if (authMode.value === "register") body.region_id = authForm.region_id;
      const payload = await request(`${authBase}/${endpoint}/`, {
        method: "POST",
        body: JSON.stringify(body),
      });

      token.value = payload.token;
      currentUsername.value = authForm.username;
      localStorage.setItem("admin_token", payload.token);
      localStorage.setItem("admin_username", authForm.username);
      dataLoaded.regions = false;
      dataLoaded.jobs = false;
      dataLoaded.applications = false;
      dataLoaded.interviews = false;
      dataLoaded.passed = false;
      dataLoaded.talent = false;
      dataLoaded.operationLogs = false;
      dataLoaded.interviewMeta = false;
      dataLoaded.users = false;
      resetPageState(interviewPagination);
      resetPageState(passedPagination);
      resetPageState(talentPagination);
      interviewPagination.pageSize = LIST_PAGE_SIZE;
      passedPagination.pageSize = LIST_PAGE_SIZE;
      talentPagination.pageSize = LIST_PAGE_SIZE;
      resetOperationLogPageState();
      operationLogs.value = [];
      selectedPassedIds.value = [];
      selectedTalentIds.value = [];
      resetJobFilters();
      resetPassedFilters();
      resetTalentFilters();
      resetOperationLogFilters();
      resetOperationLogMeta();
      operationLogPagination.pageSize = LIST_PAGE_SIZE;

      notifySuccess("登录成功");
      await loadProfile();
      await ensureTabData(activeTab.value, true);
    } catch (err) {
      notifyError(err);
    }
  };

  const logout = async (silent = false) => {
    const isConfirmed =
      silent ||
      (await askConfirm({
        title: "退出确认",
        content: "您确定要退出当前账号吗？",
        confirmText: "退出",
        type: "danger",
      }));
    if (!isConfirmed) return;

    if (token.value) {
      try {
        await request(`${authBase}/logout/`, { method: "POST" });
      } catch (err) {
        console.warn("logout api failed", err);
      }
    }

    token.value = "";
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_username");
    localStorage.removeItem("admin_is_superuser");
    localStorage.removeItem("admin_can_view_all");
    currentUsername.value = "";
    regions.value = [];
    jobs.value = [];
    applications.value = [];
    interviewCandidates.value = [];
    passedCandidates.value = [];
    talentPoolCandidates.value = [];
    operationLogs.value = [];
    users.value = [];
    selectedApplicationIds.value = [];
    selectedInterviewIds.value = [];
    selectedPassedIds.value = [];
    selectedTalentIds.value = [];
    dataLoaded.regions = false;
    dataLoaded.jobs = false;
    dataLoaded.applications = false;
    dataLoaded.interviews = false;
    dataLoaded.passed = false;
    dataLoaded.talent = false;
    dataLoaded.operationLogs = false;
    dataLoaded.interviewMeta = false;
    dataLoaded.users = false;
    dataLoading.regions = false;
    dataLoading.jobs = false;
    dataLoading.applications = false;
    dataLoading.interviews = false;
    dataLoading.passed = false;
    dataLoading.talent = false;
    dataLoading.operationLogs = false;
    dataLoading.interviewMeta = false;
    dataLoading.users = false;
    resetPageState(interviewPagination);
    resetPageState(passedPagination);
    resetPageState(talentPagination);
    interviewPagination.pageSize = LIST_PAGE_SIZE;
    passedPagination.pageSize = LIST_PAGE_SIZE;
    talentPagination.pageSize = LIST_PAGE_SIZE;
    resetOperationLogPageState();
    Object.assign(interviewMeta, createInterviewMeta());
    activeApplication.value = null;
    applicationDetailLoading.value = false;
    applicationOperationLogs.value = [];
    applicationLogsLoading.value = false;
    showInterviewScheduleForm.value = false;
    scheduleSaving.value = false;
    resetInterviewScheduleForm();
    showInterviewResultForm.value = false;
    resultSaving.value = false;
    resetInterviewResultForm();
    resetJobFilters();
    resetApplicationFilters();
    resetInterviewFilters();
    resetPassedFilters();
    resetTalentFilters();
    resetOperationLogFilters();
    resetOperationLogMeta();
    operationLogPagination.pageSize = LIST_PAGE_SIZE;
    userProfile.can_view_all = false;
    userProfile.region_name = "";
    userProfile.region_id = null;
    userProfile.is_superuser = false;
    activeTab.value = "jobs";
    fetchPublicRegions();
    if (!silent) notifySuccess("已退出登录");
  };

  return {
    submitAuth,
    logout,
  };
};
