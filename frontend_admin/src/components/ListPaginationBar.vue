<template>
  <div v-if="showPagination" class="list-pagination op-pagination">
    <div class="pagination-meta">
      第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ totalCount }} 条
    </div>
    <div class="op-pagination-right">
      <label v-if="showPageSize" class="op-page-size">
        每页
        <select
          :value="pageSize"
          :disabled="loading"
          @change="$emit('change-page-size', Number($event.target.value || pageSize))"
        >
          <option v-for="size in normalizedPageSizeOptions" :key="size" :value="size">
            {{ size }}
          </option>
        </select>
        条
      </label>
      <div class="pagination-actions">
        <button
          class="op-page-btn"
          type="button"
          :disabled="loading || !canPrev"
          @click="$emit('change-page', currentPage - 1)"
        >
          上一页
        </button>
        <button
          v-for="item in pageItems"
          :key="item.key"
          class="op-page-btn"
          type="button"
          :disabled="loading || item.type === 'ellipsis'"
          :class="{ active: item.type === 'page' && item.value === currentPage }"
          @click="
            item.type === 'page' && item.value !== currentPage
              ? $emit('change-page', item.value)
              : null
          "
        >
          {{ item.type === "ellipsis" ? "..." : item.value }}
        </button>
        <button
          class="op-page-btn"
          type="button"
          :disabled="loading || !canNext"
          @click="$emit('change-page', currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { buildPageItems, LIST_PAGE_SIZE, LIST_PAGE_SIZE_OPTIONS } from "../utils/pagination";

const props = defineProps({
  pagination: {
    type: Object,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  pageSizeOptions: {
    type: Array,
    default: () => LIST_PAGE_SIZE_OPTIONS,
  },
  showPageSize: {
    type: Boolean,
    default: true,
  },
});

defineEmits(["change-page", "change-page-size"]);

const pageSize = computed(() => Math.max(Number(props.pagination?.pageSize || LIST_PAGE_SIZE), 1));
const totalCount = computed(() => Math.max(Number(props.pagination?.count || 0), 0));
const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)));
const currentPage = computed(() => {
  const page = Math.max(Number(props.pagination?.page || 1), 1);
  return Math.min(page, totalPages.value);
});
const canPrev = computed(() => currentPage.value > 1);
const canNext = computed(() => currentPage.value < totalPages.value);
const showPagination = computed(() => true);
const pageItems = computed(() => buildPageItems(currentPage.value, totalPages.value));
const normalizedPageSizeOptions = computed(() => {
  const source = Array.isArray(props.pageSizeOptions) && props.pageSizeOptions.length
    ? props.pageSizeOptions
    : LIST_PAGE_SIZE_OPTIONS;
  return source
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value) && value > 0);
});
</script>
