<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import {
  startStudentQuickDiagnosisSession,
  submitStudentQuickDiagnosisSession,
} from '../../api/services/student.js'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const sessionPayload = ref(null)
const submitResult = ref(null)
const answerMap = ref({})

function clampQuestionCount(value) {
  const count = Number(value || 5)
  if (!Number.isInteger(count)) {
    return 5
  }
  return Math.max(3, Math.min(5, count))
}

const questionItems = computed(() => {
  const ids = Array.isArray(sessionPayload.value?.questionIds) ? sessionPayload.value.questionIds : []
  return ids.map((questionId, index) => ({
    id: String(questionId || '').trim(),
    index: index + 1,
  })).filter((item) => item.id)
})

const isCompleted = computed(() => String(submitResult.value?.status || '').trim().toUpperCase() === 'COMPLETED')

async function startDiagnosis() {
  loading.value = true
  submitResult.value = null
  answerMap.value = {}
  try {
    const payload = await startStudentQuickDiagnosisSession({
      questionCount: clampQuestionCount(route.query.questionCount),
      subjectCode: String(route.query.subjectCode || '').trim(),
      sourceType: 'ONBOARDING',
    })
    sessionPayload.value = payload
    questionItems.value.forEach((item) => {
      answerMap.value[item.id] = ''
    })
  } catch (error) {
    ElMessage.error(error?.message || '快诊初始化失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

async function submitDiagnosis() {
  if (!sessionPayload.value?.sessionId) {
    ElMessage.warning('快诊会话不存在，请重新开始。')
    return
  }
  const answers = questionItems.value.map((item) => ({
    questionId: item.id,
    answer: String(answerMap.value[item.id] || '').trim(),
    elapsedSec: 20,
  }))
  if (answers.some((item) => !item.answer)) {
    ElMessage.warning('请完成全部快诊题再提交。')
    return
  }

  submitting.value = true
  try {
    const payload = await submitStudentQuickDiagnosisSession(sessionPayload.value.sessionId, {
      answers,
      sourceType: 'ONBOARDING',
    })
    submitResult.value = payload
    ElMessage.success('快诊完成，已生成学习建议。')
  } catch (error) {
    ElMessage.error(error?.message || '快诊提交失败，请稍后重试。')
  } finally {
    submitting.value = false
  }
}

function goCheckout() {
  router.push({
    path: '/student/subscription/checkout',
    query: {
      sessionId: String(sessionPayload.value?.sessionId || '').trim(),
    },
  })
}

onMounted(() => {
  startDiagnosis()
})
</script>

<template>
  <section class="diagnosis-page">
    <header class="diagnosis-header">
      <p class="diagnosis-tag">AI 快诊引导</p>
      <h2>先做 3-5 题，系统给你学习建议和开通推荐</h2>
      <p>快诊用于快速定位当前状态，帮助你更快进入提分节奏。</p>
    </header>

    <article v-if="loading" class="diagnosis-card">
      <p>正在生成快诊题目...</p>
    </article>

    <article v-else-if="isCompleted" class="diagnosis-card result-card">
      <h3>快诊已完成</h3>
      <div class="result-grid">
        <div>
          <span>答题数</span>
          <strong>{{ submitResult?.answeredCount || 0 }}</strong>
        </div>
        <div>
          <span>正确数</span>
          <strong>{{ submitResult?.correctCount || 0 }}</strong>
        </div>
        <div>
          <span>正确率</span>
          <strong>{{ Math.round((Number(submitResult?.accuracy || 0) * 100)) }}%</strong>
        </div>
      </div>
      <p class="result-title">{{ submitResult?.result?.recommendation?.title || '继续练习，稳定输出。' }}</p>
      <p class="result-copy">{{ submitResult?.result?.recommendation?.nextAction || '建议进入订阅开通页继续完成首日动作。' }}</p>
      <div class="result-actions">
        <el-button type="primary" @click="goCheckout">去开通权益</el-button>
        <el-button @click="startDiagnosis">重新快诊</el-button>
      </div>
    </article>

    <article v-else class="diagnosis-card">
      <h3>本次快诊（{{ questionItems.length }} 题）</h3>
      <p>为了保证评估有效，请按你当前真实水平作答。</p>

      <div class="question-list">
        <label
          v-for="item in questionItems"
          :key="item.id"
          class="question-item"
        >
          <span>第 {{ item.index }} 题（ID: {{ item.id }}）</span>
          <el-input
            v-model="answerMap[item.id]"
            :placeholder="'请输入答案，例如 A 或 AC'"
            maxlength="200"
          />
        </label>
      </div>

      <div class="actions">
        <el-button :loading="submitting" type="primary" @click="submitDiagnosis">提交快诊</el-button>
        <el-button @click="router.push('/student/home')">返回首页</el-button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.diagnosis-page {
  display: grid;
  gap: 16px;
  padding: 20px;
}

.diagnosis-header {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: linear-gradient(
    120deg,
    var(--qb-surface-soft-info) 0%,
    var(--qb-surface-soft-primary) 100%
  );
}

.diagnosis-header h2 {
  margin: 8px 0 6px;
  color: var(--qb-text-heading);
}

.diagnosis-header p {
  margin: 0;
  color: var(--qb-text-copy);
}

.diagnosis-tag {
  display: inline-block;
  margin: 0;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--qb-surface-soft-info);
  color: var(--qb-text-info-ink);
  font-size: 12px;
  font-weight: 700;
}

.diagnosis-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: var(--qb-bg-card);
}

.diagnosis-card h3 {
  margin: 0;
}

.diagnosis-card p {
  margin: 0;
  color: var(--qb-text-copy);
}

.question-list {
  display: grid;
  gap: 12px;
}

.question-item {
  display: grid;
  gap: 8px;
  color: var(--qb-text-subtle);
  font-size: 13px;
}

.actions,
.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.result-grid div {
  padding: 12px;
  border-radius: 12px;
  background: var(--qb-surface-soft-neutral);
  display: grid;
  gap: 4px;
}

.result-grid span {
  color: var(--qb-text-subtle);
  font-size: 12px;
}

.result-grid strong {
  color: var(--qb-text-heading);
  font-size: 20px;
}

.result-title {
  color: var(--qb-text-heading);
  font-weight: 700;
}

@media (max-width: 768px) {
  .diagnosis-page {
    padding: 12px;
  }

  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
