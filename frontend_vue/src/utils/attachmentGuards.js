// 附件大小校验工具，避免在页面组件中重复堆叠计算逻辑。
export const BYTES_PER_MB = 1024 * 1024;

export const fileSize = (file) => Number(file?.size || 0);

export const sumFileSizes = (files) =>
  (Array.isArray(files) ? files : []).reduce((sum, file) => sum + fileSize(file), 0);

export const buildCurrentAttachmentSize = (attachments) =>
  sumFileSizes([
    attachments?.photo || null,
    attachments?.id_front || null,
    attachments?.id_back || null,
    attachments?.resume || null,
    ...((attachments?.other && Array.isArray(attachments.other)) ? attachments.other : []),
  ]);

export const buildReplacingAttachmentSize = (attachments, type) => {
  if (type === "other") {
    return sumFileSizes(attachments?.other || []);
  }
  return fileSize(attachments?.[type]);
};

export const validateAttachmentFiles = ({
  attachments,
  type,
  incomingFiles,
  maxFileMb,
  maxTotalMb,
}) => {
  const maxFileBytes = Number(maxFileMb || 0) * BYTES_PER_MB;
  const maxTotalBytes = Number(maxTotalMb || 0) * BYTES_PER_MB;

  const oversized = incomingFiles.find((file) => fileSize(file) > maxFileBytes);
  if (oversized) {
    return {
      ok: false,
      error: `文件“${oversized.name}”超过单文件${maxFileMb}MB限制`,
    };
  }

  const currentTotal = buildCurrentAttachmentSize(attachments);
  const replacingSize = buildReplacingAttachmentSize(attachments, type);
  const incomingTotal = sumFileSizes(incomingFiles);
  const projectedTotal = Math.max(currentTotal - replacingSize, 0) + incomingTotal;
  if (projectedTotal > maxTotalBytes) {
    return {
      ok: false,
      error: `附件总大小不能超过${maxTotalMb}MB`,
    };
  }

  return { ok: true, error: "" };
};
