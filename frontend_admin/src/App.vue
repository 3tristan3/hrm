<template>
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
              <span class="chip">{{ jobs.length }} 个岗位</span>
            </div>
          </div>
          <div class="card-body job-body">
            <div class="job-toolbar">
              <div class="job-toolbar-left">
                <button class="btn btn-sm btn-primary" @click="openNewJob">新增岗位</button>
                <button class="btn btn-sm btn-default" @click="fetchJobs">刷新列表</button>
              </div>
              <div class="job-toolbar-right">
                <span class="chip subtle">已选 {{ selectedJobsCount }} 个</span>
                <button
                  class="btn btn-sm btn-danger"
                  :disabled="selectedJobIds.length === 0"
                  @click="batchDeleteJobs"
                >
                  批量删除
                </button>
              </div>
            </div>

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
                <tr v-for="item in jobs" :key="item.id">
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
        <div v-else-if="activeTab === 'applications'" class="card">
          <div class="card-header applications-header">
            <div>
              <h3>应聘记录明细</h3>
              <p class="header-sub">显示 {{ filteredApplications.length }} / {{ applications.length }} 条</p>
            </div>
            <button class="btn btn-sm btn-primary" type="button" @click="refreshApplications">刷新数据</button>
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
            <div v-if="groupedApplications.length" class="application-groups">
              <section v-for="group in groupedApplications" :key="group.title" class="application-group">
                <div class="group-header">
                  <div>
                    <h4>{{ group.title }}</h4>
                    <p class="text-muted">共 {{ group.items.length }} 条应聘记录</p>
                  </div>
                  <span class="chip subtle">{{ group.items.length }} 条</span>
                </div>
                <div class="application-grid">
                  <div v-for="item in group.items" :key="item.id" class="application-card" @click="openApplication(item)">
                    <div class="card-photo">
                      <img v-if="item.photo_url" :src="item.photo_url" alt="个人照片" />
                      <div v-else class="photo-fallback">{{ item.name ? item.name.slice(0, 1) : "?" }}</div>
                      <span class="card-pill">{{ item.job_title }}</span>
                    </div>
                    <div class="app-card-body">
                      <div class="card-title-row">
                        <div class="card-name">{{ item.name }}</div>
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
                    <div class="card-cta">
                      <span>查看详情</span>
                      <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none">
                        <polyline points="9 18 15 12 9 6"></polyline>
                      </svg>
                    </div>
                  </div>
                </div>
              </section>
            </div>
            <div v-else class="empty-state">暂无匹配的应聘记录</div>
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
              <img v-if="activeApplication.photo_url" :src="activeApplication.photo_url" alt="个人照片" />
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
// 引入新拆分的组件
import UISwitch from './components/UISwitch.vue';
import Toast from './components/Toast.vue';
import ConfirmDialog from './components/ConfirmDialog.vue';
import { buildApiUrl } from "./config/runtime";

const toastRef = ref(null);
const confirmRef = ref(null);

// === 环境变量与基础配置 ===
const adminBase = buildApiUrl("api/admin");
const authBase = buildApiUrl("api/auth");

// === 状态管理 ===
const token = ref(localStorage.getItem("admin_token") || "");
const currentUsername = ref(localStorage.getItem("admin_username") || "");
const authMode = ref("login");
const activeTab = ref("jobs");

const tabs = [
  { key: "regions", label: "地区管理", adminOnly: true },
  { key: "jobs", label: "岗位管理", adminOnly: false },
  { key: "applications", label: "应聘记录", adminOnly: false },
  { key: "accounts", label: "账号管理", adminOnly: true },
];

const authForm = reactive({ username: "", password: "", region_id: "" });
const jobForm = reactive({ id: null, region: "", title: "", description: "", salary: "", education: "", order: 0, is_active: true });
const passwordForm = reactive({ user_id: "", password: "" });
const selfPasswordForm = reactive({ old_password: "", new_password: "", confirm_password: "" });
const selectedJobIds = ref([]);
const showJobForm = ref(false);
const applicationFilters = reactive({ job: "all", region: "" });

const publicRegions = ref([]);
const regions = ref([]);
const jobs = ref([]);
const applications = ref([]);
const users = ref([]);
const userProfile = reactive({ can_view_all: false, region_name: "", region_id: null, is_superuser: false });
const activeApplication = ref(null);
const applicationDetailLoading = ref(false);
const dataLoaded = reactive({ regions: false, jobs: false, applications: false, users: false });
const dataLoading = reactive({ regions: false, jobs: false, applications: false, users: false });

// === 计算属性 ===
const visibleTabs = computed(() =>
  tabs.filter((tab) => (tab.adminOnly ? userProfile.is_superuser : true))
);
const currentTitle = computed(
  () => visibleTabs.value.find((t) => t.key === activeTab.value)?.label || "管理后台"
);
const userInitial = computed(() => (currentUsername.value ? currentUsername.value[0].toUpperCase() : "A"));
const showRegionFilter = computed(() => userProfile.can_view_all || userProfile.is_superuser);
const regionFilteredApplications = computed(() => {
  const regionKeyword = applicationFilters.region.trim().toLowerCase();
  return applications.value.filter((item) => {
    const regionValue = (item.region_name || "").toLowerCase();
    return !regionKeyword || regionValue === regionKeyword;
  });
});
const jobCategories = computed(() => {
  const counts = new Map();
  regionFilteredApplications.value.forEach((item) => {
    const title = item.job_title || "未填写岗位";
    counts.set(title, (counts.get(title) || 0) + 1);
  });
  const categories = Array.from(counts.entries())
    .map(([title, count]) => ({ label: title, value: title, count }))
    .sort((a, b) => a.label.localeCompare(b.label, "zh-Hans-CN"));
  return [{ label: "全部岗位", value: "all", count: regionFilteredApplications.value.length }, ...categories];
});
const filteredApplications = computed(() => {
  const jobKeyword = applicationFilters.job;
  if (jobKeyword === "all") return regionFilteredApplications.value;
  return regionFilteredApplications.value.filter((item) => (item.job_title || "未填写岗位") === jobKeyword);
});
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

const selectedJobsCount = computed(() => selectedJobIds.value.length);
const isAllJobsSelected = computed({
  get() {
    return jobs.value.length > 0 && jobs.value.every((job) => selectedJobIds.value.includes(job.id));
  },
  set(value) {
    selectedJobIds.value = value ? jobs.value.map((job) => job.id) : [];
  }
});

// === API 请求封装 ===
const extractErrorMessage = (payload) => {
  if (!payload || typeof payload !== "object") return "请求失败";
  if (payload.error) return payload.error;
  if (payload.detail) return payload.detail;
  if (payload.details) {
    if (typeof payload.details === "string") return payload.details;
    const detailKeys = Object.keys(payload.details);
    if (detailKeys.length) {
      const val = payload.details[detailKeys[0]];
      if (Array.isArray(val) && val.length) return val[0];
      if (typeof val === "string") return val;
    }
  }
  const keys = Object.keys(payload);
  if (keys.length) {
    const val = payload[keys[0]];
    if (Array.isArray(val) && val.length) return val[0];
    if (typeof val === "string") return val;
  }
  return "请求失败";
};

const request = async (url, options = {}) => {
  const headers = { "Content-Type": "application/json" };
  if (token.value) headers.Authorization = `Token ${token.value}`;
  
  const response = await fetch(url, { headers, ...options });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(extractErrorMessage(payload));
  }
  return response.status === 204 ? {} : response.json();
};

const notifyError = (err) => {
  console.error(err);
  // 修正：使用自定义 Toast
  toastRef.value?.show(err.message || "操作失败", 'error');
};
const notifySuccess = (msg) => {
  toastRef.value?.show(msg, 'success');
};

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
    if (!res.ok) throw new Error(extractErrorMessage(payload));

    token.value = payload.token;
    currentUsername.value = authForm.username;
    localStorage.setItem("admin_token", payload.token);
    localStorage.setItem("admin_username", authForm.username);
    dataLoaded.regions = false;
    dataLoaded.jobs = false;
    dataLoaded.applications = false;
    dataLoaded.users = false;

    notifySuccess("登录成功");
    await loadProfile();
    await ensureTabData(activeTab.value, true);
  } catch (err) {
    notifyError(err);
  }
};

const logout = async (silent = false) => {
  let isConfirmed = true;
  if (!silent) {
    isConfirmed = await confirmRef.value.open({
      title: '退出确认',
      content: '您确定要退出当前账号吗？',
      confirmText: '退出',
      type: 'danger'
    });
  }
  if (isConfirmed) {
    token.value = "";
    localStorage.removeItem("admin_token");
    localStorage.removeItem("admin_username");
    currentUsername.value = "";
    regions.value = [];
    jobs.value = [];
    applications.value = [];
    users.value = [];
    dataLoaded.regions = false;
    dataLoaded.jobs = false;
    dataLoaded.applications = false;
    dataLoaded.users = false;
    dataLoading.regions = false;
    dataLoading.jobs = false;
    dataLoading.applications = false;
    dataLoading.users = false;
    activeApplication.value = null;
    applicationDetailLoading.value = false;
    userProfile.can_view_all = false;
    userProfile.region_name = "";
    userProfile.region_id = null;
    userProfile.is_superuser = false;
    activeTab.value = "jobs";
    fetchPublicRegions();
    if (!silent) notifySuccess("已退出登录");
  }
};

// === CRUD 操作 ===
const regionName = (id) => regions.value.find(r => r.id === id)?.name || "-";
const formatTime = (v) => v ? new Date(v).toLocaleString() : "-";
const formatDate = (v) => {
  if (!v) return "-";
  const date = new Date(v);
  if (Number.isNaN(date.getTime())) return v;
  return date.toLocaleDateString();
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
  const ok = await confirmRef.value.open({
    title: '删除岗位',
    content: '此操作将永久删除该岗位及其关联数据，是否继续？',
    type: 'danger',
  });
  if (!ok) return;
  try {
    await request(`${adminBase}/jobs/${id}/`, { method: "DELETE" });
    notifySuccess("删除成功");
    await loadJobs(true);
  } catch (err) {
    notifyError(err);
  }
};
const batchDeleteJobs = async () => {
  if (!selectedJobIds.value.length) return;
  const ok = await confirmRef.value.open({
    title: "批量删除岗位",
    content: `将删除已选中的 ${selectedJobIds.value.length} 个岗位，是否继续？`,
    type: "danger",
    confirmText: "删除"
  });
  if (!ok) return;
  const ids = [...selectedJobIds.value];
  const results = await Promise.allSettled(
    ids.map((id) => request(`${adminBase}/jobs/${id}/`, { method: "DELETE" }))
  );
  const success = results.filter((item) => item.status === "fulfilled").length;
  const fail = results.length - success;
  if (success) notifySuccess(`已删除 ${success} 个岗位`);
  if (fail) toastRef.value?.show(`${fail} 个岗位删除失败`, "error");
  await loadJobs(true);
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
    await request(`${authBase}/password/`, {
      method: "POST",
      body: JSON.stringify({ old_password, new_password })
    });
    notifySuccess("密码已更新");
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
  const ok = await confirmRef.value.open({
    title: "删除账号",
    content: `确定删除账号「${item.username}」吗？该操作不可恢复。`,
    type: "danger",
    confirmText: "删除"
  });
  if (!ok) return;
  try {
    await request(`${adminBase}/users/${item.id}/`, { method: "DELETE" });
    notifySuccess("账号已删除");
    await loadUsers(true);
  } catch (err) {
    notifyError(err);
  }
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

const resetApplicationFilters = () => {
  applicationFilters.job = "all";
  applicationFilters.region = "";
};

const openApplication = async (item) => {
  applicationDetailLoading.value = true;
  activeApplication.value = { ...item };
  try {
    const detail = await request(`${adminBase}/applications/${item.id}/`);
    activeApplication.value = detail;
  } catch (err) {
    notifyError(err);
    activeApplication.value = null;
  } finally {
    applicationDetailLoading.value = false;
  }
};

const closeApplication = () => {
  activeApplication.value = null;
  applicationDetailLoading.value = false;
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
