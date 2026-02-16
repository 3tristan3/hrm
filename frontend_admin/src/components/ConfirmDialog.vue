<template>
  <!-- 文件说明：全局确认弹窗组件，用于危险操作二次确认与回调执行。 -->
  <transition name="modal-fade">
    <div v-if="visible" class="modal-backdrop">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ title }}</h3>
        </div>
        <div class="modal-body">
          <p>{{ content }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="handleCancel">取消</button>
          <button class="btn-confirm" :class="{ 'danger': isDanger }" @click="handleConfirm">
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue';

const visible = ref(false);
const title = ref('');
const content = ref('');
const isDanger = ref(false);
const confirmText = ref('确定');

let resolvePromise = null;

const open = (options) => {
  title.value = options.title || '提示';
  content.value = options.content || '';
  isDanger.value = options.type === 'danger';
  confirmText.value = options.confirmText || '确定';
  visible.value = true;
  
  return new Promise((resolve) => {
    resolvePromise = resolve;
  });
};

const handleConfirm = () => {
  visible.value = false;
  if (resolvePromise) resolvePromise(true);
};

const handleCancel = () => {
  visible.value = false;
  if (resolvePromise) resolvePromise(false);
};

defineExpose({ open });
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3200;
}
.modal-content {
  background: white;
  width: 400px;
  border-radius: 8px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
  overflow: hidden;
}
.modal-header {
  padding: 20px 24px 10px;
}
.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1f2329;
}
.modal-body {
  padding: 0 24px 24px;
  color: #646a73;
  font-size: 14px;
  line-height: 1.5;
}
.modal-footer {
  padding: 16px 24px;
  background: #fbfbfc;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
button {
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-cancel {
  background: #fff;
  border: 1px solid #dee0e3;
  color: #1f2329;
}
.btn-cancel:hover {
  background: #f5f6f7;
}
.btn-confirm {
  background: #2b77f0;
  color: white;
}
.btn-confirm:hover {
  background: #1764eb;
}
.btn-confirm.danger {
  background: #ff4d4f;
}
.btn-confirm.danger:hover {
  background: #ff2a2d;
}

/* 动画 */
.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.2s;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}
</style>
