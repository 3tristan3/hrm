import { createRouter, createWebHistory } from "vue-router";

const EmptyView = { name: "EmptyView", render: () => null };

const routes = [
  { path: "/", redirect: "/jobs" },
  { path: "/login", name: "login", component: EmptyView },
  { path: "/regions", name: "regions", component: EmptyView, meta: { adminOnly: true } },
  { path: "/jobs", name: "jobs", component: EmptyView },
  { path: "/applications", name: "applications", component: EmptyView },
  { path: "/interviews", name: "interviews", component: EmptyView },
  { path: "/passed", name: "passed", component: EmptyView },
  { path: "/talent", name: "talent", component: EmptyView },
  { path: "/operation-logs", name: "operationLogs", component: EmptyView },
  { path: "/accounts", name: "accounts", component: EmptyView, meta: { adminOnly: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  const hasToken = Boolean(localStorage.getItem("admin_token"));
  if (to.name === "login") {
    if (hasToken) return { path: "/jobs", replace: true };
    return true;
  }
  if (!hasToken) {
    return { path: "/login", query: to.query, replace: true };
  }
  if (!to.meta?.adminOnly) return true;
  const flag = localStorage.getItem("admin_is_superuser");
  if (flag === "false") {
    return { path: "/jobs", replace: true };
  }
  return true;
});

export default router;
