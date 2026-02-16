// 管理后台运行时配置：解析环境变量并生成 API/资源地址。
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

export const API_BASE = trimTrailingSlash(
  resolveValue(import.meta.env.VITE_API_BASE, getDefaultOrigin())
);

const getApiOrigin = () => {
  try {
    return new URL(API_BASE, getDefaultOrigin()).origin;
  } catch {
    return getDefaultOrigin();
  }
};

export const API_ORIGIN = trimTrailingSlash(getApiOrigin());

export const buildApiUrl = (path) => {
  const cleanPath = String(path || "").replace(/^\/+/, "");
  return `${API_BASE}/${cleanPath}`;
};

export const resolveAssetUrl = (rawUrl) => {
  const value = String(rawUrl || "").trim();
  if (!value) return "";
  if (/^(?:https?:)?\/\//i.test(value) || value.startsWith("data:") || value.startsWith("blob:")) {
    return value;
  }
  const normalized = value.startsWith("/") ? value : `/${value}`;
  return `${API_ORIGIN}${normalized}`;
};

