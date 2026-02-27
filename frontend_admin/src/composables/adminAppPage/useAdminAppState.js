import { reactive, ref } from "vue";
import { createInterviewMeta, defaultInterviewMeta } from "../../utils/interviewMeta";
import { createPageState, LIST_PAGE_SIZE_OPTIONS } from "../../utils/pagination";
import {
  DEFAULT_OPERATION_LOG_META,
  normalizeOperationLogMeta,
} from "../../constants/operationLog";

export function createAdminAppState() {
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
  const jobForm = reactive({
    id: null,
    region: "",
    title: "",
    description: "",
    salary: "",
    education: "",
    order: 0,
    is_active: true,
  });
  const regionForm = reactive({ name: "", code: "", order: 0, is_active: true });
  const showRegionCreateModal = ref(false);
  const showRegionDeleteModal = ref(false);
  const regionDeleteSubmitting = ref(false);
  const regionDeletePassword = ref("");
  const pendingDeleteRegion = ref(null);
  const passwordForm = reactive({ user_id: "", password: "" });
  const selfPasswordForm = reactive({
    old_password: "",
    new_password: "",
    confirm_password: "",
  });
  const showResetPasswordModal = ref(false);
  const showSelfPasswordModal = ref(false);
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
  const interviewResultForm = reactive({
    id: null,
    name: "",
    interview_round: 1,
    status: "",
    result: defaultInterviewMeta.result_next_round,
    score: null,
    interviewer_scores: [{ interviewer: "", score: null }],
    result_note: "",
  });

  const publicRegions = ref([]);
  const regions = ref([]);
  const jobs = ref([]);
  const applications = ref([]);
  const interviewCandidates = ref([]);
  const interviewPagination = reactive(createPageState());
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
  const userProfile = reactive({
    can_view_all: false,
    region_name: "",
    region_id: null,
    is_superuser: false,
  });
  const activeApplication = ref(null);
  const applicationDetailLoading = ref(false);
  const applicationOperationLogs = ref([]);
  const applicationLogsLoading = ref(false);
  const operationLogsQueried = ref(false);
  const operationLogMeta = reactive({
    ...normalizeOperationLogMeta(DEFAULT_OPERATION_LOG_META),
    loaded: false,
  });
  const listPageSizeOptions = LIST_PAGE_SIZE_OPTIONS;
  const dataLoaded = reactive({
    regions: false,
    jobs: false,
    applications: false,
    interviews: false,
    passed: false,
    talent: false,
    operationLogs: false,
    interviewMeta: false,
    users: false,
  });
  const dataLoading = reactive({
    regions: false,
    jobs: false,
    applications: false,
    interviews: false,
    passed: false,
    talent: false,
    operationLogs: false,
    interviewMeta: false,
    users: false,
  });

  return {
    token,
    currentUsername,
    authMode,
    activeTab,
    tabs,
    authForm,
    jobForm,
    regionForm,
    showRegionCreateModal,
    showRegionDeleteModal,
    regionDeleteSubmitting,
    regionDeletePassword,
    pendingDeleteRegion,
    passwordForm,
    selfPasswordForm,
    showResetPasswordModal,
    showSelfPasswordModal,
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
    interviewPagination,
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
    listPageSizeOptions,
    dataLoaded,
    dataLoading,
  };
}
