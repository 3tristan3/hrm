import { buildExtraFieldsPayload, buildRowPayload } from "../../utils/formPayload";

export const createApplicationSubmitter = ({
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
}) => {
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
        work_history: buildRowPayload(workRows.value, ["company", "position", "start", "end"]),
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

  return {
    submitForm,
  };
};
