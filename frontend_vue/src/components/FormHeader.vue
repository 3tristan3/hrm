<template>
  <!-- 文件说明：应聘页头部，展示品牌信息与当前提交状态提示。 -->
  <header class="page-header">
    <div class="brand">
      <div class="brand-mark">WIN</div>
      <div>
        <p class="brand-eyebrow">亚通集团</p>
        <h1>亚通集团招聘信息收集</h1>
        <p class="brand-subtitle">
          请如实填写以下信息，带 <em class="required">*</em> 的为必填项。
        </p>
      </div>
    </div>
    <div class="header-meta">
      <div class="meta-item">
        <span class="meta-label">状态</span>
        <span class="meta-value">{{ submitting ? "提交中" : submitted ? "已提交" : "待提交" }}</span>
      </div>
    </div>
  </header>
</template>

<script setup>
defineProps({
  submitting: Boolean,
  submitted: Boolean,
});
</script>
