// 管理后台主页面逻辑：状态管理、数据加载与业务动作。
import { onMounted, ref, watch } from "vue";
import { buildApiUrl, resolveAssetUrl } from "../config/runtime";
import { useConfirmAction } from "./useConfirmAction";
import { createInterviewApi } from "../api/interview";
import {
  createRequest,
  resolveErrorCodeMessage,
} from "../api/client";
import { resetPageState } from "../utils/pagination";
import { useAdminDataLoaders } from "./adminAppPage/useAdminDataLoaders";
import { useAdminDerivedState } from "./adminAppPage/useAdminDerivedState";
import { useAdminApplicationActions } from "./adminAppPage/useAdminApplicationActions";
import { useAdminApplicationDetail } from "./adminAppPage/useAdminApplicationDetail";
import { useAdminSessionActions } from "./adminAppPage/useAdminSessionActions";
import { useAdminInterviewActions } from "./adminAppPage/useAdminInterviewActions";
import { useAdminRegionActions } from "./adminAppPage/useAdminRegionActions";
import { useAdminJobActions } from "./adminAppPage/useAdminJobActions";
import { useAdminAccountActions } from "./adminAppPage/useAdminAccountActions";
import { createAdminDisplayHelpers } from "./adminAppPage/useAdminDisplayHelpers";
import { createAdminResetHelpers } from "./adminAppPage/useAdminResetHelpers";
import { createAdminAppState } from "./adminAppPage/useAdminAppState";
import { createAdminAppPublicApi } from "./adminAppPage/useAdminAppPublicApi";

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
  const {
    token, currentUsername, authMode, activeTab, tabs, authForm, jobForm, regionForm, showRegionCreateModal, showRegionDeleteModal, regionDeleteSubmitting, regionDeletePassword, pendingDeleteRegion, passwordForm, selfPasswordForm, showResetPasswordModal, showSelfPasswordModal, selectedJobIds, selectedApplicationIds, selectedInterviewIds,
    selectedPassedIds, selectedTalentIds, jobFilters, showJobForm, showInterviewScheduleForm, showInterviewResultForm, interviewScheduleHasExisting, scheduleSaving, resultSaving, interviewTimeSort, applicationFilters, interviewFilters, passedFilters, talentFilters, operationLogFilters, interviewScheduleForm, interviewResultForm, publicRegions, regions, jobs,
    applications, interviewCandidates, interviewPagination, passedCandidates, talentPoolCandidates, operationLogs, passedPagination, talentPagination, operationLogPagination, operationLogPageCursorMap, interviewMeta, users, userProfile, activeApplication, applicationDetailLoading, applicationOperationLogs, applicationLogsLoading, operationLogsQueried, operationLogMeta, listPageSizeOptions,
    dataLoaded, dataLoading,
  } = createAdminAppState();

  const {
    visibleTabs, interviewRoundHint, interviewResultOptions, currentTitle, userInitial, showRegionFilter, hasJobKeyword, filteredJobs, selectedJobStats, canBatchActivateJobs, canBatchDeactivateJobs, operationModuleOptions, operationLogSuccessCount, operationLogFailedCount, operationLogPageSizeOptions, operationLogKnownMaxPage, operationLogPageItems, jobCategories, filteredApplications, groupedApplications,
    interviewJobCategories, filteredInterviewCandidates, sortedInterviewCandidates, passedJobCategories, passedStatusOptions, filteredPassedCandidates, talentJobCategories, filteredTalentCandidates, selectedApplicationsCount, selectedJobsCount, isAllJobsSelected, selectedInterviewCount, isAllVisibleInterviewsSelected, isAllVisiblePassedSelected, selectedTalentCount, isAllVisibleTalentSelected,
  } = useAdminDerivedState({
    tabs, userProfile, interviewScheduleForm, interviewScheduleHasExisting, interviewMeta, activeTab, currentUsername, jobFilters, jobs, selectedJobIds, operationLogs, operationLogMeta, operationLogPageCursorMap, operationLogPagination, applications, applicationFilters, interviewCandidates, interviewFilters, interviewTimeSort, passedCandidates,
    passedFilters, talentPoolCandidates, talentFilters, selectedApplicationIds, selectedInterviewIds, selectedPassedIds, selectedTalentIds,
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
    fetchPublicRegions, loadRegions, loadJobs, loadApplications, loadInterviewCandidates, loadInterviewMeta, loadPassedCandidates, loadTalentPoolCandidates, loadOperationLogMeta, loadOperationLogs, loadApplicationOperationLogs, loadUsers, ensureTabData, loadProfile,
  } = useAdminDataLoaders({
    buildApiUrl, request, adminBase, authBase, interviewApi, dataLoaded, dataLoading, publicRegions, regions, jobs, applications, interviewCandidates, interviewPagination, passedCandidates, talentPoolCandidates, operationLogs, applicationOperationLogs, applicationLogsLoading, operationLogFilters, operationLogMeta,
    operationLogPagination, operationLogPageCursorMap, operationLogsQueried, users, userProfile, jobForm, activeTab, visibleTabs, token, selectedJobIds, selectedApplicationIds, selectedInterviewIds, selectedPassedIds, selectedTalentIds, applicationFilters, interviewFilters, passedFilters, talentFilters, interviewMeta, passedPagination,
    talentPagination, jobCategories, interviewJobCategories, passedJobCategories, talentJobCategories, operationLogPageSizeOptions, notifyError,
  });

  const {
    resetJobFilters, resetApplicationFilters, resetInterviewFilters, resetPassedFilters, resetTalentFilters, resetOperationLogFilters, resetOperationLogMeta, toggleInterviewTimeSort, resetInterviewScheduleForm, resetInterviewResultForm,
  } = createAdminResetHelpers({
    jobFilters, applicationFilters, interviewFilters, interviewTimeSort, passedFilters, talentFilters, operationLogFilters, operationLogMeta, operationLogsQueried, interviewScheduleForm, interviewResultForm, interviewMeta,
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
    interviewPagination,
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
  const {
    regionName, operationModuleLabel, operationActionLabel, operationResultLabel, operationResultClass, interviewStatusClass, interviewStatusText, formatTime, canScheduleInterview, scheduleActionLabel,
  } = createAdminDisplayHelpers({
    regions, operationLogMeta, interviewMeta,
  });

  const {
    resetRegionForm, openRegionCreateModal, closeRegionCreateModal, saveRegion, openDeleteRegionModal, closeDeleteRegionModal, confirmDeleteRegion,
  } = useAdminRegionActions({
    regionForm, showRegionCreateModal, showRegionDeleteModal, regionDeleteSubmitting, regionDeletePassword, pendingDeleteRegion, request, adminBase, dataLoaded, publicRegions, loadRegions, loadJobs, fetchPublicRegions, notifySuccess, notifyError, toastRef,
  });

  const {
    resetJobForm, openNewJob, closeJobForm, editJob, deleteJob, batchUpdateJobsStatus, batchActivateJobs, batchDeactivateJobs, batchDeleteJobs, saveJob,
  } = useAdminJobActions({
    jobForm, userProfile, showJobForm, selectedJobIds, jobs, dataLoaded, request, adminBase, loadJobs, loadApplications, runWithConfirm, notifySuccess, notifyError, toastRef,
  });

  const {
    openResetPasswordModal, closeResetPasswordModal, openSelfPasswordModal, closeSelfPasswordModal, resetUserPassword, changeMyPassword, selectUserForReset, deleteUser,
  } = useAdminAccountActions({
    passwordForm, selfPasswordForm, showResetPasswordModal, showSelfPasswordModal, request, adminBase, authBase, logout, runWithConfirm, loadUsers, notifySuccess, notifyError, toastRef,
  });

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

  const {
    isApplicationSelected, getApplicationGroupIds, isApplicationGroupFullySelected, toggleApplicationGroupSelection, toggleApplicationSelection, addSelectedToInterviewPool, addSelectedToTalentPool, addSelectedTalentToInterviewPool, refreshInterviewCandidates, changeInterviewPage, changePassedPage, changeTalentPage, changeInterviewPageSize, changePassedPageSize, changeTalentPageSize, changeOperationLogPage, changeOperationLogPageSize, refreshPassedCandidates, confirmSelectedPassedHires, changePassedCandidateStatus, refreshTalentPoolCandidates,
    searchOperationLogs, refreshOperationLogs, refreshInterviewModules, batchRemoveInterviewCandidates, removeInterviewCandidate,
  } = useAdminApplicationActions({
    selectedApplicationIds, selectedInterviewIds, selectedPassedIds, selectedTalentIds, activeTab, dataLoaded, interviewPagination, passedPagination, talentPagination, operationLogPagination, operationLogPageCursorMap, runWithConfirm, interviewApi, loadApplications, loadInterviewCandidates, loadPassedCandidates, loadTalentPoolCandidates, loadOperationLogs, resetInterviewFilters, resetPassedFilters,
    resetTalentFilters, resetOperationLogPageState, notifySuccess, notifyError,
  });

  const {
    openInterviewSchedule, closeInterviewSchedule, openInterviewResult, closeInterviewResult, saveInterviewSchedule, retryInterviewSms, cancelInterviewSchedule, cancelInterviewScheduleFromForm, saveInterviewResult,
  } = useAdminInterviewActions({
    interviewScheduleForm, interviewResultForm, interviewMeta, activeApplication, applicationDetailLoading, interviewScheduleHasExisting, showInterviewScheduleForm, showInterviewResultForm, scheduleSaving, resultSaving, toastRef, interviewApi, loadInterviewCandidates, refreshInterviewModules, dataLoaded, notifySuccess, notifyError, runWithConfirm, resetInterviewScheduleForm, resetInterviewResultForm,
  });

  const {
    openApplicationFromInterview, openApplicationFromOutcome, openApplication, closeApplication, attachmentCardMeta, applicationAttachments, keyAttachmentCards, otherAttachmentFiles, openAttachment, detailSections,
  } = useAdminApplicationDetail({
    activeApplication, applicationDetailLoading, applicationOperationLogs, applicationLogsLoading, resolveMediaUrl, request, adminBase, loadApplicationOperationLogs, notifyError,
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

  return createAdminAppPublicApi({
    toastRef, confirmRef, adminBase, authBase,
    resolveMediaUrl, resetOperationLogPageState, token, currentUsername,
    authMode, activeTab, tabs, authForm,
    jobForm, regionForm, showRegionCreateModal, showRegionDeleteModal,
    regionDeleteSubmitting, regionDeletePassword, pendingDeleteRegion, passwordForm,
    selfPasswordForm, showResetPasswordModal, showSelfPasswordModal, selectedJobIds,
    selectedApplicationIds, selectedInterviewIds, selectedPassedIds, selectedTalentIds,
    jobFilters, showJobForm, showInterviewScheduleForm, showInterviewResultForm,
    interviewScheduleHasExisting, scheduleSaving, resultSaving, interviewTimeSort,
    applicationFilters, interviewFilters, passedFilters, talentFilters,
    operationLogFilters, interviewScheduleForm, interviewResultForm, publicRegions,
    regions, jobs, applications, interviewCandidates,
    passedCandidates, talentPoolCandidates, operationLogs, listPageSizeOptions,
    interviewPagination, passedPagination, talentPagination, operationLogPagination,
    operationLogPageCursorMap, interviewMeta, users, userProfile,
    activeApplication, applicationDetailLoading, applicationOperationLogs, applicationLogsLoading,
    operationLogsQueried, operationLogMeta, dataLoaded, dataLoading,
    visibleTabs, interviewRoundHint, interviewResultOptions, currentTitle,
    userInitial, showRegionFilter, hasJobKeyword, filteredJobs,
    selectedJobStats, canBatchActivateJobs, canBatchDeactivateJobs, operationModuleOptions,
    operationLogSuccessCount, operationLogFailedCount, operationLogPageSizeOptions, operationLogKnownMaxPage,
    operationLogPageItems, jobCategories, filteredApplications, groupedApplications,
    interviewJobCategories, filteredInterviewCandidates, sortedInterviewCandidates, passedJobCategories,
    passedStatusOptions, filteredPassedCandidates, talentJobCategories, filteredTalentCandidates,
    selectedApplicationsCount, selectedJobsCount, isAllJobsSelected, selectedInterviewCount,
    isAllVisibleInterviewsSelected, isAllVisiblePassedSelected, selectedTalentCount, isAllVisibleTalentSelected,
    request, interviewApi, notifyError, notifySuccess,
    askConfirm, runWithConfirm, fetchPublicRegions, loadRegions,
    loadJobs, loadApplications, loadInterviewCandidates, loadInterviewMeta,
    loadPassedCandidates, loadTalentPoolCandidates, loadOperationLogMeta, loadOperationLogs,
    loadApplicationOperationLogs, loadUsers, ensureTabData, loadProfile,
    submitAuth, logout, regionName, operationModuleLabel,
    operationActionLabel, operationResultLabel, operationResultClass, interviewStatusClass,
    interviewStatusText, formatTime, canScheduleInterview, scheduleActionLabel,
    openRegionCreateModal, closeRegionCreateModal, resetRegionForm, saveRegion,
    openDeleteRegionModal, closeDeleteRegionModal, confirmDeleteRegion, resetJobForm,
    openNewJob, closeJobForm, editJob, deleteJob,
    batchUpdateJobsStatus, batchActivateJobs, batchDeactivateJobs, batchDeleteJobs,
    saveJob, openResetPasswordModal, closeResetPasswordModal, openSelfPasswordModal,
    closeSelfPasswordModal, resetUserPassword, changeMyPassword, selectUserForReset,
    deleteUser, fetchApplications, refreshApplications, fetchJobs,
    resetJobFilters, resetApplicationFilters, resetInterviewFilters, resetPassedFilters,
    resetTalentFilters, resetOperationLogFilters, resetOperationLogMeta, toggleInterviewTimeSort,
    resetInterviewScheduleForm, resetInterviewResultForm, openInterviewSchedule, closeInterviewSchedule,
    openInterviewResult, closeInterviewResult, saveInterviewSchedule, retryInterviewSms,
    cancelInterviewSchedule, cancelInterviewScheduleFromForm, saveInterviewResult, isApplicationSelected,
    getApplicationGroupIds, isApplicationGroupFullySelected, toggleApplicationGroupSelection, toggleApplicationSelection,
    addSelectedToInterviewPool, addSelectedToTalentPool, addSelectedTalentToInterviewPool, refreshInterviewCandidates,
    changeInterviewPage, changePassedPage, changeTalentPage, changeInterviewPageSize,
    changePassedPageSize, changeTalentPageSize, changeOperationLogPage, changeOperationLogPageSize,
    refreshPassedCandidates, confirmSelectedPassedHires, changePassedCandidateStatus, refreshTalentPoolCandidates, searchOperationLogs,
    refreshOperationLogs, refreshInterviewModules, batchRemoveInterviewCandidates, removeInterviewCandidate,
    openApplicationFromInterview, openApplicationFromOutcome, openApplication, closeApplication,
    attachmentCardMeta, applicationAttachments, keyAttachmentCards, otherAttachmentFiles,
    openAttachment, detailSections,
  });
};
