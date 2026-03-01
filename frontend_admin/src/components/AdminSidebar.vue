<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="logo-icon">H</span>
      <span class="app-name">应聘管理</span>
    </div>
    <nav class="sidebar-nav">
      <RouterLink
        v-for="item in visibleTabs"
        :key="item.key"
        class="nav-item"
        :class="{ active: activeTab === item.key }"
        :to="{ name: item.key }"
      >
        {{ item.label }}
      </RouterLink>
    </nav>
    <div class="sidebar-footer">
      <div class="user-info">
        <div class="avatar">{{ userInitial }}</div>
        <div class="info-text">
          <div class="username">{{ userProfile.real_name || currentUsername || "管理员" }}</div>
          <div class="role-badge">{{ userProfile.can_view_all ? "总部" : userProfile.region_name }}</div>
        </div>
        <button class="logout-btn" title="退出" @click="$emit('logout')">
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  visibleTabs: {
    type: Array,
    default: () => [],
  },
  activeTab: {
    type: String,
    default: "",
  },
  userInitial: {
    type: String,
    default: "",
  },
  currentUsername: {
    type: String,
    default: "",
  },
  userProfile: {
    type: Object,
    required: true,
  },
});

defineEmits(["logout"]);
</script>
