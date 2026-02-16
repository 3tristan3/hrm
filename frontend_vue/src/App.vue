<template>
  <!-- 文件说明：应聘端主页面，承载报名流程入口与表单容器。 -->
  <div class="page">
    <FormHeader :submitting="submitting" :submitted="submitted" />

    <main class="form-shell">
      <form ref="formRef" class="form" @submit.prevent="submitForm">
        <ApplyInfoSection
          :regions="regions"
          :jobs="jobs"
          :selected-region-id="selectedRegionId"
          :selected-job-id="selectedJobId"
          :job-detail="jobDetail"
          :errors="errors"
          :form="form"
          @update:selectedRegionId="(val) => (selectedRegionId = val)"
          @update:selectedJobId="(val) => (selectedJobId = val)"
        />

        <BasicInfoSection
          :form="form"
          :errors="errors"
          :attachments="attachments"
          :file-input-key="fileInputKey"
          @file-change="onFileChange"
        />
        <ProfileSection :form="form" />
        <EducationHistorySection :rows="educationRows" :errors="errors" @add="addEducationRow" @remove="removeEducationRow" />
        <ContactSection :form="form" :errors="errors" />
        <EmergencySection :form="form" />
        <WorkHistorySection :rows="workRows" :errors="errors" @add="addWorkRow" @remove="removeWorkRow" />
        <FamilySection :rows="familyRows" :errors="errors" @add="addFamilyRow" @remove="removeFamilyRow" />
        <HobbySection :form="form" />
        <RegionExtraSection
          :region-fields="regionFields"
          :extra-fields="extraFields"
          :errors="errors"
          :input-type="inputType"
        />

        <AttachmentSection
          :attachments="attachments"
          :errors="errors"
          :file-input-key="fileInputKey"
          :max-file-mb="ATTACHMENT_MAX_FILE_MB"
          :max-total-mb="ATTACHMENT_MAX_TOTAL_MB"
          @file-change="onFileChange"
        />

        <div v-if="errorMessage" class="form-alert error">{{ errorMessage }}</div>

        <div class="form-actions">
          <button class="btn btn-primary" type="submit" :disabled="submitting || submitted">
            {{ submitting ? "提交中..." : submitted ? "已提交" : "提交信息" }}
          </button>
          <button class="btn btn-default" type="button" @click="resetForm">重置表单</button>
        </div>
      </form>
    </main>

    <SuccessModal
      :visible="modal.visible"
      :title="modal.title"
      :message="modal.message"
      @close="closeModal"
    />
  </div>
</template>

<script setup>
import FormHeader from "./components/FormHeader.vue";
import ApplyInfoSection from "./components/ApplyInfoSection.vue";
import BasicInfoSection from "./components/BasicInfoSection.vue";
import ProfileSection from "./components/ProfileSection.vue";
import ContactSection from "./components/ContactSection.vue";
import EmergencySection from "./components/EmergencySection.vue";
import EducationHistorySection from "./components/EducationHistorySection.vue";
import WorkHistorySection from "./components/WorkHistorySection.vue";
import FamilySection from "./components/FamilySection.vue";
import HobbySection from "./components/HobbySection.vue";
import RegionExtraSection from "./components/RegionExtraSection.vue";
import AttachmentSection from "./components/AttachmentSection.vue";
import SuccessModal from "./components/SuccessModal.vue";
import { useApplicationFormPage } from "./composables/useApplicationFormPage";

const {
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
} = useApplicationFormPage();
</script>
