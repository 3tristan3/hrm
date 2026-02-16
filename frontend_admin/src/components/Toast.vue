<template>
  <!-- 文件说明：轻提示组件，统一成功/失败/信息反馈的展示与自动关闭。 -->
  <transition name="toast-fade">
    <div v-if="visible" class="toast-wrapper" :class="type">
      <div class="toast-icon">
        <span v-if="type === 'success'">✔</span>
        <span v-else-if="type === 'error'">!</span>
        <span v-else>i</span>
      </div>
      <span class="toast-message">{{ message }}</span>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue';

const visible = ref(false);
const message = ref('');
const type = ref('info'); // success, error, info
let timer = null;

const show = (msg, msgType = 'info', duration = 3000) => {
  message.value = msg;
  type.value = msgType;
  visible.value = true;
  
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => {
    visible.value = false;
  }, duration);
};

defineExpose({ show });
</script>

<style scoped>
.toast-wrapper {
  position: fixed;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  padding: 12px 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.12);
  z-index: 9999;
  min-width: 300px;
  border: 1px solid #ebeef5;
}
.toast-message {
  font-size: 14px;
  color: #333;
}
.toast-icon {
  margin-right: 12px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: white;
}
/* 类型样式 */
.toast-wrapper.success .toast-icon { background: #52c41a; }
.toast-wrapper.error .toast-icon { background: #ff4d4f; }
.toast-wrapper.info .toast-icon { background: #2b77f0; }

/* 动画 */
.toast-fade-enter-active, .toast-fade-leave-active {
  transition: all 0.3s ease;
}
.toast-fade-enter-from, .toast-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px);
}
</style>
