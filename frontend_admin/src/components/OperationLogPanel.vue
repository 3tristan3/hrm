<template>
  <div class="card operation-log-card">
    <div class="card-header op-header">
      <div>
        <h3>操作日志</h3>
        <p class="header-sub">审计轨迹</p>
      </div>
      <div class="op-header-metrics">
        <span class="chip chip-subtle">当前页 {{ operationLogs.length }} 条</span>
        <span class="chip chip-pass">成功 {{ operationLogSuccessCount }}</span>
        <span class="chip chip-reject">失败 {{ operationLogFailedCount }}</span>
        <button class="btn btn-sm btn-default" type="button" @click="onRefresh">刷新数据</button>
      </div>
    </div>
    <div class="card-body op-body">
      <div class="op-filter-panel">
        <div class="filter-actions log-filters">
          <div class="filter-field">
            <label>模块</label>
            <div class="op-field-control">
              <select v-model="operationLogFilters.module">
                <option value="">全部模块</option>
                <option v-for="item in operationModuleOptions" :key="item.value" :value="item.value">
                  {{ item.label }}
                </option>
              </select>
            </div>
          </div>
          <div class="filter-field">
            <label>操作人</label>
            <div class="op-field-control">
              <input
                v-model.trim="operationLogFilters.operator"
                type="text"
                placeholder="输入账号名"
                @keyup.enter="onSearch"
              />
            </div>
          </div>
          <div class="filter-field">
            <label>开始日期</label>
            <div class="op-field-control">
              <input v-model="operationLogFilters.date_from" type="date" />
            </div>
          </div>
          <div class="filter-field">
            <label>结束日期</label>
            <div class="op-field-control">
              <input v-model="operationLogFilters.date_to" type="date" />
            </div>
          </div>
          <div class="filter-field op-search-actions">
            <button class="btn btn-sm btn-primary" type="button" @click="onSearch">查询</button>
            <button class="btn btn-sm btn-default" type="button" @click="handleResetAndSearch">
              重置
            </button>
          </div>
        </div>
      </div>
      <div class="op-table-wrap">
        <table class="data-table passed-table operation-log-table">
          <thead>
            <tr>
              <th width="16%">时间</th>
              <th width="10%">操作人</th>
              <th width="11%">模块</th>
              <th width="14%">动作</th>
              <th width="13%">对象</th>
              <th width="8%">结果</th>
              <th width="28%">摘要</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in operationLogs"
              :key="item.id"
              class="op-row"
              :class="{ failed: item.result === 'failed' }"
            >
              <td>{{ formatTime(item.created_at) }}</td>
              <td>{{ item.operator_username || "-" }}</td>
              <td>
                <span class="op-module-tag" :class="`mod-${item.module || 'default'}`">
                  {{ operationModuleLabel(item.module) }}
                </span>
              </td>
              <td>
                <span class="op-action-text">{{ operationActionLabel(item.action) }}</span>
              </td>
              <td class="font-medium">{{ item.target_label || "-" }}</td>
              <td>
                <span class="chip" :class="operationResultClass(item.result)">
                  {{ operationResultLabel(item.result) }}
                </span>
              </td>
              <td class="log-summary-cell">
                <div class="log-summary-main">{{ item.summary || "-" }}</div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="!operationLogs.length && !loading" class="empty-state">暂无操作日志</div>
      </div>
      <div v-if="operationLogsQueried" class="list-pagination op-pagination">
        <div class="pagination-meta">第 {{ operationLogPagination.page }} 页</div>
        <div class="op-pagination-right">
          <div class="op-page-size">
            <span>每页</span>
            <select :value="operationLogPagination.pageSize" @change="onChangePageSize($event.target.value)">
              <option v-for="size in operationLogPageSizeOptions" :key="size" :value="size">
                {{ size }}
              </option>
            </select>
          </div>
          <div class="pagination-actions">
            <button
              class="btn btn-xs btn-default"
              type="button"
              :disabled="operationLogPagination.page <= 1"
              @click="onChangePage('previous')"
            >
              上一页
            </button>
            <button
              v-for="item in operationLogPageItems"
              :key="item.key"
              class="op-page-btn"
              :class="{ active: item.type === 'page' && item.value === operationLogPagination.page }"
              type="button"
              :disabled="item.type !== 'page' || (item.value !== 1 && typeof operationLogPageCursorMap[item.value] !== 'string')"
              @click="item.type === 'page' && onChangePage(item.value)"
            >
              {{ item.type === "page" ? item.value : "..." }}
            </button>
            <button
              class="btn btn-xs btn-default"
              type="button"
              :disabled="!operationLogPagination.next"
              @click="onChangePage('next')"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  operationLogs: {
    type: Array,
    default: () => [],
  },
  operationLogSuccessCount: {
    type: Number,
    default: 0,
  },
  operationLogFailedCount: {
    type: Number,
    default: 0,
  },
  operationModuleOptions: {
    type: Array,
    default: () => [],
  },
  operationLogFilters: {
    type: Object,
    required: true,
  },
  operationLogsQueried: {
    type: Boolean,
    default: false,
  },
  operationLogPagination: {
    type: Object,
    required: true,
  },
  operationLogPageSizeOptions: {
    type: Array,
    default: () => [],
  },
  operationLogPageItems: {
    type: Array,
    default: () => [],
  },
  operationLogPageCursorMap: {
    type: Object,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  onRefresh: {
    type: Function,
    required: true,
  },
  onSearch: {
    type: Function,
    required: true,
  },
  onResetFilters: {
    type: Function,
    required: true,
  },
  onChangePageSize: {
    type: Function,
    required: true,
  },
  onChangePage: {
    type: Function,
    required: true,
  },
  formatTime: {
    type: Function,
    required: true,
  },
  operationModuleLabel: {
    type: Function,
    required: true,
  },
  operationActionLabel: {
    type: Function,
    required: true,
  },
  operationResultClass: {
    type: Function,
    required: true,
  },
  operationResultLabel: {
    type: Function,
    required: true,
  },
});

const handleResetAndSearch = () => {
  props.onResetFilters();
  props.onSearch();
};
</script>
