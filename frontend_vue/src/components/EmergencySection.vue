<template>
  <!-- 文件说明：紧急联系人区，用于采集突发场景下的联系人与联系电话。 -->
  <section class="section-card">
    <div class="section-header">
      <div>
        <p class="section-tag">06</p>
        <h2>紧急联系人</h2>
        <p>如有需要便于联系。</p>
      </div>
    </div>
    <div class="section-body">
      <div class="grid-3">
        <label class="field">
          <span>紧急联系人姓名</span>
          <input v-model.trim="form.emergency_name" type="text" />
        </label>
        <label class="field">
          <span>紧急联系人手机号</span>
          <input v-model.trim="form.emergency_phone" type="tel" />
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
