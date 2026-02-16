// 表单错误聚焦工具：定位首个错误字段并执行滚动与高亮反馈。
const ERROR_FIELD_SELECTORS = Object.freeze({
  recruit_type: '[name="recruit_type"]',
  region_id: '[name="region_id"]',
  job_id: '[name="job_id"]',
  name: '[name="name"]',
  age: '[name="age"]',
  gender: '[name="gender"]',
  height_cm: '[name="height_cm"]',
  weight_kg: '[name="weight_kg"]',
  marital_status: '[name="marital_status"]',
  political_status: '[name="political_status"]',
  ethnicity: '[name="ethnicity"]',
  education_level: '[name="education_level"]',
  education_period: '[name="education_start"]',
  id_number: '[name="id_number"]',
  phone: '[name="phone"]',
  qq: '[name="qq"]',
  wechat: '[name="wechat"]',
  email: '[name="email"]',
  photo: '[data-error-anchor="photo"]',
  id_front: '[data-error-anchor="id_front"]',
  id_back: '[data-error-anchor="id_back"]',
  resume: '[data-error-anchor="resume"]',
  education_history: '[data-error-anchor="education_history"]',
  work_history: '[data-error-anchor="work_history"]',
  family_members: '[data-error-anchor="family_members"]',
});

const ensureElementFocusable = (el) => {
  if (!el || typeof el.focus !== "function") return;
  const focusableTags = ["INPUT", "SELECT", "TEXTAREA", "BUTTON", "A"];
  if (focusableTags.includes(el.tagName)) return;
  if (!el.hasAttribute("tabindex")) {
    el.setAttribute("tabindex", "-1");
  }
};

const highlightAndFocusErrorTarget = (target) => {
  if (!target) return;
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  target.classList?.add("error-focus");
  window.setTimeout(() => target.classList?.remove("error-focus"), 1500);
  ensureElementFocusable(target);
  try {
    target.focus({ preventScroll: true });
  } catch {
    target.focus?.();
  }
};

const findErrorTarget = (key, rootEl) => {
  if (!rootEl || !key) return null;
  const explicitSelector = ERROR_FIELD_SELECTORS[key];
  if (explicitSelector) {
    const found = rootEl.querySelector(explicitSelector);
    if (found) return found;
  }
  return (
    rootEl.querySelector(`[name="${key}"]`) ||
    rootEl.querySelector(`[name="extra_${key}"]`) ||
    rootEl.querySelector(`[data-error-anchor="${key}"]`)
  );
};

export const scrollToFirstError = async ({ nextTick, formRef, errors }) => {
  await nextTick();
  const rootEl = formRef?.value;
  if (!rootEl) return;
  const keys = Object.keys(errors || {});
  if (!keys.length) return;
  for (const key of keys) {
    const target = findErrorTarget(key, rootEl);
    if (target) {
      highlightAndFocusErrorTarget(target);
      return;
    }
  }
  const fallback = rootEl.querySelector(".form-alert.error");
  if (fallback) highlightAndFocusErrorTarget(fallback);
};
