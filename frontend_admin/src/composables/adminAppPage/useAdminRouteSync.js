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
    [() => route.name, () => token.value],
    ([name, hasToken]) => {
      const tabKey = typeof name === "string" ? name : "";
      if (tabKey === "login") {
        if (hasToken) {
          const fallback = resolveFallbackTab();
          if (fallback && route.name !== fallback) {
            router.replace({ name: fallback });
          }
        }
        return;
      }
      if (!isKnownTab(tabKey)) {
        if (!hasToken) {
          if (route.name !== "login") router.replace({ name: "login" });
          return;
        }
        const fallback = resolveFallbackTab();
        if (fallback && route.name !== fallback) {
          if (activeTab.value !== fallback) activeTab.value = fallback;
          router.replace({ name: fallback });
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
      if (!tab || route.name === tab || route.name === "login") return;
      if (isKnownTab(tab)) {
        router.replace({ name: tab });
      }
    }
  );
}
