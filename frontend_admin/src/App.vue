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

        <InterviewPassedCard
          v-else-if="activeTab === 'passed'"
          :items="passedCandidates"
          :filtered-items="filteredPassedCandidates"
          :job-categories="passedJobCategories"
          :filters="passedFilters"
          :interview-status-class="interviewStatusClass"
          :interview-status-text="interviewStatusText"
          :selected-ids="selectedPassedIds"
          :is-all-visible-selected="isAllVisiblePassedSelected"
          title="面试通过人员"
          count-prefix="已通过"
          empty-text="暂无面试通过人员"
          :pagination="passedPagination"
          :loading="dataLoading.passed"
          @refresh="refreshPassedCandidates"
          @reset-filters="resetPassedFilters"
          @open-detail="openApplicationFromOutcome"
          @update:selected-ids="selectedPassedIds = $event"
          @update:is-all-visible-selected="isAllVisiblePassedSelected = $event"
          @change-page="changePassedPage"
        />

        <InterviewPassedCard
          v-else-if="activeTab === 'talent'"
          :items="talentPoolCandidates"
          :filtered-items="filteredTalentCandidates"
          :job-categories="talentJobCategories"
          :filters="talentFilters"
          :interview-status-class="interviewStatusClass"
          :interview-status-text="interviewStatusText"
          :selected-ids="selectedTalentIds"
          :is-all-visible-selected="isAllVisibleTalentSelected"
          title="人才库"
          count-prefix="已入库"
          empty-text="暂无人才库人员"
          :show-primary-action="true"
          primary-action-label="加入拟面试人员"
          primary-action-class="btn-primary"
          :primary-action-disabled="selectedTalentCount === 0"
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
import { computed, onMounted, reactive, ref, watch } from "vue";
// 业务模块组件
import UISwitch from './components/UISwitch.vue';
import Toast from './components/Toast.vue';
import ConfirmDialog from './components/ConfirmDialog.vue';
import InterviewCandidatesModule from './components/InterviewCandidatesModule.vue';
import InterviewPassedCard from './components/InterviewPassedCard.vue';
import { buildApiUrl, resolveAssetUrl } from "./config/runtime";
import { useJobCategoryFilter } from "./composables/useJobCategoryFilter";
import { useSelectionState } from "./composables/useSelectionState";
import { useConfirmAction } from "./composables/useConfirmAction";
import { createInterviewApi } from "./api/interview";
import { getInterviewStatusClass, getInterviewStatusText } from "./utils/interviewStatus";
import {
  DEFAULT_OPERATION_LOG_META,
  buildOperationModuleOptions,
  normalizeOperationLogMeta,
  resolveOperationActionLabel,
  resolveOperationModuleLabel,
} from "./constants/operationLog";

const toastRef = ref(null);
const confirmRef = ref(null);

// === 环境变量与基础配置 ===
const adminBase = buildApiUrl("api/admin");
const authBase = buildApiUrl("api/auth");
const resolveMediaUrl = (url) => resolveAssetUrl(url);

// 面试常量默认值：接口未返回时仍可保证前端可运行
const defaultInterviewMeta = Object.freeze({
  status_pending: "待安排",
  status_scheduled: "已安排",
  status_completed: "已完成",
  result_pending: "待定",
  result_next_round: "进入下一轮",
  result_pass: "通过",
  result_reject: "淘汰",
  status_choices: [
    { value: "待安排", label: "待安排" },
    { value: "已安排", label: "已安排" },
    { value: "已完成", label: "已完成" },
  ],
  result_choices: [
    { value: "进入下一轮", label: "进入下一轮" },
    { value: "通过", label: "通过" },
    { value: "淘汰", label: "淘汰" },
    { value: "待定", label: "待定" },
  ],
  final_results: ["通过", "淘汰"],
  max_round: 3,
});

const createInterviewMeta = (payload = {}) => {
  // 兜底和类型收敛，避免后端字段缺失导致前端判定异常
  const merged = { ...defaultInterviewMeta, ...(payload || {}) };
  const maxRound = Number(merged.max_round);
  return {
    ...merged,
    status_choices:
      Array.isArray(merged.status_choices) && merged.status_choices.length
        ? merged.status_choices
        : defaultInterviewMeta.status_choices,
    result_choices:
      Array.isArray(merged.result_choices) && merged.result_choices.length
        ? merged.result_choices
        : defaultInterviewMeta.result_choices,
    final_results:
      Array.isArray(merged.final_results) && merged.final_results.length
        ? merged.final_results
        : defaultInterviewMeta.final_results,
    max_round: Number.isFinite(maxRound) && maxRound > 0 ? Math.floor(maxRound) : defaultInterviewMeta.max_round,
  };
};

const LIST_PAGE_SIZE = 30;
const createPageState = () => ({
  page: 1,
  pageSize: LIST_PAGE_SIZE,
  count: 0,
  next: "",
  previous: "",
});
const isPaginatedPayload = (payload) =>
  Boolean(payload && typeof payload === "object" && Array.isArray(payload.results));
const applyListPagePayload = (state, payload, requestedPage = 1) => {
  if (isPaginatedPayload(payload)) {
    state.page = Math.max(Number(requestedPage || 1), 1);
    state.count = Number(payload.count || 0);
    state.next = payload.next || "";
    state.previous = payload.previous || "";
    return payload.results;
  }
  state.page = 1;
  state.count = Array.isArray(payload) ? payload.length : 0;
  state.next = "";
  state.previous = "";
  return Array.isArray(payload) ? payload : [];
};
const resetPageState = (state) => {
  state.page = 1;
  state.count = 0;
  state.next = "";
  state.previous = "";
};
const resetOperationLogPageState = () => {
  resetPageState(operationLogPagination);
  operationLogPagination.cursor = "";
  operationLogPageCursorMap.value = { 1: "" };
};

// === 状态管理 ===
const token = ref(localStorage.getItem("admin_token") || "");
const currentUsername = ref(localStorage.getItem("admin_username") || "");
const authMode = ref("login");
const activeTab = ref("jobs");

const tabs = [
  { key: "regions", label: "地区管理", adminOnly: true },
  { key: "jobs", label: "岗位管理", adminOnly: false },
  { key: "applications", label: "应聘记录", adminOnly: false },
  { key: "interviews", label: "拟面试人员", adminOnly: false },
  { key: "passed", label: "面试通过人员", adminOnly: false },
  { key: "talent", label: "人才库", adminOnly: false },
  { key: "operationLogs", label: "操作日志", adminOnly: false },
  { key: "accounts", label: "账号管理", adminOnly: true },
];

const authForm = reactive({ username: "", password: "", region_id: "" });
const jobForm = reactive({ id: null, region: "", title: "", description: "", salary: "", education: "", order: 0, is_active: true });
const passwordForm = reactive({ user_id: "", password: "" });
const selfPasswordForm = reactive({ old_password: "", new_password: "", confirm_password: "" });
const selectedJobIds = ref([]);
const selectedApplicationIds = ref([]);
const selectedInterviewIds = ref([]);
const selectedPassedIds = ref([]);
const selectedTalentIds = ref([]);
const jobFilters = reactive({ keyword: "" });
const showJobForm = ref(false);
const showInterviewScheduleForm = ref(false);
const showInterviewResultForm = ref(false);
const interviewScheduleHasExisting = ref(false);
const scheduleSaving = ref(false);
const resultSaving = ref(false);
const interviewTimeSort = ref("none");
const applicationFilters = reactive({ job: "all", region: "" });
const interviewFilters = reactive({ job: "all", region: "", keyword: "" });
const passedFilters = reactive({ job: "all" });
const talentFilters = reactive({ job: "all" });
const operationLogFilters = reactive({
  module: "",
  operator: "",
  date_from: "",
  date_to: "",
});
const interviewScheduleForm = reactive({
  id: null,
  name: "",
  interview_round: 1,
  interview_at: "",
  interviewer: "",
  interview_location: "",
  note: "",
});
const interviewResultForm = reactive({
  id: null,
  name: "",
  interview_round: 1,
  status: "",
  result: defaultInterviewMeta.result_next_round,
  score: null,
  result_note: "",
});

const publicRegions = ref([]);
const regions = ref([]);
const jobs = ref([]);
const applications = ref([]);
const interviewCandidates = ref([]);
const passedCandidates = ref([]);
const talentPoolCandidates = ref([]);
const operationLogs = ref([]);
const passedPagination = reactive(createPageState());
const talentPagination = reactive(createPageState());
const operationLogPagination = reactive({
  ...createPageState(),
  cursor: "",
});
const operationLogPageCursorMap = ref({ 1: "" });
const interviewMeta = reactive(createInterviewMeta());
const users = ref([]);
const userProfile = reactive({ can_view_all: false, region_name: "", region_id: null, is_superuser: false });
const activeApplication = ref(null);
const applicationDetailLoading = ref(false);
const applicationOperationLogs = ref([]);
const applicationLogsLoading = ref(false);
const operationLogsQueried = ref(false);
const operationLogMeta = reactive({
  ...normalizeOperationLogMeta(DEFAULT_OPERATION_LOG_META),
  loaded: false,
});
const dataLoaded = reactive({ regions: false, jobs: false, applications: false, interviews: false, passed: false, talent: false, operationLogs: false, interviewMeta: false, users: false });
const dataLoading = reactive({ regions: false, jobs: false, applications: false, interviews: false, passed: false, talent: false, operationLogs: false, interviewMeta: false, users: false });

// === 计算属性 ===
const visibleTabs = computed(() =>
  tabs.filter((tab) => (tab.adminOnly ? userProfile.is_superuser : true))
);
const interviewRoundHint = computed(() => {
  const round = Math.max(Number(interviewScheduleForm.interview_round || 1), 1);
  if (interviewScheduleHasExisting.value) {
    return `第${round}轮（改期）`;
  }
  return `第${round}轮`;
});
const interviewResultOptions = computed(() => {
  const preferredOrder = [
    interviewMeta.result_next_round,
    interviewMeta.result_pass,
    interviewMeta.result_reject,
    interviewMeta.result_pending,
  ].filter(Boolean);
  const source = Array.isArray(interviewMeta.result_choices) ? interviewMeta.result_choices : [];
  const byValue = new Map(source.map((item) => [item.value, item]));
  const ordered = preferredOrder
    .filter((value) => byValue.has(value))
    .map((value) => byValue.get(value));
  source.forEach((item) => {
    if (!ordered.find((v) => v.value === item.value)) {
      ordered.push(item);
    }
  });
  return ordered.length
    ? ordered
    : defaultInterviewMeta.result_choices.map((item) => ({ ...item }));
});
const currentTitle = computed(
  () => visibleTabs.value.find((t) => t.key === activeTab.value)?.label || "管理后台"
);
const userInitial = computed(() => (currentUsername.value ? currentUsername.value[0].toUpperCase() : "A"));
const showRegionFilter = computed(() => userProfile.can_view_all || userProfile.is_superuser);
const hasJobKeyword = computed(() => Boolean(jobFilters.keyword.trim()));
const filteredJobs = computed(() => {
  const keyword = jobFilters.keyword.trim().toLowerCase();
  if (!keyword) return jobs.value;
  return jobs.value.filter((item) =>
    [
      item?.title,
      item?.region_name,
      item?.description,
      item?.salary,
      item?.education,
      item?.is_active ? "上架 启用" : "下架 停用",
      item?.region,
    ]
      .filter((value) => value !== null && value !== undefined)
      .some((value) => String(value).toLowerCase().includes(keyword))
  );
});
const selectedJobStats = computed(() => {
  const selectedSet = new Set(selectedJobIds.value);
  let activeCount = 0;
  let inactiveCount = 0;
  jobs.value.forEach((item) => {
    if (!selectedSet.has(item.id)) return;
    if (item.is_active) activeCount += 1;
    else inactiveCount += 1;
  });
  return {
    activeCount,
    inactiveCount,
  };
});
const canBatchActivateJobs = computed(() => selectedJobStats.value.inactiveCount > 0);
const canBatchDeactivateJobs = computed(() => selectedJobStats.value.activeCount > 0);
const operationModuleOptions = computed(() =>
  buildOperationModuleOptions(operationLogs.value, operationLogMeta.module_labels)
);
const operationLogSuccessCount = computed(
  () => operationLogs.value.filter((item) => item?.result === "success").length
);
const operationLogFailedCount = computed(
  () => operationLogs.value.filter((item) => item?.result === "failed").length
);
const operationLogPageSizeOptions = computed(() =>
  Array.isArray(operationLogMeta.page_size_options) && operationLogMeta.page_size_options.length
    ? operationLogMeta.page_size_options
    : DEFAULT_OPERATION_LOG_META.page_size_options
);
const operationLogKnownMaxPage = computed(() => {
  const knownPages = Object.keys(operationLogPageCursorMap.value || {})
    .map((item) => Number(item))
    .filter((item) => Number.isFinite(item) && item > 0);
  return knownPages.length ? Math.max(...knownPages) : 1;
});
const operationLogPageItems = computed(() => {
  const maxPage = Math.max(operationLogKnownMaxPage.value, 1);
  const current = Math.max(Number(operationLogPagination.page || 1), 1);
  if (maxPage <= 7) {
    return Array.from({ length: maxPage }, (_, index) => ({
      type: "page",
      value: index + 1,
      key: `page-${index + 1}`,
    }));
  }

  const pageSet = new Set([1, maxPage, current - 1, current, current + 1]);
  if (current <= 3) [2, 3, 4].forEach((page) => pageSet.add(page));
  if (current >= maxPage - 2) [maxPage - 1, maxPage - 2, maxPage - 3].forEach((page) => pageSet.add(page));
  const sortedPages = Array.from(pageSet)
    .filter((page) => page >= 1 && page <= maxPage)
    .sort((a, b) => a - b);

  const items = [];
  sortedPages.forEach((page, index) => {
    const previousPage = sortedPages[index - 1];
    if (index > 0 && page - previousPage > 1) {
      items.push({
        type: "ellipsis",
        key: `ellipsis-${previousPage}-${page}`,
      });
    }
    items.push({
      type: "page",
      value: page,
      key: `page-${page}`,
    });
  });
  return items;
});
const { jobCategories, filteredItems: filteredApplications } = useJobCategoryFilter(
  applications,
  applicationFilters,
  {
    titleKey: "job_title",
    regionKey: "region_name",
    jobFilterKey: "job",
    regionFilterKey: "region",
    allValue: "all",
    allLabel: "全部岗位",
    unknownJobLabel: "未填写岗位",
  }
);

const groupedApplications = computed(() => {
  const groups = new Map();
  filteredApplications.value.forEach((item) => {
    const title = item.job_title || "未填写岗位";
    if (!groups.has(title)) groups.set(title, []);
    groups.get(title).push(item);
  });
  return Array.from(groups.entries())
    .map(([title, items]) => ({ title, items }))
    .sort((a, b) => a.title.localeCompare(b.title, "zh-Hans-CN"));
});

const { jobCategories: interviewJobCategories, filteredItems: filteredInterviewCandidates } =
  useJobCategoryFilter(interviewCandidates, interviewFilters, {
    titleKey: "job_title",
    regionKey: "region_name",
    jobFilterKey: "job",
    regionFilterKey: "region",
    keywordFilterKey: "keyword",
    keywordFields: ["name", "phone"],
    allValue: "all",
    allLabel: "全部岗位",
    unknownJobLabel: "未填写岗位",
  });

const sortedInterviewCandidates = computed(() => {
  const list = [...filteredInterviewCandidates.value];
  if (interviewTimeSort.value === "none") return list;

  const getTimestamp = (value) => {
    if (!value) return null;
    const time = new Date(value).getTime();
    return Number.isNaN(time) ? null : time;
  };

  list.sort((a, b) => {
    const aTime = getTimestamp(a.interview_at);
    const bTime = getTimestamp(b.interview_at);
    if (aTime === null && bTime === null) return 0;
    if (aTime === null) return 1;
    if (bTime === null) return -1;
    return interviewTimeSort.value === "asc" ? aTime - bTime : bTime - aTime;
  });
  return list;
});

const { jobCategories: passedJobCategories, filteredItems: filteredPassedCandidates } =
  useJobCategoryFilter(passedCandidates, passedFilters, {
    titleKey: "job_title",
    regionKey: "region_name",
    jobFilterKey: "job",
    allValue: "all",
    allLabel: "全部岗位",
    unknownJobLabel: "未填写岗位",
  });

const { jobCategories: talentJobCategories, filteredItems: filteredTalentCandidates } =
  useJobCategoryFilter(talentPoolCandidates, talentFilters, {
    titleKey: "job_title",
    regionKey: "region_name",
    jobFilterKey: "job",
    allValue: "all",
    allLabel: "全部岗位",
    unknownJobLabel: "未填写岗位",
  });

const selectedApplicationsCount = computed(() => selectedApplicationIds.value.length);
const { selectedCount: selectedJobsCount, isAllVisibleSelected: isAllJobsSelected } =
  useSelectionState(selectedJobIds, filteredJobs);
const {
  selectedCount: selectedInterviewCount,
  isAllVisibleSelected: isAllVisibleInterviewsSelected,
} = useSelectionState(selectedInterviewIds, filteredInterviewCandidates);
const { isAllVisibleSelected: isAllVisiblePassedSelected } =
  useSelectionState(selectedPassedIds, filteredPassedCandidates);
const {
  selectedCount: selectedTalentCount,
  isAllVisibleSelected: isAllVisibleTalentSelected,
} = useSelectionState(selectedTalentIds, filteredTalentCandidates);

// === API 请求封装 ===
const extractErrorMessage = (payload) => {
  if (!payload || typeof payload !== "object") return "请求失败";
  if (payload.details) {
    if (typeof payload.details === "string") return payload.details;
    const detailKeys = Object.keys(payload.details);
    if (detailKeys.length) {
      const val = payload.details[detailKeys[0]];
      if (Array.isArray(val) && val.length) return val[0];
      if (typeof val === "string") return val;
    }
  }
  if (payload.detail) return payload.detail;
  if (payload.error) return payload.error;
  const keys = Object.keys(payload);
  if (keys.length) {
    const val = payload[keys[0]];
    if (Array.isArray(val) && val.length) return val[0];
    if (typeof val === "string") return val;
  }
  return "请求失败";
};

const errorCodeMessageMap = Object.freeze({
  INTERVIEW_FLOW_CLOSED: "当前面试流程已结束，无法继续安排",
  INTERVIEW_NOT_SCHEDULED: "当前未安排面试",
  INTERVIEW_NOT_SCHEDULED_FOR_RESULT: "请先安排面试后再记录结果",
  INTERVIEW_ROUND_LIMIT_REACHED: "当前已是最后一轮，不能再进入下一轮",
});

const createApiError = (payload, fallback = "请求失败") => {
  const error = new Error(extractErrorMessage(payload) || fallback);
  error.code = payload?.error_code || "";
  error.payload = payload;
  return error;
};

const request = async (url, options = {}) => {
  const headers = { "Content-Type": "application/json" };
  if (token.value) headers.Authorization = `Token ${token.value}`;
  
  const response = await fetch(url, { headers, ...options });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw createApiError(payload);
  }
  return response.status === 204 ? {} : response.json();
};

const interviewApi = createInterviewApi({ adminBase, request });
const withQuery = (url, params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") return;
    query.set(key, String(value));
  });
  const search = query.toString();
  return search ? `${url}?${search}` : url;
};
const cursorFromLink = (link) => {
  if (!link) return "";
  try {
    const parsed = new URL(link, typeof window !== "undefined" ? window.location.origin : "http://localhost");
    return parsed.searchParams.get("cursor") || "";
  } catch {
    const matched = String(link).match(/[?&]cursor=([^&]+)/);
    return matched ? decodeURIComponent(matched[1]) : "";
  }
};

const notifyError = (err) => {
  console.error(err);
  const code = typeof err?.code === "string" ? err.code : "";
  const mapped = code ? errorCodeMessageMap[code] : "";
  toastRef.value?.show(mapped || err?.message || "操作失败", "error");
};
const notifySuccess = (msg) => {
  toastRef.value?.show(msg, 'success');
};
const { askConfirm, runWithConfirm } = useConfirmAction(confirmRef, {
  onError: notifyError,
  onSuccess: notifySuccess,
});

// === 业务逻辑 ===
const fetchPublicRegions = async () => {
  if (publicRegions.value.length) return;
  try {
    const res = await fetch(buildApiUrl("api/regions/"));
    if (res.ok) publicRegions.value = await res.json();
  } catch (err) {
    notifyError(err);
  }
};

const loadRegions = async (force = false) => {
  if (dataLoading.regions) return;
  if (!force && dataLoaded.regions) return;
  dataLoading.regions = true;
  try {
    regions.value = await request(`${adminBase}/regions/`);
    dataLoaded.regions = true;
  } catch (err) {
    notifyError(err);
  } finally {
    dataLoading.regions = false;
  }
};

const loadJobs = async (force = false) => {
  if (dataLoading.jobs) return;
  if (!force && dataLoaded.jobs) return;
  dataLoading.jobs = true;
  try {
    jobs.value = await request(`${adminBase}/jobs/`);
    selectedJobIds.value = [];
    dataLoaded.jobs = true;
  } catch (err) {
    notifyError(err);
  } finally {
    dataLoading.jobs = false;
  }
};

const loadApplications = async (force = false) => {
  if (dataLoading.applications) return;
  if (!force && dataLoaded.applications) return;
  dataLoading.applications = true;
  try {
    applications.value = await request(`${adminBase}/applications/`);
    const availableIds = new Set(applications.value.map((item) => item.id));
    selectedApplicationIds.value = selectedApplicationIds.value.filter((id) => availableIds.has(id));
    dataLoaded.applications = true;
    const availableJobs = jobCategories.value.map((item) => item.value);
    if (!availableJobs.includes(applicationFilters.job)) {
      applicationFilters.job = "all";
    }
    return true;
  } catch (err) {
    notifyError(err);
    return false;
  } finally {
    dataLoading.applications = false;
  }
};

const loadInterviewCandidates = async (force = false) => {
  // 拉取拟面试池，同时清理已失效的选中项
  if (dataLoading.interviews) return;
  if (!force && dataLoaded.interviews) return;
  dataLoading.interviews = true;
  try {
    interviewCandidates.value = await interviewApi.listCandidates();
    const availableIds = new Set(interviewCandidates.value.map((item) => item.id));
    selectedInterviewIds.value = selectedInterviewIds.value.filter((id) => availableIds.has(id));
    const availableJobs = interviewJobCategories.value.map((item) => item.value);
    if (!availableJobs.includes(interviewFilters.job)) {
      interviewFilters.job = "all";
    }
    dataLoaded.interviews = true;
  } catch (err) {
    notifyError(err);
  } finally {
    dataLoading.interviews = false;
  }
};

const loadInterviewMeta = async (force = false) => {
  // 从后端同步面试状态/结果枚举，统一前后端规则
  if (dataLoading.interviewMeta) return;
  if (!force && dataLoaded.interviewMeta) return;
  dataLoading.interviewMeta = true;
  try {
    const payload = await interviewApi.getMeta();
    Object.assign(interviewMeta, createInterviewMeta(payload));
    dataLoaded.interviewMeta = true;
  } catch (err) {
    notifyError(err);
  } finally {
    dataLoading.interviewMeta = false;
  }
};

const loadPassedCandidates = async (force = false, page = passedPagination.page) => {
  // 拉取面试通过人员（含多轮历史快照）
  if (dataLoading.passed) return;
  if (!force && dataLoaded.passed && page === passedPagination.page) return;
  dataLoading.passed = true;
  try {
    const payload = await interviewApi.listPassedCandidates({
      page,
      page_size: passedPagination.pageSize,
    });
    passedCandidates.value = applyListPagePayload(passedPagination, payload, page);
    const availableIds = new Set(passedCandidates.value.map((item) => item.id));
    selectedPassedIds.value = selectedPassedIds.value.filter((id) => availableIds.has(id));
    const availableJobs = passedJobCategories.value.map((item) => item.value);
    if (!availableJobs.includes(passedFilters.job)) {
      passedFilters.job = "all";
    }
    dataLoaded.passed = true;
  } catch (err) {
    notifyError(err);
  } finally {
    dataLoading.passed = false;
  }
};

const loadTalentPoolCandidates = async (force = false, page = talentPagination.page) => {
  // 拉取人才库（面试淘汰人员，含多轮历史快照）
  if (dataLoading.talent) return;
  if (!force && dataLoaded.talent && page === talentPagination.page) return;
  dataLoading.talent = true;
  try {
    const payload = await interviewApi.listTalentPoolCandidates({
      page,
      page_size: talentPagination.pageSize,
    });
    talentPoolCandidates.value = applyListPagePayload(talentPagination, payload, page);
    const availableIds = new Set(talentPoolCandidates.value.map((item) => item.id));
    selectedTalentIds.value = selectedTalentIds.value.filter((id) => availableIds.has(id));
    const availableJobs = talentJobCategories.value.map((item) => item.value);
    if (!availableJobs.includes(talentFilters.job)) {
      talentFilters.job = "all";
    }
    dataLoaded.talent = true;
  } catch (err) {
    notifyError(err);
  } finally {
    dataLoading.talent = false;
  }
};

const loadOperationLogMeta = async (force = false) => {
  if (operationLogMeta.loaded && !force) return;
  try {
    const payload = await request(`${adminBase}/operation-logs/meta/`);
    const normalized = normalizeOperationLogMeta(payload);
    operationLogMeta.module_labels = normalized.module_labels;
    operationLogMeta.action_labels = normalized.action_labels;
    operationLogMeta.result_labels = normalized.result_labels;
    operationLogMeta.page_size_options = normalized.page_size_options;
    operationLogMeta.default_recent_days = normalized.default_recent_days;
    operationLogMeta.pagination_mode = normalized.pagination_mode;
    const availableSizes = operationLogPageSizeOptions.value;
    if (!availableSizes.includes(Number(operationLogPagination.pageSize))) {
      operationLogPagination.pageSize = availableSizes[0] || LIST_PAGE_SIZE;
    }
  } catch (err) {
    notifyError(err);
  } finally {
    operationLogMeta.loaded = true;
  }
};

const loadOperationLogs = async (force = false, cursor = "", page = 1) => {
  if (dataLoading.operationLogs) return;
  const targetCursor = String(cursor || "");
  if (!force && dataLoaded.operationLogs && targetCursor === String(operationLogPagination.cursor || "")) {
    return;
  }
  operationLogsQueried.value = true;
  dataLoading.operationLogs = true;
  try {
    const payload = await request(
      withQuery(`${adminBase}/operation-logs/`, {
        page_size: operationLogPagination.pageSize,
        cursor: targetCursor,
        ...operationLogFilters,
      })
    );
    operationLogs.value = Array.isArray(payload?.results)
      ? payload.results
      : Array.isArray(payload)
        ? payload
        : [];
    const targetPage = Math.max(Number(page || 1), 1);
    operationLogPagination.page = targetPage;
    operationLogPagination.next = payload?.next || "";
    operationLogPagination.previous = payload?.previous || "";
    operationLogPagination.cursor = targetCursor;
    operationLogPageCursorMap.value[targetPage] = targetCursor;
    const previousCursor = cursorFromLink(payload?.previous || "");
    if (targetPage > 1 && previousCursor) {
      operationLogPageCursorMap.value[targetPage - 1] = previousCursor;
    }
    const nextCursor = cursorFromLink(payload?.next || "");
    if (nextCursor) {
      operationLogPageCursorMap.value[targetPage + 1] = nextCursor;
    } else {
      Object.keys(operationLogPageCursorMap.value).forEach((key) => {
        const keyNum = Number(key);
        if (Number.isFinite(keyNum) && keyNum > targetPage) {
          delete operationLogPageCursorMap.value[keyNum];
        }
      });
    }
    dataLoaded.operationLogs = true;
  } catch (err) {
    notifyError(err);
  } finally {
    dataLoading.operationLogs = false;
  }
};

const loadApplicationOperationLogs = async (applicationId) => {
  if (!applicationId) {
    applicationOperationLogs.value = [];
    return;
  }
  applicationLogsLoading.value = true;
  try {
    const payload = await request(
      withQuery(`${adminBase}/operation-logs/`, {
        application_id: applicationId,
        page: 1,
        page_size: 20,
      })
    );
    applicationOperationLogs.value = Array.isArray(payload?.results)
      ? payload.results
      : Array.isArray(payload)
        ? payload
        : [];
  } catch (err) {
    notifyError(err);
    applicationOperationLogs.value = [];
  } finally {
    applicationLogsLoading.value = false;
  }
};

const loadUsers = async (force = false) => {
  if (!userProfile.is_superuser) return;
  if (dataLoading.users) return;
  if (!force && dataLoaded.users) return;
  dataLoading.users = true;
  try {
    users.value = await request(`${adminBase}/users/`);
    dataLoaded.users = true;
  } catch (err) {
    notifyError(err);
  } finally {
    dataLoading.users = false;
  }
};

const ensureTabData = async (tabKey, force = false) => {
  // 按当前标签按需加载，减少无关接口请求
  if (!token.value) return;
  if (tabKey === "regions") {
    await loadRegions(force);
    return;
  }
  if (tabKey === "jobs") {
    await Promise.all([loadRegions(force), loadJobs(force)]);
    return;
  }
  if (tabKey === "applications") {
    await Promise.all([loadRegions(force), loadApplications(force)]);
    return;
  }
  if (tabKey === "interviews") {
    await Promise.all([loadInterviewMeta(force), loadInterviewCandidates(force)]);
    return;
  }
  if (tabKey === "passed") {
    await Promise.all([loadInterviewMeta(force), loadPassedCandidates(force)]);
    return;
  }
  if (tabKey === "talent") {
    await Promise.all([loadInterviewMeta(force), loadTalentPoolCandidates(force)]);
    return;
  }
  if (tabKey === "operationLogs") {
    await loadOperationLogMeta(force);
    return;
  }
  if (tabKey === "accounts") {
    await loadUsers(force);
  }
};

const loadProfile = async () => {
  const data = await request(`${authBase}/me/`);
  userProfile.can_view_all = data?.profile?.can_view_all || false;
  userProfile.region_name = data?.profile?.region_name || "";
  userProfile.region_id = data?.profile?.region ?? null;
  userProfile.is_superuser = data?.is_superuser || false;
  if (!userProfile.can_view_all && userProfile.region_id) {
    jobForm.region = userProfile.region_id;
  }
  if (!visibleTabs.value.find(t => t.key === activeTab.value)) {
    activeTab.value = visibleTabs.value[0]?.key || "jobs";
  }
};

const submitAuth = async () => {
  try {
    const endpoint = authMode.value === "register" ? "register" : "login";
    const body = { username: authForm.username, password: authForm.password };
    if (authMode.value === "register") body.region_id = authForm.region_id;

    const res = await fetch(`${authBase}/${endpoint}/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    
    const payload = await res.json();
    if (!res.ok) throw createApiError(payload);

    token.value = payload.token;
    currentUsername.value = authForm.username;
    localStorage.setItem("admin_token", payload.token);
    localStorage.setItem("admin_username", authForm.username);
    dataLoaded.regions = false;
    dataLoaded.jobs = false;
    dataLoaded.applications = false;
    dataLoaded.interviews = false;
    dataLoaded.passed = false;
    dataLoaded.talent = false;
    dataLoaded.operationLogs = false;
    dataLoaded.interviewMeta = false;
    dataLoaded.users = false;
    resetPageState(passedPagination);
    resetPageState(talentPagination);
    resetOperationLogPageState();
    operationLogs.value = [];
    selectedPassedIds.value = [];
    selectedTalentIds.value = [];
    resetJobFilters();
    resetPassedFilters();
    resetTalentFilters();
    resetOperationLogFilters();
    resetOperationLogMeta();
    operationLogPagination.pageSize = LIST_PAGE_SIZE;

    notifySuccess("登录成功");
    await loadProfile();
    await ensureTabData(activeTab.value, true);
  } catch (err) {
    notifyError(err);
  }
};

const logout = async (silent = false) => {
  const isConfirmed =
    silent ||
    (await askConfirm({
      title: "退出确认",
      content: "您确定要退出当前账号吗？",
      confirmText: "退出",
      type: "danger",
    }));
  if (!isConfirmed) return;

  if (token.value) {
    try {
      await request(`${authBase}/logout/`, { method: "POST" });
    } catch (err) {
      // 本地退出优先，登出接口失败不阻断清理（如 token 已过期）。
      console.warn("logout api failed", err);
    }
  }

  token.value = "";
  localStorage.removeItem("admin_token");
  localStorage.removeItem("admin_username");
  currentUsername.value = "";
  regions.value = [];
  jobs.value = [];
  applications.value = [];
  interviewCandidates.value = [];
  passedCandidates.value = [];
  talentPoolCandidates.value = [];
  operationLogs.value = [];
  users.value = [];
  selectedApplicationIds.value = [];
  selectedInterviewIds.value = [];
  selectedPassedIds.value = [];
  selectedTalentIds.value = [];
  dataLoaded.regions = false;
  dataLoaded.jobs = false;
  dataLoaded.applications = false;
  dataLoaded.interviews = false;
  dataLoaded.passed = false;
  dataLoaded.talent = false;
  dataLoaded.operationLogs = false;
  dataLoaded.interviewMeta = false;
  dataLoaded.users = false;
  dataLoading.regions = false;
  dataLoading.jobs = false;
  dataLoading.applications = false;
  dataLoading.interviews = false;
  dataLoading.passed = false;
  dataLoading.talent = false;
  dataLoading.operationLogs = false;
  dataLoading.interviewMeta = false;
  dataLoading.users = false;
  resetPageState(passedPagination);
  resetPageState(talentPagination);
  resetOperationLogPageState();
  Object.assign(interviewMeta, createInterviewMeta());
  activeApplication.value = null;
  applicationDetailLoading.value = false;
  applicationOperationLogs.value = [];
  applicationLogsLoading.value = false;
  showInterviewScheduleForm.value = false;
  scheduleSaving.value = false;
  resetInterviewScheduleForm();
  showInterviewResultForm.value = false;
  resultSaving.value = false;
  resetInterviewResultForm();
  resetJobFilters();
  resetApplicationFilters();
  resetInterviewFilters();
  resetPassedFilters();
  resetTalentFilters();
  resetOperationLogFilters();
  resetOperationLogMeta();
  operationLogPagination.pageSize = LIST_PAGE_SIZE;
  userProfile.can_view_all = false;
  userProfile.region_name = "";
  userProfile.region_id = null;
  userProfile.is_superuser = false;
  activeTab.value = "jobs";
  fetchPublicRegions();
  if (!silent) notifySuccess("已退出登录");
};

// === CRUD 操作 ===
const regionName = (id) => regions.value.find(r => r.id === id)?.name || "-";
const formatTime = (v) => v ? new Date(v).toLocaleString() : "-";
const operationModuleLabel = (value) => resolveOperationModuleLabel(value, operationLogMeta.module_labels);
const operationActionLabel = (value) => resolveOperationActionLabel(value, operationLogMeta.action_labels);
const operationResultLabel = (value) =>
  operationLogMeta.result_labels?.[value] || value || "-";
const operationResultClass = (value) => (value === "failed" ? "chip-reject" : "chip-pass");
const toDateTimeLocal = (v) => {
  if (!v) return "";
  const date = new Date(v);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
};
const formatDate = (v) => {
  if (!v) return "-";
  const date = new Date(v);
  if (Number.isNaN(date.getTime())) return v;
  return date.toLocaleDateString();
};
const interviewStatusClass = (item) => getInterviewStatusClass(item, interviewMeta);
const interviewStatusText = (item) => getInterviewStatusText(item, interviewMeta);
const canScheduleInterview = (item) =>
  !(
    item.status === interviewMeta.status_completed &&
    interviewMeta.final_results.includes(item.result || "")
  );
const scheduleActionLabel = (item) => {
  if (!canScheduleInterview(item)) return "不可安排";
  return item.interview_at ? "改期安排" : "安排面试";
};
const displayValue = (v) => {
  if (v === 0) return "0";
  if (v === null || v === undefined || v === "") return "-";
  return v;
};

const isFilledValue = (value) => value !== null && value !== undefined && value !== "";

const formatStructuredList = (list, fields) => {
  if (!Array.isArray(list) || list.length === 0) return "暂无";
  const fieldKeys = new Set(fields.map((field) => field.key));
  return list
    .map((item) => {
      if (!item || typeof item !== "object") return `- ${item ?? "-"}`;
      const orderedParts = fields
        .map((field) => {
          const value = item[field.key];
          if (!isFilledValue(value)) return "";
          return `${field.label}：${value}`;
        })
        .filter(Boolean);
      const extraParts = Object.entries(item)
        .filter(([key, value]) => isFilledValue(value) && !fieldKeys.has(key))
        .map(([key, value]) => `${key}：${value}`);
      const parts = orderedParts.concat(extraParts);
      return `- ${parts.length ? parts.join("，") : "-"}`;
    })
    .join("\n");
};

const formatList = (list) => {
  if (!Array.isArray(list) || list.length === 0) return "暂无";
  return list
    .map((item) => {
      if (!item || typeof item !== "object") return `- ${item ?? "-"}`;
      const parts = Object.entries(item)
        .filter(([, value]) => isFilledValue(value))
        .map(([key, value]) => `${key}：${value}`);
      return `- ${parts.length ? parts.join("，") : "-"}`;
    })
    .join("\n");
};
const formatObject = (obj) => {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return "暂无";
  const entries = Object.entries(obj).filter(([, value]) => value !== null && value !== undefined && value !== "");
  if (!entries.length) return "暂无";
  return entries.map(([key, value]) => `- ${key}：${value}`).join("\n");
};

// 岗位
const resetJobForm = () => {
  Object.assign(jobForm, { id: null, region: "", title: "", description: "", salary: "", education: "", order: 0, is_active: true });
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

// 账号
const resetUserPassword = async () => {
  const { user_id, password } = passwordForm;
  if (!user_id || !password) return;
  try {
    await request(`${adminBase}/users/${user_id}/password/`, {
      method: "POST",
      body: JSON.stringify({ password })
    });
    notifySuccess("密码已更新");
    passwordForm.user_id = "";
    passwordForm.password = "";
  } catch (err) {
    notifyError(err);
  }
};

const changeMyPassword = async () => {
  const { old_password, new_password, confirm_password } = selfPasswordForm;
  if (!old_password || !new_password || !confirm_password) return;
  if (new_password !== confirm_password) {
    toastRef.value?.show("两次输入的新密码不一致", "error");
    return;
  }
  try {
    const result = await request(`${authBase}/password/`, {
      method: "POST",
      body: JSON.stringify({ old_password, new_password })
    });
    if (result?.force_relogin) {
      notifySuccess(result?.message || "密码已更新，请重新登录");
      await logout(true);
      return;
    }
    notifySuccess(result?.message || "密码已更新");
    selfPasswordForm.old_password = "";
    selfPasswordForm.new_password = "";
    selfPasswordForm.confirm_password = "";
  } catch (err) {
    notifyError(err);
  }
};

const selectUserForReset = (item) => {
  passwordForm.user_id = item.id;
  passwordForm.password = "";
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

const fetchApplications = async () => {
  const ok = await loadApplications(true);
  if (!ok) return;
  activeApplication.value = null;
  applicationDetailLoading.value = false;
  notifySuccess("数据已刷新");
};

const refreshApplications = async () => {
  await fetchApplications();
  resetApplicationFilters();
};

const fetchJobs = async () => {
  await loadJobs(true);
};

const resetJobFilters = () => {
  jobFilters.keyword = "";
};

const resetApplicationFilters = () => {
  applicationFilters.job = "all";
  applicationFilters.region = "";
};

const resetInterviewFilters = () => {
  interviewFilters.job = "all";
  interviewFilters.region = "";
  interviewFilters.keyword = "";
  interviewTimeSort.value = "none";
};

const resetPassedFilters = () => {
  passedFilters.job = "all";
};

const resetTalentFilters = () => {
  talentFilters.job = "all";
};

const resetOperationLogFilters = () => {
  operationLogFilters.module = "";
  operationLogFilters.operator = "";
  operationLogFilters.date_from = "";
  operationLogFilters.date_to = "";
};

const resetOperationLogMeta = () => {
  operationLogMeta.module_labels = { ...DEFAULT_OPERATION_LOG_META.module_labels };
  operationLogMeta.action_labels = { ...DEFAULT_OPERATION_LOG_META.action_labels };
  operationLogMeta.result_labels = { ...DEFAULT_OPERATION_LOG_META.result_labels };
  operationLogMeta.page_size_options = [...DEFAULT_OPERATION_LOG_META.page_size_options];
  operationLogMeta.default_recent_days = DEFAULT_OPERATION_LOG_META.default_recent_days;
  operationLogMeta.pagination_mode = DEFAULT_OPERATION_LOG_META.pagination_mode;
  operationLogMeta.loaded = false;
  operationLogsQueried.value = false;
};

// 面试时间排序在“升序/降序”间切换
const toggleInterviewTimeSort = () => {
  interviewTimeSort.value = interviewTimeSort.value === "asc" ? "desc" : "asc";
};

const resetInterviewScheduleForm = () => {
  Object.assign(interviewScheduleForm, {
    id: null,
    name: "",
    interview_round: 1,
    interview_at: "",
    interviewer: "",
    interview_location: "",
    note: "",
  });
};

const resetInterviewResultForm = () => {
  Object.assign(interviewResultForm, {
    id: null,
    name: "",
    interview_round: 1,
    status: "",
    result: interviewMeta.result_next_round,
    score: null,
    result_note: "",
  });
};

// 打开安排面试弹窗：自动推导当前应安排轮次（仅展示）
const openInterviewSchedule = (item) => {
  activeApplication.value = null;
  applicationDetailLoading.value = false;
  interviewScheduleHasExisting.value = Boolean(
    item.interview_at || item.status === interviewMeta.status_scheduled
  );
  const currentRound = Math.max(Number(item.interview_round || 1), 1);
  const autoRound =
    item.interview_at || item.status === interviewMeta.status_scheduled
      ? currentRound
      : item.status === interviewMeta.status_completed ||
          (item.status === interviewMeta.status_pending &&
            item.result === interviewMeta.result_next_round)
        ? Math.min(currentRound + 1, interviewMeta.max_round)
        : currentRound;
  Object.assign(interviewScheduleForm, {
    id: item.id,
    name: item.name || "",
    interview_round: autoRound,
    interview_at: toDateTimeLocal(item.interview_at),
    interviewer: item.interviewer || "",
    interview_location: item.interview_location || "",
    note: item.note || "",
  });
  showInterviewScheduleForm.value = true;
};

// 关闭安排弹窗并清理临时状态
const closeInterviewSchedule = () => {
  showInterviewScheduleForm.value = false;
  interviewScheduleHasExisting.value = false;
  scheduleSaving.value = false;
  resetInterviewScheduleForm();
};

// 打开结果录入弹窗，带入当前轮次与历史评分
const openInterviewResult = (item) => {
  Object.assign(interviewResultForm, {
    id: item.id,
    name: item.name || "",
    interview_round: item.interview_round || 1,
    status: item.status || "",
    result: interviewMeta.result_next_round,
    score: item.score ?? null,
    result_note: item.result_note || "",
  });
  showInterviewResultForm.value = true;
};

// 关闭结果弹窗并重置表单
const closeInterviewResult = () => {
  showInterviewResultForm.value = false;
  resultSaving.value = false;
  resetInterviewResultForm();
};

// 保存安排：做前端基础校验后提交后端状态机
const saveInterviewSchedule = async () => {
  if (!interviewScheduleForm.id) return;
  if (!interviewScheduleForm.interview_at) {
    toastRef.value?.show("请填写面试时间", "error");
    return;
  }
  const interviewTime = new Date(interviewScheduleForm.interview_at);
  if (Number.isNaN(interviewTime.getTime())) {
    toastRef.value?.show("面试时间格式不正确", "error");
    return;
  }
  if (interviewTime.getTime() <= Date.now()) {
    toastRef.value?.show("面试时间不能早于当前时间", "error");
    return;
  }
  scheduleSaving.value = true;
  try {
    await interviewApi.scheduleCandidate(interviewScheduleForm.id, {
      interview_at: interviewScheduleForm.interview_at,
      interviewer: interviewScheduleForm.interviewer,
      interview_location: interviewScheduleForm.interview_location,
      note: interviewScheduleForm.note,
    });
    notifySuccess("面试安排已保存");
    closeInterviewSchedule();
    await loadInterviewCandidates(true);
  } catch (err) {
    notifyError(err);
  } finally {
    scheduleSaving.value = false;
  }
};

// 取消当前已安排的面试（保留候选人在拟面试池）
const cancelInterviewSchedule = async ({ id, name }) => {
  const { done } = await runWithConfirm({
    confirm: {
      title: "取消面试安排",
      content: `确认取消「${name || "该候选人"}」当前面试安排吗？`,
      confirmText: "取消安排",
      type: "danger",
    },
    action: async () => {
      await interviewApi.cancelSchedule(id);
      notifySuccess("已取消面试安排");
      await loadInterviewCandidates(true);
    },
  });
  return done;
};

// 从安排弹窗内触发取消安排
const cancelInterviewScheduleFromForm = async () => {
  if (!interviewScheduleForm.id) return;
  const done = await cancelInterviewSchedule({
    id: interviewScheduleForm.id,
    name: interviewScheduleForm.name,
  });
  if (done) closeInterviewSchedule();
};

// 保存结果：支持进入下一轮/通过/淘汰，并按需刷新通过列表与人才库
const saveInterviewResult = async () => {
  if (!interviewResultForm.id) return;
  if (interviewResultForm.score !== null && interviewResultForm.score !== "") {
    const score = Number(interviewResultForm.score);
    if (!Number.isInteger(score) || score < 0 || score > 100) {
      toastRef.value?.show("评分需为 0-100 的整数", "error");
      return;
    }
  }
  resultSaving.value = true;
  try {
    const payload = {
      result: interviewResultForm.result,
      result_note: interviewResultForm.result_note,
      score:
        interviewResultForm.score === null || interviewResultForm.score === ""
          ? null
          : Number(interviewResultForm.score),
    };
    await interviewApi.saveResult(interviewResultForm.id, payload);
    const shouldRefreshPassed =
      dataLoaded.passed || interviewResultForm.result === interviewMeta.result_pass;
    const shouldRefreshTalent =
      dataLoaded.talent || interviewResultForm.result === interviewMeta.result_reject;
    notifySuccess("面试结果已保存");
    closeInterviewResult();
    await refreshInterviewModules({
      forcePassed: shouldRefreshPassed,
      forceTalent: shouldRefreshTalent,
    });
  } catch (err) {
    notifyError(err);
  } finally {
    resultSaving.value = false;
  }
};

const isApplicationSelected = (applicationId) =>
  selectedApplicationIds.value.includes(applicationId);

const getApplicationGroupIds = (items) =>
  (Array.isArray(items) ? items : [])
    .map((item) => item?.id)
    .filter((id) => typeof id === "number");

const isApplicationGroupFullySelected = (items) => {
  const groupIds = getApplicationGroupIds(items);
  return (
    groupIds.length > 0 &&
    groupIds.every((id) => selectedApplicationIds.value.includes(id))
  );
};

const toggleApplicationGroupSelection = (items) => {
  const groupIds = getApplicationGroupIds(items);
  if (!groupIds.length) return;

  if (isApplicationGroupFullySelected(items)) {
    const groupSet = new Set(groupIds);
    selectedApplicationIds.value = selectedApplicationIds.value.filter(
      (id) => !groupSet.has(id)
    );
    return;
  }

  const merged = new Set([...selectedApplicationIds.value, ...groupIds]);
  selectedApplicationIds.value = Array.from(merged);
};

const toggleApplicationSelection = (applicationId) => {
  if (isApplicationSelected(applicationId)) {
    selectedApplicationIds.value = selectedApplicationIds.value.filter(
      (id) => id !== applicationId
    );
    return;
  }
  selectedApplicationIds.value = [...selectedApplicationIds.value, applicationId];
};

const addSelectedToInterviewPool = async () => {
  if (!selectedApplicationIds.value.length) return;
  await runWithConfirm({
    confirm: {
      title: "加入拟面试人员",
      content: `确认将已选 ${selectedApplicationIds.value.length} 人加入拟面试人员吗？`,
      confirmText: "加入",
      type: "default",
    },
    action: async () => {
      const result = await interviewApi.batchAddFromApplications(selectedApplicationIds.value);
      const parts = [];
      if (result.added) parts.push(`新增 ${result.added} 人`);
      if (result.existing) parts.push(`已存在 ${result.existing} 人`);
      notifySuccess(parts.length ? `操作完成：${parts.join("，")}` : "操作完成");
      selectedApplicationIds.value = [];
      await Promise.all([loadApplications(true), loadInterviewCandidates(true)]);
      activeTab.value = "interviews";
    },
  });
};

const addSelectedToTalentPool = async () => {
  if (!selectedApplicationIds.value.length) return;
  await runWithConfirm({
    confirm: {
      title: "加入人才库",
      content: `确认将已选 ${selectedApplicationIds.value.length} 人加入人才库吗？加入后将标记为“简历初筛未通过”，并从应聘记录中移除。`,
      confirmText: "确认加入",
      type: "danger",
    },
    action: async () => {
      const result = await interviewApi.batchAddToTalentPool(selectedApplicationIds.value);
      const parts = [];
      if (result.moved) parts.push(`加入 ${result.moved} 人`);
      if (result.existing) parts.push(`已在人才库 ${result.existing} 人`);
      if (result.blocked) parts.push(`已通过未处理 ${result.blocked} 人`);
      notifySuccess(parts.length ? `操作完成：${parts.join("，")}` : "操作完成");
      selectedApplicationIds.value = [];
      await loadApplications(true);
      if (dataLoaded.interviews) {
        await loadInterviewCandidates(true);
      }
      if (dataLoaded.talent) {
        await loadTalentPoolCandidates(true, 1);
      } else {
        dataLoaded.talent = false;
      }
    },
  });
};

const addSelectedTalentToInterviewPool = async () => {
  if (!selectedTalentIds.value.length) return;
  await runWithConfirm({
    confirm: {
      title: "加入拟面试人员",
      content: `确认将已选 ${selectedTalentIds.value.length} 人加入拟面试人员吗？加入后将从人才库移除。`,
      confirmText: "确认加入",
      type: "default",
    },
    action: async () => {
      const result = await interviewApi.batchMoveTalentToInterview(selectedTalentIds.value);
      selectedTalentIds.value = [];
      await Promise.all([loadTalentPoolCandidates(true, 1), loadInterviewCandidates(true)]);
      if (dataLoaded.applications) {
        await loadApplications(true);
      }
      notifySuccess(`已加入拟面试人员 ${result.moved || 0} 人`);
    },
  });
};

const refreshInterviewCandidates = async () => {
  await loadInterviewCandidates(true);
  resetInterviewFilters();
  notifySuccess("拟面试人员列表已刷新");
};

const changePassedPage = async (nextPage) => {
  const page = Math.max(Number(nextPage || 1), 1);
  if (page === passedPagination.page) return;
  await loadPassedCandidates(true, page);
};

const changeTalentPage = async (nextPage) => {
  const page = Math.max(Number(nextPage || 1), 1);
  if (page === talentPagination.page) return;
  await loadTalentPoolCandidates(true, page);
};

const changeOperationLogPage = async (target) => {
  if (target === "next") {
    if (!operationLogPagination.next) return;
    await loadOperationLogs(
      true,
      cursorFromLink(operationLogPagination.next),
      operationLogPagination.page + 1
    );
    return;
  }
  if (target === "previous") {
    if (!operationLogPagination.previous) return;
    await loadOperationLogs(
      true,
      cursorFromLink(operationLogPagination.previous),
      Math.max(operationLogPagination.page - 1, 1)
    );
    return;
  }
  const targetPage = Math.max(Number(target || 1), 1);
  if (!Number.isFinite(targetPage) || targetPage === operationLogPagination.page) return;
  const targetCursor = operationLogPageCursorMap.value[targetPage];
  if (targetPage !== 1 && typeof targetCursor !== "string") return;
  await loadOperationLogs(true, targetPage === 1 ? "" : targetCursor, targetPage);
};

const changeOperationLogPageSize = async (nextPageSize) => {
  const pageSize = Number(nextPageSize || operationLogPagination.pageSize);
  if (!Number.isFinite(pageSize) || pageSize <= 0) return;
  if (pageSize === Number(operationLogPagination.pageSize)) return;
  operationLogPagination.pageSize = pageSize;
  resetOperationLogPageState();
  await loadOperationLogs(true, "", 1);
};

const refreshPassedCandidates = async () => {
  await loadPassedCandidates(true, 1);
  selectedPassedIds.value = [];
  resetPassedFilters();
  notifySuccess("面试通过人员列表已刷新");
};

const refreshTalentPoolCandidates = async () => {
  await loadTalentPoolCandidates(true, 1);
  selectedTalentIds.value = [];
  resetTalentFilters();
  notifySuccess("人才库列表已刷新");
};

const searchOperationLogs = async () => {
  resetOperationLogPageState();
  await loadOperationLogs(true, "", 1);
};

const refreshOperationLogs = async () => {
  resetOperationLogPageState();
  await loadOperationLogs(true, "", 1);
  notifySuccess("操作日志已刷新");
};

// 统一刷新面试相关模块，避免多处重复刷新逻辑
const refreshInterviewModules = async ({ forcePassed = false, forceTalent = false } = {}) => {
  await loadInterviewCandidates(true);
  if (forcePassed || dataLoaded.passed) {
    await loadPassedCandidates(true);
  }
  if (forceTalent || dataLoaded.talent) {
    await loadTalentPoolCandidates(true);
  }
};

const batchRemoveInterviewCandidates = async () => {
  if (!selectedInterviewIds.value.length) return;
  await runWithConfirm({
    confirm: {
      title: "批量移出拟面试人员",
      content: `确认移出已选 ${selectedInterviewIds.value.length} 人吗？`,
      confirmText: "移出",
      type: "danger",
    },
    action: async () => {
      const result = await interviewApi.batchRemoveCandidates(selectedInterviewIds.value);
      selectedInterviewIds.value = [];
      await refreshInterviewModules();
      notifySuccess(`已移出 ${result.removed || 0} 人`);
    },
  });
};

const removeInterviewCandidate = async (item) => {
  await runWithConfirm({
    confirm: {
      title: "移出拟面试人员",
      content: `确认将「${item.name || "该应聘者"}」移出拟面试人员吗？`,
      confirmText: "移出",
      type: "danger",
    },
    action: async () => {
      await interviewApi.removeCandidate(item.id);
      selectedInterviewIds.value = selectedInterviewIds.value.filter((id) => id !== item.id);
      notifySuccess("已移出拟面试人员");
      await refreshInterviewModules();
    },
  });
};

const openApplicationFromInterview = async (item) => {
  // 从面试列表跳转到同一人的应聘详情弹窗
  await openApplication({
    id: item.application_id,
    name: item.name,
    job_title: item.job_title,
    region_name: item.region_name,
    photo_url: item.photo_url,
  });
};

const openApplicationFromOutcome = async (item) => {
  await openApplication({
    id: item.application_id,
    name: item.name,
    job_title: item.job_title,
    region_name: item.region_name,
  });
};

const openApplication = async (item) => {
  applicationDetailLoading.value = true;
  applicationOperationLogs.value = [];
  applicationLogsLoading.value = true;
  activeApplication.value = { ...item };
  try {
    const [detail] = await Promise.all([
      request(`${adminBase}/applications/${item.id}/`),
      loadApplicationOperationLogs(item.id),
    ]);
    activeApplication.value = detail;
  } catch (err) {
    notifyError(err);
    activeApplication.value = null;
    applicationOperationLogs.value = [];
    applicationLogsLoading.value = false;
  } finally {
    applicationDetailLoading.value = false;
  }
};

const closeApplication = () => {
  activeApplication.value = null;
  applicationDetailLoading.value = false;
  applicationOperationLogs.value = [];
  applicationLogsLoading.value = false;
};

const attachmentCardMeta = Object.freeze([
  { key: "id_front", label: "身份证正面", hint: "核对身份信息" },
  { key: "id_back", label: "身份证反面", hint: "核对有效期限" },
  { key: "resume", label: "个人简历", hint: "查看完整履历" },
]);

const applicationAttachments = computed(() => {
  const attachments = activeApplication.value?.attachments;
  return Array.isArray(attachments) ? attachments : [];
});

const keyAttachmentCards = computed(() => {
  const firstByCategory = new Map();
  applicationAttachments.value.forEach((item) => {
    if (!item?.category || firstByCategory.has(item.category)) return;
    firstByCategory.set(item.category, item);
  });
  return attachmentCardMeta.map((meta) => {
    const file = firstByCategory.get(meta.key);
    const url = file?.file_url || "";
    const fileName = file?.file_name || "";
    const isImage = isImageFile(fileName || url);
    return {
      ...meta,
      url,
      fileName,
      isImage,
      previewTag: url ? attachmentPreviewTag(fileName || url, isImage) : "无",
    };
  });
});

const otherAttachmentFiles = computed(() => {
  const keySet = new Set(attachmentCardMeta.map((item) => item.key));
  return applicationAttachments.value.filter((item) => item?.category && !keySet.has(item.category));
});

const attachmentExtension = (value) => {
  const normalized = String(value || "").split("?")[0].split("#")[0];
  const parts = normalized.split(".");
  if (parts.length < 2) return "";
  return String(parts[parts.length - 1] || "").trim().toLowerCase();
};

const isImageFile = (value) => {
  const ext = attachmentExtension(value);
  return ["jpg", "jpeg", "png", "webp", "gif", "bmp", "svg"].includes(ext);
};

const attachmentPreviewTag = (value, isImage) => {
  if (!value) return "无";
  if (isImage) return "图";
  const ext = attachmentExtension(value);
  return ext ? ext.toUpperCase() : "文件";
};

const openAttachment = (rawUrl) => {
  if (!rawUrl || typeof window === "undefined") return;
  const url = resolveMediaUrl(rawUrl);
  window.open(url, "_blank", "noopener,noreferrer");
};

const detailSections = computed(() => {
  if (!activeApplication.value) return [];
  const app = activeApplication.value;
  return [
    {
      title: "基础信息",
      items: [
        { label: "姓名", value: displayValue(app.name) },
        { label: "性别", value: displayValue(app.gender) },
        { label: "年龄", value: displayValue(app.age) },
        { label: "手机号", value: displayValue(app.phone) },
        { label: "邮箱", value: displayValue(app.email) },
        { label: "微信号", value: displayValue(app.wechat) },
        { label: "招聘类型", value: displayValue(app.recruit_type) },
      ],
    },
    {
      title: "应聘信息",
      items: [
        { label: "应聘岗位", value: displayValue(app.job_title) },
        { label: "所属地区", value: displayValue(app.region_name) },
        { label: "应聘区域", value: displayValue(app.apply_region) },
        { label: "应聘公司", value: displayValue(app.apply_company) },
        { label: "期望薪资", value: displayValue(app.expected_salary) },
        { label: "可到岗日期", value: formatDate(app.available_date) },
      ],
    },
    {
      title: "推荐信息",
      items: [
        { label: "招聘来源", value: displayValue(app.recruitment_source) },
        { label: "介绍人姓名", value: displayValue(app.referrer_name) },
        { label: "介绍人关系", value: displayValue(app.referrer_relation) },
        { label: "介绍人单位", value: displayValue(app.referrer_company) },
      ],
    },
    {
      title: "个人情况",
      items: [
        { label: "婚姻情况", value: displayValue(app.marital_status) },
        { label: "出生年月", value: formatDate(app.birth_month) },
        { label: "身高(cm)", value: displayValue(app.height_cm) },
        { label: "体重(kg)", value: displayValue(app.weight_kg) },
        { label: "健康情况", value: displayValue(app.health_status) },
        { label: "民族", value: displayValue(app.ethnicity) },
      ],
    },
    {
      title: "教育信息",
      items: [
        { label: "最高学历", value: displayValue(app.education_level) },
        { label: "起止时间", value: displayValue(app.education_period) },
        { label: "毕业院校", value: displayValue(app.graduate_school) },
        { label: "专业", value: displayValue(app.major) },
        { label: "毕业时间", value: formatDate(app.graduation_date) },
        { label: "职称证书", value: displayValue(app.title_cert) },
        { label: "毕业证编号", value: displayValue(app.diploma_number) },
      ],
    },
    {
      title: "户籍与身份",
      items: [
        { label: "政治面貌", value: displayValue(app.political_status) },
        { label: "户口性质", value: displayValue(app.hukou_type) },
        { label: "籍贯", value: displayValue(app.native_place) },
        { label: "户口所在地", value: displayValue(app.hukou_address) },
        { label: "现住地址", value: displayValue(app.current_address) },
        { label: "身份证号", value: displayValue(app.id_number) },
        { label: "QQ", value: displayValue(app.qq) },
      ],
    },
    {
      title: "紧急联系人",
      items: [
        { label: "联系人姓名", value: displayValue(app.emergency_name) },
        { label: "联系人手机号", value: displayValue(app.emergency_phone) },
        { label: "兴趣爱好", value: displayValue(app.hobbies) },
        { label: "自我评价", value: displayValue(app.self_evaluation) },
      ],
    },
    {
      title: "教育/培训经历",
      blocks: [
        {
          label: "记录",
          value: formatStructuredList(app.education_history, [
            { key: "school", label: "院校" },
            { key: "major", label: "专业" },
            { key: "degree", label: "学历" },
            { key: "start", label: "开始时间" },
            { key: "end", label: "结束时间" },
          ]),
        },
      ],
    },
    {
      title: "工作经历",
      blocks: [
        {
          label: "记录",
          value: formatStructuredList(app.work_history, [
            { key: "company", label: "公司" },
            { key: "position", label: "岗位" },
            { key: "start", label: "开始时间" },
            { key: "end", label: "结束时间" },
          ]),
        },
      ],
    },
    {
      title: "家庭成员",
      blocks: [
        {
          label: "记录",
          value: formatStructuredList(app.family_members, [
            { key: "name", label: "姓名" },
            { key: "relation", label: "关系" },
            { key: "age", label: "年龄" },
            { key: "company", label: "单位" },
            { key: "position", label: "岗位" },
            { key: "phone", label: "手机号" },
          ]),
        },
      ],
    },
  ];
});

watch(
  () => activeTab.value,
  (tab) => {
    ensureTabData(tab);
  }
);

onMounted(async () => {
  if (!token.value) {
    await fetchPublicRegions();
    return;
  }
  try {
    await loadProfile();
    await ensureTabData(activeTab.value, true);
  } catch {
    await logout(true);
  }
});
</script>
