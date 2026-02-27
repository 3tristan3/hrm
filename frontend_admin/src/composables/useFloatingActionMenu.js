import { computed, nextTick, onBeforeUnmount, ref } from "vue";

export const useFloatingActionMenu = ({
  findItemById,
  estimatedWidth = 132,
  offsetY = 6,
}) => {
  const activeMenuItemId = ref(null);
  const menuRef = ref(null);
  const menuAnchor = ref(null);
  const menuStyle = ref({
    top: "0px",
    left: "0px",
  });
  let listenersAttached = false;
  let clickListenerAttached = false;

  const activeMenuItem = computed(() => {
    const itemId = Number(activeMenuItemId.value || 0);
    if (!Number.isFinite(itemId) || itemId <= 0) return null;
    return typeof findItemById === "function" ? findItemById(itemId) : null;
  });

  const detachPositionListeners = () => {
    if (!listenersAttached) return;
    window.removeEventListener("scroll", updateMenuPosition, true);
    window.removeEventListener("resize", updateMenuPosition);
    listenersAttached = false;
  };

  const closeMenu = () => {
    activeMenuItemId.value = null;
    menuAnchor.value = null;
    detachPositionListeners();
  };

  const onGlobalClick = () => {
    closeMenu();
  };

  const bindGlobalClickClose = () => {
    if (clickListenerAttached) return;
    window.addEventListener("click", onGlobalClick);
    clickListenerAttached = true;
  };

  const unbindGlobalClickClose = () => {
    if (!clickListenerAttached) return;
    window.removeEventListener("click", onGlobalClick);
    clickListenerAttached = false;
  };

  const attachPositionListeners = () => {
    if (listenersAttached) return;
    window.addEventListener("scroll", updateMenuPosition, true);
    window.addEventListener("resize", updateMenuPosition);
    listenersAttached = true;
  };

  const updateMenuPosition = async () => {
    if (!menuAnchor.value || !activeMenuItem.value) return;
    const anchorRect = menuAnchor.value.getBoundingClientRect();
    const margin = 8;
    let top = anchorRect.bottom + offsetY;
    let left = anchorRect.right - estimatedWidth;
    left = Math.max(margin, Math.min(left, window.innerWidth - estimatedWidth - margin));
    menuStyle.value = { top: `${top}px`, left: `${left}px` };
    await nextTick();

    const menu = menuRef.value;
    if (!menu) return;
    const width = menu.offsetWidth || estimatedWidth;
    const height = menu.offsetHeight || 0;
    left = anchorRect.right - width;
    left = Math.max(margin, Math.min(left, window.innerWidth - width - margin));
    if (top + height > window.innerHeight - margin) {
      const aboveTop = anchorRect.top - height - offsetY;
      top = aboveTop >= margin ? aboveTop : Math.max(margin, window.innerHeight - height - margin);
    }
    menuStyle.value = { top: `${top}px`, left: `${left}px` };
  };

  const toggleMenuById = (itemId, event) => {
    const normalizedId = Number(itemId || 0);
    if (!Number.isFinite(normalizedId) || normalizedId <= 0) return;
    if (activeMenuItemId.value === normalizedId) {
      closeMenu();
      return;
    }
    activeMenuItemId.value = normalizedId;
    menuAnchor.value = event?.currentTarget || null;
    attachPositionListeners();
    updateMenuPosition();
  };

  onBeforeUnmount(() => {
    unbindGlobalClickClose();
    detachPositionListeners();
  });

  return {
    activeMenuItem,
    menuRef,
    menuStyle,
    closeMenu,
    toggleMenuById,
    bindGlobalClickClose,
    unbindGlobalClickClose,
  };
};
