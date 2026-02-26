<template>
  <div class="card account-card">
    <div class="card-header account-header">
      <div>
        <h3>账号管理</h3>
        <p class="header-sub">管理各地区 HR 账号、权限与密码安全</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-sm btn-default" type="button" @click="$emit('open-self-password')">
          修改我的密码
        </button>
        <span class="chip">{{ users.length }} 个账号</span>
      </div>
    </div>
    <div class="card-body">
      <div class="account-table">
        <div class="table-header">
          <div>
            <h4>账号列表</h4>
            <p class="text-muted">展示账号所属地区与权限状态</p>
          </div>
          <div class="table-meta">
            <span class="chip subtle">仅系统管理员可操作</span>
          </div>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>账号</th>
              <th>地区</th>
              <th>权限</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in users" :key="item.id">
              <td class="font-medium">{{ item.username }}</td>
              <td><span class="tag">{{ item.region_name || "-" }}</span></td>
              <td>{{ item.is_superuser ? "系统管理员" : "区域账号" }}</td>
              <td>
                <span class="status-dot" :class="{ active: item.is_active }"></span>
                {{ item.is_active ? "启用" : "停用" }}
              </td>
              <td class="action-cell">
                <button class="btn btn-xs btn-default" @click="$emit('select-user-reset', item)">重置密码</button>
                <button
                  class="btn btn-xs btn-danger"
                  :disabled="item.is_superuser || item.username === currentUsername"
                  @click="$emit('delete-user', item)"
                >
                  删除账号
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  users: {
    type: Array,
    default: () => [],
  },
  currentUsername: {
    type: String,
    default: "",
  },
});

defineEmits(["open-self-password", "select-user-reset", "delete-user"]);
</script>
