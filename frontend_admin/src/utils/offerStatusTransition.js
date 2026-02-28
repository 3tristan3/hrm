export const OFFER_STATUS = Object.freeze({
  PENDING: "pending_hire",
  ISSUED: "offer_issued",
  PENDING_ONBOARD: "confirmed_hire",
  ONBOARDED: "onboarded_hire",
  REJECTED: "offer_rejected",
});

export const OFFER_STATUS_LABELS = Object.freeze({
  [OFFER_STATUS.PENDING]: "待发offer",
  [OFFER_STATUS.ISSUED]: "已发offer",
  [OFFER_STATUS.PENDING_ONBOARD]: "待确认入职",
  [OFFER_STATUS.ONBOARDED]: "已确认入职",
  [OFFER_STATUS.REJECTED]: "拒绝offer",
});

export const OFFER_STATUS_ACTION_OPTIONS = Object.freeze([
  { value: OFFER_STATUS.REJECTED, label: OFFER_STATUS_LABELS[OFFER_STATUS.REJECTED] },
  {
    value: OFFER_STATUS.PENDING_ONBOARD,
    label: OFFER_STATUS_LABELS[OFFER_STATUS.PENDING_ONBOARD],
  },
]);

export const resolveOfferStatus = (item) => {
  const rawStatus = String(item?.offer_status || "").trim();
  if (rawStatus === OFFER_STATUS.PENDING_ONBOARD && item?.is_hired) {
    return OFFER_STATUS.ONBOARDED;
  }
  if (rawStatus) return rawStatus;
  return item?.is_hired ? OFFER_STATUS.PENDING_ONBOARD : OFFER_STATUS.PENDING;
};

export const canConfirmHireByOfferStatus = (item) =>
  resolveOfferStatus(item) === OFFER_STATUS.PENDING;

export const canConfirmOnboardByOfferStatus = (item) =>
  resolveOfferStatus(item) === OFFER_STATUS.PENDING_ONBOARD;

export const canModifyOfferStatus = (item) =>
  [
    OFFER_STATUS.ISSUED,
    OFFER_STATUS.PENDING_ONBOARD,
    OFFER_STATUS.REJECTED,
  ].includes(resolveOfferStatus(item));

export const getAvailableOfferStatusActions = (item, options = []) => {
  const currentStatus = resolveOfferStatus(item);
  if (!canModifyOfferStatus(item)) return [];
  return (Array.isArray(options) ? options : []).filter(
    (option) =>
      (option?.value === OFFER_STATUS.REJECTED ||
        option?.value === OFFER_STATUS.PENDING_ONBOARD) &&
      option?.value !== currentStatus
  );
};
