<template>
  <div class="auth-container">
    <div class="auth-box">
      <div class="auth-header">
        <div class="logo-circle">HR</div>
        <h1>应聘管理后台</h1>
      </div>

      <div class="auth-tabs">
        <div
          class="tab-item"
          :class="{ active: authMode === 'login' }"
          @click="$emit('update:authMode', 'login')"
        >
          登录账号
        </div>
        <div
          class="tab-item"
          :class="{ active: authMode === 'register' }"
          @click="$emit('update:authMode', 'register')"
        >
          注册新号
        </div>
      </div>

      <form class="auth-form" @submit.prevent="$emit('submit')">
        <div class="form-item">
          <input v-model="authForm.username" placeholder="请输入账号" required />
        </div>
        <div class="form-item">
          <input v-model="authForm.password" type="password" placeholder="请输入密码" required />
        </div>
        <div v-if="authMode === 'register'" class="form-item">
          <select v-model.number="authForm.region_id" required>
            <option value="" disabled>选择所属地区</option>
            <option v-for="item in publicRegions" :key="item.id" :value="item.id">
              {{ item.name }}
            </option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary btn-block">
          {{ authMode === "login" ? "登 录" : "注 册 并 登 录" }}
        </button>
      </form>
    </div>
    <div class="auth-footer">HRM System &copy; {{ currentYear }}</div>
  </div>
</template>

<script setup>
defineProps({
  authMode: {
    type: String,
    required: true,
  },
  authForm: {
    type: Object,
    required: true,
  },
  publicRegions: {
    type: Array,
    default: () => [],
  },
  currentYear: {
    type: Number,
    required: true,
  },
});

defineEmits(["update:authMode", "submit"]);
</script>
