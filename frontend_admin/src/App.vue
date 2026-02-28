<template>
  <!-- 文件说明：管理后台主页面，组织标签页、数据加载与主要业务交互。 -->
  <!-- 全局组件挂载点 -->
  <Toast ref="toastRef" />
  <ConfirmDialog ref="confirmRef" />

  <!-- 登录/注册页面 -->
  <AdminAuthPanel
    v-if="!token"
    :auth-mode="authMode"
    :auth-form="authForm"
    :public-regions="publicRegions"
    :current-year="currentYear"
    @update:auth-mode="authMode = $event"
    @submit="submitAuth"
  />

  <!-- 管理后台主界面 -->
  <div v-else class="admin-layout">
    <!-- 侧边栏 -->
    <AdminSidebar
      :visible-tabs="visibleTabs"
      :active-tab="activeTab"
      :user-initial="userInitial"
      :current-username="currentUsername"
      :user-profile="userProfile"
      @logout="logout"
    />

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="top-bar">
        <h2 class="page-title">{{ currentTitle }}</h2>
      </header>

      <div class="content-body">
        
        <!-- 地区管理 -->
        <RegionsTabPanel
          v-if="activeTab === 'regions' && userProfile.is_superuser"
          :regions="regions"
          @open-create="openRegionCreateModal"
          @open-delete="openDeleteRegionModal"
        />

        <!-- 岗位管理 -->
        <JobsTabPanel
          v-else-if="activeTab === 'jobs'"
          :jobs="jobs"
          :filtered-jobs="filteredJobs"
          :job-filters="jobFilters"
          :has-job-keyword="hasJobKeyword"
          :selected-jobs-count="selectedJobsCount"
          :can-batch-activate-jobs="canBatchActivateJobs"
          :can-batch-deactivate-jobs="canBatchDeactivateJobs"
          :selected-job-ids="selectedJobIds"
          :is-all-jobs-selected="isAllJobsSelected"
          :region-name="regionName"
          :on-open-new-job="openNewJob"
          :on-fetch-jobs="fetchJobs"
          :on-reset-job-filters="resetJobFilters"
          :on-batch-activate-jobs="batchActivateJobs"
          :on-batch-deactivate-jobs="batchDeactivateJobs"
          :on-batch-delete-jobs="batchDeleteJobs"
          :on-edit-job="editJob"
          :on-delete-job="deleteJob"
          @update:selected-job-ids="selectedJobIds = $event"
          @update:is-all-jobs-selected="isAllJobsSelected = $event"
        />

        <!-- 账号管理 -->
        <AccountsTabPanel
          v-else-if="activeTab === 'accounts' && userProfile.is_superuser"
          :users="users"
          :current-username="currentUsername"
          @open-self-password="openSelfPasswordModal"
          @select-user-reset="selectUserForReset"
          @delete-user="deleteUser"
        />

        <!-- 应聘记录 -->
        <ApplicationsTabPanel
          v-else-if="activeTab === 'applications'"
          :filtered-applications="filteredApplications"
          :applications="applications"
          :selected-applications-count="selectedApplicationsCount"
          :job-categories="jobCategories"
          :application-filters="applicationFilters"
          :show-region-filter="showRegionFilter"
          :regions="regions"
          :grouped-applications="groupedApplications"
          :resolve-media-url="resolveMediaUrl"
          :on-add-selected-to-interview-pool="addSelectedToInterviewPool"
          :on-add-selected-to-talent-pool="addSelectedToTalentPool"
          :on-refresh-applications="refreshApplications"
          :on-reset-application-filters="resetApplicationFilters"
          :on-toggle-application-group-selection="toggleApplicationGroupSelection"
          :on-is-application-group-fully-selected="isApplicationGroupFullySelected"
          :on-is-application-selected="isApplicationSelected"
          :on-toggle-application-selection="toggleApplicationSelection"
          :on-open-application="openApplication"
        />

        <InterviewCandidatesModule
          v-else-if="activeTab === 'interviews'"
          :filtered-interview-candidates="filteredInterviewCandidates"
          :interview-candidates="interviewCandidates"
          :pagination="interviewPagination"
          :page-size-options="listPageSizeOptions"
          :loading="dataLoading.interviews"
          :selected-interview-count="selectedInterviewCount"
          :selected-interview-ids="selectedInterviewIds"
          :is-all-visible-interviews-selected="isAllVisibleInterviewsSelected"
          :interview-job-categories="interviewJobCategories"
          :interview-filters="interviewFilters"
          :show-region-filter="showRegionFilter"
          :regions="regions"
          :sorted-interview-candidates="sortedInterviewCandidates"
          :interview-time-sort="interviewTimeSort"
          :interview-meta="interviewMeta"
          :interview-result-options="interviewResultOptions"
          :show-interview-schedule-form="showInterviewScheduleForm"
          :show-interview-result-form="showInterviewResultForm"
          :interview-schedule-has-existing="interviewScheduleHasExisting"
          :schedule-saving="scheduleSaving"
          :result-saving="resultSaving"
          :interview-schedule-form="interviewScheduleForm"
          :interview-result-form="interviewResultForm"
          :interview-round-hint="interviewRoundHint"
          :format-time="formatTime"
          :interview-status-class="interviewStatusClass"
          :interview-status-text="interviewStatusText"
          :can-schedule-interview="canScheduleInterview"
          :schedule-action-label="scheduleActionLabel"
          @update:selected-interview-ids="selectedInterviewIds = $event"
          @update:is-all-visible-interviews-selected="isAllVisibleInterviewsSelected = $event"
          @refresh="refreshInterviewCandidates"
          @batch-remove="batchRemoveInterviewCandidates"
          @reset-filters="resetInterviewFilters"
          @change-page="changeInterviewPage"
          @change-page-size="changeInterviewPageSize"
          @toggle-time-sort="toggleInterviewTimeSort"
          @open-schedule="openInterviewSchedule"
          @open-result="openInterviewResult"
          @retry-sms="retryInterviewSms"
          @open-detail="openApplicationFromInterview"
          @remove="removeInterviewCandidate"
          @close-schedule="closeInterviewSchedule"
          @save-schedule="saveInterviewSchedule"
          @cancel-schedule-from-form="cancelInterviewScheduleFromForm"
          @close-result="closeInterviewResult"
          @save-result="saveInterviewResult"
        />

        <PassedCandidatesSection
          v-else-if="activeTab === 'passed'"
          :items="passedCandidates"
          :filtered-items="filteredPassedCandidates"
          :job-categories="passedJobCategories"
          :status-options="passedStatusOptions"
          :status-action-options="passedStatusActionOptions"
          :filters="passedFilters"
          :interview-status-class="interviewStatusClass"
          :interview-status-text="interviewStatusText"
          :selected-ids="selectedPassedIds"
          :is-all-visible-selected="isAllVisiblePassedSelected"
          :pagination="passedPagination"
          :page-size-options="listPageSizeOptions"
          :loading="dataLoading.passed"
          @refresh="refreshPassedCandidates"
          @primary-action="confirmSelectedPassedHires"
          @secondary-action="confirmSelectedPassedOnboard"
          @change-status="changePassedCandidateStatus"
          @reset-filters="resetPassedFilters"
          @open-detail="openApplicationFromOutcome"
          @update:selected-ids="selectedPassedIds = $event"
          @update:is-all-visible-selected="isAllVisiblePassedSelected = $event"
          @change-page="changePassedPage"
          @change-page-size="changePassedPageSize"
        />

        <TalentPoolCandidatesSection
          v-else-if="activeTab === 'talent'"
          :items="talentPoolCandidates"
          :filtered-items="filteredTalentCandidates"
          :job-categories="talentJobCategories"
          :filters="talentFilters"
          :interview-status-class="interviewStatusClass"
          :interview-status-text="interviewStatusText"
          :selected-ids="selectedTalentIds"
          :is-all-visible-selected="isAllVisibleTalentSelected"
          :pagination="talentPagination"
          :page-size-options="listPageSizeOptions"
          :loading="dataLoading.talent"
          @refresh="refreshTalentPoolCandidates"
          @reset-filters="resetTalentFilters"
          @open-detail="openApplicationFromOutcome"
          @primary-action="addSelectedTalentToInterviewPool"
          @update:selected-ids="selectedTalentIds = $event"
          @update:is-all-visible-selected="isAllVisibleTalentSelected = $event"
          @change-page="changeTalentPage"
          @change-page-size="changeTalentPageSize"
        />

        <OperationLogPanel
          v-else-if="activeTab === 'operationLogs'"
          :operation-logs="operationLogs"
          :operation-log-success-count="operationLogSuccessCount"
          :operation-log-failed-count="operationLogFailedCount"
          :operation-module-options="operationModuleOptions"
          :operation-log-filters="operationLogFilters"
          :operation-logs-queried="operationLogsQueried"
          :operation-log-pagination="operationLogPagination"
          :operation-log-page-size-options="operationLogPageSizeOptions"
          :operation-log-page-items="operationLogPageItems"
          :operation-log-page-cursor-map="operationLogPageCursorMap"
          :loading="dataLoading.operationLogs"
          :on-refresh="refreshOperationLogs"
          :on-search="searchOperationLogs"
          :on-reset-filters="resetOperationLogFilters"
          :on-change-page-size="changeOperationLogPageSize"
          :on-change-page="changeOperationLogPage"
          :format-time="formatTime"
          :operation-module-label="operationModuleLabel"
          :operation-action-label="operationActionLabel"
          :operation-result-class="operationResultClass"
          :operation-result-label="operationResultLabel"
        />

        <div v-else class="card">
          <div class="card-body">暂无内容</div>
        </div>

      </div>
    </main>

    <ApplicationDetailModal
      :active-application="activeApplication"
      :application-detail-loading="applicationDetailLoading"
      :detail-sections="detailSections"
      :key-attachment-cards="keyAttachmentCards"
      :other-attachment-files="otherAttachmentFiles"
      :application-logs-loading="applicationLogsLoading"
      :application-operation-logs="applicationOperationLogs"
      :resolve-media-url="resolveMediaUrl"
      :format-time="formatTime"
      :operation-result-class="operationResultClass"
      :operation-result-label="operationResultLabel"
      :operation-module-label="operationModuleLabel"
      :operation-action-label="operationActionLabel"
      @close="closeApplication"
      @open-attachment="openAttachment"
    />

    <AccountPasswordModals
      :show-reset-password-modal="showResetPasswordModal"
      :show-self-password-modal="showSelfPasswordModal"
      :users="users"
      :password-form="passwordForm"
      :self-password-form="selfPasswordForm"
      @close-reset="closeResetPasswordModal"
      @submit-reset="submitResetPassword"
      @close-self="closeSelfPasswordModal"
      @submit-self="submitSelfPassword"
    />

    <RegionModals
      :show-region-create-modal="showRegionCreateModal"
      :show-region-delete-modal="showRegionDeleteModal"
      :region-form="regionForm"
      :pending-delete-region="pendingDeleteRegion"
      :region-delete-password="regionDeletePassword"
      :region-delete-submitting="regionDeleteSubmitting"
      @close-create="closeRegionCreateModal"
      @submit-create="submitRegionCreate"
      @reset-region-form="resetRegionForm"
      @close-delete="closeDeleteRegionModal"
      @update:region-delete-password="regionDeletePassword = $event"
      @confirm-delete="confirmDeleteRegion"
    />

    <JobEditorModal
      :show-job-form="showJobForm"
      :job-form="jobForm"
      :user-profile="userProfile"
      :regions="regions"
      @close="closeJobForm"
      @save="saveJob"
      @reset="resetJobForm"
    />

  </div>
</template>

<script setup>
// 业务模块组件
import { useRoute, useRouter } from "vue-router";
import Toast from "./components/Toast.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import AdminAuthPanel from "./components/AdminAuthPanel.vue";
import AdminSidebar from "./components/AdminSidebar.vue";
import InterviewCandidatesModule from "./components/InterviewCandidatesModule.vue";
import PassedCandidatesSection from "./components/PassedCandidatesSection.vue";
import TalentPoolCandidatesSection from "./components/TalentPoolCandidatesSection.vue";
import ApplicationDetailModal from "./components/ApplicationDetailModal.vue";
import AccountPasswordModals from "./components/AccountPasswordModals.vue";
import OperationLogPanel from "./components/OperationLogPanel.vue";
import RegionModals from "./components/RegionModals.vue";
import JobEditorModal from "./components/JobEditorModal.vue";
import RegionsTabPanel from "./components/RegionsTabPanel.vue";
import AccountsTabPanel from "./components/AccountsTabPanel.vue";
import JobsTabPanel from "./components/JobsTabPanel.vue";
import ApplicationsTabPanel from "./components/ApplicationsTabPanel.vue";
import { useAdminRouteSync } from "./composables/adminAppPage/useAdminRouteSync";
import { createAdminModalSubmitters } from "./composables/adminAppPage/useAdminModalSubmitters";
import { useAdminAppPage } from "./composables/useAdminAppPage";
import { OFFER_STATUS_ACTION_OPTIONS } from "./utils/offerStatusTransition";

const {
  toastRef, confirmRef, resolveMediaUrl, token,
  currentUsername, authMode, activeTab, tabs,
  authForm, jobForm, regionForm, showRegionCreateModal,
  showRegionDeleteModal, regionDeleteSubmitting, regionDeletePassword, pendingDeleteRegion,
  passwordForm, selfPasswordForm, showResetPasswordModal, showSelfPasswordModal,
  selectedJobIds, selectedInterviewIds, selectedPassedIds, selectedTalentIds,
  jobFilters, showJobForm, showInterviewScheduleForm, showInterviewResultForm,
  interviewScheduleHasExisting, scheduleSaving, resultSaving, interviewTimeSort,
  applicationFilters, interviewFilters, passedFilters, talentFilters,
  operationLogFilters, interviewScheduleForm, interviewResultForm, publicRegions,
  regions, jobs, applications, interviewCandidates,
  interviewPagination, passedCandidates, talentPoolCandidates, operationLogs,
  listPageSizeOptions, passedPagination, talentPagination, operationLogPagination,
  operationLogPageCursorMap, interviewMeta, users, userProfile,
  activeApplication, applicationDetailLoading, applicationOperationLogs, applicationLogsLoading,
  operationLogsQueried, dataLoading, visibleTabs, interviewRoundHint,
  interviewResultOptions, currentTitle, userInitial, showRegionFilter,
  hasJobKeyword, filteredJobs, canBatchActivateJobs, canBatchDeactivateJobs,
  operationModuleOptions, operationLogSuccessCount, operationLogFailedCount, operationLogPageSizeOptions,
  operationLogPageItems, jobCategories, filteredApplications, groupedApplications,
  interviewJobCategories, filteredInterviewCandidates, sortedInterviewCandidates, passedJobCategories,
  passedStatusOptions, filteredPassedCandidates, talentJobCategories, filteredTalentCandidates,
  selectedApplicationsCount, selectedJobsCount, isAllJobsSelected, selectedInterviewCount,
  isAllVisibleInterviewsSelected, isAllVisiblePassedSelected, isAllVisibleTalentSelected, submitAuth,
  logout, regionName, operationModuleLabel, operationActionLabel,
  operationResultLabel, operationResultClass, interviewStatusClass, interviewStatusText,
  formatTime, canScheduleInterview, scheduleActionLabel, openRegionCreateModal,
  closeRegionCreateModal, resetRegionForm, saveRegion, openDeleteRegionModal,
  closeDeleteRegionModal, confirmDeleteRegion, resetJobForm, openNewJob,
  closeJobForm, editJob, deleteJob, batchActivateJobs,
  batchDeactivateJobs, batchDeleteJobs, saveJob, closeResetPasswordModal,
  openSelfPasswordModal, closeSelfPasswordModal, resetUserPassword, changeMyPassword,
  selectUserForReset, deleteUser, refreshApplications, fetchJobs,
  resetJobFilters, resetApplicationFilters, resetInterviewFilters, resetPassedFilters,
  resetTalentFilters, resetOperationLogFilters, toggleInterviewTimeSort, openInterviewSchedule,
  closeInterviewSchedule, openInterviewResult, closeInterviewResult, saveInterviewSchedule,
  retryInterviewSms, cancelInterviewScheduleFromForm, saveInterviewResult, isApplicationSelected,
  isApplicationGroupFullySelected, toggleApplicationGroupSelection, toggleApplicationSelection, addSelectedToInterviewPool,
  addSelectedToTalentPool, addSelectedTalentToInterviewPool, refreshInterviewCandidates, changeInterviewPage,
  changePassedPage, changeTalentPage, changeInterviewPageSize, changePassedPageSize,
  changeTalentPageSize, changeOperationLogPage, changeOperationLogPageSize, refreshPassedCandidates,
  confirmSelectedPassedHires, confirmSelectedPassedOnboard, changePassedCandidateStatus, refreshTalentPoolCandidates, searchOperationLogs, refreshOperationLogs,
  batchRemoveInterviewCandidates, removeInterviewCandidate, openApplicationFromInterview, openApplicationFromOutcome,
  openApplication, closeApplication, keyAttachmentCards, otherAttachmentFiles,
  openAttachment, detailSections,
} = useAdminAppPage();

const route = useRoute();
const router = useRouter();
const currentYear = new Date().getFullYear();
const passedStatusActionOptions = OFFER_STATUS_ACTION_OPTIONS;

useAdminRouteSync({
  route,
  router,
  tabs,
  visibleTabs,
  activeTab,
  token,
  userProfile,
});

const {
  submitRegionCreate,
  submitResetPassword,
  submitSelfPassword,
} = createAdminModalSubmitters({
  saveRegion,
  closeRegionCreateModal,
  resetUserPassword,
  closeResetPasswordModal,
  changeMyPassword,
  closeSelfPasswordModal,
});
</script>
