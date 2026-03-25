<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import {
  confirmStudentSubscriptionOrder,
  createStudentSubscriptionOrder,
  fetchStudentSubscriptionPlans,
  fetchStudentSubscriptionStatus,
  redeemStudentSubscriptionCode,
} from '../../api/services/student.js'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const payLoading = ref(false)
const redeemLoading = ref(false)
const plans = ref([])
const statusPayload = ref({})
const redeemCode = ref('')

const selectedPlan = computed(() => (Array.isArray(plans.value) ? plans.value[0] : null))
const currentSubscription = computed(() => statusPayload.value?.subscription || {})
const subscriptionActive = computed(() => Boolean(statusPayload.value?.subscriptionActive))

async function loadData() {
  loading.value = true
  try {
    const [statusData, planRows] = await Promise.all([
      fetchStudentSubscriptionStatus(),
      fetchStudentSubscriptionPlans(),
    ])
    statusPayload.value = statusData || {}
    plans.value = Array.isArray(planRows) ? planRows : []
  } catch (error) {
    ElMessage.error(error?.message || '加载订阅信息失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

async function submitRedeemCode() {
  const code = String(redeemCode.value || '').trim()
  if (!code) {
    ElMessage.warning('请输入兑换码。')
    return
  }
  redeemLoading.value = true
  try {
    const result = await redeemStudentSubscriptionCode({
      code,
      requestId: `redeem-${Date.now()}`,
    })
    ElMessage.success('兑换成功，权益已开通。')
    router.push({
      path: '/student/subscription/success',
      query: {
        source: 'redeem',
        endTime: String(result?.subscription?.endTime || '').trim(),
      },
    })
  } catch (error) {
    ElMessage.error(error?.message || '兑换失败，请检查兑换码后重试。')
  } finally {
    redeemLoading.value = false
  }
}

async function submitMockPayment() {
  if (!selectedPlan.value?.planCode) {
    ElMessage.warning('当前暂无可用套餐。')
    return
  }
  payLoading.value = true
  try {
    const created = await createStudentSubscriptionOrder({
      planCode: String(selectedPlan.value.planCode).trim(),
      sourceType: 'CHECKOUT',
      sessionId: String(route.query.sessionId || '').trim(),
    })
    const orderId = String(created?.order?.orderId || '').trim()
    if (!orderId) {
      throw new Error('订单创建失败，请稍后重试。')
    }
    const transactionNo = `MOCK-TXN-${Date.now()}`
    const confirmed = await confirmStudentSubscriptionOrder(orderId, {
      transactionNo,
      requestId: `mock-${Date.now()}`,
    })
    ElMessage.success(confirmed?.idempotent ? '订单已确认。' : '模拟支付成功，权益已开通。')
    router.push({
      path: '/student/subscription/success',
      query: {
        source: 'mock',
        orderId,
      },
    })
  } catch (error) {
    ElMessage.error(error?.message || '模拟支付失败，请稍后重试。')
  } finally {
    payLoading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <section class="checkout-page">
    <header class="checkout-header">
      <p class="checkout-tag">订阅开通</p>
      <h2>完成兑换或模拟支付，立即开通 AI 提分权益</h2>
      <p>本页用于 MVP 阶段转化闭环验证，真实支付将于后续批次接入。</p>
    </header>

    <article v-if="loading" class="checkout-card">
      正在加载订阅信息...
    </article>

    <template v-else>
      <article class="checkout-card status-card">
        <h3>当前权益状态</h3>
        <p>
          状态：
          <strong :class="{ active: subscriptionActive }">
            {{ currentSubscription?.status || 'INACTIVE' }}
          </strong>
        </p>
        <p>到期时间：{{ currentSubscription?.endTime || '-' }}</p>
      </article>

      <article class="checkout-card plan-card">
        <h3>套餐信息</h3>
        <p v-if="selectedPlan">
          {{ selectedPlan.planName }}（{{ selectedPlan.durationDays }} 天）
          <span class="price-tag">¥{{ (Number(selectedPlan.salePriceFen || 0) / 100).toFixed(2) }}</span>
        </p>
        <p v-else>当前暂无可用套餐。</p>
      </article>

      <article class="checkout-card">
        <h3>兑换码开通</h3>
        <div class="row">
          <el-input
            v-model="redeemCode"
            maxlength="64"
            placeholder="请输入兑换码"
          />
          <el-button :loading="redeemLoading" type="primary" @click="submitRedeemCode">
            立即兑换
          </el-button>
        </div>
      </article>

      <article class="checkout-card">
        <h3>模拟支付开通</h3>
        <p>用于联调和转化验收，确认后会立即开通权益。</p>
        <div class="row">
          <el-button :loading="payLoading" type="success" @click="submitMockPayment">
            一键模拟支付
          </el-button>
          <el-button @click="router.push('/student/onboarding/diagnosis')">返回快诊</el-button>
          <el-button @click="router.push('/student/home')">返回首页</el-button>
        </div>
      </article>
    </template>
  </section>
</template>

<style scoped>
.checkout-page {
  display: grid;
  gap: 16px;
  padding: 20px;
}

.checkout-header {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: linear-gradient(
    120deg,
    var(--qb-surface-soft-info) 0%,
    var(--qb-surface-soft-success) 100%
  );
}

.checkout-tag {
  display: inline-block;
  margin: 0;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--qb-surface-soft-success);
  color: var(--qb-text-success-ink);
  font-size: 12px;
  font-weight: 700;
}

.checkout-header h2 {
  margin: 8px 0 6px;
}

.checkout-header p {
  margin: 0;
  color: var(--qb-text-copy);
}

.checkout-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: var(--qb-bg-card);
}

.checkout-card h3,
.checkout-card p {
  margin: 0;
}

.checkout-card p {
  color: var(--qb-text-copy);
}

.status-card strong {
  color: var(--qb-text-danger-strong);
}

.status-card strong.active {
  color: var(--qb-text-success-strong);
}

.price-tag {
  margin-left: 8px;
  color: var(--qb-text-success-ink);
  font-weight: 700;
}

.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.row :deep(.el-input) {
  min-width: 260px;
  flex: 1;
}

@media (max-width: 768px) {
  .checkout-page {
    padding: 12px;
  }

  .row {
    flex-direction: column;
  }

  .row :deep(.el-input) {
    min-width: 0;
    width: 100%;
  }
}
</style>
