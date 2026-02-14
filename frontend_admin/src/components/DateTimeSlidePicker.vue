<template>
  <div ref="rootRef" class="dt-classic-picker" role="group" aria-label="日期时间选择器">
    <button type="button" class="dt-trigger" @click="toggleOpen">
      <span class="dt-trigger-label">面试时间</span>
      <span class="dt-trigger-value">{{ selectedDisplayText }}</span>
      <span class="dt-trigger-caret" aria-hidden="true">▾</span>
    </button>

    <div v-if="isOpen" class="dt-popover">
      <div class="dt-popover-head">
        <strong>选择日期时间</strong>
        <button type="button" class="dt-link-btn" @click="closeOpen">完成</button>
      </div>

      <div class="dt-picker-body">
        <div class="dt-date-section">
          <div class="dt-section-title-row">
            <span class="dt-section-title">选择日期</span>
            <div class="dt-month-switch">
              <button type="button" class="dt-month-btn" @click="goPrevMonth" aria-label="上个月">‹</button>
              <span class="dt-month-title">{{ calendarTitle }}</span>
              <button type="button" class="dt-month-btn" @click="goNextMonth" aria-label="下个月">›</button>
            </div>
          </div>

          <div class="dt-week-row">
            <span v-for="week in weekLabels" :key="week">{{ week }}</span>
          </div>

          <div class="dt-calendar-grid">
            <button
              v-for="cell in calendarCells"
              :key="cell.key"
              type="button"
              class="dt-day-cell"
              :class="{
                outside: !cell.currentMonth,
                active: cell.isSelected,
                today: cell.isToday,
              }"
              :disabled="cell.disabled"
              @click="pickDate(cell.value)"
            >
              <span class="dt-day-text">{{ cell.day }}</span>
            </button>
          </div>
        </div>

        <div class="dt-time-section right">
          <div class="dt-section-title">时间</div>
          <div class="dt-wheels narrow">
            <div class="dt-wheel-col">
              <div class="dt-wheel-label">时</div>
              <div class="dt-wheel-box compact">
                <div ref="hourTrackRef" class="dt-wheel-track compact" @scroll.passive="onTrackScroll('hour')">
                  <button
                    v-for="hour in hourOptions"
                    :key="hour"
                    type="button"
                    class="dt-wheel-option"
                    :class="{ active: selectedHour === hour }"
                  :data-hour="hour"
                  @click="pickHour(hour)"
                >
                  <span class="dt-wheel-text">{{ toTwoDigits(hour) }}</span>
                </button>
                </div>
              </div>
            </div>

            <div class="dt-wheel-col">
              <div class="dt-wheel-label">分</div>
              <div class="dt-wheel-box compact">
                <div ref="minuteTrackRef" class="dt-wheel-track compact" @scroll.passive="onTrackScroll('minute')">
                  <button
                    v-for="minute in minuteOptions"
                    :key="minute"
                    type="button"
                    class="dt-wheel-option"
                    :class="{ active: selectedMinute === minute }"
                  :data-minute="minute"
                  @click="pickMinute(minute)"
                >
                  <span class="dt-wheel-text">{{ toTwoDigits(minute) }}</span>
                </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="dt-preview">{{ selectedDisplayText }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  minDate: { type: String, default: "" },
  days: { type: Number, default: 14 },
  startTime: { type: String, default: "00:00" },
  endTime: { type: String, default: "23:55" },
  stepMinutes: { type: Number, default: 5 },
});

const emit = defineEmits(["update:modelValue"]);

const weekLabels = Object.freeze(["一", "二", "三", "四", "五", "六", "日"]);
const rootRef = ref(null);
const hourTrackRef = ref(null);
const minuteTrackRef = ref(null);
const isOpen = ref(false);
const calendarCursor = ref(new Date());

const scrollTimers = {
  hour: null,
  minute: null,
};

const toTwoDigits = (value) => String(value).padStart(2, "0");

const parseTimeToMinutes = (value) => {
  if (!/^\d{2}:\d{2}$/.test(String(value || ""))) return null;
  const [hourText, minuteText] = String(value).split(":");
  const hour = Number(hourText);
  const minute = Number(minuteText);
  if (!Number.isInteger(hour) || !Number.isInteger(minute)) return null;
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return null;
  return hour * 60 + minute;
};

const formatDate = (date) =>
  `${date.getFullYear()}-${toTwoDigits(date.getMonth() + 1)}-${toTwoDigits(date.getDate())}`;

const parseDate = (value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ""))) return null;
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const startOfDay = (value) => new Date(value.getFullYear(), value.getMonth(), value.getDate());

const compareDay = (a, b) => {
  const aStart = startOfDay(a).getTime();
  const bStart = startOfDay(b).getTime();
  if (aStart < bStart) return -1;
  if (aStart > bStart) return 1;
  return 0;
};

const startMinutes = computed(() => parseTimeToMinutes(props.startTime) ?? 8 * 60);
const endMinutes = computed(() => parseTimeToMinutes(props.endTime) ?? 21 * 60 + 55);

const minSelectableDate = computed(() => {
  const base = parseDate(props.minDate) || new Date();
  return startOfDay(base);
});

const hourOptions = computed(() => {
  const startHour = Math.floor(startMinutes.value / 60);
  const endHour = Math.floor(endMinutes.value / 60);
  const list = [];
  for (let hour = startHour; hour <= endHour; hour += 1) list.push(hour);
  return list;
});

const minuteOptions = computed(() => {
  const step = Math.max(props.stepMinutes, 1);
  const list = [];
  for (let minute = 0; minute < 60; minute += step) list.push(minute);
  return list;
});

const clampAndNormalizeTime = (hour, minute) => {
  const step = Math.max(props.stepMinutes, 1);
  let totalMinutes = hour * 60 + minute;
  totalMinutes = Math.max(startMinutes.value, Math.min(endMinutes.value, totalMinutes));
  totalMinutes = Math.round(totalMinutes / step) * step;
  totalMinutes = Math.max(startMinutes.value, Math.min(endMinutes.value, totalMinutes));
  return {
    hour: Math.floor(totalMinutes / 60),
    minute: totalMinutes % 60,
  };
};

const parseModelValue = computed(() => {
  const raw = String(props.modelValue || "");
  if (!raw.includes("T")) return { date: "", hour: null, minute: null };
  const [datePart, timePartRaw = ""] = raw.split("T");
  const totalMinutes = parseTimeToMinutes(timePartRaw.slice(0, 5));
  if (totalMinutes === null) return { date: datePart || "", hour: null, minute: null };
  const normalized = clampAndNormalizeTime(Math.floor(totalMinutes / 60), totalMinutes % 60);
  return {
    date: datePart || "",
    hour: normalized.hour,
    minute: normalized.minute,
  };
});

const selectedDate = computed(() => parseModelValue.value.date || "");
const selectedHour = computed(() => parseModelValue.value.hour);
const selectedMinute = computed(() => parseModelValue.value.minute);
const selectedDateObject = computed(() => parseDate(selectedDate.value));

const getDefaultDate = () => formatDate(minSelectableDate.value);

const getDefaultTime = () => {
  const seedHour = Math.floor(startMinutes.value / 60);
  const seedMinute = startMinutes.value % 60;
  return clampAndNormalizeTime(seedHour, seedMinute);
};

const emitDateTime = (date, hour, minute) => {
  if (!date || hour === null || minute === null) return;
  const normalized = clampAndNormalizeTime(hour, minute);
  const next = `${date}T${toTwoDigits(normalized.hour)}:${toTwoDigits(normalized.minute)}`;
  if (next === String(props.modelValue || "")) return;
  emit("update:modelValue", next);
};

const ensureInitialized = () => {
  if (String(props.modelValue || "").includes("T")) return;
  const date = getDefaultDate();
  const time = getDefaultTime();
  emitDateTime(date, time.hour, time.minute);
};

const syncCalendarCursor = () => {
  const base = selectedDateObject.value || minSelectableDate.value;
  calendarCursor.value = new Date(base.getFullYear(), base.getMonth(), 1);
};

const pickDate = (date) => {
  const parsed = parseDate(date);
  if (!parsed) return;
  if (compareDay(parsed, minSelectableDate.value) < 0 && date !== selectedDate.value) return;
  const hour = selectedHour.value ?? getDefaultTime().hour;
  const minute = selectedMinute.value ?? getDefaultTime().minute;
  emitDateTime(date, hour, minute);
  calendarCursor.value = new Date(parsed.getFullYear(), parsed.getMonth(), 1);
};

const pickHour = (hour) => {
  const minute = selectedMinute.value ?? getDefaultTime().minute;
  emitDateTime(selectedDate.value || getDefaultDate(), hour, minute);
};

const pickMinute = (minute) => {
  const hour = selectedHour.value ?? getDefaultTime().hour;
  emitDateTime(selectedDate.value || getDefaultDate(), hour, minute);
};

const goPrevMonth = () => {
  const current = calendarCursor.value;
  calendarCursor.value = new Date(current.getFullYear(), current.getMonth() - 1, 1);
};

const goNextMonth = () => {
  const current = calendarCursor.value;
  calendarCursor.value = new Date(current.getFullYear(), current.getMonth() + 1, 1);
};

const calendarTitle = computed(() =>
  new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long" }).format(calendarCursor.value),
);

const calendarCells = computed(() => {
  const year = calendarCursor.value.getFullYear();
  const month = calendarCursor.value.getMonth();
  const firstDay = new Date(year, month, 1);
  const daysInCurrentMonth = new Date(year, month + 1, 0).getDate();
  const leading = (firstDay.getDay() + 6) % 7;
  const total = 42;
  const cells = [];

  for (let index = 0; index < total; index += 1) {
    const offset = index - leading;
    const cellDate = new Date(year, month, 1 + offset);
    const value = formatDate(cellDate);
    const currentMonth = cellDate.getMonth() === month;
    const disabledByMin = compareDay(cellDate, minSelectableDate.value) < 0;
    const disabled = disabledByMin && value !== selectedDate.value;
    const isToday = compareDay(cellDate, new Date()) === 0;
    const isSelected = value === selectedDate.value;

    cells.push({
      key: `${value}-${index}`,
      day: cellDate.getDate(),
      value,
      currentMonth,
      disabled,
      isToday,
      isSelected,
      inRange: cellDate.getDate() <= daysInCurrentMonth,
    });
  }

  return cells;
});

const selectedDisplayText = computed(() => {
  const value = String(props.modelValue || "");
  if (!value.includes("T")) return "请选择日期时间";
  const parsed = new Date(value.length === 16 ? `${value}:00` : value);
  if (Number.isNaN(parsed.getTime())) return value.replace("T", " ");
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(parsed);
});

const centerOption = (trackRef, selector, behavior = "smooth") => {
  const track = trackRef.value;
  if (!track) return;
  const target = track.querySelector(selector);
  if (!target) return;
  target.scrollIntoView({ behavior, block: "center", inline: "nearest" });
};

const nearestByCenter = (trackRef, selector) => {
  const track = trackRef.value;
  if (!track) return null;
  const items = Array.from(track.querySelectorAll(selector));
  if (!items.length) return null;
  const rect = track.getBoundingClientRect();
  const centerY = rect.top + rect.height / 2;
  let closest = items[0];
  let minDiff = Number.POSITIVE_INFINITY;
  for (const item of items) {
    const itemRect = item.getBoundingClientRect();
    const diff = Math.abs(itemRect.top + itemRect.height / 2 - centerY);
    if (diff < minDiff) {
      minDiff = diff;
      closest = item;
    }
  }
  return closest;
};

const onTrackScroll = (kind) => {
  if (scrollTimers[kind]) clearTimeout(scrollTimers[kind]);
  scrollTimers[kind] = setTimeout(() => {
    if (kind === "hour") {
      const target = nearestByCenter(hourTrackRef, "[data-hour]");
      const value = Number(target?.dataset?.hour);
      if (Number.isInteger(value) && value !== selectedHour.value) pickHour(value);
      if (target) centerOption(hourTrackRef, `[data-hour="${value}"]`);
      return;
    }
    const target = nearestByCenter(minuteTrackRef, "[data-minute]");
    const value = Number(target?.dataset?.minute);
    if (Number.isInteger(value) && value !== selectedMinute.value) pickMinute(value);
    if (target) centerOption(minuteTrackRef, `[data-minute="${value}"]`);
  }, 90);
};

const syncWheelCenter = (behavior = "smooth") => {
  if (selectedHour.value !== null) {
    centerOption(hourTrackRef, `[data-hour="${selectedHour.value}"]`, behavior);
  }
  if (selectedMinute.value !== null) {
    centerOption(minuteTrackRef, `[data-minute="${selectedMinute.value}"]`, behavior);
  }
};

const closeOpen = () => {
  isOpen.value = false;
};

const toggleOpen = async () => {
  isOpen.value = !isOpen.value;
  if (!isOpen.value) return;
  syncCalendarCursor();
  await nextTick();
  syncWheelCenter("auto");
};

const onPointerDown = (event) => {
  if (!isOpen.value) return;
  const root = rootRef.value;
  if (!root) return;
  const target = event.target;
  if (target instanceof Node && !root.contains(target)) {
    isOpen.value = false;
  }
};

watch(selectedHour, async (value) => {
  if (value === null || !isOpen.value) return;
  await nextTick();
  centerOption(hourTrackRef, `[data-hour="${value}"]`);
});

watch(selectedMinute, async (value) => {
  if (value === null || !isOpen.value) return;
  await nextTick();
  centerOption(minuteTrackRef, `[data-minute="${value}"]`);
});

watch(
  () => props.minDate,
  () => {
    if (!selectedDateObject.value) {
      ensureInitialized();
    } else {
      syncCalendarCursor();
    }
  },
  { immediate: true },
);

onMounted(() => {
  ensureInitialized();
  syncCalendarCursor();
  document.addEventListener("pointerdown", onPointerDown);
});

onBeforeUnmount(() => {
  Object.keys(scrollTimers).forEach((key) => {
    if (scrollTimers[key]) clearTimeout(scrollTimers[key]);
  });
  document.removeEventListener("pointerdown", onPointerDown);
});
</script>

<style scoped>
.dt-classic-picker {
  position: relative;
  width: min(100%, 330px);
}
.dt-trigger {
  width: 100%;
  border: 1px solid #cfd8e6;
  border-radius: 8px;
  background: #ffffff;
  min-height: 32px;
  padding: 3px 7px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}
.dt-trigger:hover {
  border-color: #93c5fd;
}
.dt-trigger:focus-visible {
  outline: none;
  border-color: #1d4ed8;
  box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.18);
}
.dt-trigger-label {
  font-size: 11px;
  color: #64748b;
}
.dt-trigger-value {
  font-size: 12px;
  color: #0f172a;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dt-trigger-caret {
  font-size: 12px;
  color: #64748b;
}
.dt-popover {
  position: absolute;
  z-index: 35;
  top: calc(100% + 6px);
  left: 0;
  width: min(100vw - 44px, 320px);
  border: 1px solid #d1dced;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.16);
  padding: 5px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.dt-picker-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 100px;
  gap: 4px;
  align-items: start;
}
.dt-popover-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dt-popover-head strong {
  font-size: 12px;
  color: #0f172a;
}
.dt-link-btn {
  border: none;
  background: transparent;
  color: #1d4ed8;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}
.dt-section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 4px;
  margin-bottom: 0;
}
.dt-section-title {
  font-size: 11px;
  color: #64748b;
}
.dt-time-section.right {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dt-month-switch {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}
.dt-month-title {
  min-width: 74px;
  text-align: center;
  font-size: 11px;
  color: #334155;
}
.dt-month-btn {
  width: 18px;
  height: 18px;
  border: 1px solid #d6dfea;
  border-radius: 6px;
  background: #ffffff;
  color: #334155;
  cursor: pointer;
  line-height: 1;
}
.dt-month-btn:hover {
  border-color: #93c5fd;
  color: #1d4ed8;
  background: #eff6ff;
}
.dt-week-row {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0;
  margin-bottom: 0;
}
.dt-week-row span {
  text-align: center;
  font-size: 10px;
  color: #94a3b8;
}
.dt-calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0;
}
.dt-day-cell {
  min-height: 22px;
  border: none;
  border-radius: 0;
  background: transparent;
  font-size: 13px;
  color: #334155;
  padding: 0;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: color 0.16s ease;
}
.dt-day-cell:hover {
  color: #1d4ed8;
}
.dt-day-text {
  width: 21px;
  height: 21px;
  border-radius: 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.16s ease, color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
}
.dt-day-cell:hover .dt-day-text {
  background: rgba(219, 234, 254, 0.45);
}
.dt-day-cell.outside {
  color: #cbd5e1;
}
.dt-day-cell.today {
  color: #2563eb;
}
.dt-day-cell.today .dt-day-text {
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.55);
}
.dt-day-cell.active {
  color: #ffffff;
  font-weight: 700;
}
.dt-day-cell.active .dt-day-text {
  background: #2563eb;
  color: #ffffff;
  box-shadow: 0 3px 8px rgba(37, 99, 235, 0.34);
  transform: translateY(-1px);
}
.dt-day-cell.outside.active .dt-day-text,
.dt-day-cell.today.active .dt-day-text {
  background: #2563eb;
  color: #ffffff;
}
.dt-day-cell.active:disabled {
  opacity: 1;
}
.dt-day-cell:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.dt-wheels {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 3px;
}
.dt-wheels.narrow {
  gap: 2px;
}
.dt-wheel-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dt-wheel-label {
  font-size: 11px;
  color: #64748b;
}
.dt-wheel-box {
  position: relative;
  border: 1px solid #d2dbe8;
  border-radius: 8px;
  background: #f8fbff;
  overflow: hidden;
  --row-height: 24px;
}
.dt-wheel-box.compact {
  --row-height: 22px;
}
.dt-wheel-box::before,
.dt-wheel-box::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  height: calc(var(--row-height) * 2);
  z-index: 1;
  pointer-events: none;
}
.dt-wheel-box::before {
  top: 0;
  background: linear-gradient(180deg, rgba(248, 251, 255, 0.96), rgba(248, 251, 255, 0));
}
.dt-wheel-box::after {
  bottom: 0;
  background: linear-gradient(0deg, rgba(248, 251, 255, 0.96), rgba(248, 251, 255, 0));
}
.dt-wheel-track {
  height: calc(var(--row-height) * 5);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: calc(var(--row-height) * 2) 0;
  scroll-snap-type: y mandatory;
  scrollbar-gutter: stable both-edges;
}
.dt-wheel-track.compact {
  height: calc(var(--row-height) * 5);
}
.dt-wheel-track::-webkit-scrollbar {
  width: 4px;
}
.dt-wheel-track::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 999px;
}
.dt-wheel-option {
  min-height: var(--row-height);
  width: 100%;
  border: none;
  border-radius: 0;
  background: transparent;
  color: #475569;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  cursor: pointer;
  scroll-snap-align: center;
  font-size: 12px;
  line-height: 1.2;
  transition: color 0.16s ease, font-weight 0.16s ease;
}
.dt-wheel-text {
  width: 21px;
  height: 21px;
  border-radius: 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
}
.dt-wheel-option:hover {
  color: #1d4ed8;
}
.dt-wheel-option.active {
  color: #ffffff;
  font-weight: 700;
}
.dt-wheel-option.active .dt-wheel-text {
  background: #2563eb;
  color: #ffffff;
  box-shadow: 0 3px 8px rgba(37, 99, 235, 0.3);
}
.dt-wheel-option:focus-visible,
.dt-day-cell:focus-visible,
.dt-link-btn:focus-visible,
.dt-month-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(29, 78, 216, 0.2);
}
.dt-preview {
  font-size: 11px;
  color: #334155;
  padding-top: 2px;
}
@media (max-width: 900px) {
  .dt-popover {
    width: min(100vw - 32px, 320px);
  }
  .dt-picker-body {
    grid-template-columns: 1fr;
  }
}
</style>
