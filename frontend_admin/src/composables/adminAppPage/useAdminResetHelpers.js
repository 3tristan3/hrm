import { DEFAULT_OPERATION_LOG_META } from "../../constants/operationLog";

export function createAdminResetHelpers({
  jobFilters,
  applicationFilters,
  interviewFilters,
  interviewTimeSort,
  passedFilters,
  talentFilters,
  operationLogFilters,
  operationLogMeta,
  operationLogsQueried,
  interviewScheduleForm,
  interviewResultForm,
  interviewMeta,
}) {
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

  const toggleInterviewTimeSort = () => {
    interviewTimeSort.value = interviewTimeSort.value === "asc" ? "desc" : "asc";
  };

  function resetInterviewScheduleForm() {
    Object.assign(interviewScheduleForm, {
      id: null,
      name: "",
      phone: "",
      job_title: "",
      interview_round: 1,
      interview_at: "",
      interviewer: "",
      interviewers: [""],
      interview_location: "",
      note: "",
      send_sms: false,
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
      interviewer_scores: [{ interviewer: "", score: null }],
      result_note: "",
    });
  }

  return {
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
  };
}
