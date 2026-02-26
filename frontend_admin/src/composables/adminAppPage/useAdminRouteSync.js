import { watch } from "vue";

export function useAdminRouteSync({
  route,
  router,
  tabs,
  visibleTabs,
  activeTab,
  token,
  userProfile,
}) {
  const isKnownTab = (key) => tabs.some((item) => item.key === key);
  const resolveFallbackTab = () => visibleTabs.value?.[0]?.key || "jobs";

  watch(
    () => route.name,
    (name) => {
      const tabKey = typeof name === "string" ? name : "";
      if (!isKnownTab(tabKey)) {
        const fallback = resolveFallbackTab();
        if (fallback) {
          if (activeTab.value !== fallback) activeTab.value = fallback;
          if (route.name !== fallback) router.replace({ name: fallback });
        }
        return;
      }
      if (activeTab.value !== tabKey) {
        activeTab.value = tabKey;
      }
    },
    { immediate: true }
  );

  watch(
    () => (visibleTabs.value || []).map((item) => item.key).join("|"),
    () => {
      const profileReady =
        Boolean(userProfile.region_id) ||
        Boolean(userProfile.is_superuser) ||
        Boolean(userProfile.can_view_all);
      if (!token.value || !profileReady) return;
      const fallback = resolveFallbackTab();
      const isVisible = (visibleTabs.value || []).some(
        (item) => item.key === activeTab.value
      );
      if (!isVisible && fallback) {
        activeTab.value = fallback;
        if (route.name !== fallback) router.replace({ name: fallback });
      }
    },
    { immediate: true }
  );

  watch(
    () => activeTab.value,
    (tab) => {
      if (!tab || route.name === tab) return;
      if (isKnownTab(tab)) {
        router.replace({ name: tab });
      }
    }
  );
}
