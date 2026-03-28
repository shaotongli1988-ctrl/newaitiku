import { beforeEach, describe, expect, it, vi } from 'vitest'

const requestMock = vi.hoisted(() => vi.fn())

vi.mock('../request', () => ({
  default: requestMock,
}))

async function loadQuestionBankService() {
  return import('./questionBank')
}

beforeEach(() => {
  vi.resetModules()
  requestMock.mockReset()
})

describe('message center service helpers', () => {
  it('normalizes unread summary payload', async () => {
    requestMock.mockResolvedValue({ data: { unreadCount: 4 } })
    const { fetchMessageUnreadSummary } = await loadQuestionBankService()

    await expect(fetchMessageUnreadSummary()).resolves.toEqual({ totalUnread: 4 })
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/messages/unread-count',
      }),
    )
  })

  it('deduplicates message ids for batch read', async () => {
    requestMock.mockResolvedValue({ data: { markedCount: 2, unreadCount: 1 } })
    const { markMessagesAsReadBatch } = await loadQuestionBankService()

    await expect(
      markMessagesAsReadBatch([' message-001 ', 'message-001', 'message-002', '']),
    ).resolves.toEqual({
      markedCount: 2,
      unreadCount: 1,
    })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/messages/read/batch',
        data: {
          messageIds: ['message-001', 'message-002'],
        },
      }),
    )
  })

  it('normalizes send message payload before request', async () => {
    requestMock.mockResolvedValue({ data: { sentCount: 2, traceId: 'msg-send-001' } })
    const { sendMessageBatch } = await loadQuestionBankService()

    await expect(
      sendMessageBatch({
        targetMode: ' userIds ',
        userIds: [' student-001 ', 'student-001', 'student-002 '],
        category: ' STUDY_REMINDER ',
        title: ' 学习提醒 ',
        content: ' 请完成今日练习。 ',
        sendAt: '2026-03-21T10:00:00',
      }),
    ).resolves.toEqual({
      sentCount: 2,
      traceId: 'msg-send-001',
    })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/messages/send',
        data: {
          targetMode: 'userIds',
          userIds: ['student-001', 'student-002'],
          examCategoryCode: '',
          jointExamGroupCode: '',
          subjectCode: '',
          sendAt: new Date('2026-03-21T10:00:00').toISOString(),
          category: 'STUDY_REMINDER',
          title: '学习提醒',
          content: '请完成今日练习。',
        },
      }),
    )
  })

  it('unwraps send history page data', async () => {
    requestMock.mockResolvedValue({
      data: {
        items: [{ traceId: 'msg-send-001', status: 'SENT' }],
        page: 2,
        size: 10,
        total: 11,
      },
    })
    const { fetchMessageSendHistoryPage } = await loadQuestionBankService()

    await expect(fetchMessageSendHistoryPage({ page: 2, size: 10 })).resolves.toEqual({
      items: [{ traceId: 'msg-send-001', status: 'SENT' }],
      page: 2,
      size: 10,
      total: 11,
    })
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/messages/send-history',
        params: {
          page: 2,
          size: 10,
        },
      }),
    )
  })

  it('loads teacher qa threads with passthrough query params', async () => {
    requestMock.mockResolvedValue({ data: { items: [], page: 1, size: 10, total: 0 } })
    const { listTeacherQaThreads } = await loadQuestionBankService()

    await listTeacherQaThreads({ status: 'OPEN', subjectCode: 'ENGLISH' })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/messages/teacher-qa/threads',
        params: {
          status: 'OPEN',
          subjectCode: 'ENGLISH',
        },
      }),
    )
  })

  it('builds teacher qa create payload as multipart form data', async () => {
    requestMock.mockResolvedValue({ data: { threadId: 'teacher-qa-001' } })
    const { createTeacherQaThread } = await loadQuestionBankService()

    await createTeacherQaThread({
      subjectCode: 'ENGLISH',
      title: '作文批改问题',
      content: '请老师帮我看看这段作文。',
      attachments: ['attachment-a'],
    })

    const payload = requestMock.mock.calls.at(-1)?.[0]
    expect(payload.method).toBe('post')
    expect(payload.url).toBe('/api/question-bank/messages/teacher-qa/threads')
    expect(payload.data).toBeInstanceOf(FormData)
    expect(payload.data.get('subjectCode')).toBe('ENGLISH')
    expect(payload.data.get('title')).toBe('作文批改问题')
    expect(payload.data.get('content')).toBe('请老师帮我看看这段作文。')
    expect(payload.data.getAll('attachments')).toEqual(['attachment-a'])
  })

  it('rejects teacher qa create payloads missing required fields', async () => {
    const { createTeacherQaThread } = await loadQuestionBankService()

    expect(() => createTeacherQaThread({ subjectCode: 'ENGLISH' })).toThrow('title is required')
    expect(requestMock).not.toHaveBeenCalled()
  })

  it('builds teacher qa reply payload as multipart form data', async () => {
    requestMock.mockResolvedValue({ data: { replyId: 'teacher-qa-message-001' } })
    const { replyTeacherQaThread } = await loadQuestionBankService()

    await replyTeacherQaThread('thread-001', {
      content: '这里建议把论点再收束一下。',
      attachments: ['attachment-b'],
    })

    const payload = requestMock.mock.calls.at(-1)?.[0]
    expect(payload.method).toBe('post')
    expect(payload.url).toBe('/api/question-bank/messages/teacher-qa/threads/thread-001/reply')
    expect(payload.data).toBeInstanceOf(FormData)
    expect(payload.data.get('content')).toBe('这里建议把论点再收束一下。')
    expect(payload.data.getAll('attachments')).toEqual(['attachment-b'])
  })

  it('loads teacher qa thread detail with canonical route path', async () => {
    requestMock.mockResolvedValue({ data: { threadId: 'thread-001' } })
    const { getTeacherQaThread } = await loadQuestionBankService()

    await getTeacherQaThread('thread-001')

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/messages/teacher-qa/threads/thread-001',
      }),
    )
  })

  it('loads teacher qa attachments with canonical route path', async () => {
    requestMock.mockResolvedValue(new Blob(['attachment']))
    const { downloadTeacherQaAttachment } = await loadQuestionBankService()

    await downloadTeacherQaAttachment('attachment-001')

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/messages/teacher-qa/attachments/attachment-001',
        responseType: 'blob',
      }),
    )
  })
})

describe('knowledge tree service helpers', () => {
  it('keeps teacher knowledge tree failures from hard-redirecting to the system error page', async () => {
    requestMock.mockResolvedValue({ data: { nodes: [], links: [] } })
    const { knowledgeTree, knowledgeTreeV2 } = await loadQuestionBankService()

    await knowledgeTree({ status: 'ACTIVE' })
    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/knowledge/tree',
        params: { status: 'ACTIVE' },
        skipGlobalLoading: true,
        skipServerErrorRedirect: true,
      }),
    )

    await knowledgeTreeV2({ subjectCode: 'POLITICS' })
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: 'get',
        url: '/api/knowledge-tree',
        params: { subjectCode: 'POLITICS' },
        skipServerErrorRedirect: true,
      }),
    )
  })
})

describe('personal bank service helpers', () => {
  it('passes archive and review-plan filters through when listing questions', async () => {
    requestMock.mockResolvedValue({ data: { items: [], total: 0, page: 1, size: 20 } })
    const { listStudentPersonalBankQuestions } = await loadQuestionBankService()

    await listStudentPersonalBankQuestions({
      keyword: '导数',
      archiveWindow: 'ARCHIVED',
      questionIds: 'q-1,q-2',
      page: 1,
      size: 20,
    })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/student/personal-bank/questions',
        params: {
          keyword: '导数',
          archiveWindow: 'ARCHIVED',
          questionIds: 'q-1,q-2',
          page: 1,
          size: 20,
        },
      }),
    )
  })

  it('passes export filters through unchanged', async () => {
    requestMock.mockResolvedValue({ data: { format: 'csv', content: 'header' } })
    const { studentPersonalBankExport } = await loadQuestionBankService()

    await studentPersonalBankExport({
      keyword: '归档',
      archiveWindow: 'EARLIER',
      questionIds: 'q-9',
      format: 'csv',
    })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/student/personal-bank/export',
        params: {
          keyword: '归档',
          archiveWindow: 'EARLIER',
          questionIds: 'q-9',
          format: 'csv',
        },
      }),
    )
  })

  it('passes current filter scope through when loading review plans', async () => {
    requestMock.mockResolvedValue({ data: [] })
    const { listStudentPersonalBankReviewPlans } = await loadQuestionBankService()

    await listStudentPersonalBankReviewPlans({
      keyword: '导数',
      archiveWindow: 'LAST_7_DAYS',
      subjectCode: 'MATH',
    })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/student/personal-bank/review-plans',
        params: {
          keyword: '导数',
          archiveWindow: 'LAST_7_DAYS',
          subjectCode: 'MATH',
        },
      }),
    )
  })

  it('requests formal review plan endpoints with the expected paths', async () => {
    requestMock.mockResolvedValue({ data: { items: [] } })
    const {
      listStudentPersonalBankReviewPlans,
      getStudentPersonalBankReviewPlan,
      startStudentPersonalBankReviewPlan,
      completeStudentPersonalBankReviewPlanQuestion,
    } = await loadQuestionBankService()

    await listStudentPersonalBankReviewPlans()
    await getStudentPersonalBankReviewPlan('plan-1', { keyword: '导数' })
    await startStudentPersonalBankReviewPlan('plan-1', { questionIds: 'question-9' })
    await completeStudentPersonalBankReviewPlanQuestion('plan-1', 'question-9', { archiveWindow: 'ARCHIVED' })

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/student/personal-bank/review-plans',
      }),
    )
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/student/personal-bank/review-plans/plan-1',
        params: { keyword: '导数' },
      }),
    )
    expect(requestMock).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/student/personal-bank/review-plans/plan-1/start',
        params: { questionIds: 'question-9' },
      }),
    )
    expect(requestMock).toHaveBeenNthCalledWith(
      4,
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/student/personal-bank/review-plans/plan-1/questions/question-9/complete',
        params: { archiveWindow: 'ARCHIVED' },
      }),
    )
  })
})

describe('learning method service helpers', () => {
  it('loads learning method list and normalizes list payload', async () => {
    requestMock.mockResolvedValue({
      data: {
        items: [{ methodCode: 'M01', methodName: '费曼学习法' }],
        total: 1,
      },
    })
    const { fetchLearningMethodList } = await loadQuestionBankService()

    await expect(fetchLearningMethodList({ status: 'ACTIVE' })).resolves.toEqual({
      items: [{ methodCode: 'M01', methodName: '费曼学习法' }],
      total: 1,
    })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/learning-methods',
        params: { status: 'ACTIVE' },
      }),
    )
  })

  it('loads learning method detail with canonical endpoint', async () => {
    requestMock.mockResolvedValue({ data: { method: { methodCode: 'M01' } } })
    const { fetchLearningMethodDetail } = await loadQuestionBankService()

    await expect(fetchLearningMethodDetail('M01')).resolves.toEqual({
      method: { methodCode: 'M01' },
    })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/learning-methods/M01',
      }),
    )
  })

  it('starts and completes learning method sessions with expected endpoints', async () => {
    requestMock
      .mockResolvedValueOnce({ data: { sessionId: 'lm-session-1' } })
      .mockResolvedValueOnce({ data: { sessionId: 'lm-session-1', updatedProgress: { status: 'COMPLETED' } } })
    const {
      startLearningMethodSession,
      completeLearningMethodSession,
    } = await loadQuestionBankService()

    await expect(startLearningMethodSession('M01', { sourceType: 'LEARNING_METHOD_PAGE' })).resolves.toEqual({
      sessionId: 'lm-session-1',
    })
    await expect(
      completeLearningMethodSession('M01', { sessionId: 'lm-session-1', accuracy: 0.8 }),
    ).resolves.toEqual({
      sessionId: 'lm-session-1',
      updatedProgress: { status: 'COMPLETED' },
    })

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/learning-methods/M01/start',
        data: { sourceType: 'LEARNING_METHOD_PAGE' },
      }),
    )
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/learning-methods/M01/complete',
        data: { sessionId: 'lm-session-1', accuracy: 0.8 },
      }),
    )
  })
})

describe('learning method matching service helpers', () => {
  it('calls admin auto-generate profile and auto-batch feature endpoints', async () => {
    requestMock
      .mockResolvedValueOnce({ data: { methodCode: 'M01', profileVersion: 'v1' } })
      .mockResolvedValueOnce({ data: { processed: 18, skipped: 2 } })

    const {
      runAutoGenerateLearningMethodProfile,
      runAutoBatchQuestionMatchFeatures,
    } = await loadQuestionBankService()

    await expect(runAutoGenerateLearningMethodProfile('M01', { forceRegenerate: true })).resolves.toEqual({
      methodCode: 'M01',
      profileVersion: 'v1',
    })

    await expect(runAutoBatchQuestionMatchFeatures({ limit: 20, forceRefresh: true })).resolves.toEqual({
      processed: 18,
      skipped: 2,
    })

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/admin/learning-methods/M01/profile/auto-generate',
        data: { forceRegenerate: true },
      }),
    )
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/admin/questions/match-features/auto-batch',
        data: { limit: 20, forceRefresh: true },
      }),
    )
  })

  it('calls student recommend and feedback endpoints', async () => {
    requestMock
      .mockResolvedValueOnce({ data: { recommendationId: 'lm-rec-001', questionCount: 12 } })
      .mockResolvedValueOnce({ data: { recommendationId: 'lm-rec-001', feedbackStatus: 'ACCEPTED' } })

    const {
      fetchLearningMethodQuestionPackRecommendation,
      submitLearningMethodQuestionPackFeedback,
    } = await loadQuestionBankService()

    await expect(
      fetchLearningMethodQuestionPackRecommendation('M01', { questionCount: 12, strategySource: 'SUGGESTED' }),
    ).resolves.toEqual({ recommendationId: 'lm-rec-001', questionCount: 12 })

    await expect(
      submitLearningMethodQuestionPackFeedback('M01', {
        recommendationId: 'lm-rec-001',
        feedbackStatus: 'ACCEPTED',
      }),
    ).resolves.toEqual({ recommendationId: 'lm-rec-001', feedbackStatus: 'ACCEPTED' })

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/learning-methods/M01/question-pack/recommend',
        data: { questionCount: 12, strategySource: 'SUGGESTED' },
      }),
    )
    expect(requestMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/learning-methods/M01/question-pack/feedback',
        data: { recommendationId: 'lm-rec-001', feedbackStatus: 'ACCEPTED' },
      }),
    )
  })

  it('loads recommendation history endpoint', async () => {
    requestMock.mockResolvedValue({ data: { items: [{ recommendationId: 'lm-rec-001' }], total: 1 } })

    const { fetchLearningMethodQuestionPackRecommendationHistory } = await loadQuestionBankService()

    await expect(fetchLearningMethodQuestionPackRecommendationHistory('M01', { limit: 10 })).resolves.toEqual({
      items: [{ recommendationId: 'lm-rec-001' }],
      total: 1,
    })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/learning-methods/M01/question-pack/recommendations',
        params: { limit: 10 },
      }),
    )
  })
})
