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
    :status-action-options="statusActionOptions"
    :is-item-selectable="isPendingHireStatus"
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
    @change-status="$emit('change-status', $event)"
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
import { canConfirmHireByOfferStatus } from "../utils/offerStatusTransition";

const props = defineProps({
  items: { type: Array, default: () => [] },
  filteredItems: { type: Array, default: () => [] },
  jobCategories: { type: Array, default: () => [] },
  statusOptions: { type: Array, default: () => [] },
  filters: { type: Object, required: true },
  interviewStatusClass: { type: Function, required: true },
  interviewStatusText: { type: Function, required: true },
  selectedIds: { type: Array, default: () => [] },
  isAllVisibleSelected: { type: Boolean, default: false },
  statusActionOptions: { type: Array, default: () => [] },
  pagination: { type: Object, required: true },
  pageSizeOptions: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

const isPendingHireStatus = (item) => {
  const candidateId = Number(item?.id || 0);
  if (!Number.isFinite(candidateId) || candidateId <= 0) return false;
  const target =
    props.filteredItems.find((row) => row?.id === candidateId) ||
    props.items.find((row) => row?.id === candidateId) ||
    item;
  return canConfirmHireByOfferStatus(target);
};

defineEmits([
  "refresh",
  "primary-action",
  "change-status",
  "reset-filters",
  "open-detail",
  "update:selected-ids",
  "update:is-all-visible-selected",
  "change-page",
  "change-page-size",
]);
</script>
