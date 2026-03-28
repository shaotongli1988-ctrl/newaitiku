<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { fetchQuestionReviews, updateQuestionStatus } from '../../api/services/questionBank'
import {
  canTransitionQuestionStatus,
  parseExtJson,
  parseOptionsJson,
  questionStatusMeta,
  questionTypeLabel,
  reviewStatusLabel,
} from '../../utils/question'

const props = defineProps({
  question: {
    type: Object,
    required: true,
  },
  currentUserId: {
    type: String,
    default: '',
  },
  enableReviewDrawer: {
    type: Boolean,
    default: true,
  },
  enableSubmitAction: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['status-updated'])

const reviewDrawerVisible = ref(false)
const reviewLoading = ref(false)
const reviewRecords = ref([])
const submitting = ref(false)

const statusMeta = computed(() => questionStatusMeta(props.question?.status))
const questionTypeText = computed(() => questionTypeLabel(props.question?.type))
const ext = computed(() => parseExtJson(props.question?.extJson))
const options = computed(() => parseOptionsJson(props.question?.optionsJson))
const isOwner = computed(() => String(props.question?.userId || '') === String(props.currentUserId || ''))

const canShowSubmitAction = computed(() => {
  if (!props.enableSubmitAction) {
    return false
  }
  const status = String(props.question?.status || '')
  if (!canTransitionQuestionStatus(status, 'REVIEW_PENDING')) {
    return false
  }
  return !(status === 'QA_IN_PROGRESS' && isOwner.value)
})

async function openReviewDrawer() {
  if (!props.enableReviewDrawer) {
    return
  }
  reviewDrawerVisible.value = true
  reviewLoading.value = true
  try {
    reviewRecords.value = await fetchQuestionReviews(props.question.id)
  } catch (error) {
    reviewRecords.value = []
    ElMessage.error(error?.response?.data?.message || error?.message || '审核轨迹加载失败')
  } finally {
    reviewLoading.value = false
  }
}

async function submitForReview(event) {
  event?.stopPropagation?.()
  if (!canShowSubmitAction.value || submitting.value) {
    return
  }
  submitting.value = true
  try {
    const updated = await updateQuestionStatus(props.question.id, 'REVIEW_PENDING', {
      reason: '教师提审',
    })
    emit('status-updated', updated)
    ElMessage.success('已提交提审')
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '提审失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <article
    class="question-card"
    @click="openReviewDrawer"
  >
    <header class="question-header">
      <div class="question-tags">
        <el-tag
          effect="light"
          size="small"
          :type="statusMeta.type"
        >
          {{ statusMeta.label }}
        </el-tag>
        <el-tag effect="plain" size="small">{{ questionTypeText }}</el-tag>
      </div>
      <el-button
        v-if="canShowSubmitAction"
        type="primary"
        size="small"
        :loading="submitting"
        @click="submitForReview"
      >
        提审
      </el-button>
    </header>

    <h4 class="question-stem question-body">{{ question.stem || '-' }}</h4>

    <ul
      v-if="options.length"
      class="option-list"
    >
      <li
        v-for="(option, index) in options"
        :key="`${question.id}-option-${index}`"
        class="option-item"
      >
        <strong>{{ option.key || String.fromCharCode(65 + index) }}.</strong>
        <span>{{ option.content || '-' }}</span>
      </li>
    </ul>
    <p
      v-else
      class="subjective-hint"
    >
      主观题作答区域，支持 AI 批改与追问。
    </p>

    <footer class="question-footer">
      <span>知识点：{{ (ext.knowledgeTags || []).join(' / ') || '-' }}</span>
      <span>拥有者：{{ question.userId || '-' }}</span>
    </footer>
  </article>

  <el-drawer
    v-model="reviewDrawerVisible"
    direction="rtl"
    size="36%"
    title="审核轨迹"
  >
    <el-skeleton
      v-if="reviewLoading"
      :rows="6"
      animated
    />
    <template v-else>
      <el-empty
        v-if="!reviewRecords.length"
        description="暂无审核记录"
      />
      <div
        v-else
        class="review-timeline"
      >
        <article
          v-for="reviewRecord in reviewRecords"
          :key="reviewRecord.id"
          class="review-card"
        >
          <div class="review-head">
            <strong>{{ reviewStatusLabel(reviewRecord.status) }}</strong>
            <span>{{ reviewRecord.createTime || '-' }}</span>
          </div>
          <p>审核人：{{ reviewRecord.reviewerUserId || '-' }}</p>
          <p>流转：{{ parseExtJson(reviewRecord.extJson).fromStatus || '-' }} → {{ parseExtJson(reviewRecord.extJson).toStatus || reviewRecord.status || '-' }}</p>
          <p>原因：{{ parseExtJson(reviewRecord.extJson).reviewReason || '-' }}</p>
        </article>
      </div>
    </template>
  </el-drawer>
</template>

<style scoped>
.question-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-radius: 14px;
  border: 1px solid var(--qb-primary-soft-border);
  background: linear-gradient(160deg, var(--qb-bg-card), var(--qb-primary-soft-bg));
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.question-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.question-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.question-stem {
  margin: 0;
  color: var(--qb-text-heading);
  line-height: 1.6;
}

.option-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-item {
  display: flex;
  gap: 8px;
  color: var(--qb-text-emphasis);
}

.subjective-hint {
  margin: 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--qb-primary-soft-bg);
  color: var(--el-color-primary);
  font-size: 13px;
}

.question-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  color: var(--qb-text-subtle-9);
  font-size: 12px;
}

.review-timeline {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.review-card {
  padding: 12px;
  border-radius: 10px;
  border: 1px solid var(--qb-border-muted);
  background: var(--qb-bg-muted);
}

.review-card p {
  margin: 6px 0 0;
  color: var(--qb-text-secondary-strong);
  font-size: 13px;
}

.review-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.review-head span {
  color: var(--qb-text-subtle-9);
  font-size: 12px;
}

@media (max-width: 900px) {
  .question-card {
    padding: 14px;
  }
}
</style>
