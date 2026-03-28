// Observability note: subject API wrappers should preserve log/trace/metric scope context.
import request from './request'

const QUESTION_BANK_API_PREFIX = '/api/question-bank'

/**
 * GET /api/question-bank/subjects
 */
export function listSubjects() {
  return request({
    method: 'get',
    url: `${QUESTION_BANK_API_PREFIX}/subjects`,
  })
}
