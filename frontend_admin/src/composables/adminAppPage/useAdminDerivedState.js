import { computed } from "vue";
import { useJobCategoryFilter } from "../useJobCategoryFilter";
import { useSelectionState } from "../useSelectionState";
import { useHireStatusFilter } from "./useHireStatusFilter";
import {
  DEFAULT_OPERATION_LOG_META,
  buildOperationModuleOptions,
} from "../../constants/operationLog";
import { defaultInterviewMeta } from "../../utils/interviewMeta";
import { resolveOfferStatus } from "../../utils/offerStatusTransition";

export const useAdminDerivedState = ({
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
}) => {
  const visibleTabs = computed(() =>
    tabs.filter((tab) => (tab.adminOnly ? userProfile.is_superuser : true))
  );
  const interviewRoundHint = computed(() => {
    const round = Math.max(Number(interviewScheduleForm.interview_round || 1), 1);
    if (interviewScheduleHasExisting.value) {
      return `第${round}轮（改期）`;
    }
    return `第${round}轮`;
  });
  const interviewResultOptions = computed(() => {
    const preferredOrder = [
      interviewMeta.result_next_round,
      interviewMeta.result_pass,
      interviewMeta.result_reject,
      interviewMeta.result_pending,
    ].filter(Boolean);
    const source = Array.isArray(interviewMeta.result_choices)
      ? interviewMeta.result_choices
      : [];
    const byValue = new Map(source.map((item) => [item.value, item]));
    const ordered = preferredOrder
      .filter((value) => byValue.has(value))
      .map((value) => byValue.get(value));
    source.forEach((item) => {
      if (!ordered.find((v) => v.value === item.value)) {
        ordered.push(item);
      }
    });
    return ordered.length
      ? ordered
      : defaultInterviewMeta.result_choices.map((item) => ({ ...item }));
  });
  const currentTitle = computed(
    () => visibleTabs.value.find((t) => t.key === activeTab.value)?.label || "管理后台"
  );
  const userInitial = computed(() =>
    currentUsername.value ? currentUsername.value[0].toUpperCase() : "A"
  );
  const showRegionFilter = computed(
    () => userProfile.can_view_all || userProfile.is_superuser
  );
  const hasJobKeyword = computed(() => Boolean(jobFilters.keyword.trim()));
  const filteredJobs = computed(() => {
    const keyword = jobFilters.keyword.trim().toLowerCase();
    if (!keyword) return jobs.value;
    return jobs.value.filter((item) =>
      [
        item?.title,
        item?.region_name,
        item?.description,
        item?.salary,
        item?.education,
        item?.is_active ? "上架 启用" : "下架 停用",
        item?.region,
      ]
        .filter((value) => value !== null && value !== undefined)
        .some((value) => String(value).toLowerCase().includes(keyword))
    );
  });
  const selectedJobStats = computed(() => {
    const selectedSet = new Set(selectedJobIds.value);
    let activeCount = 0;
    let inactiveCount = 0;
    jobs.value.forEach((item) => {
      if (!selectedSet.has(item.id)) return;
      if (item.is_active) activeCount += 1;
      else inactiveCount += 1;
    });
    return {
      activeCount,
      inactiveCount,
    };
  });
  const canBatchActivateJobs = computed(() => selectedJobStats.value.inactiveCount > 0);
  const canBatchDeactivateJobs = computed(() => selectedJobStats.value.activeCount > 0);
  const operationModuleOptions = computed(() =>
    buildOperationModuleOptions(operationLogs.value, operationLogMeta.module_labels)
  );
  const operationLogSuccessCount = computed(
    () => operationLogs.value.filter((item) => item?.result === "success").length
  );
  const operationLogFailedCount = computed(
    () => operationLogs.value.filter((item) => item?.result === "failed").length
  );
  const operationLogPageSizeOptions = computed(() =>
    Array.isArray(operationLogMeta.page_size_options) && operationLogMeta.page_size_options.length
      ? operationLogMeta.page_size_options
      : DEFAULT_OPERATION_LOG_META.page_size_options
  );
  const operationLogKnownMaxPage = computed(() => {
    const knownPages = Object.keys(operationLogPageCursorMap.value || {})
      .map((item) => Number(item))
      .filter((item) => Number.isFinite(item) && item > 0);
    return knownPages.length ? Math.max(...knownPages) : 1;
  });
  const operationLogPageItems = computed(() => {
    const maxPage = Math.max(operationLogKnownMaxPage.value, 1);
    const current = Math.max(Number(operationLogPagination.page || 1), 1);
    if (maxPage <= 7) {
      return Array.from({ length: maxPage }, (_, index) => ({
        type: "page",
        value: index + 1,
        key: `page-${index + 1}`,
      }));
    }

    const pageSet = new Set([1, maxPage, current - 1, current, current + 1]);
    if (current <= 3) [2, 3, 4].forEach((page) => pageSet.add(page));
    if (current >= maxPage - 2) {
      [maxPage - 1, maxPage - 2, maxPage - 3].forEach((page) => pageSet.add(page));
    }
    const sortedPages = Array.from(pageSet)
      .filter((page) => page >= 1 && page <= maxPage)
      .sort((a, b) => a - b);

    const items = [];
    sortedPages.forEach((page, index) => {
      const previousPage = sortedPages[index - 1];
      if (index > 0 && page - previousPage > 1) {
        items.push({
          type: "ellipsis",
          key: `ellipsis-${previousPage}-${page}`,
        });
      }
      items.push({
        type: "page",
        value: page,
        key: `page-${page}`,
      });
    });
    return items;
  });

  const { jobCategories, filteredItems: filteredApplications } = useJobCategoryFilter(
    applications,
    applicationFilters,
    {
      titleKey: "job_title",
      regionKey: "region_name",
      jobFilterKey: "job",
      regionFilterKey: "region",
      allValue: "all",
      allLabel: "全部岗位",
      unknownJobLabel: "未填写岗位",
    }
  );

  const groupedApplications = computed(() => {
    const groups = new Map();
    filteredApplications.value.forEach((item) => {
      const title = item.job_title || "未填写岗位";
      if (!groups.has(title)) groups.set(title, []);
      groups.get(title).push(item);
    });
    return Array.from(groups.entries())
      .map(([title, items]) => ({ title, items }))
      .sort((a, b) => a.title.localeCompare(b.title, "zh-Hans-CN"));
  });

  const { jobCategories: interviewJobCategories, filteredItems: filteredInterviewCandidates } =
    useJobCategoryFilter(interviewCandidates, interviewFilters, {
      titleKey: "job_title",
      regionKey: "region_name",
      jobFilterKey: "job",
      regionFilterKey: "region",
      keywordFilterKey: "keyword",
      keywordFields: ["name", "phone"],
      allValue: "all",
      allLabel: "全部岗位",
      unknownJobLabel: "未填写岗位",
    });

  const sortedInterviewCandidates = computed(() => {
    const list = [...filteredInterviewCandidates.value];
    if (interviewTimeSort.value === "none") return list;

    const getTimestamp = (value) => {
      if (!value) return null;
      const time = new Date(value).getTime();
      return Number.isNaN(time) ? null : time;
    };

    list.sort((a, b) => {
      const aTime = getTimestamp(a.interview_at);
      const bTime = getTimestamp(b.interview_at);
      if (aTime === null && bTime === null) return 0;
      if (aTime === null) return 1;
      if (bTime === null) return -1;
      return interviewTimeSort.value === "asc" ? aTime - bTime : bTime - aTime;
    });
    return list;
  });

  const { filteredItems: passedCandidatesByHireStatus, statusOptions: passedStatusOptions } =
    useHireStatusFilter(passedCandidates, passedFilters, {
      filterKey: "hire_status",
      allValue: "all",
      pendingValue: "pending_hire",
      confirmedValue: "confirmed_hire",
      allLabel: "全部状态",
      pendingLabel: "待确认入职",
      confirmedLabel: "已确认入职",
      statusLabelMap: {
        offer_rejected: "拒绝offer",
      },
      resolveStatus: (item) => resolveOfferStatus(item),
    });

  const { jobCategories: passedJobCategories, filteredItems: filteredPassedCandidates } =
    useJobCategoryFilter(passedCandidatesByHireStatus, passedFilters, {
      titleKey: "job_title",
      regionKey: "region_name",
      jobFilterKey: "job",
      allValue: "all",
      allLabel: "全部岗位",
      unknownJobLabel: "未填写岗位",
    });

  const { jobCategories: talentJobCategories, filteredItems: filteredTalentCandidates } =
    useJobCategoryFilter(talentPoolCandidates, talentFilters, {
      titleKey: "job_title",
      regionKey: "region_name",
      jobFilterKey: "job",
      allValue: "all",
      allLabel: "全部岗位",
      unknownJobLabel: "未填写岗位",
    });

  const selectedApplicationsCount = computed(() => selectedApplicationIds.value.length);
  const { selectedCount: selectedJobsCount, isAllVisibleSelected: isAllJobsSelected } =
    useSelectionState(selectedJobIds, filteredJobs);
  const {
    selectedCount: selectedInterviewCount,
    isAllVisibleSelected: isAllVisibleInterviewsSelected,
  } = useSelectionState(selectedInterviewIds, filteredInterviewCandidates);
  const { isAllVisibleSelected: isAllVisiblePassedSelected } =
    useSelectionState(selectedPassedIds, filteredPassedCandidates);
  const {
    selectedCount: selectedTalentCount,
    isAllVisibleSelected: isAllVisibleTalentSelected,
  } = useSelectionState(selectedTalentIds, filteredTalentCandidates);

  return {
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
  };
};
