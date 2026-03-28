import { afterEach, describe, expect, it } from 'vitest'
import {
  consumeAllLearningMethodFeedbackNotices,
  consumeLearningMethodFeedbackNotice,
  saveLearningMethodFeedbackNotice,
} from './learningMethodFeedbackNotice'

function createSessionStorageMock() {
  const store = new Map()
  return {
    getItem(key) {
      return store.has(key) ? store.get(key) : null
    },
    setItem(key, value) {
      store.set(key, String(value))
    },
    removeItem(key) {
      store.delete(key)
    },
  }
}

afterEach(() => {
  delete globalThis.window
})

describe('learningMethodFeedbackNotice', () => {
  it('saves and consumes feedback notice once', () => {
    globalThis.window = { sessionStorage: createSessionStorageMock() }
    saveLearningMethodFeedbackNotice({
      feedbackStatus: 'accepted',
      methodCode: 'LM_TIME_BLOCK',
      recommendationId: 'lm-rec-001',
    })

    expect(consumeLearningMethodFeedbackNotice()).toMatchObject({
      feedbackStatus: 'ACCEPTED',
      methodCode: 'LM_TIME_BLOCK',
      recommendationId: 'lm-rec-001',
    })
    expect(consumeLearningMethodFeedbackNotice()).toBeNull()
  })

  it('returns null for invalid payloads', () => {
    globalThis.window = { sessionStorage: createSessionStorageMock() }
    saveLearningMethodFeedbackNotice({
      feedbackStatus: '',
    })
    expect(consumeLearningMethodFeedbackNotice()).toBeNull()
  })

  it('consumes queued notices in order', () => {
    globalThis.window = { sessionStorage: createSessionStorageMock() }
    saveLearningMethodFeedbackNotice({
      feedbackStatus: 'accepted',
      methodCode: 'LM_TIME_BLOCK',
      recommendationId: 'lm-rec-001',
      updateTime: '2026-03-26T10:00:00.000Z',
    })
    saveLearningMethodFeedbackNotice({
      feedbackStatus: 'partial',
      methodCode: 'LM_ACTIVE_RECALL',
      recommendationId: 'lm-rec-002',
      updateTime: '2026-03-26T10:01:00.000Z',
    })

    expect(consumeAllLearningMethodFeedbackNotices()).toEqual([
      {
        feedbackStatus: 'ACCEPTED',
        methodCode: 'LM_TIME_BLOCK',
        recommendationId: 'lm-rec-001',
        updateTime: '2026-03-26T10:00:00.000Z',
      },
      {
        feedbackStatus: 'PARTIAL',
        methodCode: 'LM_ACTIVE_RECALL',
        recommendationId: 'lm-rec-002',
        updateTime: '2026-03-26T10:01:00.000Z',
      },
    ])
    expect(consumeAllLearningMethodFeedbackNotices()).toEqual([])
  })

  it('deduplicates notice by method and recommendation id', () => {
    globalThis.window = { sessionStorage: createSessionStorageMock() }
    saveLearningMethodFeedbackNotice({
      feedbackStatus: 'partial',
      methodCode: 'LM_TIME_BLOCK',
      recommendationId: 'lm-rec-001',
      updateTime: '2026-03-26T10:00:00.000Z',
    })
    saveLearningMethodFeedbackNotice({
      feedbackStatus: 'accepted',
      methodCode: 'LM_TIME_BLOCK',
      recommendationId: 'lm-rec-001',
      updateTime: '2026-03-26T10:02:00.000Z',
    })

    expect(consumeAllLearningMethodFeedbackNotices()).toEqual([
      {
        feedbackStatus: 'ACCEPTED',
        methodCode: 'LM_TIME_BLOCK',
        recommendationId: 'lm-rec-001',
        updateTime: '2026-03-26T10:02:00.000Z',
      },
    ])
  })
})
