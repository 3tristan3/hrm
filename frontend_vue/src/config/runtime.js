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

export const buildApiUrl = (path) => {
  const cleanPath = String(path || "").replace(/^\/+/, "");
  return `${API_BASE}/${cleanPath}`;
};

export const FORM_URL = resolveValue(
  import.meta.env.VITE_FORM_URL,
  `${getDefaultOrigin()}/`
);
