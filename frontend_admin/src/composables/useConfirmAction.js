// useConfirmAction 文件，统一二次确认 + 执行动作 + 错误处理流程。
import { unref } from "vue";

const noop = () => {};

export const useConfirmAction = (
  confirmRef,
  { onError = noop, onSuccess = noop } = {}
) => {
  const askConfirm = async (options = {}) => {
    const dialog = unref(confirmRef);
    if (!dialog || typeof dialog.open !== "function") return true;
    return Boolean(await dialog.open(options));
  };

  const runWithConfirm = async ({
    confirm,
    action,
    successMessage = "",
    successType = "success",
    skipConfirm = false,
    onActionSuccess,
    onActionError,
  }) => {
    if (typeof action !== "function") {
      throw new Error("runWithConfirm requires an action function");
    }

    const confirmed = skipConfirm ? true : await askConfirm(confirm || {});
    if (!confirmed) return { confirmed: false, done: false };

    try {
      const result = await action();
      if (successMessage) onSuccess(successMessage, successType);
      if (typeof onActionSuccess === "function") {
        await onActionSuccess(result);
      }
      return { confirmed: true, done: true, result };
    } catch (err) {
      if (typeof onActionError === "function") {
        await onActionError(err);
      } else {
        onError(err);
      }
      return { confirmed: true, done: false, error: err };
    }
  };

  return {
    askConfirm,
    runWithConfirm,
  };
};
