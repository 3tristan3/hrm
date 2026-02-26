<template>
  <div v-if="activeApplication" class="detail-overlay" @click.self="$emit('close')">
    <div class="detail-modal">
      <div class="detail-header">
        <div class="detail-header-left">
          <div class="detail-photo">
            <img
              v-if="activeApplication.photo_url"
              :src="resolveMediaUrl(activeApplication.photo_url)"
              alt="个人照片"
              loading="lazy"
              decoding="async"
            />
            <div v-else class="photo-fallback">
              {{ activeApplication.name ? activeApplication.name.slice(0, 1) : "?" }}
            </div>
          </div>
          <div>
            <div class="detail-title">{{ activeApplication.name }}</div>
            <div class="detail-subtitle">
              {{ activeApplication.job_title }} · {{ activeApplication.region_name }}
            </div>
          </div>
        </div>
        <button class="detail-close" @click="$emit('close')" title="关闭">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="detail-body">
        <div v-if="applicationDetailLoading" class="detail-loading">正在加载详情...</div>
        <div v-else>
          <div v-for="section in detailSections" :key="section.title" class="detail-section">
            <div class="section-title">{{ section.title }}</div>
            <div v-if="section.items" class="detail-grid">
              <div v-for="item in section.items" :key="item.label" class="detail-item">
                <div class="detail-label">{{ item.label }}</div>
                <div class="detail-value" :class="{ muted: item.value === '-' || item.value === '暂无' }">
                  {{ item.value }}
                </div>
              </div>
            </div>
            <div v-if="section.blocks" class="detail-blocks">
              <div v-for="block in section.blocks" :key="block.label">
                <div class="detail-label">{{ block.label }}</div>
                <div class="detail-multiline">{{ block.value }}</div>
              </div>
            </div>
          </div>
          <div class="detail-section detail-attachments-section">
            <div class="section-title">证件与附件</div>
            <div class="detail-attachments-grid">
              <button
                v-for="card in keyAttachmentCards"
                :key="card.key"
                type="button"
                class="detail-attachment-card"
                :class="{ missing: !card.url }"
                :disabled="!card.url"
                @click="$emit('open-attachment', card.url)"
              >
                <span class="detail-attachment-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                </span>
                <span class="detail-attachment-main">
                  <span class="detail-attachment-title">{{ card.label }}</span>
                  <span class="detail-attachment-hint">{{ card.hint }}</span>
                </span>
                <span class="detail-attachment-preview" :class="{ placeholder: !card.url }" aria-hidden="true">
                  <img
                    v-if="card.url && card.isImage"
                    :src="resolveMediaUrl(card.url)"
                    :alt="`${card.label}预览`"
                    loading="lazy"
                    decoding="async"
                  />
                  <span v-else>{{ card.previewTag }}</span>
                </span>
                <span class="detail-attachment-action">{{ card.url ? "查看文件" : "未上传" }}</span>
              </button>
            </div>
            <div v-if="otherAttachmentFiles.length" class="detail-attachments-extra">
              <div class="detail-label">其他附件</div>
              <div class="detail-attachments-extra-list">
                <button
                  v-for="item in otherAttachmentFiles"
                  :key="item.id"
                  type="button"
                  class="detail-attachment-link"
                  @click="$emit('open-attachment', item.file_url)"
                >
                  {{ item.category_label || item.category || "附件" }} · {{ item.file_name || "点击查看" }}
                </button>
              </div>
            </div>
          </div>
          <div class="detail-section detail-log-section">
            <div class="section-title">操作日志</div>
            <div v-if="applicationLogsLoading" class="detail-loading-inline">正在加载操作日志...</div>
            <div v-else-if="applicationOperationLogs.length" class="detail-log-timeline">
              <div v-for="item in applicationOperationLogs" :key="item.id" class="detail-log-node">
                <span class="detail-log-dot" :class="item.result === 'success' ? 'success' : 'failed'"></span>
                <div class="detail-log-item">
                  <div class="detail-log-meta">
                    <span class="detail-log-time">{{ formatTime(item.created_at) }}</span>
                    <span class="detail-log-operator">{{ item.operator_username || "-" }}</span>
                    <span class="chip" :class="operationResultClass(item.result)">
                      {{ operationResultLabel(item.result) }}
                    </span>
                  </div>
                  <div class="detail-log-content">
                    <span class="op-module-tag mini" :class="`mod-${item.module || 'default'}`">
                      {{ operationModuleLabel(item.module) }}
                    </span>
                    <strong>{{ operationActionLabel(item.action) }}</strong>
                  </div>
                  <div class="detail-log-summary">{{ item.summary || "-" }}</div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">暂无操作日志</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  activeApplication: {
    type: Object,
    default: null,
  },
  applicationDetailLoading: {
    type: Boolean,
    default: false,
  },
  detailSections: {
    type: Array,
    default: () => [],
  },
  keyAttachmentCards: {
    type: Array,
    default: () => [],
  },
  otherAttachmentFiles: {
    type: Array,
    default: () => [],
  },
  applicationLogsLoading: {
    type: Boolean,
    default: false,
  },
  applicationOperationLogs: {
    type: Array,
    default: () => [],
  },
  resolveMediaUrl: {
    type: Function,
    required: true,
  },
  formatTime: {
    type: Function,
    required: true,
  },
  operationResultClass: {
    type: Function,
    required: true,
  },
  operationResultLabel: {
    type: Function,
    required: true,
  },
  operationModuleLabel: {
    type: Function,
    required: true,
  },
  operationActionLabel: {
    type: Function,
    required: true,
  },
});

defineEmits(["close", "open-attachment"]);
</script>
