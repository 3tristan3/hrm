export const useAdminRegionActions = ({
  regionForm,
  showRegionCreateModal,
  showRegionDeleteModal,
  regionDeleteSubmitting,
  regionDeletePassword,
  pendingDeleteRegion,
  request,
  adminBase,
  dataLoaded,
  publicRegions,
  loadRegions,
  loadJobs,
  fetchPublicRegions,
  notifySuccess,
  notifyError,
  toastRef,
}) => {
  const resetRegionForm = () => {
    Object.assign(regionForm, { name: "", code: "", order: 0, is_active: true });
  };

  const openRegionCreateModal = () => {
    resetRegionForm();
    showRegionCreateModal.value = true;
  };

  const closeRegionCreateModal = () => {
    showRegionCreateModal.value = false;
  };

  const saveRegion = async () => {
    const payload = {
      name: regionForm.name.trim(),
      code: regionForm.code.trim(),
      order: Number.isFinite(Number(regionForm.order)) ? Number(regionForm.order) : 0,
      is_active: Boolean(regionForm.is_active),
    };
    if (!payload.name || !payload.code) {
      toastRef.value?.show("请填写地区名称和地区编码", "error");
      return false;
    }
    try {
      await request(`${adminBase}/regions/`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      notifySuccess("地区已新增");
      resetRegionForm();
      await loadRegions(true);
      if (dataLoaded.jobs) {
        await loadJobs(true);
      }
      publicRegions.value = [];
      await fetchPublicRegions();
      return true;
    } catch (err) {
      notifyError(err);
      return false;
    }
  };

  const openDeleteRegionModal = (item) => {
    pendingDeleteRegion.value = item;
    regionDeletePassword.value = "";
    regionDeleteSubmitting.value = false;
    showRegionDeleteModal.value = true;
  };

  const closeDeleteRegionModal = () => {
    showRegionDeleteModal.value = false;
    regionDeleteSubmitting.value = false;
    regionDeletePassword.value = "";
    pendingDeleteRegion.value = null;
  };

  const confirmDeleteRegion = async () => {
    const target = pendingDeleteRegion.value;
    if (!target) return;
    if (!regionDeletePassword.value.trim()) {
      toastRef.value?.show("请输入当前登录密码", "error");
      return;
    }
    regionDeleteSubmitting.value = true;
    try {
      await request(`${adminBase}/regions/${target.id}/`, {
        method: "DELETE",
        body: JSON.stringify({ password: regionDeletePassword.value }),
      });
      notifySuccess("地区已删除");
      closeDeleteRegionModal();
      await loadRegions(true);
      if (dataLoaded.jobs) {
        await loadJobs(true);
      }
      publicRegions.value = [];
      await fetchPublicRegions();
    } catch (err) {
      notifyError(err);
    } finally {
      regionDeleteSubmitting.value = false;
    }
  };

  return {
    resetRegionForm,
    openRegionCreateModal,
    closeRegionCreateModal,
    saveRegion,
    openDeleteRegionModal,
    closeDeleteRegionModal,
    confirmDeleteRegion,
  };
};
