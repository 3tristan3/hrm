import { computed, unref } from "vue";

const toArray = (value) => (Array.isArray(unref(value)) ? unref(value) : []);

export const useHireStatusFilter = (itemsRef, filtersRef, options = {}) => {
  const filterKey = options.filterKey || "hire_status";
  const allValue = options.allValue || "all";
  const pendingValue = options.pendingValue || "pending_hire";
  const confirmedValue = options.confirmedValue || "confirmed_hire";
  const allLabel = options.allLabel || "全部状态";
  const pendingLabel = options.pendingLabel || "待发offer";
  const confirmedLabel = options.confirmedLabel || "已发offer";
  const statusLabelMap = {
    [pendingValue]: pendingLabel,
    [confirmedValue]: confirmedLabel,
    ...(options.statusLabelMap || {}),
  };
  const resolveStatus =
    typeof options.resolveStatus === "function"
      ? options.resolveStatus
      : (item) => (item?.is_hired ? confirmedValue : pendingValue);

  const normalizeStatus = (item) => String(resolveStatus(item) || "").trim();

  const statusCounts = computed(() => {
    const counter = new Map();
    toArray(itemsRef).forEach((item) => {
      const status = normalizeStatus(item);
      if (!status) return;
      counter.set(status, (counter.get(status) || 0) + 1);
    });
    return counter;
  });

  const sortByLabels = options.sortByLabels !== false;
  const statusSortLocale = options.statusSortLocale || "zh-Hans-CN";

  const sortOptions = (items) => {
    if (!sortByLabels) return items;
    return items.sort((a, b) =>
      String(a.label || a.value).localeCompare(
        String(b.label || b.value),
        statusSortLocale
      )
    );
  };

  const resolveStatusLabel = (value) => {
    if (statusLabelMap[value]) return statusLabelMap[value];
    return value;
  };

  const resolveStatusOptions = () => {
    const dynamic = [];
    statusCounts.value.forEach((count, value) => {
      if (count <= 0) return;
      dynamic.push({
        value,
        label: resolveStatusLabel(value),
        count,
      });
    });
    return sortOptions(dynamic);
  };

  const totalCount = computed(() =>
    Array.from(statusCounts.value.values()).reduce((sum, value) => sum + Number(value || 0), 0)
  );

  const statusOptions = computed(() => {
    const dynamicOptions = resolveStatusOptions();
    return [
      { value: allValue, label: allLabel, count: totalCount.value },
      ...dynamicOptions,
    ];
  });

  const guardedFilteredItems = computed(() => {
    const list = toArray(itemsRef);
    const filters = unref(filtersRef) || {};
    const selectedStatus = String(filters[filterKey] || allValue);
    if (selectedStatus === allValue) return list;
    const existsInList = list.some((item) => normalizeStatus(item) === selectedStatus);
    if (!existsInList) return list;
    return list.filter((item) => normalizeStatus(item) === selectedStatus);
  });

  return {
    filteredItems: guardedFilteredItems,
    statusOptions,
  };
};
