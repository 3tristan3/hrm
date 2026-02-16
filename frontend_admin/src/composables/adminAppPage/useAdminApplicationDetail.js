import { computed } from "vue";
import {
  attachmentPreviewTag,
  displayValue,
  formatDate,
  formatStructuredList,
  isImageFile,
} from "../../utils/detailFormatters";

export const useAdminApplicationDetail = ({
  activeApplication,
  applicationDetailLoading,
  applicationOperationLogs,
  applicationLogsLoading,
  resolveMediaUrl,
  request,
  adminBase,
  loadApplicationOperationLogs,
  notifyError,
}) => {
  const openApplicationFromInterview = async (item) => {
    await openApplication({
      id: item.application_id,
      name: item.name,
      job_title: item.job_title,
      region_name: item.region_name,
      photo_url: item.photo_url,
    });
  };

  const openApplicationFromOutcome = async (item) => {
    await openApplication({
      id: item.application_id,
      name: item.name,
      job_title: item.job_title,
      region_name: item.region_name,
    });
  };

  const openApplication = async (item) => {
    applicationDetailLoading.value = true;
    applicationOperationLogs.value = [];
    applicationLogsLoading.value = true;
    activeApplication.value = { ...item };
    try {
      const [detail] = await Promise.all([
        request(`${adminBase}/applications/${item.id}/`),
        loadApplicationOperationLogs(item.id),
      ]);
      activeApplication.value = detail;
    } catch (err) {
      notifyError(err);
      activeApplication.value = null;
      applicationOperationLogs.value = [];
      applicationLogsLoading.value = false;
    } finally {
      applicationDetailLoading.value = false;
    }
  };

  const closeApplication = () => {
    activeApplication.value = null;
    applicationDetailLoading.value = false;
    applicationOperationLogs.value = [];
    applicationLogsLoading.value = false;
  };

  const attachmentCardMeta = Object.freeze([
    { key: "id_front", label: "身份证正面", hint: "核对身份信息" },
    { key: "id_back", label: "身份证反面", hint: "核对有效期限" },
    { key: "resume", label: "个人简历", hint: "查看完整履历" },
  ]);

  const applicationAttachments = computed(() => {
    const attachments = activeApplication.value?.attachments;
    return Array.isArray(attachments) ? attachments : [];
  });

  const keyAttachmentCards = computed(() => {
    const firstByCategory = new Map();
    applicationAttachments.value.forEach((item) => {
      if (!item?.category || firstByCategory.has(item.category)) return;
      firstByCategory.set(item.category, item);
    });
    return attachmentCardMeta.map((meta) => {
      const file = firstByCategory.get(meta.key);
      const url = file?.file_url || "";
      const fileName = file?.file_name || "";
      const isImage = isImageFile(fileName || url);
      return {
        ...meta,
        url,
        fileName,
        isImage,
        previewTag: url ? attachmentPreviewTag(fileName || url, isImage) : "无",
      };
    });
  });

  const otherAttachmentFiles = computed(() => {
    const keySet = new Set(attachmentCardMeta.map((item) => item.key));
    return applicationAttachments.value.filter(
      (item) => item?.category && !keySet.has(item.category)
    );
  });

  const openAttachment = (rawUrl) => {
    if (!rawUrl || typeof window === "undefined") return;
    const url = resolveMediaUrl(rawUrl);
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const detailSections = computed(() => {
    if (!activeApplication.value) return [];
    const app = activeApplication.value;
    return [
      {
        title: "基础信息",
        items: [
          { label: "姓名", value: displayValue(app.name) },
          { label: "性别", value: displayValue(app.gender) },
          { label: "年龄", value: displayValue(app.age) },
          { label: "手机号", value: displayValue(app.phone) },
          { label: "邮箱", value: displayValue(app.email) },
          { label: "微信号", value: displayValue(app.wechat) },
          { label: "招聘类型", value: displayValue(app.recruit_type) },
        ],
      },
      {
        title: "应聘信息",
        items: [
          { label: "应聘岗位", value: displayValue(app.job_title) },
          { label: "所属地区", value: displayValue(app.region_name) },
          { label: "应聘区域", value: displayValue(app.apply_region) },
          { label: "应聘公司", value: displayValue(app.apply_company) },
          { label: "期望薪资", value: displayValue(app.expected_salary) },
          { label: "可到岗日期", value: formatDate(app.available_date) },
        ],
      },
      {
        title: "推荐信息",
        items: [
          { label: "招聘来源", value: displayValue(app.recruitment_source) },
          { label: "介绍人姓名", value: displayValue(app.referrer_name) },
          { label: "介绍人关系", value: displayValue(app.referrer_relation) },
          { label: "介绍人单位", value: displayValue(app.referrer_company) },
        ],
      },
      {
        title: "个人情况",
        items: [
          { label: "婚姻情况", value: displayValue(app.marital_status) },
          { label: "出生年月", value: formatDate(app.birth_month) },
          { label: "身高(cm)", value: displayValue(app.height_cm) },
          { label: "体重(kg)", value: displayValue(app.weight_kg) },
          { label: "健康情况", value: displayValue(app.health_status) },
          { label: "民族", value: displayValue(app.ethnicity) },
        ],
      },
      {
        title: "教育信息",
        items: [
          { label: "最高学历", value: displayValue(app.education_level) },
          { label: "起止时间", value: displayValue(app.education_period) },
          { label: "毕业院校", value: displayValue(app.graduate_school) },
          { label: "专业", value: displayValue(app.major) },
          { label: "毕业时间", value: formatDate(app.graduation_date) },
          { label: "职称证书", value: displayValue(app.title_cert) },
          { label: "毕业证编号", value: displayValue(app.diploma_number) },
        ],
      },
      {
        title: "户籍与身份",
        items: [
          { label: "政治面貌", value: displayValue(app.political_status) },
          { label: "户口性质", value: displayValue(app.hukou_type) },
          { label: "籍贯", value: displayValue(app.native_place) },
          { label: "户口所在地", value: displayValue(app.hukou_address) },
          { label: "现住地址", value: displayValue(app.current_address) },
          { label: "身份证号", value: displayValue(app.id_number) },
          { label: "QQ", value: displayValue(app.qq) },
        ],
      },
      {
        title: "紧急联系人",
        items: [
          { label: "联系人姓名", value: displayValue(app.emergency_name) },
          { label: "联系人手机号", value: displayValue(app.emergency_phone) },
          { label: "兴趣爱好", value: displayValue(app.hobbies) },
          { label: "自我评价", value: displayValue(app.self_evaluation) },
        ],
      },
      {
        title: "教育/培训经历",
        blocks: [
          {
            label: "记录",
            value: formatStructuredList(app.education_history, [
              { key: "school", label: "院校" },
              { key: "major", label: "专业" },
              { key: "degree", label: "学历" },
              { key: "start", label: "开始时间" },
              { key: "end", label: "结束时间" },
            ]),
          },
        ],
      },
      {
        title: "工作经历",
        blocks: [
          {
            label: "记录",
            value: formatStructuredList(app.work_history, [
              { key: "company", label: "公司" },
              { key: "position", label: "岗位" },
              { key: "start", label: "开始时间" },
              { key: "end", label: "结束时间" },
            ]),
          },
        ],
      },
      {
        title: "家庭成员",
        blocks: [
          {
            label: "记录",
            value: formatStructuredList(app.family_members, [
              { key: "name", label: "姓名" },
              { key: "relation", label: "关系" },
              { key: "age", label: "年龄" },
              { key: "company", label: "单位" },
              { key: "position", label: "岗位" },
              { key: "phone", label: "手机号" },
            ]),
          },
        ],
      },
    ];
  });

  return {
    openApplicationFromInterview,
    openApplicationFromOutcome,
    openApplication,
    closeApplication,
    attachmentCardMeta,
    applicationAttachments,
    keyAttachmentCards,
    otherAttachmentFiles,
    openAttachment,
    detailSections,
  };
};
