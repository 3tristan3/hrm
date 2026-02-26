export function createAdminModalSubmitters({
  saveRegion,
  closeRegionCreateModal,
  resetUserPassword,
  closeResetPasswordModal,
  changeMyPassword,
  closeSelfPasswordModal,
}) {
  const submitRegionCreate = async () => {
    const success = await saveRegion();
    if (success) {
      closeRegionCreateModal();
    }
  };

  const submitResetPassword = async () => {
    const success = await resetUserPassword();
    if (success) {
      closeResetPasswordModal();
    }
  };

  const submitSelfPassword = async () => {
    const success = await changeMyPassword();
    if (success) {
      closeSelfPasswordModal();
    }
  };

  return {
    submitRegionCreate,
    submitResetPassword,
    submitSelfPassword,
  };
}
