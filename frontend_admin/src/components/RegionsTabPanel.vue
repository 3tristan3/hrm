<template>
  <div class="card region-card">
    <div class="card-header region-header">
      <div>
        <h3>地区管理</h3>
        <p class="header-sub">仅系统管理员可新增或删除地区，删除需输入密码二次确认</p>
      </div>
      <div class="header-actions">
        <button type="button" class="btn btn-sm btn-primary" @click="$emit('open-create')">新增地区</button>
        <span class="chip">{{ regions.length }} 个地区</span>
      </div>
    </div>
    <div class="card-body region-body">
      <div class="region-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>编码</th>
              <th>排序</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in regions" :key="item.id">
              <td class="font-medium">{{ item.name }}</td>
              <td>{{ item.code }}</td>
              <td>{{ item.order }}</td>
              <td>
                <span class="status-dot" :class="{ active: item.is_active }"></span>
                {{ item.is_active ? "启用" : "停用" }}
              </td>
              <td>
                <button class="btn btn-xs btn-danger" type="button" @click="$emit('open-delete', item)">
                  删除
                </button>
              </td>
            </tr>
            <tr v-if="!regions.length">
              <td colspan="5" class="text-muted">暂无地区数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  regions: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["open-create", "open-delete"]);
</script>
