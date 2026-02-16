// 应聘端主页面逻辑：管理报名状态、字段校验、提交与附件上传。
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import {
  ATTACHMENT_MAX_FILE_MB,
  ATTACHMENT_MAX_TOTAL_MB,
  PREWARM_JOBS,
  PREWARM_REGION_LIMIT,
  buildApiUrl,
} from "../config/runtime";
import { validateAttachmentFiles } from "../utils/attachmentGuards";
import { scrollToFirstError } from "../utils/formErrorFocus";
import { buildExtraFieldsPayload, buildRowPayload } from "../utils/formPayload";

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
  const jobsRequestMap = new Map();

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

  const canUseSessionStorage = () => typeof window !== "undefined" && !!window.sessionStorage;

  const readCache = (key) => {
    if (!canUseSessionStorage()) return null;
    try {
      const raw = window.sessionStorage.getItem(key);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || !parsed.timestamp || !("data" in parsed)) return null;
      if (Date.now() - parsed.timestamp > CACHE_TTL_MS) return null;
      return parsed.data;
    } catch {
      return null;
    }
  };

  const writeCache = (key, data) => {
    if (!canUseSessionStorage()) return;
    try {
      window.sessionStorage.setItem(
        key,
        JSON.stringify({
          timestamp: Date.now(),
          data,
        })
      );
    } catch {
      // Ignore cache write failures (e.g. private mode / quota)
    }
  };

  const fetchJobsByRegion = async (regionId, { silent = false } = {}) => {
    if (!regionId) return [];
    if (jobsRequestMap.has(regionId)) {
      return jobsRequestMap.get(regionId);
    }

    const request = (async () => {
      try {
        const response = await fetch(`${jobUrl}?region_id=${regionId}`);
        if (!response.ok) return [];
        const data = await response.json();
        writeCache(`${JOBS_CACHE_PREFIX}${regionId}`, data);
        return data;
      } catch (err) {
        if (!silent) throw err;
        return [];
      } finally {
        jobsRequestMap.delete(regionId);
      }
    })();

    jobsRequestMap.set(regionId, request);
    return request;
  };

  const prewarmJobs = async () => {
    if (!PREWARM_JOBS || !regions.value.length) return;
    const regionIds = regions.value
      .map((item) => Number(item.id))
      .filter((id) => Number.isInteger(id) && id > 0)
      .slice(0, PREWARM_REGION_LIMIT);
    if (!regionIds.length) return;

    await Promise.allSettled(
      regionIds.map(async (regionId) => {
        const cacheKey = `${JOBS_CACHE_PREFIX}${regionId}`;
        if (Array.isArray(readCache(cacheKey))) return;
        await fetchJobsByRegion(regionId, { silent: true });
      })
    );
  };

  const fetchRegions = async () => {
    const cachedRegions = readCache(REGIONS_CACHE_KEY);
    if (Array.isArray(cachedRegions)) {
      regions.value = cachedRegions;
      void prewarmJobs();
      return;
    }
    try {
      const response = await fetch(regionUrl);
      if (!response.ok) return;
      const data = await response.json();
      regions.value = data;
      writeCache(REGIONS_CACHE_KEY, data);
      void prewarmJobs();
    } catch (err) {
      errorMessage.value = "无法加载地区配置，请检查后端接口";
    }
  };

  const fetchJobs = async (regionId) => {
    if (!regionId) return;
    const cacheKey = `${JOBS_CACHE_PREFIX}${regionId}`;
    const cachedJobs = readCache(cacheKey);
    if (Array.isArray(cachedJobs)) {
      jobs.value = cachedJobs;
      return;
    }
    try {
      jobs.value = await fetchJobsByRegion(regionId);
    } catch (err) {
      errorMessage.value = "无法加载岗位列表，请检查后端接口";
    }
  };

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

  const validate = () => {
    clearErrors();
    errorMessage.value = "";

    if (!form.recruit_type) errors.recruit_type = "请选择招聘类型";
    if (!selectedRegionId.value) errors.region_id = "请选择应聘区域";
    if (!selectedJobId.value) errors.job_id = "请选择岗位";
    if (!form.name) errors.name = "请填写姓名";
    if (!form.age) errors.age = "请填写年龄";
    if (!form.gender) errors.gender = "请选择性别";
    if (!form.phone) errors.phone = "请填写手机号";
    if (!form.qq) errors.qq = "请填写QQ号";
    if (!form.wechat) errors.wechat = "请填写微信号";
    if (!form.email) errors.email = "请填写邮箱";
    if (!form.marital_status) errors.marital_status = "请选择婚姻情况";
    if (!form.height_cm) errors.height_cm = "请填写身高";
    if (!form.weight_kg) errors.weight_kg = "请填写体重";
    if (!form.education_level) errors.education_level = "请选择学历";
    if (!form.education_start || !form.education_end) {
      errors.education_period = "请填写最高学历入学与毕业时间";
    } else if (form.education_start > form.education_end) {
      errors.education_period = "最高学历入学时间需早于毕业时间";
    }
    if (!form.political_status) errors.political_status = "请选择政治面貌";
    if (!form.ethnicity) errors.ethnicity = "请填写民族";
    if (!form.id_number) errors.id_number = "请填写身份证号";

    regionFields.value.forEach((field) => {
      if (!field.required) return;
      const value = extraFields[field.key];
      if (value === undefined || value === null || String(value).trim() === "") {
        errors[field.key] = `请填写${field.label}`;
      }
    });

    const educationRequiredFields = ["school", "major", "degree", "start", "end"];
    const workRequiredFields = ["company", "position", "start", "end"];
    const familyRequiredFields = ["name", "relation", "age", "company", "position", "phone"];
    const isRowComplete = (row, fields) =>
      fields.every((field) => {
        const value = row[field];
        if (field === "age") return value !== "" && value !== null && value !== undefined;
        return String(value ?? "").trim() !== "";
      });

    if (educationRows.value.length < 1) {
      errors.education_history = "请至少填写一条教育/培训经历";
    } else if (educationRows.value.some((row) => !isRowComplete(row, educationRequiredFields))) {
      errors.education_history = "教育/培训经历每一条内容均为必填";
    }

    if (familyRows.value.length < 2) {
      errors.family_members = "请至少填写两位家庭成员";
    } else if (familyRows.value.some((row) => !isRowComplete(row, familyRequiredFields))) {
      errors.family_members = "家庭成员信息每一条内容均为必填";
    }

    if (workRows.value.length < 1) {
      errors.work_history = "请至少填写一条工作经历";
    } else if (workRows.value.some((row) => !isRowComplete(row, workRequiredFields))) {
      errors.work_history = "工作经历每一条内容均为必填";
    }

    if (form.phone && !/^\d{11}$/.test(form.phone)) errors.phone = "手机号格式不正确";
    if (form.email && !/^\S+@\S+\.\S+$/.test(form.email)) errors.email = "邮箱格式不正确";
    if (form.id_number && form.id_number.length !== 18) errors.id_number = "身份证号需为18位";

    if (!attachments.photo) errors.photo = "请上传个人照片";
    if (!attachments.id_front) errors.id_front = "请上传身份证正面";
    if (!attachments.id_back) errors.id_back = "请上传身份证反面";
    if (!attachments.resume) errors.resume = "请上传个人简历";

    return Object.keys(errors).length === 0;
  };

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

  const uploadAttachment = async (appId, token, category, files) => {
    if (!files || (Array.isArray(files) && files.length === 0)) return;
    const formData = new FormData();
    formData.append("category", category);
    if (Array.isArray(files)) {
      files.forEach((file) => formData.append("file", file));
    } else {
      formData.append("file", files);
    }
    const response = await fetch(`${submitUrl}${appId}/attachments/`, {
      method: "POST",
      headers: {
        "X-Application-Token": token,
      },
      body: formData,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || "附件上传失败");
    }
  };

  const discardDraftApplication = async (appId, token) => {
    if (!appId || !token) return false;
    const response = await fetch(`${submitUrl}${appId}/discard/`, {
      method: "POST",
      headers: {
        "X-Application-Token": token,
      },
    });
    return response.ok;
  };

  const submitForm = async () => {
    if (submitting.value) return;
    if (submitted.value) {
      errorMessage.value = "已提交，请勿重复提交。如需重新提交请点击重置。";
      return;
    }

    if (!validate()) {
      errorMessage.value = "请先完成必填项，并修正标红错误字段。";
      await scrollToFirstError({ nextTick, formRef, errors });
      return;
    }

    const regionId = Number(selectedRegionId.value || 0);
    if (!regionId) return;

    submitting.value = true;
    errorMessage.value = "";
    try {
      const payload = {
        region_id: regionId,
        job_id: Number(selectedJobId.value),
        recruit_type: form.recruit_type,
        apply_region: form.apply_region.trim(),
        available_date: form.available_date || null,
        referrer_name: form.referrer_name.trim(),
        referrer_relation: form.referrer_relation.trim(),
        referrer_company: form.referrer_company.trim(),
        name: form.name.trim(),
        age: Number(form.age),
        gender: form.gender,
        marital_status: form.marital_status,
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        birth_month: form.birth_month || null,
        health_status: form.health_status.trim(),
        hukou_type: form.hukou_type,
        hukou_address: form.hukou_address.trim(),
        current_address: form.current_address.trim(),
        native_place: form.native_place.trim(),
        political_status: form.political_status,
        ethnicity: form.ethnicity.trim(),
        graduate_school: form.graduate_school.trim(),
        graduation_date: form.graduation_date || null,
        major: form.major.trim(),
        diploma_number: form.diploma_number.trim(),
        title_cert: form.title_cert.trim(),
        education_level: form.education_level,
        education_period: `${form.education_start}-${form.education_end}`,
        id_number: form.id_number.trim(),
        phone: form.phone.trim(),
        qq: form.qq.trim(),
        wechat: form.wechat.trim(),
        email: form.email.trim(),
        emergency_name: form.emergency_name.trim(),
        emergency_phone: form.emergency_phone.trim(),
        hobbies: form.hobbies.trim(),
        self_evaluation: form.self_evaluation.trim(),
        education_history: buildRowPayload(educationRows.value, [
          "school",
          "major",
          "degree",
          "start",
          "end",
        ]),
        work_history: buildRowPayload(workRows.value, [
          "company",
          "position",
          "start",
          "end",
        ]),
        family_members: buildRowPayload(familyRows.value, [
          "name",
          "relation",
          "age",
          "company",
          "position",
          "phone",
        ]),
        extra_fields: buildExtraFieldsPayload(extraFields),
      };

      const response = await fetch(submitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        if (body.details && typeof body.details === "object") {
          Object.entries(body.details).forEach(([field, messages]) => {
            const text = Array.isArray(messages) ? messages.join("，") : String(messages);
            errors[field] = text;
          });
        }
        errorMessage.value = body.error || "提交失败，请检查填写内容";
        await scrollToFirstError({ nextTick, formRef, errors });
        return;
      }

      applicationId.value = body.applicationId || "";
      attachmentToken.value = body.attachmentToken || "";
      if (!applicationId.value || !attachmentToken.value) {
        throw new Error("提交失败：未获取到附件凭证，请稍后重试");
      }

      try {
        await uploadAttachment(applicationId.value, attachmentToken.value, "photo", attachments.photo);
        await uploadAttachment(applicationId.value, attachmentToken.value, "id_front", attachments.id_front);
        await uploadAttachment(applicationId.value, attachmentToken.value, "id_back", attachments.id_back);
        await uploadAttachment(applicationId.value, attachmentToken.value, "resume", attachments.resume);
        await uploadAttachment(applicationId.value, attachmentToken.value, "other", attachments.other);
        submitted.value = true;
        openModal("提交成功", "您的信息已提交完成，我们会尽快联系您。");
      } catch (uploadErr) {
        const rollbackOk = await discardDraftApplication(applicationId.value, attachmentToken.value).catch(
          () => false
        );
        submitted.value = false;
        applicationId.value = "";
        attachmentToken.value = "";
        if (rollbackOk) {
          errorMessage.value = uploadErr?.message || "附件上传失败，已自动回滚，请重新提交";
          openModal("提交失败", "附件上传失败，本次提交已自动回滚，请检查后重试。");
        } else {
          errorMessage.value = uploadErr?.message || "附件上传失败，请联系管理员处理";
          openModal("提交异常", "附件上传失败，且自动回滚未完成，请联系管理员处理。");
        }
      }
    } catch (err) {
      errorMessage.value = err?.message || "无法连接后端服务，请确认接口地址";
    } finally {
      submitting.value = false;
    }
  };

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
