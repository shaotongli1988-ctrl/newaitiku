import { computed, onBeforeUnmount, ref } from 'vue'
import { fetchTaskProgress, submitAiMarkingTask } from '../api/services/questionBank'

const TERMINAL_TASK_STATUSES = new Set(['COMPLETED', 'FAILED', 'CANCELLED'])

export function useAiMarking() {
  const loading = ref(false)
  const polling = ref(false)
  const taskId = ref('')
  const taskStatus = ref('')
  const taskProgress = ref(0)
  const resultSummary = ref('')
  const errorMessage = ref('')
  const pollTimer = ref(0)

  const isFinished = computed(() => TERMINAL_TASK_STATUSES.has(String(taskStatus.value || '').trim()))

  function stopPolling() {
    if (pollTimer.value) {
      window.clearInterval(pollTimer.value)
      pollTimer.value = 0
    }
    polling.value = false
  }

  async function refreshTask() {
    if (!taskId.value) {
      return null
    }
    const taskData = await fetchTaskProgress(taskId.value)
    taskStatus.value = String(taskData.status || '')
    taskProgress.value = Number(taskData.progress || 0)
    resultSummary.value = String(taskData.extJson || '')
    if (isFinished.value) {
      stopPolling()
    }
    return taskData
  }

  function startPolling() {
    stopPolling()
    polling.value = true
    pollTimer.value = window.setInterval(() => {
      refreshTask().catch(() => {})
    }, 2500)
  }

  async function submitMarking(questionId, answer, extraPayload = {}) {
    loading.value = true
    errorMessage.value = ''
    try {
      const taskData = await submitAiMarkingTask(questionId, {
        answer: String(answer || '').trim(),
        answerImageUrl: '',
        ...(extraPayload && typeof extraPayload === 'object' ? extraPayload : {}),
      })
      taskId.value = String(taskData.id || taskData.taskId || '')
      taskStatus.value = String(taskData.status || 'QUEUED')
      taskProgress.value = Number(taskData.progress || 0)
      resultSummary.value = String(taskData.extJson || '')
      startPolling()
      await refreshTask()
      return taskData
    } catch (error) {
      errorMessage.value = String(error?.response?.data?.message || error?.message || 'AI 批改任务提交失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  onBeforeUnmount(() => {
    stopPolling()
  })

  return {
    loading,
    polling,
    taskId,
    taskStatus,
    taskProgress,
    resultSummary,
    errorMessage,
    isFinished,
    submitMarking,
    refreshTask,
    stopPolling,
  }
}
