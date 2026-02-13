<template>
  <!-- 文件说明：面试通过人员模块组件，展示多轮面试结果摘要。 -->
  <!-- 面试通过人员列表（按轮次拆分展示关键字段） -->
  <div class="card passed-card">
    <div class="card-header interview-header">
      <div>
        <h3>{{ title }}</h3>
        <p class="header-sub">{{ countPrefix }} {{ items.length }} 人</p>
      </div>
      <div class="applications-header-actions">
        <button class="btn btn-sm btn-default" type="button" @click="$emit('refresh')">刷新列表</button>
      </div>
    </div>
    <div class="card-body">
      <div class="passed-scroll">
        <div v-if="items.length" class="passed-table-wrap">
          <table class="data-table passed-table">
            <thead>
              <tr>
                <th>姓名</th>
                <th>岗位</th>
                <th>地区</th>
                <th>手机号</th>
                <th>招聘类型</th>
                <th>学历</th>
                <th>第一轮</th>
                <th>第一轮评分</th>
                <th>第一轮面试官</th>
                <th>第二轮</th>
                <th>第二轮评分</th>
                <th>第二轮面试官</th>
                <th>第三轮</th>
                <th>第三轮评分</th>
                <th>第三轮面试官</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id">
                <td class="font-medium">{{ item.name || "-" }}</td>
                <td>{{ item.job_title || "-" }}</td>
                <td>{{ item.region_name || "-" }}</td>
                <td>{{ item.phone || "-" }}</td>
                <td>{{ item.recruit_type || "-" }}</td>
                <td>{{ item.education_level || "-" }}</td>
                <td>{{ formatTime(item.first_round_at) }}</td>
                <td>{{ item.first_round_score ?? "-" }}</td>
                <td>{{ item.first_round_interviewer || "-" }}</td>
                <td>{{ formatTime(item.second_round_at) }}</td>
                <td>{{ item.second_round_score ?? "-" }}</td>
                <td>{{ item.second_round_interviewer || "-" }}</td>
                <td>{{ formatTime(item.third_round_at) }}</td>
                <td>{{ item.third_round_score ?? "-" }}</td>
                <td>{{ item.third_round_interviewer || "-" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">{{ emptyText }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  title: {
    type: String,
    default: "面试通过人员",
  },
  countPrefix: {
    type: String,
    default: "已通过",
  },
  emptyText: {
    type: String,
    default: "暂无面试通过人员",
  },
});

defineEmits(["refresh"]);

// 列表内统一时间展示
const formatTime = (value) => (value ? new Date(value).toLocaleString() : "-");
</script>
