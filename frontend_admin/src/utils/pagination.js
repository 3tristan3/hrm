// 通用分页工具：封装分页状态、结果归一化和重置逻辑。
export const LIST_PAGE_SIZE = 30;
export const LIST_PAGE_SIZE_OPTIONS = Object.freeze([30, 50, 100]);

export const createPageState = () => ({
  page: 1,
  pageSize: LIST_PAGE_SIZE,
  count: 0,
  next: "",
  previous: "",
});

const isPaginatedPayload = (payload) =>
  Boolean(payload && typeof payload === "object" && Array.isArray(payload.results));

export const applyListPagePayload = (state, payload, requestedPage = 1) => {
  if (isPaginatedPayload(payload)) {
    state.page = Math.max(Number(requestedPage || 1), 1);
    state.count = Number(payload.count || 0);
    state.next = payload.next || "";
    state.previous = payload.previous || "";
    return payload.results;
  }
  state.page = 1;
  state.count = Array.isArray(payload) ? payload.length : 0;
  state.next = "";
  state.previous = "";
  return Array.isArray(payload) ? payload : [];
};

export const resetPageState = (state) => {
  state.page = 1;
  state.count = 0;
  state.next = "";
  state.previous = "";
};

export const buildPageItems = (currentPage, totalPages) => {
  const current = Math.max(Number(currentPage || 1), 1);
  const total = Math.max(Number(totalPages || 1), 1);
  if (total <= 7) {
    return Array.from({ length: total }, (_, index) => ({
      type: "page",
      value: index + 1,
      key: `page-${index + 1}`,
    }));
  }

  const pageSet = new Set([1, total, current - 1, current, current + 1]);
  if (current <= 3) [2, 3, 4].forEach((page) => pageSet.add(page));
  if (current >= total - 2) {
    [total - 1, total - 2, total - 3].forEach((page) => pageSet.add(page));
  }

  const sortedPages = Array.from(pageSet)
    .filter((page) => page >= 1 && page <= total)
    .sort((a, b) => a - b);

  const items = [];
  sortedPages.forEach((page, index) => {
    const previousPage = sortedPages[index - 1];
    if (index > 0 && page - previousPage > 1) {
      items.push({
        type: "ellipsis",
        key: `ellipsis-${previousPage}-${page}`,
      });
    }
    items.push({
      type: "page",
      value: page,
      key: `page-${page}`,
    });
  });
  return items;
};
