"""兼容导出层：面试批量动作视图已拆分到子模块。"""

from .batch_interview_pool import (  # noqa: F401
    AdminInterviewCandidateBatchAddView,
    AdminInterviewCandidateBatchRemoveView,
)
from .batch_talent_pool import (  # noqa: F401
    AdminTalentPoolCandidateBatchAddView,
    AdminTalentPoolCandidateBatchToInterviewView,
)

__all__ = [
    "AdminInterviewCandidateBatchAddView",
    "AdminInterviewCandidateBatchRemoveView",
    "AdminTalentPoolCandidateBatchAddView",
    "AdminTalentPoolCandidateBatchToInterviewView",
]
