// 运行时配置工具：解析环境变量并生成前端 API/页面地址。
const trimTrailingSlash = (value) => String(value || "").replace(/\/+$/, "");

const getDefaultOrigin = () => {
  if (typeof window !== "undefined" && window.location?.origin) {
    return window.location.origin;
  }
  return "http://127.0.0.1:8000";
};

const resolveValue = (value, fallback) => {
  const text = String(value || "").trim();
  return text || fallback;
};

const parseBool = (value, fallback) => {
  const text = String(value ?? "").trim().toLowerCase();
  if (!text) return fallback;
  if (["1", "true", "yes", "on"].includes(text)) return true;
  if (["0", "false", "no", "off"].includes(text)) return false;
  return fallback;
};

const parsePositiveInt = (value, fallback) => {
  const parsed = Number.parseInt(String(value ?? "").trim(), 10);
  if (Number.isNaN(parsed) || parsed <= 0) return fallback;
  return parsed;
};

export const API_BASE = trimTrailingSlash(
  resolveValue(import.meta.env.VITE_API_BASE, getDefaultOrigin())
);

export const buildApiUrl = (path) => {
  const cleanPath = String(path || "").replace(/^\/+/, "");
  return `${API_BASE}/${cleanPath}`;
};

export const FORM_URL = resolveValue(
  import.meta.env.VITE_FORM_URL,
  `${getDefaultOrigin()}/`
);

export const PREWARM_JOBS = parseBool(import.meta.env.VITE_PREWARM_JOBS, true);
export const PREWARM_REGION_LIMIT = parsePositiveInt(
  import.meta.env.VITE_PREWARM_REGION_LIMIT,
  3
);
export const ATTACHMENT_MAX_FILE_MB = parsePositiveInt(
  import.meta.env.VITE_ATTACHMENT_MAX_FILE_MB,
  10
);
export const ATTACHMENT_MAX_TOTAL_MB = parsePositiveInt(
  import.meta.env.VITE_ATTACHMENT_MAX_TOTAL_MB,
  40
);

