import { createInterviewMeta } from "../../utils/interviewMeta";
import { applyListPagePayload } from "../../utils/pagination";
import { createOperationLogLoaders } from "./useOperationLogLoaders";

export const useAdminDataLoaders = ({
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
  interviewPagination,
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
}) => {
  const fetchPublicRegions = async () => {
    if (publicRegions.value.length) return;
    try {
      const res = await fetch(buildApiUrl("api/regions/"));
      if (res.ok) publicRegions.value = await res.json();
    } catch (err) {
      notifyError(err);
    }
  };

  const loadRegions = async (force = false) => {
    if (dataLoading.regions) return;
    if (!force && dataLoaded.regions) return;
    dataLoading.regions = true;
    try {
      regions.value = await request(`${adminBase}/regions/`);
      dataLoaded.regions = true;
    } catch (err) {
      notifyError(err);
    } finally {
      dataLoading.regions = false;
    }
  };

  const loadJobs = async (force = false) => {
    if (dataLoading.jobs) return;
    if (!force && dataLoaded.jobs) return;
    dataLoading.jobs = true;
    try {
      jobs.value = await request(`${adminBase}/jobs/`);
      selectedJobIds.value = [];
      dataLoaded.jobs = true;
    } catch (err) {
      notifyError(err);
    } finally {
      dataLoading.jobs = false;
    }
  };

  const loadApplications = async (force = false) => {
    if (dataLoading.applications) return;
    if (!force && dataLoaded.applications) return;
    dataLoading.applications = true;
    try {
      applications.value = await request(`${adminBase}/applications/`);
      const availableIds = new Set(applications.value.map((item) => item.id));
      selectedApplicationIds.value = selectedApplicationIds.value.filter((id) =>
        availableIds.has(id)
      );
      dataLoaded.applications = true;
      const availableJobs = jobCategories.value.map((item) => item.value);
      if (!availableJobs.includes(applicationFilters.job)) {
        applicationFilters.job = "all";
      }
      return true;
    } catch (err) {
      notifyError(err);
      return false;
    } finally {
      dataLoading.applications = false;
    }
  };

  const loadInterviewCandidates = async (
    force = false,
    page = interviewPagination.page
  ) => {
    if (dataLoading.interviews) return;
    if (!force && dataLoaded.interviews && page === interviewPagination.page) return;
    dataLoading.interviews = true;
    try {
      const payload = await interviewApi.listCandidates({
        page,
        page_size: interviewPagination.pageSize,
      });
      interviewCandidates.value = applyListPagePayload(interviewPagination, payload, page);
      const availableIds = new Set(interviewCandidates.value.map((item) => item.id));
      selectedInterviewIds.value = selectedInterviewIds.value.filter((id) =>
        availableIds.has(id)
      );
      const availableJobs = interviewJobCategories.value.map((item) => item.value);
      if (!availableJobs.includes(interviewFilters.job)) {
        interviewFilters.job = "all";
      }
      dataLoaded.interviews = true;
    } catch (err) {
      notifyError(err);
    } finally {
      dataLoading.interviews = false;
    }
  };

  const loadInterviewMeta = async (force = false) => {
    if (dataLoading.interviewMeta) return;
    if (!force && dataLoaded.interviewMeta) return;
    dataLoading.interviewMeta = true;
    try {
      const payload = await interviewApi.getMeta();
      Object.assign(interviewMeta, createInterviewMeta(payload));
      dataLoaded.interviewMeta = true;
    } catch (err) {
      notifyError(err);
    } finally {
      dataLoading.interviewMeta = false;
    }
  };

  const loadPassedCandidates = async (force = false, page = passedPagination.page) => {
    if (dataLoading.passed) return;
    if (!force && dataLoaded.passed && page === passedPagination.page) return;
    dataLoading.passed = true;
    try {
      const payload = await interviewApi.listPassedCandidates({
        page,
        page_size: passedPagination.pageSize,
      });
      passedCandidates.value = applyListPagePayload(passedPagination, payload, page);
      const availableIds = new Set(passedCandidates.value.map((item) => item.id));
      selectedPassedIds.value = selectedPassedIds.value.filter((id) => availableIds.has(id));
      const availableJobs = passedJobCategories.value.map((item) => item.value);
      if (!availableJobs.includes(passedFilters.job)) {
        passedFilters.job = "all";
      }
      dataLoaded.passed = true;
    } catch (err) {
      notifyError(err);
    } finally {
      dataLoading.passed = false;
    }
  };

  const loadTalentPoolCandidates = async (
    force = false,
    page = talentPagination.page
  ) => {
    if (dataLoading.talent) return;
    if (!force && dataLoaded.talent && page === talentPagination.page) return;
    dataLoading.talent = true;
    try {
      const payload = await interviewApi.listTalentPoolCandidates({
        page,
        page_size: talentPagination.pageSize,
      });
      talentPoolCandidates.value = applyListPagePayload(talentPagination, payload, page);
      const availableIds = new Set(talentPoolCandidates.value.map((item) => item.id));
      selectedTalentIds.value = selectedTalentIds.value.filter((id) =>
        availableIds.has(id)
      );
      const availableJobs = talentJobCategories.value.map((item) => item.value);
      if (!availableJobs.includes(talentFilters.job)) {
        talentFilters.job = "all";
      }
      dataLoaded.talent = true;
    } catch (err) {
      notifyError(err);
    } finally {
      dataLoading.talent = false;
    }
  };

  const {
    loadOperationLogMeta,
    loadOperationLogs,
    loadApplicationOperationLogs,
  } = createOperationLogLoaders({
    request,
    adminBase,
    notifyError,
    operationLogMeta,
    operationLogPageSizeOptions,
    operationLogPagination,
    operationLogFilters,
    operationLogs,
    operationLogPageCursorMap,
    operationLogsQueried,
    dataLoaded,
    dataLoading,
    applicationOperationLogs,
    applicationLogsLoading,
  });

  const loadUsers = async (force = false) => {
    if (!userProfile.is_superuser) return;
    if (dataLoading.users) return;
    if (!force && dataLoaded.users) return;
    dataLoading.users = true;
    try {
      users.value = await request(`${adminBase}/users/`);
      dataLoaded.users = true;
    } catch (err) {
      notifyError(err);
    } finally {
      dataLoading.users = false;
    }
  };

  const ensureTabData = async (tabKey, force = false) => {
    if (!token.value) return;
    if (tabKey === "regions") {
      await loadRegions(force);
      return;
    }
    if (tabKey === "jobs") {
      await Promise.all([loadRegions(force), loadJobs(force)]);
      return;
    }
    if (tabKey === "applications") {
      await Promise.all([loadRegions(force), loadApplications(force)]);
      return;
    }
    if (tabKey === "interviews") {
      await Promise.all([loadInterviewMeta(force), loadInterviewCandidates(force)]);
      return;
    }
    if (tabKey === "passed") {
      await Promise.all([loadInterviewMeta(force), loadPassedCandidates(force)]);
      return;
    }
    if (tabKey === "talent") {
      await Promise.all([loadInterviewMeta(force), loadTalentPoolCandidates(force)]);
      return;
    }
    if (tabKey === "operationLogs") {
      await loadOperationLogMeta(force);
      return;
    }
    if (tabKey === "accounts") {
      await loadUsers(force);
    }
  };

  const loadProfile = async () => {
    const data = await request(`${authBase}/me/`);
    userProfile.can_view_all = data?.profile?.can_view_all || false;
    userProfile.region_name = data?.profile?.region_name || "";
    userProfile.region_id = data?.profile?.region ?? null;
    userProfile.is_superuser = data?.is_superuser || false;
    try {
      localStorage.setItem(
        "admin_is_superuser",
        userProfile.is_superuser ? "true" : "false"
      );
      localStorage.setItem(
        "admin_can_view_all",
        userProfile.can_view_all ? "true" : "false"
      );
    } catch {
      // ignore storage errors
    }
    if (!userProfile.can_view_all && userProfile.region_id) {
      jobForm.region = userProfile.region_id;
    }
    if (!visibleTabs.value.find((t) => t.key === activeTab.value)) {
      activeTab.value = visibleTabs.value[0]?.key || "jobs";
    }
  };

  return {
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
  };
};
