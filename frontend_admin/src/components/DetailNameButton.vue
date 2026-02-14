<template>
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

