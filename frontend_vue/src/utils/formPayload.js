// 表单 payload 工具：统一行数据清洗与扩展字段序列化。
export const normalizeText = (value) =>
  typeof value === "string" ? value.trim() : value;

export const buildRowPayload = (rows, fields) =>
  rows
    .map((row) => {
      const payload = {};
      fields.forEach((field) => {
        const raw = row[field];
        if (field === "age") {
          payload[field] =
            raw === "" || raw === null || raw === undefined ? "" : Number(raw);
        } else {
          payload[field] = normalizeText(raw ?? "");
        }
      });
      return payload;
    })
    .filter((row) =>
      Object.values(row).some((value) => value !== "" && value !== null)
    );

export const buildExtraFieldsPayload = (extraFields) => {
  const payload = {};
  Object.entries(extraFields || {}).forEach(([key, value]) => {
    payload[key] = normalizeText(value ?? "");
  });
  return payload;
};
