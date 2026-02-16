"""操作日志元信息：提供模块/动作展示文案等统一配置。"""

OPERATION_MODULE_LABELS = {
    "applications": "应聘记录",
    "interviews": "拟面试",
    "talent": "人才库",
    "jobs": "岗位管理",
    "accounts": "账号管理",
}

OPERATION_ACTION_LABELS = {
    "ADD_TO_INTERVIEW_POOL": "加入拟面试人员",
    "BATCH_ADD_TO_INTERVIEW_POOL": "批量加入拟面试人员",
    "ADD_TO_TALENT_POOL": "加入人才库",
    "BATCH_ADD_TO_TALENT_POOL": "批量加入人才库",
    "SCHEDULE_INTERVIEW": "安排面试",
    "RESCHEDULE_INTERVIEW": "改期安排",
    "CANCEL_INTERVIEW_SCHEDULE": "取消面试",
    "SAVE_INTERVIEW_RESULT": "记录面试结果",
    "REMOVE_FROM_INTERVIEW_POOL": "移出拟面试",
    "BATCH_REMOVE_FROM_INTERVIEW_POOL": "批量移出拟面试",
    "MOVE_TALENT_TO_INTERVIEW": "加入拟面试人员",
    "BATCH_MOVE_TALENT_TO_INTERVIEW": "批量加入拟面试人员",
    "CONFIRM_HIRE": "确认入职",
    "BATCH_CONFIRM_HIRE": "批量确认入职",
    "DELETE_JOB": "删除岗位",
    "BATCH_DEACTIVATE_JOB": "批量下架岗位",
    "BATCH_ACTIVATE_JOB": "批量上架岗位",
    "BATCH_DELETE_JOB": "批量删除岗位",
    "RESET_USER_PASSWORD": "重置密码",
    "DELETE_USER": "删除账号",
}

OPERATION_RESULT_LABELS = {
    "success": "成功",
    "failed": "失败",
}

OPERATION_LOG_PAGE_SIZE_OPTIONS = [20, 30, 50, 100]
OPERATION_LOG_DEFAULT_DAYS = 90
