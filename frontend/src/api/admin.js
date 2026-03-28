// Observability note: admin API helpers follow the shared log/trace/metric rollout baseline.
import request from './request'

/**
 * GET /api/question-bank/admin/console
 */
export function fetchAdminConsole() {
  return request({
    method: 'get',
    url: '/api/question-bank/admin/console',
  })
}

/**
 * GET /api/question-bank/admin/settings
 */
export function fetchAdminSettings() {
  return request({
    method: 'get',
    url: '/api/question-bank/admin/settings',
  })
}

/**
 * POST /api/question-bank/admin/settings
 */
export function saveAdminSettings(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/admin/settings',
    data,
  })
}

/**
 * GET /api/question-bank/admin/users
 */
export function listManagedUsers(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/admin/users',
    params,
  })
}

/**
 * POST /api/question-bank/admin/users
 */
export function saveManagedUser(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/admin/users',
    data,
  })
}

/**
 * POST /api/question-bank/admin/students/import
 */
export function importStudents(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/admin/students/import',
    data,
  })
}

/**
 * GET /api/question-bank/admin/students/export
 */
export function exportStudents(params = {}) {
  return request({
    method: 'get',
    url: '/api/question-bank/admin/students/export',
    params,
  })
}
