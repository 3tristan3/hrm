<template>
  <!-- 文件说明：工作经历区，支持多条经历维护并提供分组级校验锚点。 -->
  <section class="section-card" data-error-anchor="work_history" tabindex="-1">
    <div class="section-header">
      <div>
        <p class="section-tag">07</p>
        <h2>主要工作经历</h2>
        <p>应届生可填写实习经历。</p>
      </div>
      <button class="btn btn-default" type="button" @click="$emit('add')">+ 新增一条</button>
    </div>
    <div class="section-body">
      <p v-if="errors.work_history" class="field-error">{{ errors.work_history }}</p>
      <div v-if="!rows.length" class="empty-tip">暂无记录</div>
      <div class="repeat-list">
        <div v-for="(row, index) in rows" :key="`work-${index}`" class="repeat-row">
          <div class="repeat-grid">
            <label class="field">
              <span>工作单位</span>
              <input v-model.trim="row.company" type="text" />
            </label>
            <label class="field">
              <span>所在岗位 / 职务</span>
              <input v-model.trim="row.position" type="text" />
            </label>
            <label class="field">
              <span>开始时间</span>
              <input v-model="row.start" type="month" />
            </label>
            <label class="field">
              <span>结束时间</span>
              <input v-model="row.end" type="month" />
            </label>
          </div>
          <div class="row-actions">
            <button class="link-btn" type="button" @click="$emit('remove', index)">删除</button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  rows: { type: Array, default: () => [] },
  errors: { type: Object, default: () => ({}) },
});
defineEmits(["add", "remove"]);
</script>
