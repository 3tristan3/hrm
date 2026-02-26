<template>
  <InterviewPassedCard
    :items="items"
    :filtered-items="filteredItems"
    :job-categories="jobCategories"
    :status-options="statusOptions"
    :filters="filters"
    :interview-status-class="interviewStatusClass"
    :interview-status-text="interviewStatusText"
    :selected-ids="selectedIds"
    :is-all-visible-selected="isAllVisibleSelected"
    title="面试通过人员"
    count-prefix="已通过"
    empty-text="暂无面试通过人员"
    :show-primary-action="true"
    primary-action-label="确认入职"
    primary-action-class="btn-confirm-hire"
    :primary-action-disabled="selectedIds.length === 0"
    :pagination="pagination"
    :page-size-options="pageSizeOptions"
    :loading="loading"
    @refresh="$emit('refresh')"
    @primary-action="$emit('primary-action')"
    @reset-filters="$emit('reset-filters')"
    @open-detail="$emit('open-detail', $event)"
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
  statusOptions: { type: Array, default: () => [] },
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
  "primary-action",
  "reset-filters",
  "open-detail",
  "update:selected-ids",
  "update:is-all-visible-selected",
  "change-page",
  "change-page-size",
]);
</script>
