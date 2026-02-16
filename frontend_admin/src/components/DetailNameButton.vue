<template>
  <!-- 文件说明：详情入口按钮，统一姓名点击交互并向父组件派发打开详情事件。 -->
  <button v-if="label" class="name-detail-btn" type="button" @click.stop="$emit('open')">
    {{ label }}
  </button>
  <span v-else>-</span>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    default: "",
  },
});

defineEmits(["open"]);
</script>
