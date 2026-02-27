export const OFFER_STATUS = Object.freeze({
  PENDING: "pending_hire",
  CONFIRMED: "confirmed_hire",
  REJECTED: "offer_rejected",
});

export const OFFER_STATUS_LABELS = Object.freeze({
  [OFFER_STATUS.PENDING]: "待确认入职",
  [OFFER_STATUS.CONFIRMED]: "确认入职",
  [OFFER_STATUS.REJECTED]: "拒绝offer",
});

export const OFFER_STATUS_ACTION_OPTIONS = Object.freeze([
  { value: OFFER_STATUS.PENDING, label: OFFER_STATUS_LABELS[OFFER_STATUS.PENDING] },
  { value: OFFER_STATUS.REJECTED, label: OFFER_STATUS_LABELS[OFFER_STATUS.REJECTED] },
]);

export const resolveOfferStatus = (item) => {
  const rawStatus = String(item?.offer_status || "").trim();
  if (rawStatus) return rawStatus;
  return item?.is_hired ? OFFER_STATUS.CONFIRMED : OFFER_STATUS.PENDING;
};

export const canConfirmHireByOfferStatus = (item) =>
  resolveOfferStatus(item) === OFFER_STATUS.PENDING;

export const canModifyOfferStatus = (item) =>
  resolveOfferStatus(item) !== OFFER_STATUS.CONFIRMED;

export const getAvailableOfferStatusActions = (item, options = []) => {
  const currentStatus = resolveOfferStatus(item);
  if (currentStatus === OFFER_STATUS.CONFIRMED) return [];
  if (currentStatus === OFFER_STATUS.REJECTED) {
    return (Array.isArray(options) ? options : []).filter(
      (option) => option?.value === OFFER_STATUS.PENDING
    );
  }
  return (Array.isArray(options) ? options : []).filter(
    (option) => option?.value === OFFER_STATUS.REJECTED
  );
};
