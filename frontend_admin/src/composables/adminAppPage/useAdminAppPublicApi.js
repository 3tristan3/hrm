import { createAdminAppReturn } from "./useAdminAppReturn";

export function createAdminAppPublicApi(args) {
  const {
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
    refreshPassedCandidates, confirmSelectedPassedHires, confirmSelectedPassedOnboard, changePassedCandidateStatus, refreshTalentPoolCandidates, searchOperationLogs,
    refreshOperationLogs, refreshInterviewModules, batchRemoveInterviewCandidates, removeInterviewCandidate,
    openApplicationFromInterview, openApplicationFromOutcome, openApplication, closeApplication,
    attachmentCardMeta, applicationAttachments, keyAttachmentCards, otherAttachmentFiles,
    openAttachment, detailSections,
  } = args;

  const stateSection = {
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
  };

  const derivedSection = {
    visibleTabs, interviewRoundHint, interviewResultOptions, currentTitle,
    userInitial, showRegionFilter, hasJobKeyword, filteredJobs,
    selectedJobStats, canBatchActivateJobs, canBatchDeactivateJobs, operationModuleOptions,
    operationLogSuccessCount, operationLogFailedCount, operationLogPageSizeOptions, operationLogKnownMaxPage,
    operationLogPageItems, jobCategories, filteredApplications, groupedApplications,
    interviewJobCategories, filteredInterviewCandidates, sortedInterviewCandidates, passedJobCategories,
    passedStatusOptions, filteredPassedCandidates, talentJobCategories, filteredTalentCandidates,
    selectedApplicationsCount, selectedJobsCount, isAllJobsSelected, selectedInterviewCount,
    isAllVisibleInterviewsSelected, isAllVisiblePassedSelected, selectedTalentCount, isAllVisibleTalentSelected,
  };

  const serviceSection = {
    request, interviewApi, notifyError, notifySuccess,
    askConfirm, runWithConfirm,
  };

  const loaderSection = {
    fetchPublicRegions, loadRegions, loadJobs, loadApplications,
    loadInterviewCandidates, loadInterviewMeta, loadPassedCandidates, loadTalentPoolCandidates,
    loadOperationLogMeta, loadOperationLogs, loadApplicationOperationLogs, loadUsers,
    ensureTabData, loadProfile,
  };

  const sessionSection = {
    submitAuth, logout,
  };

  const displaySection = {
    regionName, operationModuleLabel, operationActionLabel, operationResultLabel,
    operationResultClass, interviewStatusClass, interviewStatusText, formatTime,
    canScheduleInterview, scheduleActionLabel,
  };

  const regionSection = {
    openRegionCreateModal, closeRegionCreateModal, resetRegionForm, saveRegion,
    openDeleteRegionModal, closeDeleteRegionModal, confirmDeleteRegion,
  };

  const jobSection = {
    resetJobForm, openNewJob, closeJobForm, editJob,
    deleteJob, batchUpdateJobsStatus, batchActivateJobs, batchDeactivateJobs,
    batchDeleteJobs, saveJob,
  };

  const accountSection = {
    openResetPasswordModal, closeResetPasswordModal, openSelfPasswordModal, closeSelfPasswordModal,
    resetUserPassword, changeMyPassword, selectUserForReset, deleteUser,
  };

  const fetchSection = {
    fetchApplications, refreshApplications, fetchJobs,
  };

  const resetSection = {
    resetJobFilters, resetApplicationFilters, resetInterviewFilters, resetPassedFilters,
    resetTalentFilters, resetOperationLogFilters, resetOperationLogMeta, toggleInterviewTimeSort,
    resetInterviewScheduleForm, resetInterviewResultForm,
  };

  const interviewSection = {
    openInterviewSchedule, closeInterviewSchedule, openInterviewResult, closeInterviewResult,
    saveInterviewSchedule, retryInterviewSms, cancelInterviewSchedule, cancelInterviewScheduleFromForm,
    saveInterviewResult,
  };

  const applicationSection = {
    isApplicationSelected, getApplicationGroupIds, isApplicationGroupFullySelected, toggleApplicationGroupSelection,
    toggleApplicationSelection, addSelectedToInterviewPool, addSelectedToTalentPool, addSelectedTalentToInterviewPool,
    refreshInterviewCandidates, changeInterviewPage, changePassedPage, changeTalentPage,
    changeInterviewPageSize, changePassedPageSize, changeTalentPageSize, changeOperationLogPage,
    changeOperationLogPageSize, refreshPassedCandidates, confirmSelectedPassedHires, confirmSelectedPassedOnboard, changePassedCandidateStatus, refreshTalentPoolCandidates,
    searchOperationLogs, refreshOperationLogs, refreshInterviewModules, batchRemoveInterviewCandidates,
    removeInterviewCandidate,
  };

  const detailSection = {
    openApplicationFromInterview, openApplicationFromOutcome, openApplication, closeApplication,
    attachmentCardMeta, applicationAttachments, keyAttachmentCards, otherAttachmentFiles,
    openAttachment, detailSections,
  };

  return createAdminAppReturn({
    stateSection,
    derivedSection,
    serviceSection,
    loaderSection,
    sessionSection,
    displaySection,
    regionSection,
    jobSection,
    accountSection,
    fetchSection,
    resetSection,
    applicationSection,
    interviewSection,
    detailSection,
  });
}
