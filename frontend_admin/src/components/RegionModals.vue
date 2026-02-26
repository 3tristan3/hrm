<template>
  <div>
    <div v-if="showRegionCreateModal" class="job-modal-overlay" @click.self="$emit('close-create')">
      <div class="region-create-modal">
        <div class="job-modal-header">
          <div>
            <div class="job-modal-title">新增地区</div>
            <div class="job-modal-subtitle">填写地区基础信息并保存，保存后会立即同步到岗位与注册地区选项</div>
          </div>
          <button class="job-modal-close" type="button" title="关闭" @click="$emit('close-create')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="job-modal-body">
          <form class="form-compact" @submit.prevent="$emit('submit-create')">
            <div class="form-grid-2">
              <div class="form-group">
                <label>地区名称</label>
                <input v-model.trim="regionForm.name" placeholder="如：华东地区" required />
              </div>
              <div class="form-group">
                <label>地区编码</label>
                <input v-model.trim="regionForm.code" placeholder="如：east" required />
              </div>
            </div>
            <div class="form-grid-2">
              <div class="form-group">
                <label>排序</label>
                <input v-model.number="regionForm.order" type="number" />
              </div>
              <div class="form-group">
                <label>状态</label>
                <select v-model="regionForm.is_active">
                  <option :value="true">启用</option>
                  <option :value="false">停用</option>
                </select>
              </div>
            </div>
            <div class="form-actions right">
              <button type="button" class="btn btn-sm btn-default" @click="$emit('reset-region-form')">重置</button>
              <button type="button" class="btn btn-sm btn-default" @click="$emit('close-create')">取消</button>
              <button type="submit" class="btn btn-sm btn-primary">保存地区</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div v-if="showRegionDeleteModal" class="job-modal-overlay" @click.self="$emit('close-delete')">
      <div class="region-delete-modal">
        <div class="job-modal-header">
          <div>
            <div class="job-modal-title">删除地区</div>
            <div class="job-modal-subtitle">
              即将删除：{{ pendingDeleteRegion?.name || "-" }}（{{ pendingDeleteRegion?.code || "-" }}）
            </div>
          </div>
          <button class="job-modal-close" type="button" title="关闭" @click="$emit('close-delete')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="job-modal-body">
          <p class="text-muted region-delete-note">此操作不可恢复，请输入当前登录密码进行二次确认。</p>
          <div class="form-group">
            <label>当前登录密码</label>
            <input
              :value="regionDeletePassword"
              type="password"
              placeholder="请输入当前登录密码"
              @input="$emit('update:region-delete-password', $event.target.value)"
              @keyup.enter="$emit('confirm-delete')"
            />
          </div>
          <div class="form-actions right">
            <button class="btn btn-default" type="button" @click="$emit('close-delete')">取消</button>
            <button
              class="btn btn-danger"
              type="button"
              :disabled="regionDeleteSubmitting || !String(regionDeletePassword || '').trim()"
              @click="$emit('confirm-delete')"
            >
              {{ regionDeleteSubmitting ? "删除中..." : "确认删除" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  showRegionCreateModal: {
    type: Boolean,
    default: false,
  },
  showRegionDeleteModal: {
    type: Boolean,
    default: false,
  },
  regionForm: {
    type: Object,
    required: true,
  },
  pendingDeleteRegion: {
    type: Object,
    default: null,
  },
  regionDeletePassword: {
    type: String,
    default: "",
  },
  regionDeleteSubmitting: {
    type: Boolean,
    default: false,
  },
});

defineEmits([
  "close-create",
  "submit-create",
  "reset-region-form",
  "close-delete",
  "update:region-delete-password",
  "confirm-delete",
]);
</script>
