<template>
  <!-- 文件说明：提交结果弹窗，用于反馈成功、失败或需联系管理员的状态。 -->
  <div v-if="visible" class="modal-backdrop">
    <div class="modal">
      <div class="modal-header">
        <h3>{{ title }}</h3>
      </div>
      <div class="modal-body">
        <p>{{ message }}</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-primary" type="button" @click="$emit('close')">知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: Boolean,
  title: { type: String, default: "" },
  message: { type: String, default: "" },
});
defineEmits(["close"]);
</script>
