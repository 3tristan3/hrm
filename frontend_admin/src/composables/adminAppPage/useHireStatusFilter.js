import { computed, unref } from "vue";

const toArray = (value) => (Array.isArray(unref(value)) ? unref(value) : []);

export const useHireStatusFilter = (itemsRef, filtersRef, options = {}) => {
  const filterKey = options.filterKey || "hire_status";
  const allValue = options.allValue || "all";
  const pendingValue = options.pendingValue || "pending_hire";
  const confirmedValue = options.confirmedValue || "confirmed_hire";
  const allLabel = options.allLabel || "全部状态";
  const pendingLabel = options.pendingLabel || "待确认入职";
  const confirmedLabel = options.confirmedLabel || "已确认入职";

  const filteredItems = computed(() => {
    const list = toArray(itemsRef);
    const filters = unref(filtersRef) || {};
    const selectedStatus = String(filters[filterKey] || allValue);

    if (selectedStatus === pendingValue) {
      return list.filter((item) => !item?.is_hired);
    }
    if (selectedStatus === confirmedValue) {
      return list.filter((item) => Boolean(item?.is_hired));
    }
    return list;
  });

  const statusOptions = computed(() => {
    const list = toArray(itemsRef);
    const confirmed = list.filter((item) => Boolean(item?.is_hired)).length;
    const pending = Math.max(list.length - confirmed, 0);

    return [
      { value: allValue, label: allLabel, count: list.length },
      { value: pendingValue, label: pendingLabel, count: pending },
      { value: confirmedValue, label: confirmedLabel, count: confirmed },
    ];
  });

  return {
    filteredItems,
    statusOptions,
  };
};
