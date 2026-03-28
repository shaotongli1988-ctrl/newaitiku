<script setup>
import { computed } from 'vue'

/**
 * 组件定位：通用 AI 任务进度条。
 * 设计目的：统一展示“任务阶段 + 进度百分比 + 状态文案”，避免每个页面重复实现。
 */
const props = defineProps({
  title: {
    type: String,
    default: 'AI 处理进度',
  },
  percentage: {
    type: Number,
    default: 0,
  },
  statusText: {
    type: String,
    default: '等待执行',
  },
})

/**
 * 对传入百分比进行边界保护，确保 Element Plus 进度条始终接收 0-100 的安全值。
 * 同时避免后端偶发脏数据导致 UI 组件报错。
 */
const safePercentage = computed(() => Math.max(0, Math.min(100, props.percentage)))
</script>

<template>
  <!--
    进度区域采用纵向 Flex 排列：标题、进度条、状态文案逐行展示。
    布局紧凑，适合在各种角色仪表盘中复用。
  -->
  <article class="progress-card">
    <!-- 中文说明：标题描述当前任务类型，例如“AI 审核任务 / AI 学习任务”。 -->
    <header class="progress-header">{{ title }}</header>
    <!-- 中文说明：核心进度条，统一使用同一视觉密度，保持跨页面一致。 -->
    <el-progress :percentage="safePercentage" :stroke-width="14" />
    <!-- 中文说明：状态文案用于承载阶段说明、异常提示或排队信息。 -->
    <p class="progress-status">{{ statusText }}</p>
  </article>
</template>

<style scoped>
.progress-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border-radius: 10px;
  background: var(--qb-primary-soft-bg);
}

.progress-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--qb-text-strong);
}

.progress-status {
  margin: 0;
  color: var(--qb-text-subtle-1);
  font-size: 13px;
}
</style>
