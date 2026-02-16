// 详情格式化工具：统一日期、结构化字段和附件预览标签的展示规则。
export const formatTime = (value) =>
  value ? new Date(value).toLocaleString() : "-";

export const toDateTimeLocal = (value) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (num) => String(num).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate()
  )}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

export const formatDate = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString();
};

export const displayValue = (value) => {
  if (value === 0) return "0";
  if (value === null || value === undefined || value === "") return "-";
  return value;
};

const isFilledValue = (value) =>
  value !== null && value !== undefined && value !== "";

export const formatStructuredList = (list, fields) => {
  if (!Array.isArray(list) || list.length === 0) return "暂无";
  const fieldKeys = new Set(fields.map((field) => field.key));
  return list
    .map((item) => {
      if (!item || typeof item !== "object") return `- ${item ?? "-"}`;
      const orderedParts = fields
        .map((field) => {
          const value = item[field.key];
          if (!isFilledValue(value)) return "";
          return `${field.label}：${value}`;
        })
        .filter(Boolean);
      const extraParts = Object.entries(item)
        .filter(([key, value]) => isFilledValue(value) && !fieldKeys.has(key))
        .map(([key, value]) => `${key}：${value}`);
      const parts = orderedParts.concat(extraParts);
      return `- ${parts.length ? parts.join("，") : "-"}`;
    })
    .join("\n");
};

export const formatList = (list) => {
  if (!Array.isArray(list) || list.length === 0) return "暂无";
  return list
    .map((item) => {
      if (!item || typeof item !== "object") return `- ${item ?? "-"}`;
      const parts = Object.entries(item)
        .filter(([, value]) => isFilledValue(value))
        .map(([key, value]) => `${key}：${value}`);
      return `- ${parts.length ? parts.join("，") : "-"}`;
    })
    .join("\n");
};

export const formatObject = (obj) => {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return "暂无";
  const entries = Object.entries(obj).filter(([, value]) =>
    isFilledValue(value)
  );
  if (!entries.length) return "暂无";
  return entries.map(([key, value]) => `- ${key}：${value}`).join("\n");
};

const attachmentExtension = (value) => {
  const normalized = String(value || "").split("?")[0].split("#")[0];
  const parts = normalized.split(".");
  if (parts.length < 2) return "";
  return String(parts[parts.length - 1] || "").trim().toLowerCase();
};

export const isImageFile = (value) => {
  const ext = attachmentExtension(value);
  return ["jpg", "jpeg", "png", "webp", "gif", "bmp", "svg"].includes(ext);
};

export const attachmentPreviewTag = (value, isImage) => {
  if (!value) return "无";
  if (isImage) return "图";
  const ext = attachmentExtension(value);
  return ext ? ext.toUpperCase() : "文件";
};
