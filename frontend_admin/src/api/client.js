// 管理端 API 客户端工具：封装错误解析、鉴权请求和常用 URL 参数处理。
export const errorCodeMessageMap = Object.freeze({
  INTERVIEW_FLOW_CLOSED: "当前面试流程已结束，无法继续安排",
  INTERVIEW_NOT_SCHEDULED: "当前未安排面试",
  INTERVIEW_NOT_SCHEDULED_FOR_RESULT: "请先安排面试后再记录结果",
  INTERVIEW_ROUND_LIMIT_REACHED: "当前已是最后一轮，不能再进入下一轮",
});

export const extractErrorMessage = (payload) => {
  if (!payload || typeof payload !== "object") return "请求失败";
  if (payload.details) {
    if (typeof payload.details === "string") return payload.details;
    const detailKeys = Object.keys(payload.details);
    if (detailKeys.length) {
      const val = payload.details[detailKeys[0]];
      if (Array.isArray(val) && val.length) return val[0];
      if (typeof val === "string") return val;
    }
  }
  if (payload.detail) return payload.detail;
  if (payload.error) return payload.error;
  const keys = Object.keys(payload);
  if (keys.length) {
    const val = payload[keys[0]];
    if (Array.isArray(val) && val.length) return val[0];
    if (typeof val === "string") return val;
  }
  return "请求失败";
};

export const createApiError = (payload, fallback = "请求失败") => {
  const error = new Error(extractErrorMessage(payload) || fallback);
  error.code = payload?.error_code || "";
  error.payload = payload;
  return error;
};

export const resolveErrorCodeMessage = (code) =>
  (code ? errorCodeMessageMap[code] : "") || "";

const isJsonResponse = (response) =>
  String(response?.headers?.get("content-type") || "")
    .toLowerCase()
    .includes("application/json");

const buildNonJsonErrorPayload = (response, text) => {
  const compact = String(text || "").replace(/\s+/g, " ").trim();
  const snippet = compact.slice(0, 120);
  return {
    detail: `接口返回非 JSON 响应（HTTP ${response.status}）`,
    raw: snippet || "",
  };
};

export const createRequest = (getToken) => async (url, options = {}) => {
  const headers = { "Content-Type": "application/json" };
  const currentToken = typeof getToken === "function" ? getToken() : "";
  if (currentToken) headers.Authorization = `Token ${currentToken}`;

  const response = await fetch(url, { headers, ...options });
  const text = await response.text();
  const hasBody = Boolean(String(text || "").trim());
  const canParseJson = isJsonResponse(response) && hasBody;

  if (!response.ok) {
    let payload = {};
    if (canParseJson) {
      try {
        payload = JSON.parse(text);
      } catch {
        payload = {
          detail: `接口返回了无效 JSON（HTTP ${response.status}）`,
        };
      }
    } else if (hasBody) {
      payload = buildNonJsonErrorPayload(response, text);
    }
    throw createApiError(payload);
  }

  if (response.status === 204 || !hasBody) return {};
  if (!canParseJson) {
    throw createApiError(buildNonJsonErrorPayload(response, text));
  }
  try {
    return JSON.parse(text);
  } catch {
    throw createApiError({ detail: "接口返回了无效 JSON" });
  }
};

export const withQuery = (url, params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") return;
    query.set(key, String(value));
  });
  const search = query.toString();
  return search ? `${url}?${search}` : url;
};

export const cursorFromLink = (link) => {
  if (!link) return "";
  try {
    const parsed = new URL(
      link,
      typeof window !== "undefined" ? window.location.origin : "http://localhost"
    );
    return parsed.searchParams.get("cursor") || "";
  } catch {
    const matched = String(link).match(/[?&]cursor=([^&]+)/);
    return matched ? decodeURIComponent(matched[1]) : "";
  }
};
