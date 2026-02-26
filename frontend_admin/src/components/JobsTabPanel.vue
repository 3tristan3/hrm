<template>
  <div class="card job-card">
    <div class="card-header job-header">
      <div>
        <h3>岗位管理</h3>
        <p class="header-sub">维护各地区岗位信息与上架状态</p>
      </div>
      <div class="header-actions">
        <span class="chip">
          {{ hasJobKeyword ? `${filteredJobs.length} / ${jobs.length} 个岗位` : `${jobs.length} 个岗位` }}
        </span>
      </div>
    </div>
    <div class="card-body job-body">
      <div class="job-toolbar">
        <div class="job-toolbar-left">
          <button class="btn btn-sm btn-primary" @click="onOpenNewJob">新增岗位</button>
          <button class="btn btn-sm btn-default" @click="onFetchJobs">刷新列表</button>
        </div>
        <div class="job-toolbar-right">
          <div class="job-search input-with-icon">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
              <circle cx="11" cy="11" r="7"></circle>
              <line x1="16.65" y1="16.65" x2="21" y2="21"></line>
            </svg>
            <input
              v-model.trim="jobFilters.keyword"
              type="text"
              placeholder="搜索岗位名称/地区/职责"
              aria-label="搜索岗位"
            />
          </div>
          <button class="btn btn-sm btn-default" :disabled="!hasJobKeyword" @click="onResetJobFilters">清空</button>
          <span class="chip subtle">已选 {{ selectedJobsCount }} 个</span>
          <button class="btn btn-sm btn-activate" :disabled="!canBatchActivateJobs" @click="onBatchActivateJobs">
            批量上架
          </button>
          <button class="btn btn-sm btn-deactivate" :disabled="!canBatchDeactivateJobs" @click="onBatchDeactivateJobs">
            批量下架
          </button>
          <button class="btn btn-sm btn-danger" :disabled="selectedJobIds.length === 0" @click="onBatchDeleteJobs">
            批量删除
          </button>
        </div>
      </div>

      <div class="job-table-wrap">
        <table class="data-table job-table">
          <thead>
            <tr>
              <th width="6%">
                <input v-model="isAllJobsSelectedModel" type="checkbox" />
              </th>
              <th width="16%">岗位名称</th>
              <th width="12%">地区</th>
              <th width="26%">岗位职责</th>
              <th width="10%">薪资</th>
              <th width="10%">学历</th>
              <th width="10%">状态</th>
              <th width="10%">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredJobs" :key="item.id">
              <td>
                <input v-model="selectedJobIdsModel" type="checkbox" :value="item.id" />
              </td>
              <td class="font-medium">{{ item.title }}</td>
              <td><span class="tag">{{ item.region_name || regionName(item.region) }}</span></td>
              <td>
                <div class="text-truncate" :title="item.description">{{ item.description || "-" }}</div>
              </td>
              <td>{{ item.salary || "-" }}</td>
              <td>{{ item.education || "-" }}</td>
              <td>
                <span class="status-dot" :class="{ active: item.is_active }"></span>
                {{ item.is_active ? "上架" : "下架" }}
              </td>
              <td>
                <a class="action-link" @click="onEditJob(item)">编辑</a>
                <a class="action-link danger" @click="onDeleteJob(item.id)">删除</a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  jobs: {
    type: Array,
    default: () => [],
  },
  filteredJobs: {
    type: Array,
    default: () => [],
  },
  jobFilters: {
    type: Object,
    required: true,
  },
  hasJobKeyword: {
    type: Boolean,
    default: false,
  },
  selectedJobsCount: {
    type: Number,
    default: 0,
  },
  canBatchActivateJobs: {
    type: Boolean,
    default: false,
  },
  canBatchDeactivateJobs: {
    type: Boolean,
    default: false,
  },
  selectedJobIds: {
    type: Array,
    default: () => [],
  },
  isAllJobsSelected: {
    type: Boolean,
    default: false,
  },
  regionName: {
    type: Function,
    required: true,
  },
  onOpenNewJob: {
    type: Function,
    required: true,
  },
  onFetchJobs: {
    type: Function,
    required: true,
  },
  onResetJobFilters: {
    type: Function,
    required: true,
  },
  onBatchActivateJobs: {
    type: Function,
    required: true,
  },
  onBatchDeactivateJobs: {
    type: Function,
    required: true,
  },
  onBatchDeleteJobs: {
    type: Function,
    required: true,
  },
  onEditJob: {
    type: Function,
    required: true,
  },
  onDeleteJob: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits(["update:selected-job-ids", "update:is-all-jobs-selected"]);

const selectedJobIdsModel = computed({
  get: () => props.selectedJobIds,
  set: (value) => emit("update:selected-job-ids", value),
});

const isAllJobsSelectedModel = computed({
  get: () => props.isAllJobsSelected,
  set: (value) => emit("update:is-all-jobs-selected", value),
});
</script>
