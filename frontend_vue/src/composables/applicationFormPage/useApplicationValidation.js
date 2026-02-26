export const createApplicationValidator = ({
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
}) => {
  const educationRequiredFields = ["school", "major", "degree", "start", "end"];
  const workRequiredFields = ["company", "position", "start", "end"];
  const familyRequiredFields = ["name", "relation", "age", "company", "position", "phone"];

  const isRowComplete = (row, fields) =>
    fields.every((field) => {
      const value = row[field];
      if (field === "age") return value !== "" && value !== null && value !== undefined;
      return String(value ?? "").trim() !== "";
    });

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

  return {
    validate,
  };
};
