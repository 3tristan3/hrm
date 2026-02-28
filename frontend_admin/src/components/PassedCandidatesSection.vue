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
    title="面试通过人员"
    count-prefix="已通过"
    empty-text="暂无面试通过人员"
    :show-primary-action="true"
    primary-action-label="发放offer"
    primary-action-class="btn-confirm-hire"
    :primary-action-disabled="!hasConfirmHireEligibleSelection"
    :show-secondary-action="true"
    secondary-action-label="确认入职"
    secondary-action-class="btn-onboard"
    :secondary-action-disabled="!hasConfirmOnboardEligibleSelection"
    :pagination="pagination"
    :page-size-options="pageSizeOptions"
    :loading="loading"
    @refresh="$emit('refresh')"
    @primary-action="$emit('primary-action')"
    @secondary-action="$emit('secondary-action')"
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
import { computed } from "vue";
import InterviewPassedCard from "./InterviewPassedCard.vue";
import {
  canConfirmHireByOfferStatus,
  canConfirmOnboardByOfferStatus,
} from "../utils/offerStatusTransition";

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

const selectedCandidateMap = computed(() => {
  const source = Array.isArray(props.items) ? props.items : [];
  return new Map(source.map((item) => [item?.id, item]));
});

const selectedCandidates = computed(() =>
  (Array.isArray(props.selectedIds) ? props.selectedIds : [])
    .map((id) => selectedCandidateMap.value.get(id))
    .filter(Boolean)
);

const hasConfirmHireEligibleSelection = computed(() =>
  selectedCandidates.value.some((item) => canConfirmHireByOfferStatus(item))
);

const hasConfirmOnboardEligibleSelection = computed(() =>
  selectedCandidates.value.some((item) => canConfirmOnboardByOfferStatus(item))
);

defineEmits([
  "refresh",
  "primary-action",
  "secondary-action",
  "change-status",
  "reset-filters",
  "open-detail",
  "update:selected-ids",
  "update:is-all-visible-selected",
  "change-page",
  "change-page-size",
]);
</script>
