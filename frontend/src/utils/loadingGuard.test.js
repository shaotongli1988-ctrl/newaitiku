import { describe, expect, it, vi } from 'vitest'
import { runWithLoadingGuard } from './loadingGuard'

describe('runWithLoadingGuard', () => {
  it('blocks duplicated execution while loading', async () => {
    const loadingRef = { value: true }
    const task = vi.fn()

    const executed = await runWithLoadingGuard(loadingRef, task)

    expect(executed).toBe(false)
    expect(task).not.toHaveBeenCalled()
    expect(loadingRef.value).toBe(true)
  })

  it('toggles loading and executes task once', async () => {
    const loadingRef = { value: false }
    const task = vi.fn(async () => {
      await Promise.resolve()
    })

    const executed = await runWithLoadingGuard(loadingRef, task)

    expect(executed).toBe(true)
    expect(task).toHaveBeenCalledTimes(1)
    expect(loadingRef.value).toBe(false)
  })

  it('supports toggling multiple loading refs together', async () => {
    const summaryLoading = { value: false }
    const recordsLoading = { value: false }
    const task = vi.fn(async () => {
      expect(summaryLoading.value).toBe(true)
      expect(recordsLoading.value).toBe(true)
    })

    const executed = await runWithLoadingGuard([summaryLoading, recordsLoading], task)

    expect(executed).toBe(true)
    expect(task).toHaveBeenCalledTimes(1)
    expect(summaryLoading.value).toBe(false)
    expect(recordsLoading.value).toBe(false)
  })
})
