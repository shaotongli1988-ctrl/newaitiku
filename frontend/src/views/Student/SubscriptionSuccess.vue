<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchStudentSubscriptionStatus } from '../../api/services/student.js'
import { useUserStore } from '../../stores/userStore.js'
import { markStudentOnboardingCompleted } from '../../utils/studentOnboarding.js'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const statusPayload = ref({})

const sourceLabel = computed(() => {
  const source = String(route.query.source || '').trim().toLowerCase()
  if (source === 'redeem') {
    return '兑换开通'
  }
  if (source === 'mock') {
    return '模拟支付开通'
  }
  return '权益开通'
})

const subscription = computed(() => statusPayload.value?.subscription || {})
const isActive = computed(() => Boolean(statusPayload.value?.subscriptionActive))

async function loadStatus() {
  loading.value = true
  try {
    statusPayload.value = (await fetchStudentSubscriptionStatus()) || {}
    if (Boolean(statusPayload.value?.subscriptionActive)) {
      markStudentOnboardingCompleted(userStore.userId)
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStatus()
})
</script>

<template>
  <section class="success-page">
    <article class="success-card">
      <p class="badge">{{ sourceLabel }}</p>
      <h2>{{ isActive ? '恭喜，订阅权益已生效' : '开通请求已受理' }}</h2>
      <p v-if="loading">正在刷新权益状态...</p>
      <template v-else>
        <p>当前状态：<strong>{{ subscription?.status || 'INACTIVE' }}</strong></p>
        <p>生效套餐：{{ subscription?.planCode || '-' }}</p>
        <p>到期时间：{{ subscription?.endTime || '-' }}</p>
      </template>

      <div class="actions">
        <el-button type="primary" @click="router.push('/student/analysis/tasks')">去看今日任务</el-button>
        <el-button @click="router.push('/student/home')">返回学习首页</el-button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.success-page {
  display: grid;
  place-items: center;
  min-height: calc(100vh - 180px);
  padding: 24px;
}

.success-card {
  width: min(560px, 100%);
  display: grid;
  gap: 12px;
  padding: 24px;
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: linear-gradient(
    150deg,
    var(--qb-bg-card) 0%,
    var(--qb-surface-soft-success) 100%
  );
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}

.badge {
  margin: 0;
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--qb-surface-soft-success);
  color: var(--qb-text-success-ink);
  font-size: 12px;
  font-weight: 700;
}

.success-card h2 {
  margin: 0;
  color: var(--qb-text-heading);
}

.success-card p {
  margin: 0;
  color: var(--qb-text-copy);
}

.success-card strong {
  color: var(--qb-text-success-strong);
}

.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 6px;
}

@media (max-width: 768px) {
  .success-page {
    padding: 12px;
    min-height: auto;
  }

  .actions {
    flex-direction: column;
  }
}
</style>
