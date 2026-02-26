<template>
  <div v-if="showJobForm" class="job-modal-overlay" @click.self="$emit('close')">
    <div class="job-modal">
      <div class="job-modal-header">
        <div>
          <div class="job-modal-title">{{ jobForm.id ? "编辑岗位" : "新增岗位" }}</div>
          <div class="job-modal-subtitle">
            {{ jobForm.id ? `正在编辑：${jobForm.title || "未命名岗位"}` : "填写岗位信息并发布" }}
          </div>
        </div>
        <div class="job-modal-actions">
          <span class="panel-pill" :class="{ warning: !jobForm.is_active }">
            {{ jobForm.is_active ? "上架中" : "草稿" }}
          </span>
          <button class="job-modal-close" title="关闭" @click="$emit('close')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
      <div class="job-modal-body">
        <form class="form-compact" @submit.prevent="$emit('save')">
          <div class="form-grid-2">
            <div class="form-group">
              <label>所属地区</label>
              <select v-model.number="jobForm.region" required :disabled="!userProfile.can_view_all">
                <option value="">请选择...</option>
                <option v-for="item in regions" :key="item.id" :value="item.id">{{ item.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>岗位名称</label>
              <input v-model="jobForm.title" placeholder="如：装置操作员" required />
            </div>
          </div>
          <div class="form-grid-3">
            <div class="form-group">
              <label>薪资范围</label>
              <input v-model="jobForm.salary" placeholder="如：5k-8k" />
            </div>
            <div class="form-group">
              <label>学历要求</label>
              <input v-model="jobForm.education" placeholder="如：本科及以上" />
            </div>
            <div class="form-group">
              <label>排序</label>
              <input v-model.number="jobForm.order" type="number" />
            </div>
          </div>
          <div class="form-group full-width">
            <label>岗位职责</label>
            <textarea v-model="jobForm.description" rows="4" placeholder="请输入岗位职责..."></textarea>
          </div>
          <div class="job-switch">
            <div>
              <div class="switch-title">上架状态</div>
              <div class="switch-desc">{{ jobForm.is_active ? "岗位可被投递" : "岗位暂不开放" }}</div>
            </div>
            <UISwitch v-model="jobForm.is_active" />
          </div>
          <div class="form-actions right">
            <button type="button" class="btn btn-default" @click="$emit('reset')">清空表单</button>
            <button type="submit" class="btn btn-primary">
              {{ jobForm.id ? "保存岗位" : "发布岗位" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import UISwitch from "./UISwitch.vue";

defineProps({
  showJobForm: {
    type: Boolean,
    default: false,
  },
  jobForm: {
    type: Object,
    required: true,
  },
  userProfile: {
    type: Object,
    required: true,
  },
  regions: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["close", "save", "reset"]);
</script>
