export const useAdminAccountActions = ({
  passwordForm,
  selfPasswordForm,
  showResetPasswordModal,
  showSelfPasswordModal,
  request,
  adminBase,
  authBase,
  logout,
  runWithConfirm,
  loadUsers,
  notifySuccess,
  notifyError,
  toastRef,
}) => {
  const resetPasswordFormFields = () => {
    passwordForm.user_id = "";
    passwordForm.password = "";
  };

  const resetSelfPasswordFormFields = () => {
    selfPasswordForm.old_password = "";
    selfPasswordForm.new_password = "";
    selfPasswordForm.confirm_password = "";
  };

  const openResetPasswordModal = () => {
    showResetPasswordModal.value = true;
  };

  const closeResetPasswordModal = () => {
    showResetPasswordModal.value = false;
    resetPasswordFormFields();
  };

  const openSelfPasswordModal = () => {
    showSelfPasswordModal.value = true;
  };

  const closeSelfPasswordModal = () => {
    showSelfPasswordModal.value = false;
    resetSelfPasswordFormFields();
  };

  const resetUserPassword = async () => {
    const { user_id, password } = passwordForm;
    if (!user_id || !password) return false;
    try {
      await request(`${adminBase}/users/${user_id}/password/`, {
        method: "POST",
        body: JSON.stringify({ password }),
      });
      notifySuccess("密码已更新");
      resetPasswordFormFields();
      return true;
    } catch (err) {
      notifyError(err);
      return false;
    }
  };

  const changeMyPassword = async () => {
    const { old_password, new_password, confirm_password } = selfPasswordForm;
    if (!old_password || !new_password || !confirm_password) return false;
    if (new_password !== confirm_password) {
      toastRef.value?.show("两次输入的新密码不一致", "error");
      return false;
    }
    try {
      const result = await request(`${authBase}/password/`, {
        method: "POST",
        body: JSON.stringify({ old_password, new_password }),
      });
      if (result?.force_relogin) {
        notifySuccess(result?.message || "密码已更新，请重新登录");
        await logout(true);
        return true;
      }
      notifySuccess(result?.message || "密码已更新");
      resetSelfPasswordFormFields();
      return true;
    } catch (err) {
      notifyError(err);
      return false;
    }
  };

  const selectUserForReset = (item) => {
    passwordForm.user_id = item.id;
    passwordForm.password = "";
    showResetPasswordModal.value = true;
  };

  const deleteUser = async (item) => {
    await runWithConfirm({
      confirm: {
        title: "删除账号",
        content: `确定删除账号「${item.username}」吗？该操作不可恢复。`,
        type: "danger",
        confirmText: "删除",
      },
      action: async () => {
        await request(`${adminBase}/users/${item.id}/`, { method: "DELETE" });
        notifySuccess("账号已删除");
        await loadUsers(true);
      },
    });
  };

  return {
    openResetPasswordModal,
    closeResetPasswordModal,
    openSelfPasswordModal,
    closeSelfPasswordModal,
    resetUserPassword,
    changeMyPassword,
    selectUserForReset,
    deleteUser,
  };
};
