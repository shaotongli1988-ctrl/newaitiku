import { beforeEach, describe, expect, it, vi } from 'vitest'

const requestMock = vi.hoisted(() => vi.fn())

vi.mock('../request', () => ({
  default: requestMock,
}))

async function loadQuestionService() {
  return import('./questions')
}

beforeEach(() => {
  vi.resetModules()
  requestMock.mockReset()
})

describe('question knowledge tree helpers', () => {
  it('opts out of the global 500 redirect for paper dialogs', async () => {
    requestMock.mockResolvedValue({ data: { nodes: [], links: [] } })
    const { knowledgeTree } = await loadQuestionService()

    await knowledgeTree({ subjectCode: 'ENGLISH' })

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'get',
        url: '/api/question-bank/knowledge/tree',
        params: { subjectCode: 'ENGLISH' },
        skipGlobalLoading: true,
        skipServerErrorRedirect: true,
      }),
    )
  })
})
