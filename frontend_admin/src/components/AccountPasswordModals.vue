<template>
  <div>
    <div
      v-if="showResetPasswordModal"
      class="job-modal-overlay"
      @click.self="$emit('close-reset')"
    >
      <div class="account-password-modal">
        <div class="job-modal-header">
          <div>
            <div class="job-modal-title">重置账号密码</div>
            <div class="job-modal-subtitle">为当前选中的账号设置新密码，提交后立即生效</div>
          </div>
          <button class="job-modal-close" type="button" title="关闭" @click="$emit('close-reset')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="job-modal-body">
          <form class="form-compact" @submit.prevent="$emit('submit-reset')">
            <div class="form-grid-2">
              <div class="form-group">
                <label>目标账号</label>
                <input :value="selectedUsername" type="text" disabled />
              </div>
              <div class="form-group">
                <label>新密码</label>
                <input
                  v-model="passwordForm.password"
                  type="password"
                  placeholder="请输入新密码"
                  required
                />
              </div>
            </div>
            <div class="form-actions right">
              <button class="btn btn-sm btn-default" type="button" @click="$emit('close-reset')">取消</button>
              <button
                class="btn btn-sm btn-primary"
                type="submit"
                :disabled="!passwordForm.user_id || !passwordForm.password"
              >
                确认重置
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div
      v-if="showSelfPasswordModal"
      class="job-modal-overlay"
      @click.self="$emit('close-self')"
    >
      <div class="account-password-modal wide">
        <div class="job-modal-header">
          <div>
            <div class="job-modal-title">修改我的密码</div>
            <div class="job-modal-subtitle">输入原密码与新密码，更新后需重新登录</div>
          </div>
          <button class="job-modal-close" type="button" title="关闭" @click="$emit('close-self')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="job-modal-body">
          <form class="form-compact" @submit.prevent="$emit('submit-self')">
            <div class="form-grid-3">
              <div class="form-group">
                <label>原密码</label>
                <input
                  v-model="selfPasswordForm.old_password"
                  type="password"
                  placeholder="请输入原密码"
                  required
                />
              </div>
              <div class="form-group">
                <label>新密码</label>
                <input
                  v-model="selfPasswordForm.new_password"
                  type="password"
                  placeholder="请输入新密码"
                  required
                />
              </div>
              <div class="form-group">
                <label>确认新密码</label>
                <input
                  v-model="selfPasswordForm.confirm_password"
                  type="password"
                  placeholder="再次输入新密码"
                  required
                />
              </div>
            </div>
            <div class="form-actions right">
              <button class="btn btn-sm btn-default" type="button" @click="$emit('close-self')">取消</button>
              <button class="btn btn-sm btn-primary" type="submit">更新密码</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  showResetPasswordModal: {
    type: Boolean,
    default: false,
  },
  showSelfPasswordModal: {
    type: Boolean,
    default: false,
  },
  users: {
    type: Array,
    default: () => [],
  },
  passwordForm: {
    type: Object,
    required: true,
  },
  selfPasswordForm: {
    type: Object,
    required: true,
  },
});

defineEmits(["close-reset", "submit-reset", "close-self", "submit-self"]);

const selectedUsername = computed(
  () => props.users.find((item) => item.id === props.passwordForm.user_id)?.username || "-"
);
</script>
