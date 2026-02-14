// useSelectionState 文件，统一列表勾选统计与“当前可见项全选”逻辑。
import { computed, unref } from "vue";

const isValidId = (value) => typeof value === "number" || typeof value === "string";

export const useSelectionState = (selectedIdsRef, visibleItemsRef, options = {}) => {
  const idKey = options.idKey || "id";

  const selectedCount = computed(() => {
    const ids = unref(selectedIdsRef);
    return Array.isArray(ids) ? ids.length : 0;
  });

  const visibleIds = computed(() => {
    const items = unref(visibleItemsRef);
    if (!Array.isArray(items)) return [];
    return items.map((item) => item?.[idKey]).filter(isValidId);
  });

  const isAllVisibleSelected = computed({
    get() {
      const visible = visibleIds.value;
      if (!visible.length) return false;
      const selected = Array.isArray(unref(selectedIdsRef)) ? unref(selectedIdsRef) : [];
      return visible.every((id) => selected.includes(id));
    },
    set(value) {
      const visible = visibleIds.value;
      if (!visible.length) return;

      const selected = Array.isArray(unref(selectedIdsRef)) ? [...unref(selectedIdsRef)] : [];
      if (value) {
        selectedIdsRef.value = Array.from(new Set([...selected, ...visible]));
        return;
      }
      const visibleSet = new Set(visible);
      selectedIdsRef.value = selected.filter((id) => !visibleSet.has(id));
    },
  });

  return {
    selectedCount,
    visibleIds,
    isAllVisibleSelected,
  };
};
