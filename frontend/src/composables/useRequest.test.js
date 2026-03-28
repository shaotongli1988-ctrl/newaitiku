import { describe, expect, it, vi } from 'vitest'

import { useRequest } from './useRequest'

describe('useRequest', () => {
  it('runs success lifecycle in order', async () => {
    const onSuccess = vi.fn()
    const onFinally = vi.fn()
    const task = vi.fn(async (value) => `${value}-done`)
    const request = useRequest(task, { onSuccess, onFinally })

    const result = await request.run('work')

    expect(result).toBe('work-done')
    expect(task).toHaveBeenCalledWith('work')
    expect(onSuccess).toHaveBeenCalledWith('work-done', 'work')
    expect(onFinally).toHaveBeenCalledWith('work')
    expect(request.loading.value).toBe(false)
    expect(request.error.value).toBe(null)
  })

  it('stores error and delegates to onError', async () => {
    const error = new Error('boom')
    const onError = vi.fn()
    const task = vi.fn(async () => {
      throw error
    })
    const request = useRequest(task, { onError })

    const result = await request.run('x')

    expect(result).toBe(null)
    expect(request.error.value).toBe(error)
    expect(onError).toHaveBeenCalledWith(error, 'x')
    expect(request.loading.value).toBe(false)
  })
})
