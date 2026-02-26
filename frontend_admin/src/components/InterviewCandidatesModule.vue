<template>
  <!-- 文件说明：拟面试人员模块组件，包含筛选、安排、改期、结果录入等交互。 -->
  <!-- 拟面试人员列表与筛选操作区 -->
  <div class="card interview-card">
    <div class="card-header interview-header">
      <div>
        <h3>拟面试人员</h3>
        <p class="header-sub">显示 {{ filteredInterviewCandidates.length }} / {{ interviewTotalCount }} 人</p>
      </div>
      <div class="applications-header-actions">
        <span class="chip subtle">已选 {{ selectedInterviewCount }} 人</span>
        <button
          class="btn btn-sm btn-danger"
          type="button"
          :disabled="selectedInterviewCount === 0"
          @click="$emit('batch-remove')"
        >
          批量移出<span v-if="selectedInterviewCount">（{{ selectedInterviewCount }}）</span>
        </button>
        <button class="btn btn-sm btn-default" type="button" @click="$emit('refresh')">刷新列表</button>
      </div>
    </div>
    <div class="card-body">
      <div class="application-toolbar">
        <div class="job-tabs">
          <button
            v-for="job in interviewJobCategories"
            :key="job.value"
            class="tab-pill"
            :class="{ active: interviewFilters.job === job.value }"
            @click="interviewFilters.job = job.value"
          >
            {{ job.label }}
            <span class="tab-count">{{ job.count }}</span>
          </button>
        </div>
        <div class="filter-actions">
          <div v-if="showRegionFilter" class="filter-field">
            <label>地区筛选</label>
            <div class="input-with-icon">
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
                <circle cx="11" cy="11" r="7"></circle>
                <line x1="16.65" y1="16.65" x2="21" y2="21"></line>
              </svg>
              <select v-model="interviewFilters.region">
                <option value="">全部地区</option>
                <option v-for="item in regions" :key="item.id" :value="item.name">{{ item.name }}</option>
              </select>
            </div>
          </div>
          <div class="filter-field">
            <div class="input-with-icon">
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
                <circle cx="11" cy="11" r="7"></circle>
                <line x1="16.65" y1="16.65" x2="21" y2="21"></line>
              </svg>
              <input v-model.trim="interviewFilters.keyword" placeholder="姓名/手机号" />
            </div>
          </div>
          <button class="btn btn-sm btn-default" @click="$emit('reset-filters')">重置筛选</button>
        </div>
      </div>
      <div class="interviews-scroll">
        <div v-if="sortedInterviewCandidates.length" class="interview-table-wrap">
          <table class="data-table interview-table">
            <thead>
              <tr>
                <th width="6%">
                  <input type="checkbox" v-model="localIsAllVisibleInterviewsSelected" />
                </th>
                <th>姓名</th>
                <th>岗位</th>
                <th>地区</th>
                <th>手机号</th>
                <th>招聘类型</th>
                <th>学历</th>
                <th>轮次</th>
                <th>
                  <button class="th-sort" type="button" @click="$emit('toggle-time-sort')">
                    <span>面试时间</span>
                    <span class="sort-triangles" aria-hidden="true">
                      <span :class="{ active: interviewTimeSort === 'asc' }">▲</span>
                      <span :class="{ active: interviewTimeSort === 'desc' }">▼</span>
                    </span>
                  </button>
                </th>
                <th>面试官</th>
                <th>面试结果</th>
                <th>评分</th>
                <th>加入时间</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in sortedInterviewCandidates" :key="item.id">
                <td>
                  <input type="checkbox" :value="item.id" v-model="localSelectedInterviewIds" />
                </td>
                <td class="font-medium">
                  <DetailNameButton :label="item.name || ''" @open="$emit('open-detail', item)" />
                </td>
                <td>{{ item.job_title || "-" }}</td>
                <td>{{ item.region_name || "-" }}</td>
                <td>{{ item.phone || "-" }}</td>
                <td>{{ item.recruit_type || "-" }}</td>
                <td>{{ item.education_level || "-" }}</td>
                <td>{{ item.interview_at ? `第${item.interview_round}轮` : "-" }}</td>
                <td>{{ formatTime(item.interview_at) }}</td>
                <td>{{ item.interviewer || "-" }}</td>
                <td>{{ item.result || "-" }}</td>
                <td>{{ item.score ?? "-" }}</td>
                <td>{{ formatTime(item.created_at) }}</td>
                <td>
                  <span :class="['chip', interviewStatusClass(item)]">
                    {{ interviewStatusText(item) }}
                  </span>
                </td>
                <td class="action-cell">
                  <div class="sms-status-shell" :class="`is-${smsStatusShell(item).status}`">
                    <button
                      type="button"
                      class="sms-status-dot-btn"
                      aria-label="查看短信状态"
                    >
                      <span class="sms-status-dot" aria-hidden="true"></span>
                    </button>
                    <div class="sms-status-popover">
                      <div class="sms-status-popover-title">短信发送状态</div>
                      <div class="sms-status-popover-row">
                        <span>状态</span>
                        <span class="sms-status-pill" :class="`is-${smsStatusShell(item).status}`">
                          {{ smsStatusShell(item).label }}
                        </span>
                      </div>
                      <div class="sms-status-popover-row">
                        <span>时间</span>
                        <span>{{ smsStatusTime(item) }}</span>
                      </div>
                      <div class="sms-status-popover-row">
                        <span>号码</span>
                        <span>{{ smsStatusShell(item).phone || "-" }}</span>
                      </div>
                      <div v-if="smsStatusShell(item).error" class="sms-status-popover-error">
                        {{ smsStatusShell(item).error }}
                      </div>
                      <div v-if="smsStatusShell(item).retryCount > 0" class="sms-status-popover-row">
                        <span>重试次数</span>
                        <span>{{ smsStatusShell(item).retryCount }} 次</span>
                      </div>
                      <div v-if="smsCanRetry(item)" class="sms-status-popover-actions">
                        <button type="button" class="sms-status-retry-btn" @click.stop="retrySms(item)">
                          失败重发
                        </button>
                      </div>
                    </div>
                  </div>
                  <button
                    class="btn btn-xs btn-primary"
                    type="button"
                    :disabled="!canScheduleInterview(item)"
                    @click.stop="$emit('open-schedule', item)"
                  >
                    {{ scheduleActionLabel(item) }}
                  </button>
                  <button
                    class="btn btn-xs btn-default"
                    type="button"
                    :disabled="item.status !== interviewMeta.status_scheduled"
                    @click.stop="$emit('open-result', item)"
                  >
                    记录结果
                  </button>
                  <button class="btn btn-xs btn-danger" type="button" @click.stop="$emit('remove', item)">移出</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">暂无拟面试人员</div>
      </div>
      <ListPaginationBar
        :pagination="pagination"
        :loading="loading"
        :page-size-options="pageSizeOptions"
        @change-page="$emit('change-page', $event)"
        @change-page-size="$emit('change-page-size', $event)"
      />
    </div>
  </div>

  <!-- 安排/改期面试弹窗 -->
  <div v-if="showInterviewScheduleForm" class="job-modal-overlay" @click.self="$emit('close-schedule')">
    <div class="job-modal">
      <div class="job-modal-header">
        <div>
          <div class="job-modal-title">安排面试</div>
          <div class="job-modal-subtitle">
            {{ interviewScheduleForm.name || "候选人" }} · {{ interviewScheduleForm.interview_at ? "修改时间" : "新增安排" }}
          </div>
        </div>
        <div class="job-modal-actions">
          <span class="panel-pill">{{ interviewRoundHint }}</span>
          <button class="job-modal-close" @click="$emit('close-schedule')" title="关闭">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
      <div class="job-modal-body">
        <form class="form-compact" @submit.prevent="onScheduleSubmit">
          <div class="form-grid-2">
            <div class="form-group">
              <label>候选人</label>
              <input :value="interviewScheduleForm.name || '-'" disabled />
            </div>
            <div class="form-group">
              <label>面试轮次</label>
              <input :value="interviewRoundHint" disabled />
            </div>
          </div>
          <div class="form-group full-width">
            <label>面试日期与时间 *</label>
            <DateTimeSlidePicker
              v-model="interviewScheduleForm.interview_at"
              :min-date="todayDate"
              :days="21"
              default-time="09:00"
              start-time="00:00"
              end-time="23:55"
              :step-minutes="5"
            />
          </div>
          <div class="form-group full-width">
            <label>面试官</label>
            <input v-model.trim="interviewScheduleForm.interviewer" />
          </div>
          <div class="form-group full-width">
            <label>面试地点 / 链接</label>
            <input v-model.trim="interviewScheduleForm.interview_location" placeholder="如：xx地点 / 腾讯会议链接" />
          </div>
          <div class="form-group full-width">
            <label>备注</label>
            <textarea v-model.trim="interviewScheduleForm.note" rows="3"></textarea>
          </div>
          <div class="form-group full-width">
            <div class="job-switch sms-shell-switch">
              <div class="switch-group">
                <div class="switch-title">发送面试通知短信</div>
              </div>
              <UISwitch
                v-model="interviewScheduleForm.send_sms"
                :label="interviewScheduleForm.send_sms ? '已开启' : '已关闭'"
              />
            </div>
            <div v-if="interviewScheduleForm.send_sms" class="sms-shell-card">
              <div class="sms-shell-head">
                <span class="panel-pill subtle">短信预览</span>
                <span class="sms-shell-recipient">接收号码：{{ interviewScheduleForm.phone || "未填写" }}</span>
              </div>
              <pre class="sms-shell-preview">{{ smsPreviewText }}</pre>
              <div class="sms-shell-footnote">预估字数：{{ smsPreviewText.length }} 字</div>
            </div>
          </div>
          <div class="form-actions schedule-form-actions">
            <div class="schedule-form-actions-left">
              <button
                v-if="interviewScheduleHasExisting"
                type="button"
                class="btn btn-danger"
                :disabled="scheduleSaving"
                @click="$emit('cancel-schedule-from-form')"
              >
                取消当前安排
              </button>
            </div>
            <div class="schedule-form-actions-right">
              <button type="button" class="btn btn-default" @click="$emit('close-schedule')">取消</button>
              <button type="submit" class="btn btn-primary" :disabled="scheduleSaving">
                {{
                  scheduleSaving
                    ? "保存中..."
                    : interviewScheduleForm.send_sms
                      ? "保存并发送短信"
                      : "保存安排"
                }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- 面试结果录入弹窗 -->
  <div v-if="showInterviewResultForm" class="job-modal-overlay" @click.self="$emit('close-result')">
    <div class="job-modal">
      <div class="job-modal-header">
        <div>
          <div class="job-modal-title">记录面试结果</div>
          <div class="job-modal-subtitle">{{ interviewResultForm.name || "候选人" }} · 第{{ interviewResultForm.interview_round }}轮</div>
        </div>
        <div class="job-modal-actions">
          <span class="panel-pill">{{ interviewResultForm.status || interviewMeta.status_scheduled }}</span>
          <button class="job-modal-close" @click="$emit('close-result')" title="关闭">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
      <div class="job-modal-body">
        <form class="form-compact" @submit.prevent="$emit('save-result')">
          <div class="form-grid-2">
            <div class="form-group">
              <label>面试结果</label>
              <select v-model="interviewResultForm.result" required>
                <option
                  v-for="item in interviewResultOptions"
                  :key="item.value"
                  :value="item.value"
                >
                  {{ item.label }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>评分（0-100）</label>
              <input v-model.number="interviewResultForm.score" type="number" min="0" max="100" placeholder="可选" />
            </div>
          </div>
          <div class="form-group full-width">
            <label>评语</label>
            <textarea v-model.trim="interviewResultForm.result_note" rows="4" placeholder="可填写面试表现、结论依据等"></textarea>
          </div>
          <div class="form-actions right">
            <button type="button" class="btn btn-default" @click="$emit('close-result')">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="resultSaving">
              {{ resultSaving ? "保存中..." : "保存结果" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import DetailNameButton from "./DetailNameButton.vue";
import DateTimeSlidePicker from "./DateTimeSlidePicker.vue";
import ListPaginationBar from "./ListPaginationBar.vue";
import UISwitch from "./UISwitch.vue";
import { useInterviewSmsShell } from "../composables/useInterviewSmsShell";

const props = defineProps({
  filteredInterviewCandidates: { type: Array, default: () => [] },
  interviewCandidates: { type: Array, default: () => [] },
  pagination: { type: Object, default: () => ({ page: 1, pageSize: 30, count: 0 }) },
  pageSizeOptions: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  selectedInterviewCount: { type: Number, default: 0 },
  selectedInterviewIds: { type: Array, default: () => [] },
  isAllVisibleInterviewsSelected: { type: Boolean, default: false },
  interviewJobCategories: { type: Array, default: () => [] },
  interviewFilters: { type: Object, required: true },
  showRegionFilter: { type: Boolean, default: false },
  regions: { type: Array, default: () => [] },
  sortedInterviewCandidates: { type: Array, default: () => [] },
  interviewTimeSort: { type: String, default: "none" },
  interviewMeta: { type: Object, required: true },
  interviewResultOptions: { type: Array, default: () => [] },
  showInterviewScheduleForm: { type: Boolean, default: false },
  showInterviewResultForm: { type: Boolean, default: false },
  interviewScheduleHasExisting: { type: Boolean, default: false },
  scheduleSaving: { type: Boolean, default: false },
  resultSaving: { type: Boolean, default: false },
  interviewScheduleForm: { type: Object, required: true },
  interviewResultForm: { type: Object, required: true },
  interviewRoundHint: { type: String, default: "" },
  formatTime: { type: Function, required: true },
  interviewStatusClass: { type: Function, required: true },
  interviewStatusText: { type: Function, required: true },
  canScheduleInterview: { type: Function, required: true },
  scheduleActionLabel: { type: Function, required: true },
});

const emit = defineEmits([
  "refresh",
  "batch-remove",
  "reset-filters",
  "change-page",
  "change-page-size",
  "toggle-time-sort",
  "open-schedule",
  "open-result",
  "retry-sms",
  "open-detail",
  "remove",
  "close-schedule",
  "save-schedule",
  "cancel-schedule-from-form",
  "close-result",
  "save-result",
  "update:selectedInterviewIds",
  "update:isAllVisibleInterviewsSelected",
]);

// v-model 透传：让父组件维护选中 ID 集合
const localSelectedInterviewIds = computed({
  get: () => props.selectedInterviewIds,
  set: (value) => emit("update:selectedInterviewIds", value),
});

// v-model 透传：让父组件维护“当前可见数据全选”
const localIsAllVisibleInterviewsSelected = computed({
  get: () => props.isAllVisibleInterviewsSelected,
  set: (value) => emit("update:isAllVisibleInterviewsSelected", value),
});

const interviewTotalCount = computed(() =>
  Math.max(
    Number(props.pagination?.count || 0),
    Array.isArray(props.interviewCandidates) ? props.interviewCandidates.length : 0
  )
);
const { smsPreviewText, smsStatusShell, smsStatusTime, smsCanRetry, retrySms } =
  useInterviewSmsShell({
    interviewScheduleForm: props.interviewScheduleForm,
    formatTime: props.formatTime,
    emit,
  });

const onScheduleSubmit = () => {
  emit("save-schedule");
};

const formatDateOffset = (offsetDays = 0) => {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};
const todayDate = formatDateOffset(0);
</script>
