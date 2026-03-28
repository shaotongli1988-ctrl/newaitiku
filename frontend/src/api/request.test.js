// Observability note: request-layer tests guard the same log/trace/metric expectations as runtime code.
import { describe, expect, it } from 'vitest'

import {
  backendErrorCodeMessageMap,
  formatPydanticValidationErrors,
  hasBackendErrorCode,
  isExplicitSyncingResponse,
  resolveApiErrorMessage,
  resolveBackendErrorCode,
  resolveSyncingMessage,
  shouldAttachJointGroupHeader,
  shouldTrackGlobalLoading,
} from './request'

describe('formatPydanticValidationErrors', () => {
  it('formats body field validation errors', () => {
    const detail = [
      {
        loc: ['body', 'mobile'],
        msg: 'Field required',
      },
    ]

    expect(formatPydanticValidationErrors(detail)).toEqual(['字段 [mobile] 校验失败：Field required'])
  })

  it('formats nested list validation errors', () => {
    const detail = [
      {
        loc: ['body', 'items', 0, 'subjectCode'],
        msg: 'Input should be a valid string',
      },
    ]

    expect(formatPydanticValidationErrors(detail)).toEqual([
      '字段 [items[0].subjectCode] 校验失败：Input should be a valid string',
    ])
  })

  it('returns empty array when detail is invalid', () => {
    expect(formatPydanticValidationErrors(null)).toEqual([])
    expect(formatPydanticValidationErrors({})).toEqual([])
    expect(formatPydanticValidationErrors('')).toEqual([])
  })

  it('deduplicates repeated errors', () => {
    const detail = [
      { loc: ['body', 'role'], msg: 'Input should be one of enum values' },
      { loc: ['body', 'role'], msg: 'Input should be one of enum values' },
    ]

    expect(formatPydanticValidationErrors(detail)).toEqual(['字段 [role] 校验失败：Input should be one of enum values'])
  })
})

describe('shouldAttachJointGroupHeader', () => {
  it('attaches the header for explicit student role requests', () => {
    expect(shouldAttachJointGroupHeader({ url: '/api/question-bank/tasks' }, 'student', 'SCIENCE_ENGINEERING_3')).toBe(true)
  })

  it('attaches the header for student question-bank routes even before role hydration', () => {
    expect(
      shouldAttachJointGroupHeader(
        { url: '/api/question-bank/student/personal-bank/questions', headers: {} },
        '',
        'SCIENCE_ENGINEERING_3',
      ),
    ).toBe(true)
  })

  it('does not overwrite explicit joint-group headers', () => {
    expect(
      shouldAttachJointGroupHeader(
        {
          url: '/api/question-bank/student/personal-bank/questions',
          headers: {
            'X-Joint-Group': 'MANAGEMENT_1',
          },
        },
        'student',
        'SCIENCE_ENGINEERING_3',
      ),
    ).toBe(false)
  })
})

describe('shouldTrackGlobalLoading', () => {
  it('tracks global loading by default', () => {
    expect(shouldTrackGlobalLoading({ url: '/api/question-bank/questions' })).toBe(true)
  })

  it('allows heavy background requests to opt out', () => {
    expect(shouldTrackGlobalLoading({ url: '/api/question-bank/knowledge/tree', skipGlobalLoading: true })).toBe(false)
  })
})

describe('isExplicitSyncingResponse', () => {
  it('treats 503 responses as explicit syncing signals', () => {
    expect(isExplicitSyncingResponse({ response: { status: 503, data: {} } })).toBe(true)
  })

  it('recognizes custom syncing codes without redirecting as generic 500s', () => {
    expect(
      isExplicitSyncingResponse({
        response: {
          status: 500,
          data: {
            code: 'data_syncing',
          },
        },
      }),
    ).toBe(true)
  })

  it('returns false for unrelated server errors', () => {
    expect(isExplicitSyncingResponse({ response: { status: 500, data: { code: 'SERVER_ERROR' } } })).toBe(false)
  })
})

describe('resolveSyncingMessage', () => {
  it('prefers backend syncing messages when provided', () => {
    expect(
      resolveSyncingMessage({
        response: {
          status: 503,
          data: {
            message: '内容数据同步中，请稍候再试',
          },
        },
      }),
    ).toBe('内容数据同步中，请稍候再试')
  })

  it('falls back to a default syncing message when needed', () => {
    expect(resolveSyncingMessage({ response: { status: 503, data: {} } })).toBe('数据同步中，请稍后重试。')
  })
})

describe('resolveBackendErrorCode', () => {
  it('reads the backend response envelope code first', () => {
    expect(resolveBackendErrorCode({ response: { data: { code: 'question_invalid_status' } } })).toBe('QUESTION_INVALID_STATUS')
  })

  it('falls back to nested errorCode when needed', () => {
    expect(resolveBackendErrorCode({ response: { data: { errorCode: 'task_not_found' } } })).toBe('TASK_NOT_FOUND')
  })
})

describe('backendErrorCodeMessageMap', () => {
  it('declares stable question and task error code mappings', () => {
    expect(backendErrorCodeMessageMap.AUTH_UNAUTHORIZED).toBeTruthy()
    expect(backendErrorCodeMessageMap.QUESTION_NOT_FOUND).toBeTruthy()
    expect(backendErrorCodeMessageMap.QUESTION_INVALID_STATUS).toBeTruthy()
    expect(backendErrorCodeMessageMap.TASK_NOT_FOUND).toBeTruthy()
  })
})

describe('hasBackendErrorCode', () => {
  it('matches backend codes case-insensitively', () => {
    expect(hasBackendErrorCode({ response: { data: { code: 'question_not_found' } } }, 'QUESTION_NOT_FOUND')).toBe(true)
  })
})

describe('resolveApiErrorMessage', () => {
  it('uses backend code semantics when no message is present', () => {
    expect(resolveApiErrorMessage({ response: { data: { code: 'QUESTION_INVALID_STATUS' } } }, '兜底')).toBe(
      '当前操作与资源状态不匹配，请刷新页面后重试。',
    )
  })

  it('prefers the explicit backend message when present', () => {
    expect(
      resolveApiErrorMessage(
        {
          response: {
            data: {
              code: 'QUESTION_NOT_FOUND',
              message: '题目不存在',
            },
          },
        },
        '兜底',
      ),
    ).toBe('题目不存在')
  })
})
