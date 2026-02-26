<template>
  <!-- 文件说明：面试结果池通用组件，支持岗位筛选、勾选、详情查看与分页。 -->
  <div class="card passed-card">
    <div class="card-header interview-header">
      <div>
        <h3>{{ title }}</h3>
        <p class="header-sub">
          {{ countPrefix }} {{ totalCount }} 人 · 显示 {{ filteredItems.length }} / {{ items.length }} 人
        </p>
      </div>
      <div class="applications-header-actions">
        <span class="chip subtle">已选 {{ selectedCount }} 人</span>
        <button
          v-if="showPrimaryAction"
          :class="['btn', 'btn-sm', primaryActionClass]"
          type="button"
          :disabled="primaryActionDisabled || selectedCount === 0"
          @click="$emit('primary-action')"
        >
          {{ primaryActionLabel }}<span v-if="selectedCount">（{{ selectedCount }}）</span>
        </button>
        <button class="btn btn-sm btn-default" type="button" @click="$emit('refresh')">刷新列表</button>
      </div>
    </div>
    <div class="card-body">
      <div class="application-toolbar">
        <div class="job-tabs">
          <button
            v-for="job in jobCategories"
            :key="job.value"
            class="tab-pill"
            :class="{ active: filters.job === job.value }"
            @click="filters.job = job.value"
          >
            {{ job.label }}
            <span class="tab-count">{{ job.count }}</span>
          </button>
        </div>
        <div class="filter-actions">
          <div v-if="statusOptions.length" class="filter-field">
            <label>状态筛选</label>
            <div class="input-with-icon">
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
                <path d="M3 5h18"></path>
                <path d="M6 12h12"></path>
                <path d="M10 19h4"></path>
              </svg>
              <select v-model="filters[statusFilterKey]">
                <option v-for="item in statusOptions" :key="item.value" :value="item.value">
                  {{ item.label }}（{{ item.count }}）
                </option>
              </select>
            </div>
          </div>
          <button class="btn btn-sm btn-default" type="button" @click="$emit('reset-filters')">重置筛选</button>
        </div>
      </div>
      <div class="passed-scroll">
        <div v-if="filteredItems.length" class="passed-table-wrap">
          <table class="data-table passed-table">
            <thead>
              <tr>
                <th width="6%">
                  <input type="checkbox" v-model="localIsAllVisibleSelected" />
                </th>
                <th>姓名</th>
                <th>岗位</th>
                <th>地区</th>
                <th>手机号</th>
                <th>招聘类型</th>
                <th>学历</th>
                <th>状态</th>
                <th>第一轮</th>
                <th>第一轮评分</th>
                <th>第一轮面试官</th>
                <th>第二轮</th>
                <th>第二轮评分</th>
                <th>第二轮面试官</th>
                <th>第三轮</th>
                <th>第三轮评分</th>
                <th>第三轮面试官</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredItems" :key="item.id">
                <td>
                  <input type="checkbox" :value="item.id" v-model="localSelectedIds" />
                </td>
                <td class="font-medium">
                  <DetailNameButton :label="item.name || ''" @open="$emit('open-detail', item)" />
                </td>
                <td>{{ item.job_title || "-" }}</td>
                <td>{{ item.region_name || "-" }}</td>
                <td>{{ item.phone || "-" }}</td>
                <td>{{ item.recruit_type || "-" }}</td>
                <td>{{ item.education_level || "-" }}</td>
                <td>
                  <span :class="['chip', interviewStatusClass(item)]">{{ interviewStatusText(item) }}</span>
                </td>
                <td>{{ formatTime(item.first_round_at) }}</td>
                <td>{{ item.first_round_score ?? "-" }}</td>
                <td>{{ item.first_round_interviewer || "-" }}</td>
                <td>{{ formatTime(item.second_round_at) }}</td>
                <td>{{ item.second_round_score ?? "-" }}</td>
                <td>{{ item.second_round_interviewer || "-" }}</td>
                <td>{{ formatTime(item.third_round_at) }}</td>
                <td>{{ item.third_round_score ?? "-" }}</td>
                <td>{{ item.third_round_interviewer || "-" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">{{ emptyText }}</div>
      </div>
      <ListPaginationBar
        :pagination="pagination"
        :loading="loading"
        :page-size-options="pageSizeOptions"
        @change-page="$emit('change-page', $event)"
        @change-page-size="$emit('change-page-size', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import DetailNameButton from "./DetailNameButton.vue";
import ListPaginationBar from "./ListPaginationBar.vue";

const emit = defineEmits([
  "refresh",
  "change-page",
  "change-page-size",
  "open-detail",
  "reset-filters",
  "primary-action",
  "update:selected-ids",
  "update:is-all-visible-selected",
]);

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  filteredItems: {
    type: Array,
    default: () => [],
  },
  jobCategories: {
    type: Array,
    default: () => [],
  },
  statusOptions: {
    type: Array,
    default: () => [],
  },
  statusFilterKey: {
    type: String,
    default: "hire_status",
  },
  filters: {
    type: Object,
    required: true,
  },
  interviewStatusClass: {
    type: Function,
    required: true,
  },
  interviewStatusText: {
    type: Function,
    required: true,
  },
  selectedIds: {
    type: Array,
    default: () => [],
  },
  isAllVisibleSelected: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: "面试通过人员",
  },
  countPrefix: {
    type: String,
    default: "已通过",
  },
  emptyText: {
    type: String,
    default: "暂无面试通过人员",
  },
  pagination: {
    type: Object,
    default: () => ({ page: 1, pageSize: 30, count: 0 }),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  pageSizeOptions: {
    type: Array,
    default: () => [],
  },
  showPrimaryAction: {
    type: Boolean,
    default: false,
  },
  primaryActionLabel: {
    type: String,
    default: "",
  },
  primaryActionClass: {
    type: String,
    default: "btn-primary",
  },
  primaryActionDisabled: {
    type: Boolean,
    default: false,
  },
});

const totalCount = computed(() => Math.max(Number(props.pagination?.count || props.items.length), props.items.length));
const selectedCount = computed(() => props.selectedIds.length);

const localSelectedIds = computed({
  get: () => props.selectedIds,
  set: (value) => emit("update:selected-ids", value),
});

const localIsAllVisibleSelected = computed({
  get: () => props.isAllVisibleSelected,
  set: (value) => emit("update:is-all-visible-selected", value),
});

// 列表内统一时间展示
const formatTime = (value) => (value ? new Date(value).toLocaleString() : "-");
</script>
