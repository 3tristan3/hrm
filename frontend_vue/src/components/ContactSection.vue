<template>
  <!-- 文件说明：联系方式区，收集手机号、QQ、微信与邮箱并承接格式校验提示。 -->
  <section class="section-card">
    <div class="section-header">
      <div>
        <p class="section-tag">05</p>
        <h2>联系方式</h2>
        <p>确保手机号码可联系到本人。</p>
      </div>
    </div>
    <div class="section-body">
      <div class="grid-4">
        <label class="field">
          <span>手机 <em class="required">*</em></span>
          <input v-model.trim="form.phone" name="phone" type="tel" placeholder="11位手机号" />
          <small v-if="errors.phone">{{ errors.phone }}</small>
        </label>

        <label class="field">
          <span>QQ 号码 <em class="required">*</em></span>
          <input v-model.trim="form.qq" name="qq" type="text" />
          <small v-if="errors.qq">{{ errors.qq }}</small>
        </label>

        <label class="field">
          <span>微信号 <em class="required">*</em></span>
          <input v-model.trim="form.wechat" name="wechat" type="text" placeholder="请输入微信号" />
          <small v-if="errors.wechat">{{ errors.wechat }}</small>
        </label>

        <label class="field">
          <span>邮箱 <em class="required">*</em></span>
          <input v-model.trim="form.email" name="email" type="email" placeholder="xxx@xx.com" />
          <small v-if="errors.email">{{ errors.email }}</small>
        </label>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  form: { type: Object, required: true },
  errors: { type: Object, default: () => ({}) },
});
</script>
