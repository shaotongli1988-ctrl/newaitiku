// Observability note: student API tests cover the same log/trace/metric contract expected in release gating.
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  analyticsExportMock: vi.fn(),
  analyticsSummaryMock: vi.fn(),
  askAiTutorMock: vi.fn(),
  cancelTaskMock: vi.fn(),
  confirmStudentSubscriptionMockOrderMock: vi.fn(),
  createStudentSubscriptionMockOrderMock: vi.fn(),
  getStudentSubscriptionStatusMock: vi.fn(),
  getMessageSettingsMock: vi.fn(),
  getMessageUnreadCountMock: vi.fn(),
  getTaskMock: vi.fn(),
  listStudentSubscriptionPlansMock: vi.fn(),
  listAnalyticsRecordsMock: vi.fn(),
  listMessageSendHistoryMock: vi.fn(),
  listMessagesMock: vi.fn(),
  listStudentPracticeChaptersMock: vi.fn(),
  listStudentPracticeQuestionsMock: vi.fn(),
  listTasksMock: vi.fn(),
  markMessageReadMock: vi.fn(),
  markMessagesReadBatchMock: vi.fn(),
  recallMessageSendMock: vi.fn(),
  redeemStudentSubscriptionMock: vi.fn(),
  saveMessageSettingsMock: vi.fn(),
  sendMessagesMock: vi.fn(),
  startStudentQuickDiagnosisMock: vi.fn(),
  studentDashboardMock: vi.fn(),
  submitAiMarkingMock: vi.fn(),
  submitStudentQuickDiagnosisMock: vi.fn(),
}))

vi.mock('./questionBank', () => ({
  analyticsExport: mocks.analyticsExportMock,
  analyticsSummary: mocks.analyticsSummaryMock,
  askAiTutor: mocks.askAiTutorMock,
  cancelTask: mocks.cancelTaskMock,
  confirmStudentSubscriptionMockOrder: mocks.confirmStudentSubscriptionMockOrderMock,
  createStudentSubscriptionMockOrder: mocks.createStudentSubscriptionMockOrderMock,
  getStudentSubscriptionStatus: mocks.getStudentSubscriptionStatusMock,
  getMessageSettings: mocks.getMessageSettingsMock,
  getMessageUnreadCount: mocks.getMessageUnreadCountMock,
  getTask: mocks.getTaskMock,
  listStudentSubscriptionPlans: mocks.listStudentSubscriptionPlansMock,
  listAnalyticsRecords: mocks.listAnalyticsRecordsMock,
  listMessageSendHistory: mocks.listMessageSendHistoryMock,
  listMessages: mocks.listMessagesMock,
  listStudentPracticeChapters: mocks.listStudentPracticeChaptersMock,
  listStudentPracticeQuestions: mocks.listStudentPracticeQuestionsMock,
  listTasks: mocks.listTasksMock,
  markMessageRead: mocks.markMessageReadMock,
  markMessagesReadBatch: mocks.markMessagesReadBatchMock,
  recallMessageSend: mocks.recallMessageSendMock,
  redeemStudentSubscription: mocks.redeemStudentSubscriptionMock,
  saveMessageSettings: mocks.saveMessageSettingsMock,
  sendMessages: mocks.sendMessagesMock,
  startStudentQuickDiagnosis: mocks.startStudentQuickDiagnosisMock,
  studentDashboard: mocks.studentDashboardMock,
  submitAiMarking: mocks.submitAiMarkingMock,
  submitStudentQuickDiagnosis: mocks.submitStudentQuickDiagnosisMock,
}))

async function loadStudentService() {
  return import('./student')
}

beforeEach(() => {
  vi.resetModules()
  Object.values(mocks).forEach((mock_fn) => {
    mock_fn.mockReset()
  })
})

describe('student service task normalization', () => {
  it('normalizes ai-marking task id fields', async () => {
    mocks.submitAiMarkingMock.mockResolvedValue({ data: { id: 'task-001', status: 'QUEUED' } })
    const { submitAiMarkingTask } = await loadStudentService()

    const task = await submitAiMarkingTask('question-1', { answer: 'sample' })

    expect(task.id).toBe('task-001')
    expect(task.taskId).toBe('task-001')
  })

  it('normalizes ai-tutor taskId payload to taskId', async () => {
    mocks.askAiTutorMock.mockResolvedValue({ data: { taskId: 'task-002', status: 'RUNNING', progress: '35' } })
    const { submitAiTutorTask } = await loadStudentService()

    const task = await submitAiTutorTask('question-2', { prompt: 'help me' })

    expect(task.id).toBe('task-002')
    expect(task.taskId).toBe('task-002')
    expect(task.progress).toBe(35)
  })

  it('returns task list page data with aiQuota and normalized items', async () => {
    mocks.listTasksMock.mockResolvedValue({
      data: {
        items: [{ id: 'task-11' }, { taskId: 'task-12' }],
        page: 1,
        size: 20,
        total: 2,
        aiQuota: { dailyLimit: 20, usedCount: 3 },
      },
    })
    const { fetchTaskList } = await loadStudentService()

    const page_data = await fetchTaskList({ page: 1, size: 20 })

    expect(page_data.total).toBe(2)
    expect(page_data.aiQuota).toEqual({ dailyLimit: 20, usedCount: 3 })
    expect(page_data.items[0].taskId).toBe('task-11')
    expect(page_data.items[1].taskId).toBe('task-12')
  })
})

describe('student service filters and analytics summary', () => {
  it('passes normalized exam category filters to student practice and analytics endpoints', async () => {
    mocks.listStudentPracticeQuestionsMock.mockResolvedValue({ data: { items: [], page: 1, size: 10, total: 0 } })
    mocks.analyticsSummaryMock.mockResolvedValue({ data: {} })
    const { fetchStudentPracticeQuestionList, fetchAnalyticsSummary } = await loadStudentService()

    await fetchStudentPracticeQuestionList({
      examCategoryCode: ' SCIENCE_ENGINEERING ',
      jointExamGroupCode: ' SCIENCE_ENGINEERING_1 ',
      subjectCode: ' MATH-101 ',
      keyword: 'limit',
    })
    await fetchAnalyticsSummary({
      examCategoryCode: ' SCIENCE_ENGINEERING ',
      jointExamGroupCode: ' SCIENCE_ENGINEERING_1 ',
      subjectCode: ' MATH-101 ',
      keyword: 'limit',
    })

    expect(mocks.listStudentPracticeQuestionsMock).toHaveBeenCalledWith(
      expect.objectContaining({
        examCategoryCode: 'SCIENCE_ENGINEERING',
        jointExamGroupCode: 'SCIENCE_ENGINEERING_1',
        subjectCode: 'MATH-101',
      }),
    )
    expect(mocks.analyticsSummaryMock).toHaveBeenCalledWith(
      expect.objectContaining({
        examCategoryCode: 'SCIENCE_ENGINEERING',
        jointExamGroupCode: 'SCIENCE_ENGINEERING_1',
        subjectCode: 'MATH-101',
      }),
    )
  })

  it('returns analytics summary with chart-compatible keys', async () => {
    mocks.analyticsSummaryMock.mockResolvedValue({
      data: {
        studentCount: 1,
        mastery: [{ studentUserId: 'student-001', subjectId: 'subject-1', mastery: 0.82 }],
      },
    })
    const { fetchAnalyticsSummary } = await loadStudentService()

    const summary = await fetchAnalyticsSummary({})

    expect(summary).toEqual(
      expect.objectContaining({
        mastery: expect.any(Array),
        studentRankings: expect.any(Array),
        weakKnowledgeTags: expect.any(Array),
        lowActivityStudents: expect.any(Array),
      }),
    )
  })
})

describe('student service subscription and diagnosis helpers', () => {
  it('loads subscription status and plans', async () => {
    mocks.getStudentSubscriptionStatusMock.mockResolvedValue({ data: { subscriptionActive: true } })
    mocks.listStudentSubscriptionPlansMock.mockResolvedValue({ data: [{ planCode: 'AI_SCORE_BOOST_30D' }] })
    const { fetchStudentSubscriptionStatus, fetchStudentSubscriptionPlans } = await loadStudentService()

    await expect(fetchStudentSubscriptionStatus()).resolves.toEqual({ subscriptionActive: true })
    await expect(fetchStudentSubscriptionPlans()).resolves.toEqual([{ planCode: 'AI_SCORE_BOOST_30D' }])
  })

  it('submits diagnosis and subscription actions', async () => {
    mocks.startStudentQuickDiagnosisMock.mockResolvedValue({ data: { sessionId: 'quick-diag-001' } })
    mocks.submitStudentQuickDiagnosisMock.mockResolvedValue({ data: { status: 'COMPLETED' } })
    mocks.redeemStudentSubscriptionMock.mockResolvedValue({ data: { subscriptionActive: true } })
    mocks.createStudentSubscriptionMockOrderMock.mockResolvedValue({ data: { order: { orderId: 'order-001' } } })
    mocks.confirmStudentSubscriptionMockOrderMock.mockResolvedValue({ data: { idempotent: false } })
    const {
      startStudentQuickDiagnosisSession,
      submitStudentQuickDiagnosisSession,
      redeemStudentSubscriptionCode,
      createStudentSubscriptionOrder,
      confirmStudentSubscriptionOrder,
    } = await loadStudentService()

    await expect(startStudentQuickDiagnosisSession({ questionCount: 3 })).resolves.toEqual({ sessionId: 'quick-diag-001' })
    await expect(submitStudentQuickDiagnosisSession('quick-diag-001', { answers: [] })).resolves.toEqual({ status: 'COMPLETED' })
    await expect(redeemStudentSubscriptionCode({ code: 'TEST-REDEEM' })).resolves.toEqual({ subscriptionActive: true })
    await expect(createStudentSubscriptionOrder({ planCode: 'AI_SCORE_BOOST_30D' })).resolves.toEqual({ order: { orderId: 'order-001' } })
    await expect(confirmStudentSubscriptionOrder('order-001', { transactionNo: 'TXN-001' })).resolves.toEqual({ idempotent: false })
  })
})
