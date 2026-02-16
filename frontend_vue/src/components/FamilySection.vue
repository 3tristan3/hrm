<template>
  <!-- 文件说明：家庭成员区，支持动态增删成员并提供分组级错误锚点。 -->
  <section class="section-card" data-error-anchor="family_members" tabindex="-1">
    <div class="section-header">
      <div>
        <p class="section-tag">08</p>
        <h2>主要家庭成员</h2>
        <p>至少填写两位家庭成员信息。</p>
      </div>
      <button class="btn btn-default" type="button" @click="$emit('add')">+ 新增一位</button>
    </div>
    <div class="section-body">
      <small v-if="errors.family_members" class="section-error">{{ errors.family_members }}</small>
      <div class="repeat-list">
        <div v-for="(row, index) in rows" :key="`family-${index}`" class="repeat-row">
          <div class="repeat-grid">
            <label class="field">
              <span>姓名 <em class="required">*</em></span>
              <input v-model.trim="row.name" type="text" />
            </label>
            <label class="field">
              <span>关系 <em class="required">*</em></span>
              <select v-model="row.relation">
                <option value="">请选择</option>
                <option value="父母">父母</option>
                <option value="配偶">配偶</option>
                <option value="子女">子女</option>
                <option value="其他">其他</option>
              </select>
            </label>
            <label class="field">
              <span>年龄 <em class="required">*</em></span>
              <input v-model.number="row.age" type="number" min="1" />
            </label>
            <label class="field">
              <span>工作单位/住址 <em class="required">*</em></span>
              <input v-model.trim="row.company" type="text" />
            </label>
            <label class="field">
              <span>岗位/职务 <em class="required">*</em></span>
              <input v-model.trim="row.position" type="text" />
            </label>
            <label class="field">
              <span>联系方式 <em class="required">*</em></span>
              <input v-model.trim="row.phone" type="text" />
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
