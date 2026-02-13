<template>
  <!-- 文件说明：HobbySection 文件，实现对应模块能力。 -->
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
