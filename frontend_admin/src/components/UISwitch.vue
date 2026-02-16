<template>
  <!-- 文件说明：通用开关组件，封装 v-model 双向绑定与禁用态展示。 -->
  <label class="ui-switch">
    <input 
      type="checkbox" 
      :checked="modelValue" 
      @change="$emit('update:modelValue', $event.target.checked)"
    >
    <span class="slider"></span>
    <span class="label-text" v-if="label">{{ label }}</span>
  </label>
</template>

<script setup>
defineProps({
  modelValue: Boolean,
  label: String
});
defineEmits(['update:modelValue']);
</script>

<style scoped>
.ui-switch {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}
.ui-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: relative;
  width: 44px;
  height: 24px;
  background-color: #e4e6eb;
  border-radius: 24px;
  transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
  margin-right: 8px;
}
.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  border-radius: 50%;
  transition: .3s cubic-bezier(0.4, 0.0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
input:checked + .slider {
  background-color: #2b77f0; /* 企业微信蓝 */
}
input:checked + .slider:before {
  transform: translateX(20px);
}
.label-text {
  font-size: 14px;
  color: #1f2329;
}
</style>
