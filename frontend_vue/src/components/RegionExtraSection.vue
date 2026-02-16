<template>
  <!-- 文件说明：地区扩展字段区，按所选地区动态渲染额外必填项。 -->
  <section v-if="regionFields.length" class="section-card">
    <div class="section-header">
      <div>
        <p class="section-tag">11</p>
        <h2>地区补充字段</h2>
        <p>由地区配置的额外信息。</p>
      </div>
    </div>
    <div class="section-body">
      <div class="grid-3">
        <label v-for="field in regionFields" :key="field.key" class="field">
          <span>
            {{ field.label }}
            <em v-if="field.required" class="required">*</em>
          </span>
          <template v-if="field.field_type === 'select'">
            <select v-model="extraFields[field.key]" :name="`extra_${field.key}`">
              <option value="">请选择</option>
              <option v-for="option in field.options || []" :key="option" :value="option">
                {{ option }}
              </option>
            </select>
          </template>
          <template v-else>
            <input
              :type="inputType(field.field_type)"
              v-model="extraFields[field.key]"
              :name="`extra_${field.key}`"
              :placeholder="`请输入${field.label}`"
            />
          </template>
          <small v-if="errors[field.key]">{{ errors[field.key] }}</small>
        </label>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  regionFields: { type: Array, default: () => [] },
  extraFields: { type: Object, required: true },
  errors: { type: Object, default: () => ({}) },
  inputType: { type: Function, required: true },
});
</script>
