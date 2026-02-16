// useJobCategoryFilter 文件，封装岗位 tab 与通用筛选逻辑。
import { computed, unref } from "vue";

const normalize = (value) => String(value || "").trim().toLowerCase();

const defaultSortLocale = "zh-Hans-CN";

export const useJobCategoryFilter = (itemsRef, filtersRef, options = {}) => {
  const titleKey = options.titleKey || "job_title";
  const regionKey = options.regionKey || "region_name";
  const allValue = options.allValue || "all";
  const allLabel = options.allLabel || "全部岗位";
  const unknownJobLabel = options.unknownJobLabel || "未填写岗位";
  const regionFilterKey = options.regionFilterKey || "region";
  const jobFilterKey = options.jobFilterKey || "job";
  const keywordFilterKey = options.keywordFilterKey || "keyword";
  const keywordFields = Array.isArray(options.keywordFields) ? options.keywordFields : [];
  const sortLocale = options.sortLocale || defaultSortLocale;

  const regionFilteredItems = computed(() => {
    const source = Array.isArray(unref(itemsRef)) ? unref(itemsRef) : [];
    const filters = unref(filtersRef) || {};
    const regionKeyword = normalize(filters[regionFilterKey]);
    return source.filter((item) => {
      const regionValue = normalize(item?.[regionKey]);
      return !regionKeyword || regionValue === regionKeyword;
    });
  });

  const jobCategories = computed(() => {
    const counts = new Map();
    regionFilteredItems.value.forEach((item) => {
      const title = item?.[titleKey] || unknownJobLabel;
      counts.set(title, (counts.get(title) || 0) + 1);
    });
    const categories = Array.from(counts.entries())
      .map(([title, count]) => ({ label: title, value: title, count }))
      .sort((a, b) => a.label.localeCompare(b.label, sortLocale));
    return [{ label: allLabel, value: allValue, count: regionFilteredItems.value.length }, ...categories];
  });

  const filteredItems = computed(() => {
    const filters = unref(filtersRef) || {};
    const selectedJob = filters[jobFilterKey];
    const keyword = normalize(filters[keywordFilterKey]);
    let result = regionFilteredItems.value;

    if (selectedJob && selectedJob !== allValue) {
      result = result.filter((item) => (item?.[titleKey] || unknownJobLabel) === selectedJob);
    }

    if (!keyword || !keywordFields.length) return result;
    return result.filter((item) =>
      keywordFields.some((field) => normalize(item?.[field]).includes(keyword))
    );
  });

  return {
    regionFilteredItems,
    jobCategories,
    filteredItems,
  };
};

