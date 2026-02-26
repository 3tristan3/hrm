<template>
  <InterviewPassedCard
    :items="items"
    :filtered-items="filteredItems"
    :job-categories="jobCategories"
    :filters="filters"
    :interview-status-class="interviewStatusClass"
    :interview-status-text="interviewStatusText"
    :selected-ids="selectedIds"
    :is-all-visible-selected="isAllVisibleSelected"
    title="人才库"
    count-prefix="已入库"
    empty-text="暂无人才库人员"
    :show-primary-action="true"
    primary-action-label="加入拟面试人员"
    primary-action-class="btn-primary"
    :primary-action-disabled="selectedIds.length === 0"
    :pagination="pagination"
    :page-size-options="pageSizeOptions"
    :loading="loading"
    @refresh="$emit('refresh')"
    @reset-filters="$emit('reset-filters')"
    @open-detail="$emit('open-detail', $event)"
    @primary-action="$emit('primary-action')"
    @update:selected-ids="$emit('update:selected-ids', $event)"
    @update:is-all-visible-selected="$emit('update:is-all-visible-selected', $event)"
    @change-page="$emit('change-page', $event)"
    @change-page-size="$emit('change-page-size', $event)"
  />
</template>

<script setup>
import InterviewPassedCard from "./InterviewPassedCard.vue";

defineProps({
  items: { type: Array, default: () => [] },
  filteredItems: { type: Array, default: () => [] },
  jobCategories: { type: Array, default: () => [] },
  filters: { type: Object, required: true },
  interviewStatusClass: { type: Function, required: true },
  interviewStatusText: { type: Function, required: true },
  selectedIds: { type: Array, default: () => [] },
  isAllVisibleSelected: { type: Boolean, default: false },
  pagination: { type: Object, required: true },
  pageSizeOptions: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

defineEmits([
  "refresh",
  "reset-filters",
  "open-detail",
  "primary-action",
  "update:selected-ids",
  "update:is-all-visible-selected",
  "change-page",
  "change-page-size",
]);
</script>
