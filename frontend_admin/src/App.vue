<template>
  <!-- 文件说明：管理后台主页面，组织标签页、数据加载与主要业务交互。 -->
  <!-- 全局组件挂载点 -->
  <Toast ref="toastRef" />
  <ConfirmDialog ref="confirmRef" />

  <!-- 登录/注册页面 -->
  <div v-if="!token" class="auth-container">
    <div class="auth-box">
      <div class="auth-header">
        <div class="logo-circle">HR</div>
        <h1>应聘管理后台</h1>
      </div>
      
      <div class="auth-tabs">
        <div class="tab-item" :class="{ active: authMode === 'login' }" @click="authMode = 'login'">
          登录账号
        </div>
        <div class="tab-item" :class="{ active: authMode === 'register' }" @click="authMode = 'register'">
          注册新号
        </div>
      </div>

      <form class="auth-form" @submit.prevent="submitAuth">
        <div class="form-item">
          <input v-model="authForm.username" placeholder="请输入账号" required />
        </div>
        <div class="form-item">
          <input v-model="authForm.password" type="password" placeholder="请输入密码" required />
        </div>
        <div class="form-item" v-if="authMode === 'register'">
          <select v-model.number="authForm.region_id" required>
            <option value="" disabled>选择所属地区</option>
            <option v-for="item in publicRegions" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary btn-block">
          {{ authMode === 'login' ? "登 录" : "注 册 并 登 录" }}
        </button>
      </form>
    </div>
    <div class="auth-footer">HRM System &copy; {{ new Date().getFullYear() }}</div>
  </div>

  <!-- 管理后台主界面 -->
  <div v-else class="admin-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="logo-icon">H</span>
        <span class="app-name">应聘管理</span>
      </div>
      <nav class="sidebar-nav">
        <a 
          v-for="item in visibleTabs" :key="item.key"
          class="nav-item" :class="{ active: activeTab === item.key }"
          @click="activeTab = item.key"
        >
          {{ item.label }}
        </a>
      </nav>
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="avatar">{{ userInitial }}</div>
          <div class="info-text">
            <div class="username">{{ currentUsername || '管理员' }}</div>
            <div class="role-badge">{{ userProfile.can_view_all ? "总部" : userProfile.region_name }}</div>
          </div>
          <button class="logout-btn" @click="logout" title="退出">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="top-bar">
        <h2 class="page-title">{{ currentTitle }}</h2>
      </header>

      <div class="content-body">
        
        <!-- 地区管理（只读） -->
        <div v-if="activeTab === 'regions'" class="card">
          <div class="card-header">
            <h3>地区列表（固定）</h3>
          </div>
          <div class="card-body">
            <table class="data-table">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>编码</th>
                  <th>排序</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in regions" :key="item.id">
                  <td>{{ item.name }}</td>
                  <td>{{ item.code }}</td>
                  <td>{{ item.order }}</td>
                  <td>
                    <span class="status-dot" :class="{ active: item.is_active }"></span>
                    {{ item.is_active ? "启用" : "停用" }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 岗位管理 -->
        <div v-else-if="activeTab === 'jobs'" class="card job-card">
          <div class="card-header job-header">
            <div>
              <h3>岗位管理</h3>
              <p class="header-sub">维护各地区岗位信息与上架状态</p>
            </div>
            <div class="header-actions">
              <span class="chip">
                {{ hasJobKeyword ? `${filteredJobs.length} / ${jobs.length} 个岗位` : `${jobs.length} 个岗位` }}
              </span>
            </div>
          </div>
          <div class="card-body job-body">
            <div class="job-toolbar">
              <div class="job-toolbar-left">
                <button class="btn btn-sm btn-primary" @click="openNewJob">新增岗位</button>
                <button class="btn btn-sm btn-default" @click="fetchJobs">刷新列表</button>
              </div>
              <div class="job-toolbar-right">
                <div class="job-search input-with-icon">
                  <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
                    <circle cx="11" cy="11" r="7"></circle>
                    <line x1="16.65" y1="16.65" x2="21" y2="21"></line>
                  </svg>
                  <input
                    v-model.trim="jobFilters.keyword"
                    type="text"
                    placeholder="搜索岗位名称/地区/职责"
                    aria-label="搜索岗位"
                  />
                </div>
                <button class="btn btn-sm btn-default" :disabled="!hasJobKeyword" @click="resetJobFilters">清空</button>
                <span class="chip subtle">已选 {{ selectedJobsCount }} 个</span>
                <button
                  class="btn btn-sm btn-activate"
                  :disabled="!canBatchActivateJobs"
                  @click="batchActivateJobs"
                >
                  批量上架
                </button>
                <button
                  class="btn btn-sm btn-deactivate"
                  :disabled="!canBatchDeactivateJobs"
                  @click="batchDeactivateJobs"
                >
                  批量下架
                </button>
                <button
                  class="btn btn-sm btn-danger"
                  :disabled="selectedJobIds.length === 0"
                  @click="batchDeleteJobs"
                >
                  批量删除
                </button>
              </div>
            </div>

            <div class="job-table-wrap">
              <table class="data-table job-table">
                <thead>
                  <tr>
                    <th width="6%">
                      <input type="checkbox" v-model="isAllJobsSelected" />
                    </th>
                    <th width="16%">岗位名称</th>
                    <th width="12%">地区</th>
                    <th width="26%">岗位职责</th>
                    <th width="10%">薪资</th>
                    <th width="10%">学历</th>
                    <th width="10%">状态</th>
                    <th width="10%">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in filteredJobs" :key="item.id">
                    <td>
                      <input type="checkbox" :value="item.id" v-model="selectedJobIds" />
                    </td>
                    <td class="font-medium">{{ item.title }}</td>
                    <td><span class="tag">{{ item.region_name || regionName(item.region) }}</span></td>
                    <td>
                      <div class="text-truncate" :title="item.description">{{ item.description || '-' }}</div>
                    </td>
                    <td>{{ item.salary || "-" }}</td>
                    <td>{{ item.education || "-" }}</td>
                    <td>
                      <span class="status-dot" :class="{ active: item.is_active }"></span>
                      {{ item.is_active ? "上架" : "下架" }}
                    </td>
                    <td>
                      <a class="action-link" @click="editJob(item)">编辑</a>
                      <a class="action-link danger" @click="deleteJob(item.id)">删除</a>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 账号管理 -->
        <div v-else-if="activeTab === 'accounts'" class="card account-card">
          <div class="card-header account-header">
            <div>
              <h3>账号管理</h3>
              <p class="header-sub">管理各地区 HR 账号、权限与密码安全</p>
            </div>
            <div class="header-actions">
              <span class="chip">{{ users.length }} 个账号</span>
            </div>
          </div>
          <div class="card-body">
            <div class="account-panels">
              <div class="account-panel">
                <div class="panel-title">
                  <div>
                    <h4>重置账号密码</h4>
                    <p>选择账号并设置新密码</p>
                  </div>
                  <span class="panel-pill">管理员操作</span>
                </div>
                <form class="form-compact" @submit.prevent="resetUserPassword">
                  <div class="form-grid-2">
                    <div class="form-group">
                      <label>选择账号</label>
                      <select v-model.number="passwordForm.user_id" required>
                        <option value="">请选择账号</option>
                        <option v-for="item in users" :key="item.id" :value="item.id">
                          {{ item.username }}（{{ item.region_name || "-" }}）
                        </option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label>新密码</label>
                      <input v-model="passwordForm.password" type="password" placeholder="请输入新密码" required />
                    </div>
                  </div>
                  <div class="form-actions right">
                    <button type="submit" class="btn btn-primary">重置密码</button>
                  </div>
                </form>
              </div>
              <div class="account-panel">
                <div class="panel-title">
                  <div>
                    <h4>修改我的密码</h4>
                    <p>更新当前登录账号的密码</p>
                  </div>
                  <span class="panel-pill subtle">安全</span>
                </div>
                <form class="form-compact" @submit.prevent="changeMyPassword">
                  <div class="form-grid-3">
                    <div class="form-group">
                      <label>原密码</label>
                      <input v-model="selfPasswordForm.old_password" type="password" placeholder="请输入原密码" required />
                    </div>
                    <div class="form-group">
                      <label>新密码</label>
                      <input v-model="selfPasswordForm.new_password" type="password" placeholder="请输入新密码" required />
                    </div>
                    <div class="form-group">
                      <label>确认新密码</label>
                      <input v-model="selfPasswordForm.confirm_password" type="password" placeholder="再次输入新密码" required />
                    </div>
                  </div>
                  <div class="form-actions right">
                    <button type="submit" class="btn btn-primary">更新密码</button>
                  </div>
                </form>
              </div>
            </div>
            <div class="divider"></div>
            <div class="account-table">
              <div class="table-header">
                <div>
                  <h4>账号列表</h4>
                  <p class="text-muted">展示账号所属地区与权限状态</p>
                </div>
                <div class="table-meta">
                  <span class="chip subtle">仅系统管理员可操作</span>
                </div>
              </div>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>账号</th>
                    <th>地区</th>
                    <th>权限</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in users" :key="item.id">
                    <td class="font-medium">{{ item.username }}</td>
                    <td><span class="tag">{{ item.region_name || "-" }}</span></td>
                    <td>{{ item.is_superuser ? "系统管理员" : "区域账号" }}</td>
                    <td>
                      <span class="status-dot" :class="{ active: item.is_active }"></span>
                      {{ item.is_active ? "启用" : "停用" }}
                    </td>
                    <td class="action-cell">
                      <button class="btn btn-xs btn-default" @click="selectUserForReset(item)">重置密码</button>
                      <button
                        class="btn btn-xs btn-danger"
                        :disabled="item.is_superuser || item.username === currentUsername"
                        @click="deleteUser(item)"
                      >
                        删除账号
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 应聘记录 -->
        <div v-else-if="activeTab === 'applications'" class="card applications-card">
          <div class="card-header applications-header">
            <div>
              <h3>应聘记录明细</h3>
              <p class="header-sub">显示 {{ filteredApplications.length }} / {{ applications.length }} 条</p>
            </div>
            <div class="applications-header-actions">
              <span class="chip subtle">已选 {{ selectedApplicationsCount }} 人</span>
              <button
                class="btn btn-sm btn-primary"
                type="button"
                :disabled="selectedApplicationsCount === 0"
                @click="addSelectedToInterviewPool"
              >
                加入拟面试人员<span v-if="selectedApplicationsCount">（{{ selectedApplicationsCount }}）</span>
              </button>
              <button
                class="btn btn-sm btn-talent"
                type="button"
                :disabled="selectedApplicationsCount === 0"
                @click="addSelectedToTalentPool"
              >
                加入人才库<span v-if="selectedApplicationsCount">（{{ selectedApplicationsCount }}）</span>
              </button>
              <button class="btn btn-sm btn-default" type="button" @click="refreshApplications">刷新数据</button>
            </div>
          </div>
          <div class="card-body">
            <div class="application-toolbar">
              <div class="job-tabs">
                <button
                  v-for="job in jobCategories"
                  :key="job.value"
                  class="tab-pill"
                  :class="{ active: applicationFilters.job === job.value }"
                  @click="applicationFilters.job = job.value"
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
                    <select v-model="applicationFilters.region">
                      <option value="">全部地区</option>
                      <option v-for="item in regions" :key="item.id" :value="item.name">{{ item.name }}</option>
                    </select>
                  </div>
                </div>
                <button class="btn btn-sm btn-default" @click="resetApplicationFilters">重置筛选</button>
              </div>
            </div>
            <div class="applications-scroll">
              <div v-if="groupedApplications.length" class="application-groups">
                <section v-for="group in groupedApplications" :key="group.title" class="application-group">
                  <div class="group-header">
                    <div>
                      <h4>{{ group.title }}</h4>
                      <p class="text-muted">共 {{ group.items.length }} 条应聘记录</p>
                    </div>
                    <div class="group-header-actions">
                      <button
                        class="btn btn-xs btn-default"
                        type="button"
                        @click="toggleApplicationGroupSelection(group.items)"
                      >
                        {{ isApplicationGroupFullySelected(group.items) ? "取消全选" : "全选" }}
                      </button>
                      <span class="chip subtle">{{ group.items.length }} 条</span>
                    </div>
                  </div>
                  <div class="application-grid">
                    <div
                      v-for="item in group.items"
                      :key="item.id"
                      class="application-card"
                      :class="{ selected: isApplicationSelected(item.id) }"
                    >
                      <div
                        class="application-card-main"
                        role="button"
                        tabindex="0"
                        @click="toggleApplicationSelection(item.id)"
                        @keydown.enter.prevent="toggleApplicationSelection(item.id)"
                        @keydown.space.prevent="toggleApplicationSelection(item.id)"
                      >
                        <div class="card-photo">
                          <img v-if="item.photo_url" :src="resolveMediaUrl(item.photo_url)" alt="个人照片" loading="lazy" decoding="async" />
                          <div v-else class="photo-fallback">{{ item.name ? item.name.slice(0, 1) : "?" }}</div>
                          <span class="card-select-indicator" :class="{ active: isApplicationSelected(item.id) }">
                            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="3" fill="none">
                              <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                          </span>
                          <span class="card-pill">{{ item.job_title }}</span>
                        </div>
                        <div class="app-card-body">
                          <div class="card-title-row">
                            <div class="card-name" :title="item.name">{{ item.name }}</div>
                            <span class="card-badge">{{ item.recruit_type || "类型未填写" }}</span>
                          </div>
                          <div class="card-info-grid">
                            <div class="info-item">
                              <span class="info-label">性别</span>
                              <span class="info-value">{{ item.gender || "-" }}</span>
                            </div>
                            <div class="info-item">
                              <span class="info-label">年龄</span>
                              <span class="info-value">{{ item.age ? `${item.age}岁` : "-" }}</span>
                            </div>
                            <div class="info-item">
                              <span class="info-label">手机号</span>
                              <span class="info-value">{{ item.phone || "-" }}</span>
                            </div>
                            <div class="info-item">
                              <span class="info-label">学历</span>
                              <span class="info-value">{{ item.education_level || "-" }}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <button class="card-cta" type="button" @click="openApplication(item)">
                        <span>查看详情</span>
                        <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none">
                          <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                      </button>
                    </div>
                  </div>
                </section>
              </div>
              <div v-else class="empty-state">暂无匹配的应聘记录</div>
            </div>
          </div>
        </div>

        <InterviewCandidatesModule
          v-else-if="activeTab === 'interviews'"
          :filtered-interview-candidates="filteredInterviewCandidates"
          :interview-candidates="interviewCandidates"
          :selected-interview-count="selectedInterviewCount"
          :selected-interview-ids="selectedInterviewIds"
          :is-all-visible-interviews-selected="isAllVisibleInterviewsSelected"
          :interview-job-categories="interviewJobCategories"
          :interview-filters="interviewFilters"
          :show-region-filter="showRegionFilter"
          :regions="regions"
          :sorted-interview-candidates="sortedInterviewCandidates"
          :interview-time-sort="interviewTimeSort"
          :interview-meta="interviewMeta"
          :interview-result-options="interviewResultOptions"
          :show-interview-schedule-form="showInterviewScheduleForm"
          :show-interview-result-form="showInterviewResultForm"
          :interview-schedule-has-existing="interviewScheduleHasExisting"
          :schedule-saving="scheduleSaving"
          :result-saving="resultSaving"
          :interview-schedule-form="interviewScheduleForm"
          :interview-result-form="interviewResultForm"
          :interview-round-hint="interviewRoundHint"
          :format-time="formatTime"
          :interview-status-class="interviewStatusClass"
          :interview-status-text="interviewStatusText"
          :can-schedule-interview="canScheduleInterview"
          :schedule-action-label="scheduleActionLabel"
          @update:selected-interview-ids="selectedInterviewIds = $event"
          @update:is-all-visible-interviews-selected="isAllVisibleInterviewsSelected = $event"
          @refresh="refreshInterviewCandidates"
          @batch-remove="batchRemoveInterviewCandidates"
          @reset-filters="resetInterviewFilters"
          @toggle-time-sort="toggleInterviewTimeSort"
          @open-schedule="openInterviewSchedule"
          @open-result="openInterviewResult"
          @open-detail="openApplicationFromInterview"
          @remove="removeInterviewCandidate"
          @close-schedule="closeInterviewSchedule"
          @save-schedule="saveInterviewSchedule"
          @cancel-schedule-from-form="cancelInterviewScheduleFromForm"
          @close-result="closeInterviewResult"
          @save-result="saveInterviewResult"
        />

        <PassedCandidatesSection
          v-else-if="activeTab === 'passed'"
          :items="passedCandidates"
          :filtered-items="filteredPassedCandidates"
          :job-categories="passedJobCategories"
          :status-options="passedStatusOptions"
          :filters="passedFilters"
          :interview-status-class="interviewStatusClass"
          :interview-status-text="interviewStatusText"
          :selected-ids="selectedPassedIds"
          :is-all-visible-selected="isAllVisiblePassedSelected"
          :pagination="passedPagination"
          :loading="dataLoading.passed"
          @refresh="refreshPassedCandidates"
          @primary-action="confirmSelectedPassedHires"
          @reset-filters="resetPassedFilters"
          @open-detail="openApplicationFromOutcome"
          @update:selected-ids="selectedPassedIds = $event"
          @update:is-all-visible-selected="isAllVisiblePassedSelected = $event"
          @change-page="changePassedPage"
        />

        <TalentPoolCandidatesSection
          v-else-if="activeTab === 'talent'"
          :items="talentPoolCandidates"
          :filtered-items="filteredTalentCandidates"
          :job-categories="talentJobCategories"
          :filters="talentFilters"
          :interview-status-class="interviewStatusClass"
          :interview-status-text="interviewStatusText"
          :selected-ids="selectedTalentIds"
          :is-all-visible-selected="isAllVisibleTalentSelected"
          :pagination="talentPagination"
          :loading="dataLoading.talent"
          @refresh="refreshTalentPoolCandidates"
          @reset-filters="resetTalentFilters"
          @open-detail="openApplicationFromOutcome"
          @primary-action="addSelectedTalentToInterviewPool"
          @update:selected-ids="selectedTalentIds = $event"
          @update:is-all-visible-selected="isAllVisibleTalentSelected = $event"
          @change-page="changeTalentPage"
        />

        <div v-else-if="activeTab === 'operationLogs'" class="card operation-log-card">
          <div class="card-header op-header">
            <div>
              <h3>操作日志</h3>
              <p class="header-sub">审计轨迹</p>
            </div>
            <div class="op-header-metrics">
              <span class="chip chip-subtle">当前页 {{ operationLogs.length }} 条</span>
              <span class="chip chip-pass">成功 {{ operationLogSuccessCount }}</span>
              <span class="chip chip-reject">失败 {{ operationLogFailedCount }}</span>
              <button class="btn btn-sm btn-default" type="button" @click="refreshOperationLogs">刷新数据</button>
            </div>
          </div>
          <div class="card-body op-body">
            <div class="op-filter-panel">
              <div class="filter-actions log-filters">
                <div class="filter-field">
                  <label>模块</label>
                  <div class="op-field-control">
                    <select v-model="operationLogFilters.module">
                      <option value="">全部模块</option>
                      <option v-for="item in operationModuleOptions" :key="item.value" :value="item.value">
                        {{ item.label }}
                      </option>
                    </select>
                  </div>
                </div>
                <div class="filter-field">
                  <label>操作人</label>
                  <div class="op-field-control">
                    <input
                      v-model.trim="operationLogFilters.operator"
                      type="text"
                      placeholder="输入账号名"
                      @keyup.enter="searchOperationLogs"
                    />
                  </div>
                </div>
                <div class="filter-field">
                  <label>开始日期</label>
                  <div class="op-field-control">
                    <input v-model="operationLogFilters.date_from" type="date" />
                  </div>
                </div>
                <div class="filter-field">
                  <label>结束日期</label>
                  <div class="op-field-control">
                    <input v-model="operationLogFilters.date_to" type="date" />
                  </div>
                </div>
                <div class="filter-field op-search-actions">
                  <button class="btn btn-sm btn-primary" type="button" @click="searchOperationLogs">查询</button>
                  <button
                    class="btn btn-sm btn-default"
                    type="button"
                    @click="resetOperationLogFilters(); searchOperationLogs()"
                  >
                    重置
                  </button>
                </div>
              </div>
            </div>
            <div class="op-table-wrap">
              <table class="data-table passed-table operation-log-table">
                <thead>
                  <tr>
                    <th width="16%">时间</th>
                    <th width="10%">操作人</th>
                    <th width="11%">模块</th>
                    <th width="14%">动作</th>
                    <th width="13%">对象</th>
                    <th width="8%">结果</th>
                    <th width="28%">摘要</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="item in operationLogs"
                    :key="item.id"
                    class="op-row"
                    :class="{ failed: item.result === 'failed' }"
                  >
                    <td>{{ formatTime(item.created_at) }}</td>
                    <td>{{ item.operator_username || "-" }}</td>
                    <td>
                      <span class="op-module-tag" :class="`mod-${item.module || 'default'}`">
                        {{ operationModuleLabel(item.module) }}
                      </span>
                    </td>
                    <td>
                      <span class="op-action-text">{{ operationActionLabel(item.action) }}</span>
                    </td>
                    <td class="font-medium">{{ item.target_label || "-" }}</td>
                    <td>
                      <span class="chip" :class="operationResultClass(item.result)">
                        {{ operationResultLabel(item.result) }}
                      </span>
                    </td>
                    <td class="log-summary-cell">
                      <div class="log-summary-main">{{ item.summary || "-" }}</div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="!operationLogs.length && !dataLoading.operationLogs" class="empty-state">
                暂无操作日志
              </div>
            </div>
            <div v-if="operationLogsQueried" class="list-pagination op-pagination">
              <div class="pagination-meta">
                第 {{ operationLogPagination.page }} 页
              </div>
              <div class="op-pagination-right">
                <div class="op-page-size">
                  <span>每页</span>
                  <select
                    :value="operationLogPagination.pageSize"
                    @change="changeOperationLogPageSize($event.target.value)"
                  >
                    <option v-for="size in operationLogPageSizeOptions" :key="size" :value="size">
                      {{ size }}
                    </option>
                  </select>
                </div>
                <div class="pagination-actions">
                  <button
                    class="btn btn-xs btn-default"
                    type="button"
                    :disabled="operationLogPagination.page <= 1"
                    @click="changeOperationLogPage('previous')"
                  >
                    上一页
                  </button>
                  <button
                    v-for="item in operationLogPageItems"
                    :key="item.key"
                    class="op-page-btn"
                    :class="{ active: item.type === 'page' && item.value === operationLogPagination.page }"
                    type="button"
                    :disabled="item.type !== 'page' || (item.value !== 1 && typeof operationLogPageCursorMap[item.value] !== 'string')"
                    @click="item.type === 'page' && changeOperationLogPage(item.value)"
                  >
                    {{ item.type === "page" ? item.value : "..." }}
                  </button>
                  <button
                    class="btn btn-xs btn-default"
                    type="button"
                    :disabled="!operationLogPagination.next"
                    @click="changeOperationLogPage('next')"
                  >
                    下一页
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="card">
          <div class="card-body">暂无内容</div>
        </div>

      </div>
    </main>

    <div v-if="activeApplication" class="detail-overlay" @click.self="closeApplication">
      <div class="detail-modal">
        <div class="detail-header">
          <div class="detail-header-left">
            <div class="detail-photo">
              <img v-if="activeApplication.photo_url" :src="resolveMediaUrl(activeApplication.photo_url)" alt="个人照片" loading="lazy" decoding="async" />
              <div v-else class="photo-fallback">{{ activeApplication.name ? activeApplication.name.slice(0, 1) : "?" }}</div>
            </div>
            <div>
              <div class="detail-title">{{ activeApplication.name }}</div>
              <div class="detail-subtitle">{{ activeApplication.job_title }} · {{ activeApplication.region_name }}</div>
            </div>
          </div>
          <button class="detail-close" @click="closeApplication" title="关闭">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="detail-body">
          <div v-if="applicationDetailLoading" class="detail-loading">正在加载详情...</div>
          <div v-else>
            <div v-for="section in detailSections" :key="section.title" class="detail-section">
              <div class="section-title">{{ section.title }}</div>
              <div v-if="section.items" class="detail-grid">
                <div v-for="item in section.items" :key="item.label" class="detail-item">
                  <div class="detail-label">{{ item.label }}</div>
                  <div class="detail-value" :class="{ muted: item.value === '-' || item.value === '暂无' }">{{ item.value }}</div>
                </div>
              </div>
              <div v-if="section.blocks" class="detail-blocks">
                <div v-for="block in section.blocks" :key="block.label">
                  <div class="detail-label">{{ block.label }}</div>
                  <div class="detail-multiline">{{ block.value }}</div>
                </div>
              </div>
            </div>
            <div class="detail-section detail-attachments-section">
              <div class="section-title">证件与附件</div>
              <div class="detail-attachments-grid">
                <button
                  v-for="card in keyAttachmentCards"
                  :key="card.key"
                  type="button"
                  class="detail-attachment-card"
                  :class="{ missing: !card.url }"
                  :disabled="!card.url"
                  @click="openAttachment(card.url)"
                >
                  <span class="detail-attachment-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                  </span>
                  <span class="detail-attachment-main">
                    <span class="detail-attachment-title">{{ card.label }}</span>
                    <span class="detail-attachment-hint">{{ card.hint }}</span>
                  </span>
                  <span class="detail-attachment-preview" :class="{ placeholder: !card.url }" aria-hidden="true">
                    <img
                      v-if="card.url && card.isImage"
                      :src="resolveMediaUrl(card.url)"
                      :alt="`${card.label}预览`"
                      loading="lazy"
                      decoding="async"
                    />
                    <span v-else>{{ card.previewTag }}</span>
                  </span>
                  <span class="detail-attachment-action">{{ card.url ? "查看文件" : "未上传" }}</span>
                </button>
              </div>
              <div v-if="otherAttachmentFiles.length" class="detail-attachments-extra">
                <div class="detail-label">其他附件</div>
                <div class="detail-attachments-extra-list">
                  <button
                    v-for="item in otherAttachmentFiles"
                    :key="item.id"
                    type="button"
                    class="detail-attachment-link"
                    @click="openAttachment(item.file_url)"
                  >
                    {{ item.category_label || item.category || "附件" }} · {{ item.file_name || "点击查看" }}
                  </button>
                </div>
              </div>
            </div>
            <div class="detail-section detail-log-section">
              <div class="section-title">操作日志</div>
              <div v-if="applicationLogsLoading" class="detail-loading-inline">正在加载操作日志...</div>
              <div v-else-if="applicationOperationLogs.length" class="detail-log-timeline">
                <div v-for="item in applicationOperationLogs" :key="item.id" class="detail-log-node">
                  <span class="detail-log-dot" :class="item.result === 'success' ? 'success' : 'failed'"></span>
                  <div class="detail-log-item">
                    <div class="detail-log-meta">
                      <span class="detail-log-time">{{ formatTime(item.created_at) }}</span>
                      <span class="detail-log-operator">{{ item.operator_username || "-" }}</span>
                      <span class="chip" :class="operationResultClass(item.result)">
                        {{ operationResultLabel(item.result) }}
                      </span>
                    </div>
                    <div class="detail-log-content">
                      <span class="op-module-tag mini" :class="`mod-${item.module || 'default'}`">
                        {{ operationModuleLabel(item.module) }}
                      </span>
                      <strong>{{ operationActionLabel(item.action) }}</strong>
                    </div>
                    <div class="detail-log-summary">{{ item.summary || "-" }}</div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state">暂无操作日志</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showJobForm" class="job-modal-overlay" @click.self="closeJobForm">
      <div class="job-modal">
        <div class="job-modal-header">
          <div>
            <div class="job-modal-title">{{ jobForm.id ? "编辑岗位" : "新增岗位" }}</div>
            <div class="job-modal-subtitle">
              {{ jobForm.id ? `正在编辑：${jobForm.title || "未命名岗位"}` : "填写岗位信息并发布" }}
            </div>
          </div>
          <div class="job-modal-actions">
            <span class="panel-pill" :class="{ warning: !jobForm.is_active }">
              {{ jobForm.is_active ? "上架中" : "草稿" }}
            </span>
            <button class="job-modal-close" @click="closeJobForm" title="关闭">
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>
        <div class="job-modal-body">
          <form class="form-compact" @submit.prevent="saveJob">
            <div class="form-grid-2">
              <div class="form-group">
                <label>所属地区</label>
                <select v-model.number="jobForm.region" required :disabled="!userProfile.can_view_all">
                  <option value="">请选择...</option>
                  <option v-for="item in regions" :key="item.id" :value="item.id">{{ item.name }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>岗位名称</label>
                <input v-model="jobForm.title" placeholder="如：装置操作员" required />
              </div>
            </div>
            <div class="form-grid-3">
              <div class="form-group">
                <label>薪资范围</label>
                <input v-model="jobForm.salary" placeholder="如：5k-8k" />
              </div>
              <div class="form-group">
                <label>学历要求</label>
                <input v-model="jobForm.education" placeholder="如：本科及以上" />
              </div>
              <div class="form-group">
                <label>排序</label>
                <input v-model.number="jobForm.order" type="number" />
              </div>
            </div>
            <div class="form-group full-width">
              <label>岗位职责</label>
              <textarea v-model="jobForm.description" rows="4" placeholder="请输入岗位职责..."></textarea>
            </div>
            <div class="job-switch">
              <div>
                <div class="switch-title">上架状态</div>
                <div class="switch-desc">{{ jobForm.is_active ? "岗位可被投递" : "岗位暂不开放" }}</div>
              </div>
              <UISwitch v-model="jobForm.is_active" />
            </div>
            <div class="form-actions right">
              <button type="button" class="btn btn-default" @click="resetJobForm">清空表单</button>
              <button type="submit" class="btn btn-primary">
                {{ jobForm.id ? "保存岗位" : "发布岗位" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
// 业务模块组件
import UISwitch from './components/UISwitch.vue';
import Toast from './components/Toast.vue';
import ConfirmDialog from './components/ConfirmDialog.vue';
import InterviewCandidatesModule from './components/InterviewCandidatesModule.vue';
import PassedCandidatesSection from './components/PassedCandidatesSection.vue';
import TalentPoolCandidatesSection from './components/TalentPoolCandidatesSection.vue';
import { useAdminAppPage } from "./composables/useAdminAppPage";

const {
  toastRef,
  confirmRef,
  adminBase,
  authBase,
  resolveMediaUrl,
  resetOperationLogPageState,
  token,
  currentUsername,
  authMode,
  activeTab,
  tabs,
  authForm,
  jobForm,
  passwordForm,
  selfPasswordForm,
  selectedJobIds,
  selectedApplicationIds,
  selectedInterviewIds,
  selectedPassedIds,
  selectedTalentIds,
  jobFilters,
  showJobForm,
  showInterviewScheduleForm,
  showInterviewResultForm,
  interviewScheduleHasExisting,
  scheduleSaving,
  resultSaving,
  interviewTimeSort,
  applicationFilters,
  interviewFilters,
  passedFilters,
  talentFilters,
  operationLogFilters,
  interviewScheduleForm,
  interviewResultForm,
  publicRegions,
  regions,
  jobs,
  applications,
  interviewCandidates,
  passedCandidates,
  talentPoolCandidates,
  operationLogs,
  passedPagination,
  talentPagination,
  operationLogPagination,
  operationLogPageCursorMap,
  interviewMeta,
  users,
  userProfile,
  activeApplication,
  applicationDetailLoading,
  applicationOperationLogs,
  applicationLogsLoading,
  operationLogsQueried,
  operationLogMeta,
  dataLoaded,
  dataLoading,
  visibleTabs,
  interviewRoundHint,
  interviewResultOptions,
  currentTitle,
  userInitial,
  showRegionFilter,
  hasJobKeyword,
  filteredJobs,
  selectedJobStats,
  canBatchActivateJobs,
  canBatchDeactivateJobs,
  operationModuleOptions,
  operationLogSuccessCount,
  operationLogFailedCount,
  operationLogPageSizeOptions,
  operationLogKnownMaxPage,
  operationLogPageItems,
  jobCategories,
  filteredApplications,
  groupedApplications,
  interviewJobCategories,
  filteredInterviewCandidates,
  sortedInterviewCandidates,
  passedJobCategories,
  passedStatusOptions,
  filteredPassedCandidates,
  talentJobCategories,
  filteredTalentCandidates,
  selectedApplicationsCount,
  selectedJobsCount,
  isAllJobsSelected,
  selectedInterviewCount,
  isAllVisibleInterviewsSelected,
  isAllVisiblePassedSelected,
  selectedTalentCount,
  isAllVisibleTalentSelected,
  request,
  interviewApi,
  notifyError,
  notifySuccess,
  askConfirm,
  runWithConfirm,
  fetchPublicRegions,
  loadRegions,
  loadJobs,
  loadApplications,
  loadInterviewCandidates,
  loadInterviewMeta,
  loadPassedCandidates,
  loadTalentPoolCandidates,
  loadOperationLogMeta,
  loadOperationLogs,
  loadApplicationOperationLogs,
  loadUsers,
  ensureTabData,
  loadProfile,
  submitAuth,
  logout,
  regionName,
  operationModuleLabel,
  operationActionLabel,
  operationResultLabel,
  operationResultClass,
  interviewStatusClass,
  interviewStatusText,
  formatTime,
  canScheduleInterview,
  scheduleActionLabel,
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
  resetUserPassword,
  changeMyPassword,
  selectUserForReset,
  deleteUser,
  fetchApplications,
  refreshApplications,
  fetchJobs,
  resetJobFilters,
  resetApplicationFilters,
  resetInterviewFilters,
  resetPassedFilters,
  resetTalentFilters,
  resetOperationLogFilters,
  resetOperationLogMeta,
  toggleInterviewTimeSort,
  resetInterviewScheduleForm,
  resetInterviewResultForm,
  openInterviewSchedule,
  closeInterviewSchedule,
  openInterviewResult,
  closeInterviewResult,
  saveInterviewSchedule,
  cancelInterviewSchedule,
  cancelInterviewScheduleFromForm,
  saveInterviewResult,
  isApplicationSelected,
  getApplicationGroupIds,
  isApplicationGroupFullySelected,
  toggleApplicationGroupSelection,
  toggleApplicationSelection,
  addSelectedToInterviewPool,
  addSelectedToTalentPool,
  addSelectedTalentToInterviewPool,
  refreshInterviewCandidates,
  changePassedPage,
  changeTalentPage,
  changeOperationLogPage,
  changeOperationLogPageSize,
  refreshPassedCandidates,
  confirmSelectedPassedHires,
  refreshTalentPoolCandidates,
  searchOperationLogs,
  refreshOperationLogs,
  refreshInterviewModules,
  batchRemoveInterviewCandidates,
  removeInterviewCandidate,
  openApplicationFromInterview,
  openApplicationFromOutcome,
  openApplication,
  closeApplication,
  attachmentCardMeta,
  applicationAttachments,
  keyAttachmentCards,
  otherAttachmentFiles,
  openAttachment,
  detailSections,
} = useAdminAppPage();
</script>
