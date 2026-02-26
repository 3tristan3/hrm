<template>
  <div class="card applications-card">
    <div class="card-header applications-header">
      <div>
        <h3>应聘记录明细</h3>
        <p class="header-sub">显示 {{ filteredApplications.length }} / {{ applications.length }} 条</p>
      </div>
      <div class="applications-header-actions">
        <span class="chip subtle">已选 {{ selectedApplicationsCount }} 人</span>
        <button
          class="btn btn-sm btn-primary"
          type="button"
          :disabled="selectedApplicationsCount === 0"
          @click="onAddSelectedToInterviewPool"
        >
          加入拟面试人员<span v-if="selectedApplicationsCount">（{{ selectedApplicationsCount }}）</span>
        </button>
        <button
          class="btn btn-sm btn-talent"
          type="button"
          :disabled="selectedApplicationsCount === 0"
          @click="onAddSelectedToTalentPool"
        >
          加入人才库<span v-if="selectedApplicationsCount">（{{ selectedApplicationsCount }}）</span>
        </button>
        <button class="btn btn-sm btn-default" type="button" @click="onRefreshApplications">刷新数据</button>
      </div>
    </div>
    <div class="card-body">
      <div class="application-toolbar">
        <div class="job-tabs">
          <button
            v-for="job in jobCategories"
            :key="job.value"
            class="tab-pill"
            :class="{ active: applicationFilters.job === job.value }"
            @click="applicationFilters.job = job.value"
          >
            {{ job.label }}
            <span class="tab-count">{{ job.count }}</span>
          </button>
        </div>
        <div class="filter-actions">
          <div v-if="showRegionFilter" class="filter-field">
            <label>地区筛选</label>
            <div class="input-with-icon">
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
                <circle cx="11" cy="11" r="7"></circle>
                <line x1="16.65" y1="16.65" x2="21" y2="21"></line>
              </svg>
              <select v-model="applicationFilters.region">
                <option value="">全部地区</option>
                <option v-for="item in regions" :key="item.id" :value="item.name">{{ item.name }}</option>
              </select>
            </div>
          </div>
          <button class="btn btn-sm btn-default" @click="onResetApplicationFilters">重置筛选</button>
        </div>
      </div>
      <div class="applications-scroll">
        <div v-if="groupedApplications.length" class="application-groups">
          <section v-for="group in groupedApplications" :key="group.title" class="application-group">
            <div class="group-header">
              <div>
                <h4>{{ group.title }}</h4>
                <p class="text-muted">共 {{ group.items.length }} 条应聘记录</p>
              </div>
              <div class="group-header-actions">
                <button class="btn btn-xs btn-default" type="button" @click="onToggleApplicationGroupSelection(group.items)">
                  {{ onIsApplicationGroupFullySelected(group.items) ? "取消全选" : "全选" }}
                </button>
                <span class="chip subtle">{{ group.items.length }} 条</span>
              </div>
            </div>
            <div class="application-grid">
              <div
                v-for="item in group.items"
                :key="item.id"
                class="application-card"
                :class="{ selected: onIsApplicationSelected(item.id) }"
              >
                <div
                  class="application-card-main"
                  role="button"
                  tabindex="0"
                  @click="onToggleApplicationSelection(item.id)"
                  @keydown.enter.prevent="onToggleApplicationSelection(item.id)"
                  @keydown.space.prevent="onToggleApplicationSelection(item.id)"
                >
                  <div class="card-photo">
                    <img
                      v-if="item.photo_url"
                      :src="resolveMediaUrl(item.photo_url)"
                      alt="个人照片"
                      loading="lazy"
                      decoding="async"
                    />
                    <div v-else class="photo-fallback">{{ item.name ? item.name.slice(0, 1) : "?" }}</div>
                    <span class="card-select-indicator" :class="{ active: onIsApplicationSelected(item.id) }">
                      <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="3" fill="none">
                        <polyline points="20 6 9 17 4 12"></polyline>
                      </svg>
                    </span>
                    <span class="card-pill">{{ item.job_title }}</span>
                  </div>
                  <div class="app-card-body">
                    <div class="card-title-row">
                      <div class="card-name" :title="item.name">{{ item.name }}</div>
                      <span class="card-badge">{{ item.recruit_type || "类型未填写" }}</span>
                    </div>
                    <div class="card-info-grid">
                      <div class="info-item">
                        <span class="info-label">性别</span>
                        <span class="info-value">{{ item.gender || "-" }}</span>
                      </div>
                      <div class="info-item">
                        <span class="info-label">年龄</span>
                        <span class="info-value">{{ item.age ? `${item.age}岁` : "-" }}</span>
                      </div>
                      <div class="info-item">
                        <span class="info-label">手机号</span>
                        <span class="info-value">{{ item.phone || "-" }}</span>
                      </div>
                      <div class="info-item">
                        <span class="info-label">学历</span>
                        <span class="info-value">{{ item.education_level || "-" }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <button class="card-cta" type="button" @click="onOpenApplication(item)">
                  <span>查看详情</span>
                  <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </button>
              </div>
            </div>
          </section>
        </div>
        <div v-else class="empty-state">暂无匹配的应聘记录</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  filteredApplications: {
    type: Array,
    default: () => [],
  },
  applications: {
    type: Array,
    default: () => [],
  },
  selectedApplicationsCount: {
    type: Number,
    default: 0,
  },
  jobCategories: {
    type: Array,
    default: () => [],
  },
  applicationFilters: {
    type: Object,
    required: true,
  },
  showRegionFilter: {
    type: Boolean,
    default: false,
  },
  regions: {
    type: Array,
    default: () => [],
  },
  groupedApplications: {
    type: Array,
    default: () => [],
  },
  resolveMediaUrl: {
    type: Function,
    required: true,
  },
  onAddSelectedToInterviewPool: {
    type: Function,
    required: true,
  },
  onAddSelectedToTalentPool: {
    type: Function,
    required: true,
  },
  onRefreshApplications: {
    type: Function,
    required: true,
  },
  onResetApplicationFilters: {
    type: Function,
    required: true,
  },
  onToggleApplicationGroupSelection: {
    type: Function,
    required: true,
  },
  onIsApplicationGroupFullySelected: {
    type: Function,
    required: true,
  },
  onIsApplicationSelected: {
    type: Function,
    required: true,
  },
  onToggleApplicationSelection: {
    type: Function,
    required: true,
  },
  onOpenApplication: {
    type: Function,
    required: true,
  },
});
</script>
