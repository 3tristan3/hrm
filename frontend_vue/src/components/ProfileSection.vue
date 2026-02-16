<template>
  <!-- 文件说明：个人概况区，采集户籍、健康、政治面貌等背景资料。 -->
  <section class="section-card">
    <div class="section-header">
      <div>
        <p class="section-tag">03</p>
        <h2>个人情况补充</h2>
        <p>教育背景、证书与身份补充信息。</p>
      </div>
    </div>
    <div class="section-body">
      <div class="grid-3">
        <label class="field">
          <span>出生年月</span>
          <input v-model="form.birth_month" type="month" />
        </label>

        <label class="field">
          <span>健康情况</span>
          <select v-model="form.health_status">
            <option value="">请选择</option>
            <option value="良好">良好</option>
            <option value="一般">一般</option>
            <option value="健康">健康</option>
            <option value="其他">其他</option>
          </select>
        </label>

        <label class="field">
          <span>户口性质</span>
          <select v-model="form.hukou_type">
            <option value="">请选择</option>
            <option value="农业">农业</option>
            <option value="非农业">非农业</option>
            <option value="居民户口">居民户口</option>
          </select>
        </label>

        <label class="field">
          <span>户口所在地</span>
          <input v-model.trim="form.hukou_address" type="text" placeholder="详细地址" />
        </label>

        <label class="field">
          <span>现住地址</span>
          <input v-model.trim="form.current_address" type="text" placeholder="详细地址" />
        </label>
      </div>

      <div class="sub-section">
        <p class="sub-title">教育信息</p>
        <div class="grid-3">
          <label class="field">
            <span>毕业院校</span>
            <input v-model.trim="form.graduate_school" type="text" placeholder="学校全称" />
          </label>

          <label class="field">
            <span>毕业时间</span>
            <input v-model="form.graduation_date" type="month" />
          </label>

          <label class="field">
            <span>专业</span>
            <input v-model.trim="form.major" type="text" />
          </label>

          <label class="field">
            <span>毕业证编号</span>
            <input v-model.trim="form.diploma_number" type="text" />
          </label>

          <label class="field">
            <span>职称证书</span>
            <input v-model.trim="form.title_cert" type="text" placeholder="证书名称/编号" />
          </label>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  form: { type: Object, required: true },
});
</script>
