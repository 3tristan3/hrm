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
                  <input
                    type="checkbox"
                    :value="item.id"
                    v-model="localSelectedIds"
                    :disabled="!canSelectItem(item)"
                  />
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
                  <div class="status-cell">
                    <span :class="['chip', interviewStatusClass(item)]">{{ interviewStatusText(item) }}</span>
                    <button
                      v-if="availableStatusActions(item).length"
                      type="button"
                      class="status-action-icon"
                      title="修改状态"
                      @click.stop="toggleStatusMenu(item, $event)"
                    >
                      <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none">
                        <path d="M6 9l6 6 6-6"></path>
                      </svg>
                    </button>
                    <span
                      v-else
                      class="status-action-placeholder"
                      aria-hidden="true"
                    ></span>
                  </div>
                </td>
                <td>{{ formatTime(item.first_round_at) }}</td>
                <td>{{ formatRoundScore(item.first_round_interviewer_scores, item.first_round_score) }}</td>
                <td>{{ formatRoundInterviewer(item.first_round_interviewer_scores, item.first_round_interviewer) }}</td>
                <td>{{ formatTime(item.second_round_at) }}</td>
                <td>{{ formatRoundScore(item.second_round_interviewer_scores, item.second_round_score) }}</td>
                <td>{{ formatRoundInterviewer(item.second_round_interviewer_scores, item.second_round_interviewer) }}</td>
                <td>{{ formatTime(item.third_round_at) }}</td>
                <td>{{ formatRoundScore(item.third_round_interviewer_scores, item.third_round_score) }}</td>
                <td>{{ formatRoundInterviewer(item.third_round_interviewer_scores, item.third_round_interviewer) }}</td>
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
  <teleport to="body">
    <div
      v-if="activeStatusMenuItem"
      ref="statusMenuRef"
      class="status-action-menu status-action-menu-floating"
      :style="statusMenuStyle"
      @click.stop
    >
      <button
        v-for="option in availableStatusActions(activeStatusMenuItem)"
        :key="`${activeStatusMenuItem.id}-${option.value}`"
        type="button"
        class="status-action-menu-item"
        @click.stop="onChangeStatus(activeStatusMenuItem, option.value)"
      >
        {{ option.label }}
      </button>
    </div>
  </teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";
import DetailNameButton from "./DetailNameButton.vue";
import ListPaginationBar from "./ListPaginationBar.vue";
import { useFloatingActionMenu } from "../composables/useFloatingActionMenu";
import {
  getAvailableOfferStatusActions,
} from "../utils/offerStatusTransition";

const emit = defineEmits([
  "refresh",
  "change-page",
  "change-page-size",
  "open-detail",
  "reset-filters",
  "primary-action",
  "change-status",
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
  statusActionOptions: {
    type: Array,
    default: () => [],
  },
  isItemSelectable: {
    type: Function,
    default: null,
  },
});

const totalCount = computed(() => Math.max(Number(props.pagination?.count || props.items.length), props.items.length));
const selectedCount = computed(() => props.selectedIds.length);

const canSelectItem = (item) => {
  if (typeof props.isItemSelectable !== "function") return true;
  return Boolean(props.isItemSelectable(item));
};

const visibleIds = computed(() =>
  (Array.isArray(props.filteredItems) ? props.filteredItems : [])
    .map((item) => item?.id)
    .filter((id) => Number.isFinite(Number(id)))
);

const selectableVisibleIds = computed(() =>
  (Array.isArray(props.filteredItems) ? props.filteredItems : [])
    .filter((item) => canSelectItem(item))
    .map((item) => item?.id)
    .filter((id) => Number.isFinite(Number(id)))
);

const localSelectedIds = computed({
  get: () => {
    const blockedVisibleSet = new Set(
      (Array.isArray(props.filteredItems) ? props.filteredItems : [])
        .filter((item) => !canSelectItem(item))
        .map((item) => item?.id)
    );
    return (Array.isArray(props.selectedIds) ? props.selectedIds : []).filter(
      (id) => !blockedVisibleSet.has(id)
    );
  },
  set: (value) => {
    const nextValue = Array.isArray(value) ? value : [];
    const visibleSet = new Set(visibleIds.value);
    const selectableSet = new Set(selectableVisibleIds.value);
    const preservedNonVisible = (Array.isArray(props.selectedIds) ? props.selectedIds : []).filter(
      (id) => !visibleSet.has(id)
    );
    const normalizedVisible = nextValue.filter((id) => selectableSet.has(id));
    emit("update:selected-ids", Array.from(new Set([...preservedNonVisible, ...normalizedVisible])));
  },
});

const localIsAllVisibleSelected = computed({
  get: () => {
    const selectableIds = selectableVisibleIds.value;
    if (!selectableIds.length) return false;
    const selectedSet = new Set(localSelectedIds.value);
    return selectableIds.every((id) => selectedSet.has(id));
  },
  set: (value) => {
    const visibleSet = new Set(visibleIds.value);
    const preservedNonVisible = (Array.isArray(props.selectedIds) ? props.selectedIds : []).filter(
      (id) => !visibleSet.has(id)
    );
    if (!value) {
      emit("update:selected-ids", preservedNonVisible);
      return;
    }
    emit(
      "update:selected-ids",
      Array.from(new Set([...preservedNonVisible, ...selectableVisibleIds.value]))
    );
  },
});

const findItemById = (candidateId) =>
  props.filteredItems.find((item) => item?.id === candidateId) ||
  props.items.find((item) => item?.id === candidateId) ||
  null;

const {
  activeMenuItem: activeStatusMenuItem,
  menuRef: statusMenuRef,
  menuStyle: statusMenuStyle,
  closeMenu: closeStatusMenu,
  toggleMenuById,
  bindGlobalClickClose,
  unbindGlobalClickClose,
} = useFloatingActionMenu({
  findItemById,
  estimatedWidth: 132,
  offsetY: 6,
});

const availableStatusActions = (item) =>
  getAvailableOfferStatusActions(item, props.statusActionOptions);

const toggleStatusMenu = (item, event) => {
  toggleMenuById(item?.id, event);
};

const onChangeStatus = (item, nextStatus) => {
  closeStatusMenu();
  emit("change-status", { item, nextStatus });
};

// 列表内统一时间展示
const formatTime = (value) => (value ? new Date(value).toLocaleString() : "-");

const normalizeScoreRows = (rows = []) =>
  (rows || [])
    .map((row) => ({
      interviewer: String(row?.interviewer || "").trim(),
      score: row?.score,
    }))
    .filter(
      (row) =>
        row.interviewer &&
        Number.isInteger(Number(row.score)) &&
        Number(row.score) >= 0 &&
        Number(row.score) <= 100
    )
    .map((row) => ({ interviewer: row.interviewer, score: Number(row.score) }));

const formatRoundScore = (rows, fallbackScore) => {
  const normalizedRows = normalizeScoreRows(rows);
  if (normalizedRows.length) {
    return normalizedRows.map((row) => `${row.interviewer}:${row.score}`).join(" / ");
  }
  return fallbackScore ?? "-";
};

const formatRoundInterviewer = (rows, fallbackInterviewer) => {
  const normalizedRows = normalizeScoreRows(rows);
  if (normalizedRows.length) {
    return normalizedRows.map((row) => row.interviewer).join("、");
  }
  return fallbackInterviewer || "-";
};

onMounted(() => {
  bindGlobalClickClose();
});

onBeforeUnmount(() => {
  unbindGlobalClickClose();
});
</script>
