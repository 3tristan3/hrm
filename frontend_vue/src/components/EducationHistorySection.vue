<template>
  <!-- 文件说明：教育/培训经历分段，支持多条经历的新增、删除和必填校验锚点。 -->
  <section class="section-card" data-error-anchor="education_history" tabindex="-1">
    <div class="section-header">
      <div>
        <p class="section-tag">04</p>
        <h2>主要教育和培训经历</h2>
        <p>高中以下学历填写最高学历毕业学校。</p>
      </div>
      <button class="btn btn-default" type="button" @click="$emit('add')">+ 新增一条</button>
    </div>
    <div class="section-body">
      <small v-if="errors.education_history" class="section-error">{{ errors.education_history }}</small>
      <div v-if="!rows.length" class="empty-tip">暂无记录</div>
      <div class="repeat-list">
        <div v-for="(row, index) in rows" :key="`edu-${index}`" class="repeat-row">
          <div class="repeat-grid">
            <label class="field">
              <span>毕业院校 <em class="required">*</em></span>
              <input v-model.trim="row.school" type="text" />
            </label>
            <label class="field">
              <span>专业 <em class="required">*</em></span>
              <input v-model.trim="row.major" type="text" />
            </label>
            <label class="field">
              <span>学历/学位 <em class="required">*</em></span>
              <input v-model.trim="row.degree" type="text" />
            </label>
            <label class="field">
              <span>开始时间 <em class="required">*</em></span>
              <input v-model="row.start" type="month" />
            </label>
            <label class="field">
              <span>结束时间 <em class="required">*</em></span>
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
