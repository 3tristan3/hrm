<template>
  <!-- 文件说明：补充信息区，填写兴趣爱好与自我评价等非结构化文本。 -->
  <section class="section-card">
    <div class="section-header">
      <div>
        <p class="section-tag">09</p>
        <h2>兴趣爱好与自我评价</h2>
        <p>可简单描述个人特点与优势。</p>
      </div>
    </div>
    <div class="section-body">
      <div class="grid-2">
        <label class="field">
          <span>兴趣爱好</span>
          <textarea v-model.trim="form.hobbies" rows="4"></textarea>
        </label>
        <label class="field">
          <span>自我评价</span>
          <textarea v-model.trim="form.self_evaluation" rows="4"></textarea>
        </label>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  form: { type: Object, required: true },
});
</script>
