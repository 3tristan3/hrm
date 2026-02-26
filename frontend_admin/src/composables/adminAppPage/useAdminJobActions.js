export const useAdminJobActions = ({
  jobForm,
  userProfile,
  showJobForm,
  selectedJobIds,
  jobs,
  dataLoaded,
  request,
  adminBase,
  loadJobs,
  loadApplications,
  runWithConfirm,
  notifySuccess,
  notifyError,
  toastRef,
}) => {
  const resetJobForm = () => {
    Object.assign(jobForm, {
      id: null,
      region: "",
      title: "",
      description: "",
      salary: "",
      education: "",
      order: 0,
      is_active: true,
    });
    if (!userProfile.can_view_all && userProfile.region_id) {
      jobForm.region = userProfile.region_id;
    }
  };

  const openNewJob = () => {
    resetJobForm();
    showJobForm.value = true;
  };

  const closeJobForm = () => {
    showJobForm.value = false;
    resetJobForm();
  };

  const editJob = (item) => {
    Object.assign(jobForm, item);
    showJobForm.value = true;
  };

  const deleteJob = async (id) => {
    await runWithConfirm({
      confirm: {
        title: "删除岗位",
        content: "此操作将永久删除该岗位及其关联数据，是否继续？",
        type: "danger",
      },
      action: async () => {
        await request(`${adminBase}/jobs/${id}/`, { method: "DELETE" });
        notifySuccess("删除成功");
        await loadJobs(true);
      },
    });
  };

  const batchUpdateJobsStatus = async (isActive) => {
    if (!selectedJobIds.value.length) return;
    const selectedSet = new Set(selectedJobIds.value);
    const targetJobIds = jobs.value
      .filter((item) => selectedSet.has(item.id) && item.is_active !== isActive)
      .map((item) => item.id);
    if (!targetJobIds.length) {
      toastRef.value?.show(isActive ? "所选岗位已全部上架" : "所选岗位已全部下架", "info");
      return;
    }

    const actionText = isActive ? "上架" : "下架";
    const title = isActive ? "批量上架岗位" : "批量下架岗位";
    const content = isActive
      ? `将上架已选中的 ${targetJobIds.length} 个岗位，上架后对应应聘记录将恢复可见，是否继续？`
      : `将下架已选中的 ${targetJobIds.length} 个岗位，下架后对应应聘记录将不再展示，是否继续？`;
    await runWithConfirm({
      confirm: {
        title,
        content,
        type: isActive ? "default" : "danger",
        confirmText: actionText,
      },
      action: async () => {
        const result = await request(`${adminBase}/jobs/batch-status/`, {
          method: "POST",
          body: JSON.stringify({ job_ids: targetJobIds, is_active: isActive }),
        });
        notifySuccess(`已${actionText} ${result.updated || 0} 个岗位`);
        await loadJobs(true);
        if (dataLoaded.applications) {
          await loadApplications(true);
        }
      },
    });
  };

  const batchActivateJobs = async () => {
    await batchUpdateJobsStatus(true);
  };

  const batchDeactivateJobs = async () => {
    await batchUpdateJobsStatus(false);
  };

  const batchDeleteJobs = async () => {
    if (!selectedJobIds.value.length) return;
    await runWithConfirm({
      confirm: {
        title: "批量删除岗位",
        content: `将删除已选中的 ${selectedJobIds.value.length} 个岗位，是否继续？`,
        type: "danger",
        confirmText: "删除",
      },
      action: async () => {
        const ids = [...selectedJobIds.value];
        const results = await Promise.allSettled(
          ids.map((targetId) => request(`${adminBase}/jobs/${targetId}/`, { method: "DELETE" }))
        );
        const success = results.filter((item) => item.status === "fulfilled").length;
        const fail = results.length - success;
        if (success) notifySuccess(`已删除 ${success} 个岗位`);
        if (fail) toastRef.value?.show(`${fail} 个岗位删除失败`, "error");
        await loadJobs(true);
      },
    });
  };

  const saveJob = async () => {
    const method = jobForm.id ? "PUT" : "POST";
    const url = jobForm.id ? `${adminBase}/jobs/${jobForm.id}/` : `${adminBase}/jobs/`;
    try {
      await request(url, { method, body: JSON.stringify(jobForm) });
      notifySuccess("保存成功");
      resetJobForm();
      showJobForm.value = false;
      await loadJobs(true);
    } catch (err) {
      notifyError(err);
    }
  };

  return {
    resetJobForm,
    openNewJob,
    closeJobForm,
    editJob,
    deleteJob,
    batchUpdateJobsStatus,
    batchActivateJobs,
    batchDeactivateJobs,
    batchDeleteJobs,
    saveJob,
  };
};
