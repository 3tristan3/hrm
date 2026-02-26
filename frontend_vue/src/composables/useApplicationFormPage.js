// 应聘端主页面逻辑：管理报名状态、字段校验、提交与附件上传。
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import {
  ATTACHMENT_MAX_FILE_MB,
  ATTACHMENT_MAX_TOTAL_MB,
  PREWARM_JOBS,
  PREWARM_REGION_LIMIT,
  buildApiUrl,
} from "../config/runtime";
import { createApplicationDataLoaders } from "./applicationFormPage/useApplicationDataLoaders";
import { createApplicationSubmitter } from "./applicationFormPage/useApplicationSubmitter";
import { createApplicationValidator } from "./applicationFormPage/useApplicationValidation";
import { validateAttachmentFiles } from "../utils/attachmentGuards";
import { scrollToFirstError } from "../utils/formErrorFocus";

export const useApplicationFormPage = () => {
  const regions = ref([]);
  const jobs = ref([]);
  const selectedRegionId = ref("");
  const selectedJobId = ref("");

  const form = reactive({
    recruit_type: "",
    apply_region: "",
    available_date: "",
    referrer_name: "",
    referrer_relation: "",
    referrer_company: "",
    name: "",
    age: "",
    gender: "",
    marital_status: "",
    birth_month: "",
    height_cm: "",
    weight_kg: "",
    health_status: "",
    hukou_type: "",
    hukou_address: "",
    current_address: "",
    native_place: "",
    political_status: "",
    ethnicity: "",
    graduate_school: "",
    graduation_date: "",
    major: "",
    diploma_number: "",
    title_cert: "",
    education_level: "",
    education_start: "",
    education_end: "",
    id_number: "",
    phone: "",
    qq: "",
    wechat: "",
    email: "",
    emergency_name: "",
    emergency_phone: "",
    hobbies: "",
    self_evaluation: "",
  });

  const educationRows = ref([]);
  const workRows = ref([]);
  const familyRows = ref([]);
  const extraFields = reactive({});

  const attachments = reactive({
    photo: null,
    id_front: null,
    id_back: null,
    resume: null,
    other: [],
  });

  const fileInputKey = ref(0);

  const errors = reactive({});

  const submitting = ref(false);
  const submitted = ref(false);
  const errorMessage = ref("");
  const applicationId = ref("");
  const attachmentToken = ref("");
  const formRef = ref(null);

  const modal = reactive({
    visible: false,
    title: "",
    message: "",
  });

  const submitUrl = buildApiUrl("api/applications/");
  const regionUrl = buildApiUrl("api/regions/");
  const jobUrl = buildApiUrl("api/jobs/");
  const REGIONS_CACHE_KEY = "hrm_regions_cache";
  const JOBS_CACHE_PREFIX = "hrm_jobs_cache_";
  const CACHE_TTL_MS = 5 * 60 * 1000;

  const selectedRegion = computed(() =>
    regions.value.find((item) => String(item.id) === String(selectedRegionId.value))
  );

  const regionFields = computed(() => selectedRegion.value?.region_fields || []);

  const jobDetail = computed(() =>
    jobs.value.find((item) => String(item.id) === String(selectedJobId.value))
  );

  const clearErrors = () => {
    Object.keys(errors).forEach((key) => delete errors[key]);
  };

  const { fetchRegions, fetchJobs } = createApplicationDataLoaders({
    regions,
    jobs,
    errorMessage,
    regionUrl,
    jobUrl,
    REGIONS_CACHE_KEY,
    JOBS_CACHE_PREFIX,
    CACHE_TTL_MS,
    PREWARM_JOBS,
    PREWARM_REGION_LIMIT,
  });

  const addEducationRow = () => {
    educationRows.value.push({
      school: "",
      major: "",
      degree: "",
      start: "",
      end: "",
    });
  };

  const removeEducationRow = (index) => {
    educationRows.value.splice(index, 1);
  };

  const addWorkRow = () => {
    workRows.value.push({
      company: "",
      position: "",
      start: "",
      end: "",
    });
  };

  const removeWorkRow = (index) => {
    workRows.value.splice(index, 1);
  };

  const addFamilyRow = () => {
    familyRows.value.push({
      name: "",
      relation: "",
      age: "",
      company: "",
      position: "",
      phone: "",
    });
  };

  const removeFamilyRow = (index) => {
    familyRows.value.splice(index, 1);
  };

  const inputType = (type) => {
    if (type === "number") return "number";
    if (type === "date") return "date";
    return "text";
  };

  const resetExtraFields = () => {
    Object.keys(extraFields).forEach((key) => delete extraFields[key]);
    regionFields.value.forEach((field) => {
      extraFields[field.key] = "";
    });
  };

  const onFileChange = (type, event) => {
    const files = Array.from(event.target.files || []);
    const incomingFiles = type === "other" ? files : files.slice(0, 1);
    const validation = validateAttachmentFiles({
      attachments,
      type,
      incomingFiles,
      maxFileMb: ATTACHMENT_MAX_FILE_MB,
      maxTotalMb: ATTACHMENT_MAX_TOTAL_MB,
    });
    if (!validation.ok) {
      errors[type] = validation.error;
      errorMessage.value = `上传失败：${validation.error}`;
      if (event?.target) event.target.value = "";
      return;
    }

    delete errors[type];
    if (errorMessage.value.startsWith("上传失败：")) {
      errorMessage.value = "";
    }

    if (type === "other") {
      attachments.other = files;
      return;
    }
    attachments[type] = files[0] || null;
  };

  const { validate } = createApplicationValidator({
    form,
    errors,
    clearErrors,
    selectedRegionId,
    selectedJobId,
    regionFields,
    extraFields,
    educationRows,
    workRows,
    familyRows,
    attachments,
    errorMessage,
  });

  const resetForm = () => {
    Object.keys(form).forEach((key) => (form[key] = ""));
    selectedRegionId.value = "";
    selectedJobId.value = "";
    jobs.value = [];
    educationRows.value = [];
    workRows.value = [];
    familyRows.value = [];
    resetExtraFields();
    Object.keys(attachments).forEach((key) => {
      if (key === "other") {
        attachments.other = [];
      } else {
        attachments[key] = null;
      }
    });
    fileInputKey.value += 1;
    clearErrors();
    errorMessage.value = "";
    submitted.value = false;
    applicationId.value = "";
    attachmentToken.value = "";
  };

  const openModal = (title, message) => {
    modal.title = title;
    modal.message = message;
    modal.visible = true;
  };

  const closeModal = () => {
    modal.visible = false;
  };

  const { submitForm } = createApplicationSubmitter({
    submitUrl,
    submitting,
    submitted,
    errorMessage,
    validate,
    nextTick,
    formRef,
    errors,
    selectedRegionId,
    selectedJobId,
    form,
    educationRows,
    workRows,
    familyRows,
    extraFields,
    attachments,
    applicationId,
    attachmentToken,
    openModal,
    scrollToFirstError,
  });

  onMounted(() => {
    fetchRegions();
  });

  watch(
    () => selectedRegionId.value,
    (value) => {
      jobs.value = [];
      selectedJobId.value = "";
      form.apply_region = selectedRegion.value?.name || "";
      resetExtraFields();
      if (value) {
        fetchJobs(value);
      }
    }
  );

  return {
    ATTACHMENT_MAX_FILE_MB,
    ATTACHMENT_MAX_TOTAL_MB,
    regions,
    jobs,
    selectedRegionId,
    selectedJobId,
    form,
    educationRows,
    workRows,
    familyRows,
    extraFields,
    attachments,
    fileInputKey,
    errors,
    submitting,
    submitted,
    errorMessage,
    formRef,
    modal,
    regionFields,
    jobDetail,
    addEducationRow,
    removeEducationRow,
    addWorkRow,
    removeWorkRow,
    addFamilyRow,
    removeFamilyRow,
    inputType,
    onFileChange,
    resetForm,
    closeModal,
    submitForm,
  };
};
