// 通用分页工具：封装分页状态、结果归一化和重置逻辑。
export const LIST_PAGE_SIZE = 30;

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
