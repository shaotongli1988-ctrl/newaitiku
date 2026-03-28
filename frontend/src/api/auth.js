import request from './request'

/**
 * POST /api/question-bank/auth/login/password
 * 必填字段: data
 */
export function login(data) {
  return request({
    method: 'post',
    url: '/api/question-bank/auth/login/password',
    data,
  })
}

/**
 * GET /api/question-bank/auth/me
 * 必填字段: 无
 */
export function fetchManagementProfile() {
  return request({
    method: 'get',
    url: '/api/question-bank/auth/me',
  })
}

/**
 * POST /api/question-bank/auth/logout
 * 必填字段: 无
 */
export function logout() {
  return request({
    method: 'post',
    url: '/api/question-bank/auth/logout',
  })
}
