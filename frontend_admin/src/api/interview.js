// interview API 资源层：统一面试相关接口路径与调用方式。
const withQuery = (url, params = {}) => {
  const search = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") return;
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `${url}?${query}` : url;
};

const resolveApiBase = (adminBase) => String(adminBase || "").replace(/\/admin\/?$/, "");

export const createInterviewApi = ({ adminBase, request, multipartRequest }) => {
  const apiBase = resolveApiBase(adminBase);
  return {
    async listCandidates(params = {}) {
      return request(withQuery(`${adminBase}/interview-candidates/`, params));
    },
    async getMeta() {
      return request(`${adminBase}/interview-meta/`);
    },
    async listPassedCandidates(params = {}) {
      return request(withQuery(`${adminBase}/passed-candidates/`, params));
    },
    async listTalentPoolCandidates(params = {}) {
      return request(withQuery(`${adminBase}/talent-pool-candidates/`, params));
    },
    async scheduleCandidate(id, payload) {
      return request(`${adminBase}/interview-candidates/${id}/schedule/`, {
        method: "POST",
        body: JSON.stringify(payload || {}),
      });
    },
    async cancelSchedule(id, payload = {}) {
      return request(`${adminBase}/interview-candidates/${id}/cancel-schedule/`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    async saveResult(id, payload) {
      return request(`${adminBase}/interview-candidates/${id}/result/`, {
        method: "POST",
        body: JSON.stringify(payload || {}),
      });
    },
    async uploadInterviewExtraAttachments(applicationId, files = []) {
      const normalizedId = Number(applicationId || 0);
      const fileList = Array.isArray(files) ? files.filter(Boolean) : [];
      if (!normalizedId || !fileList.length) return [];
      if (typeof multipartRequest !== "function") {
        throw new Error("上传能力未初始化");
      }
      const formData = new FormData();
      formData.append("category", "interview_extra");
      fileList.forEach((file) => {
        formData.append("file", file);
      });
      return multipartRequest(`${apiBase}/applications/${normalizedId}/attachments/`, {
        method: "POST",
        body: formData,
      });
    },
    async resendSms(id, payload = {}) {
      return request(`${adminBase}/interview-candidates/${id}/resend-sms/`, {
        method: "POST",
        body: JSON.stringify(payload || {}),
      });
    },
    async batchAddFromApplications(applicationIds) {
      return request(`${adminBase}/interview-candidates/batch-add/`, {
        method: "POST",
        body: JSON.stringify({ application_ids: applicationIds }),
      });
    },
    async batchAddToTalentPool(applicationIds) {
      return request(`${adminBase}/talent-pool-candidates/batch-add/`, {
        method: "POST",
        body: JSON.stringify({ application_ids: applicationIds }),
      });
    },
    async batchMoveTalentToInterview(candidateIds) {
      return request(`${adminBase}/talent-pool-candidates/batch-to-interview/`, {
        method: "POST",
        body: JSON.stringify({ interview_candidate_ids: candidateIds }),
      });
    },
    async batchRemoveCandidates(candidateIds) {
      return request(`${adminBase}/interview-candidates/batch-remove/`, {
        method: "POST",
        body: JSON.stringify({ interview_candidate_ids: candidateIds }),
      });
    },
    async batchConfirmHires(candidateIds) {
      return request(`${adminBase}/passed-candidates/batch-confirm-hire/`, {
        method: "POST",
        body: JSON.stringify({
          interview_candidate_ids: candidateIds,
        }),
      });
    },
    async batchConfirmOnboard(candidateIds) {
      return request(`${adminBase}/passed-candidates/batch-confirm-onboard/`, {
        method: "POST",
        body: JSON.stringify({
          interview_candidate_ids: candidateIds,
        }),
      });
    },
    async updatePassedCandidateOfferStatus(id, payload) {
      return request(`${adminBase}/passed-candidates/${id}/offer-status/`, {
        method: "POST",
        body: JSON.stringify(payload || {}),
      });
    },
    async removeCandidate(id) {
      return request(`${adminBase}/interview-candidates/${id}/`, {
        method: "DELETE",
      });
    },
  };
};
