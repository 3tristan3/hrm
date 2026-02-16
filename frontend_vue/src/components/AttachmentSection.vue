<template>
  <!-- 文件说明：附件上传区，管理必传证件与可选附件并展示上传校验信息。 -->
  <section class="section-card" :key="fileInputKey">
    <div class="section-header">
      <div>
        <p class="section-tag">10</p>
        <h2>附件上传</h2>
        <p>支持图片、PDF、Word 文件。单文件不超过 {{ maxFileMb }}MB，附件总大小不超过 {{ maxTotalMb }}MB。</p>
      </div>
    </div>
    <div class="section-body">
      <div class="upload-grid">
        <div class="upload-item" data-error-anchor="id_front" tabindex="-1">
          <div class="upload-label">身份证正面 <em class="required">*</em></div>
          <label class="upload-control">
            <input class="upload-input" name="id_front" type="file" accept="image/*" @change="$emit('file-change', 'id_front', $event)" />
            <span class="upload-btn">选择文件</span>
          </label>
          <p class="file-name">{{ attachments.id_front?.name || "未选择文件" }}</p>
          <small v-if="errors.id_front">{{ errors.id_front }}</small>
        </div>
        <div class="upload-item" data-error-anchor="id_back" tabindex="-1">
          <div class="upload-label">身份证反面 <em class="required">*</em></div>
          <label class="upload-control">
            <input class="upload-input" name="id_back" type="file" accept="image/*" @change="$emit('file-change', 'id_back', $event)" />
            <span class="upload-btn">选择文件</span>
          </label>
          <p class="file-name">{{ attachments.id_back?.name || "未选择文件" }}</p>
          <small v-if="errors.id_back">{{ errors.id_back }}</small>
        </div>
        <div class="upload-item" data-error-anchor="resume" tabindex="-1">
          <div class="upload-label">个人简历 <em class="required">*</em></div>
          <label class="upload-control">
            <input class="upload-input" name="resume" type="file" accept=".pdf,.doc,.docx" @change="$emit('file-change', 'resume', $event)" />
            <span class="upload-btn">选择文件</span>
          </label>
          <p class="file-name">{{ attachments.resume?.name || "未选择文件" }}</p>
          <small v-if="errors.resume">{{ errors.resume }}</small>
        </div>
        <div class="upload-item wide">
          <div class="upload-label">其他相关附件（可多文件）</div>
          <label class="upload-control">
            <input class="upload-input" type="file" multiple accept="image/*,.pdf,.doc,.docx" @change="$emit('file-change', 'other', $event)" />
            <span class="upload-btn">选择文件</span>
          </label>
          <p class="file-name">
            {{ attachments.other.length ? attachments.other.map(f => f.name).join("、") : "未选择文件" }}
          </p>
          <small v-if="errors.other">{{ errors.other }}</small>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  attachments: { type: Object, required: true },
  errors: { type: Object, default: () => ({}) },
  fileInputKey: { type: Number, default: 0 },
  maxFileMb: { type: Number, default: 10 },
  maxTotalMb: { type: Number, default: 40 },
});
defineEmits(["file-change"]);
</script>
