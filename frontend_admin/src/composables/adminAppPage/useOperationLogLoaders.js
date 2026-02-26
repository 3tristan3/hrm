import { cursorFromLink, withQuery } from "../../api/client";
import { LIST_PAGE_SIZE } from "../../utils/pagination";
import { normalizeOperationLogMeta } from "../../constants/operationLog";

export function createOperationLogLoaders({
  request,
  adminBase,
  notifyError,
  operationLogMeta,
  operationLogPageSizeOptions,
  operationLogPagination,
  operationLogFilters,
  operationLogs,
  operationLogPageCursorMap,
  operationLogsQueried,
  dataLoaded,
  dataLoading,
  applicationOperationLogs,
  applicationLogsLoading,
}) {
  const loadOperationLogMeta = async (force = false) => {
    if (operationLogMeta.loaded && !force) return;
    try {
      const payload = await request(`${adminBase}/operation-logs/meta/`);
      const normalized = normalizeOperationLogMeta(payload);
      operationLogMeta.module_labels = normalized.module_labels;
      operationLogMeta.action_labels = normalized.action_labels;
      operationLogMeta.result_labels = normalized.result_labels;
      operationLogMeta.page_size_options = normalized.page_size_options;
      operationLogMeta.default_recent_days = normalized.default_recent_days;
      operationLogMeta.pagination_mode = normalized.pagination_mode;
      const availableSizes = operationLogPageSizeOptions.value;
      if (!availableSizes.includes(Number(operationLogPagination.pageSize))) {
        operationLogPagination.pageSize = availableSizes[0] || LIST_PAGE_SIZE;
      }
    } catch (err) {
      notifyError(err);
    } finally {
      operationLogMeta.loaded = true;
    }
  };

  const loadOperationLogs = async (force = false, cursor = "", page = 1) => {
    if (dataLoading.operationLogs) return;
    const targetCursor = String(cursor || "");
    if (
      !force &&
      dataLoaded.operationLogs &&
      targetCursor === String(operationLogPagination.cursor || "")
    ) {
      return;
    }
    operationLogsQueried.value = true;
    dataLoading.operationLogs = true;
    try {
      const payload = await request(
        withQuery(`${adminBase}/operation-logs/`, {
          page_size: operationLogPagination.pageSize,
          cursor: targetCursor,
          ...operationLogFilters,
        })
      );
      operationLogs.value = Array.isArray(payload?.results)
        ? payload.results
        : Array.isArray(payload)
          ? payload
          : [];
      const targetPage = Math.max(Number(page || 1), 1);
      operationLogPagination.page = targetPage;
      operationLogPagination.next = payload?.next || "";
      operationLogPagination.previous = payload?.previous || "";
      operationLogPagination.cursor = targetCursor;
      operationLogPageCursorMap.value[targetPage] = targetCursor;
      const previousCursor = cursorFromLink(payload?.previous || "");
      if (targetPage > 1 && previousCursor) {
        operationLogPageCursorMap.value[targetPage - 1] = previousCursor;
      }
      const nextCursor = cursorFromLink(payload?.next || "");
      if (nextCursor) {
        operationLogPageCursorMap.value[targetPage + 1] = nextCursor;
      } else {
        Object.keys(operationLogPageCursorMap.value).forEach((key) => {
          const keyNum = Number(key);
          if (Number.isFinite(keyNum) && keyNum > targetPage) {
            delete operationLogPageCursorMap.value[keyNum];
          }
        });
      }
      dataLoaded.operationLogs = true;
    } catch (err) {
      notifyError(err);
    } finally {
      dataLoading.operationLogs = false;
    }
  };

  const loadApplicationOperationLogs = async (applicationId) => {
    if (!applicationId) {
      applicationOperationLogs.value = [];
      return;
    }
    await loadOperationLogMeta();
    applicationLogsLoading.value = true;
    try {
      const payload = await request(
        withQuery(`${adminBase}/operation-logs/`, {
          application_id: applicationId,
          page: 1,
          page_size: 20,
        })
      );
      applicationOperationLogs.value = Array.isArray(payload?.results)
        ? payload.results
        : Array.isArray(payload)
          ? payload
          : [];
    } catch (err) {
      notifyError(err);
      applicationOperationLogs.value = [];
    } finally {
      applicationLogsLoading.value = false;
    }
  };

  return {
    loadOperationLogMeta,
    loadOperationLogs,
    loadApplicationOperationLogs,
  };
}
