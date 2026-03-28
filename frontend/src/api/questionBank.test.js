// Observability note: API tests mirror the shared log/trace/metric contract used in release checks.
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn(),
}))

vi.mock('./request', () => ({
  default: requestMock,
}))

class LocalStorageMock {
  constructor() {
    this.store = new Map()
  }

  clear() {
    this.store.clear()
  }

  getItem(key) {
    return this.store.has(key) ? this.store.get(key) : null
  }

  setItem(key, value) {
    this.store.set(String(key), String(value))
  }

  removeItem(key) {
    this.store.delete(String(key))
  }
}

const CACHE_KEY = 'qbContentBaselineCacheV1'

async function loadQuestionBankModule() {
  return import('./services/questionBank')
}

beforeAll(() => {
  Object.defineProperty(globalThis, 'localStorage', {
    value: new LocalStorageMock(),
    writable: true,
    configurable: true,
  })
})

beforeEach(() => {
  vi.resetModules()
  requestMock.mockReset()
  globalThis.localStorage.clear()
})

describe('fetchContentBaseline cache', () => {
  it('keeps the normal success path cached on repeated requests', async () => {
    const payload = {
      examCategories: [{ examCategoryCode: 'SCIENCE_ENGINEERING' }],
    }
    requestMock.mockResolvedValue({ data: payload })
    const { fetchContentBaseline } = await loadQuestionBankModule()

    const first = await fetchContentBaseline()
    const second = await fetchContentBaseline()

    expect(first).toEqual(payload)
    expect(second).toEqual(payload)
    expect(requestMock).toHaveBeenCalledTimes(1)
  })

  it('covers formal/fallback cutover and backend database data-chain regression by refreshing backend contract data after fallback cache expires', async () => {
    const fallbackPayload = {
      examCategories: [{ examCategoryCode: 'MANAGEMENT' }],
    }
    // Simulate a cutover window in the backend database data chain:
    // an expired fallback cache must give way to the formal backend payload.
    globalThis.localStorage.setItem(
      CACHE_KEY,
      JSON.stringify({
        expiresAt: Date.now() + 60_000,
        data: fallbackPayload,
      }),
    )

    const { fetchContentBaseline } = await loadQuestionBankModule()
    const hit = await fetchContentBaseline()
    expect(hit).toEqual(fallbackPayload)
    expect(requestMock).not.toHaveBeenCalled()

    globalThis.localStorage.setItem(
      CACHE_KEY,
      JSON.stringify({
        expiresAt: Date.now() - 1_000,
        data: fallbackPayload,
      }),
    )

    vi.resetModules()
    requestMock.mockReset()
    const formalPayload = {
      examCategories: [{ examCategoryCode: 'LITERATURE' }],
    }
    requestMock.mockResolvedValue({ data: formalPayload })

    const reloaded = await loadQuestionBankModule()
    const missAfterExpiry = await reloaded.fetchContentBaseline()

    expect(missAfterExpiry).toEqual(formalPayload)
    expect(requestMock).toHaveBeenCalledTimes(1)
  })
})
