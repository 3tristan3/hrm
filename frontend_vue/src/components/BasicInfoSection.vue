<template>
  <!-- 文件说明：个人基础资料区，采集姓名/性别/身份证等核心身份信息。 -->
  <section class="section-card">
    <div class="section-header">
      <div>
        <p class="section-tag">02</p>
        <h2>个人基本信息</h2>
        <p>请填写真实姓名与基础信息。</p>
      </div>
    </div>
    <div class="section-body">
      <div class="grid-3">
        <label class="field">
          <span>姓名 <em class="required">*</em></span>
          <input v-model.trim="form.name" name="name" type="text" placeholder="真实姓名" />
          <small v-if="errors.name">{{ errors.name }}</small>
        </label>

        <div class="upload-item" :key="fileInputKey" data-error-anchor="photo" tabindex="-1">
          <div class="upload-label">个人照片 <em class="required">*</em></div>
          <label class="upload-control">
            <input
              :key="fileInputKey"
              class="upload-input"
              name="photo"
              type="file"
              accept="image/*"
              @change="$emit('file-change', 'photo', $event)"
            />
            <span class="upload-btn">选择文件</span>
          </label>
          <p class="file-name">{{ attachments.photo?.name || "未选择文件" }}</p>
          <small v-if="errors.photo">{{ errors.photo }}</small>
        </div>

        <label class="field">
          <span>年龄 <em class="required">*</em></span>
          <input v-model.number="form.age" name="age" type="number" min="1" placeholder="周岁" />
          <small v-if="errors.age">{{ errors.age }}</small>
        </label>

        <label class="field">
          <span>性别 <em class="required">*</em></span>
          <select v-model="form.gender" name="gender">
            <option value="">请选择</option>
            <option value="男">男</option>
            <option value="女">女</option>
          </select>
          <small v-if="errors.gender">{{ errors.gender }}</small>
        </label>

        <label class="field">
          <span>身高 (cm) <em class="required">*</em></span>
          <input v-model.number="form.height_cm" name="height_cm" type="number" min="1" />
          <small v-if="errors.height_cm">{{ errors.height_cm }}</small>
        </label>

        <label class="field">
          <span>体重 (kg) <em class="required">*</em></span>
          <input v-model.number="form.weight_kg" name="weight_kg" type="number" min="1" />
          <small v-if="errors.weight_kg">{{ errors.weight_kg }}</small>
        </label>

        <label class="field">
          <span>婚姻情况 <em class="required">*</em></span>
          <select v-model="form.marital_status" name="marital_status">
            <option value="">请选择</option>
            <option value="未婚">未婚</option>
            <option value="已婚">已婚</option>
            <option value="离异">离异</option>
            <option value="丧偶">丧偶</option>
          </select>
          <small v-if="errors.marital_status">{{ errors.marital_status }}</small>
        </label>

        <label class="field">
          <span>籍贯</span>
          <input v-model.trim="form.native_place" type="text" placeholder="省 / 市 / 县" />
        </label>

        <label class="field">
          <span>政治面貌 <em class="required">*</em></span>
          <select v-model="form.political_status" name="political_status">
            <option value="">请选择</option>
            <option value="群众">群众</option>
            <option value="共青团员">共青团员</option>
            <option value="中共党员">中共党员</option>
            <option value="民主党派">民主党派</option>
            <option value="其他">其他</option>
          </select>
          <small v-if="errors.political_status">{{ errors.political_status }}</small>
        </label>

        <label class="field">
          <span>民族 <em class="required">*</em></span>
          <input v-model.trim="form.ethnicity" name="ethnicity" type="text" placeholder="如 汉族" />
          <small v-if="errors.ethnicity">{{ errors.ethnicity }}</small>
        </label>

        <label class="field">
          <span>全日职统招最高学历 <em class="required">*</em></span>
          <select v-model="form.education_level" name="education_level">
            <option value="">请选择</option>
            <option value="初中">初中</option>
            <option value="高中">高中</option>
            <option value="中专">中专</option>
            <option value="大专">大专</option>
            <option value="本科">本科</option>
            <option value="985/211本科">985/211本科</option>
            <option value="硕士">硕士</option>
            <option value="985/211硕士">985/211硕士</option>
            <option value="博士">博士</option>
          </select>
          <small v-if="errors.education_level">{{ errors.education_level }}</small>
        </label>

        <label class="field">
          <span>最高学历入学时间 <em class="required">*</em></span>
          <input v-model="form.education_start" name="education_start" type="month" />
          <small v-if="errors.education_period">{{ errors.education_period }}</small>
        </label>

        <label class="field">
          <span>最高学历毕业时间 <em class="required">*</em></span>
          <input v-model="form.education_end" name="education_end" type="month" />
          <small v-if="errors.education_period">{{ errors.education_period }}</small>
        </label>

        <label class="field">
          <span>身份证号 <em class="required">*</em></span>
          <input v-model.trim="form.id_number" name="id_number" type="text" placeholder="18位身份证号码" />
          <small v-if="errors.id_number">{{ errors.id_number }}</small>
        </label>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  form: { type: Object, required: true },
  errors: { type: Object, default: () => ({}) },
  attachments: { type: Object, required: true },
  fileInputKey: { type: Number, default: 0 },
});
defineEmits(["file-change"]);
</script>
