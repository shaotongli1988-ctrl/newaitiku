import { beforeEach, describe, expect, it, vi } from 'vitest'

const requestMock = vi.hoisted(() => vi.fn())

vi.mock('../request', () => ({
  default: requestMock,
}))

async function loadPapersService() {
  return import('./papers')
}

beforeEach(() => {
  vi.resetModules()
  requestMock.mockReset()
})

describe('paper service ai generate payload normalization', () => {
  it('accepts the teacher dialog snake_case payload and sends camelCase fields', async () => {
    requestMock.mockResolvedValue({ data: { paperId: 'paper-001' } })
    const { aiGeneratePaper } = await loadPapersService()

    await aiGeneratePaper({
      subject_id: ' ECONOMICS-n00001 ',
      exam_category_code: ' ECONOMICS ',
      joint_exam_group_code: ' SCIENCE_3 ',
      subject_code: ' ECONOMICS_BASIC ',
      class_ids: [' class-a ', 'class-a', ' class-b '],
      total_count: 20,
      difficulty_level: 3,
      knowledge_scope: [' knowledge-1 ', 'knowledge-1'],
    })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'post',
        url: '/api/question-bank/papers/ai-generate',
        data: {
          policyVersion: 'HB_ZSB_2026',
          subjectId: 'ECONOMICS-n00001',
          examCategoryCode: 'ECONOMICS',
          jointExamGroupCode: 'SCIENCE_3',
          subjectCode: 'ECONOMICS_BASIC',
          classIds: ['class-a', 'class-b'],
          totalCount: 20,
          difficulty: 3,
          knowledgeScope: ['knowledge-1'],
        },
      }),
    )
  })
})
