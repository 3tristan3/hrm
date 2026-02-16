<template>
  <!-- 文件说明：应聘基础选择区，承载招聘类型、地区、岗位及岗位摘要信息。 -->
  <section class="section-card">
    <div class="section-header">
      <div>
        <p class="section-tag">01</p>
        <h2>社招 / 校招</h2>
        <p>选择招聘类型与岗位。</p>
      </div>
      <div class="section-note">带 <em class="required">*</em> 为必填</div>
    </div>
    <div class="section-body">
      <div class="grid-3">
        <label class="field">
          <span>招聘类型 <em class="required">*</em></span>
          <select v-model="form.recruit_type" name="recruit_type">
            <option value="">请选择</option>
            <option value="社招">社招</option>
            <option value="校招">校招</option>
          </select>
          <small v-if="errors.recruit_type">{{ errors.recruit_type }}</small>
        </label>

        <label class="field">
          <span>应聘区域 <em class="required">*</em></span>
          <select :value="selectedRegionId" name="region_id" @change="onRegionChange">
            <option value="">请选择</option>
            <option v-for="region in regions" :key="region.id" :value="region.id">
              {{ region.name }}
            </option>
          </select>
          <small v-if="errors.region_id">{{ errors.region_id }}</small>
        </label>

        <label class="field">
          <span>应聘职位 <em class="required">*</em></span>
          <select :value="selectedJobId" name="job_id" :disabled="!jobs.length" @change="onJobChange">
            <option value="">请选择岗位</option>
            <option v-for="job in jobs" :key="job.id" :value="job.id">
              {{ job.title }}
            </option>
          </select>
          <small v-if="errors.job_id">{{ errors.job_id }}</small>
        </label>

        <label class="field">
          <span>能上岗日期</span>
          <input v-model="form.available_date" type="date" />
        </label>
      </div>

      <div class="job-preview" v-if="jobDetail">
        <div>
          <p class="job-title">{{ jobDetail.title }}</p>
          <p class="job-desc">{{ jobDetail.description || "暂无岗位描述" }}</p>
        </div>
        <div class="job-meta">
          <span>学历：{{ jobDetail.education || "不限" }}</span>
        </div>
      </div>

      <div class="sub-section">
        <p class="sub-title">介绍人情况（如有）</p>
        <div class="grid-3">
          <label class="field">
            <span>介绍人姓名</span>
            <input v-model.trim="form.referrer_name" type="text" placeholder="姓名" />
          </label>

          <label class="field">
            <span>介绍人关系</span>
            <input v-model.trim="form.referrer_relation" type="text" placeholder="关系" />
          </label>

          <label class="field">
            <span>介绍人工作单位</span>
            <input v-model.trim="form.referrer_company" type="text" placeholder="单位" />
          </label>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  regions: { type: Array, default: () => [] },
  jobs: { type: Array, default: () => [] },
  selectedRegionId: { type: [String, Number], default: "" },
  selectedJobId: { type: [String, Number], default: "" },
  jobDetail: { type: Object, default: null },
  errors: { type: Object, default: () => ({}) },
  form: { type: Object, required: true },
});

const emit = defineEmits(["update:selectedRegionId", "update:selectedJobId"]);

const onRegionChange = (event) => {
  emit("update:selectedRegionId", event.target.value);
};

const onJobChange = (event) => {
  emit("update:selectedJobId", event.target.value);
};
</script>
