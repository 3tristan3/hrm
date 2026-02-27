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

export const createInterviewApi = ({ adminBase, request }) => ({
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
  async batchConfirmHires(candidateIds, pushTargets = []) {
    return request(`${adminBase}/passed-candidates/batch-confirm-hire/`, {
      method: "POST",
      body: JSON.stringify({
        interview_candidate_ids: candidateIds,
        push_targets: pushTargets,
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
});
