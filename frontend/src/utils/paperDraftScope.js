import { normalizeScopePath } from './professionalScope'

function normalizeString(value) {
  return String(value || '').trim()
}

export function resolveManualDraftScope(source = {}, fallback = {}) {
  const sourcePayload = source && typeof source === 'object' ? source : {}
  const fallbackPayload = fallback && typeof fallback === 'object' ? fallback : {}
  const fallbackScopePath = normalizeScopePath(
    sourcePayload.scope_path ?? sourcePayload.scopePath ?? fallbackPayload.scope_path ?? fallbackPayload.scopePath,
  )

  const examCategoryCode = normalizeString(
    sourcePayload.exam_category_code
    ?? sourcePayload.examCategoryCode
    ?? fallbackPayload.exam_category_code
    ?? fallbackPayload.examCategoryCode
    ?? fallbackScopePath[0],
  )
  const jointExamGroupCode = normalizeString(
    sourcePayload.joint_exam_group_code
    ?? sourcePayload.jointExamGroupCode
    ?? fallbackPayload.joint_exam_group_code
    ?? fallbackPayload.jointExamGroupCode
    ?? fallbackScopePath[1],
  )
  const subjectCode = normalizeString(
    sourcePayload.subject_code
    ?? sourcePayload.subjectCode
    ?? fallbackPayload.subject_code
    ?? fallbackPayload.subjectCode
    ?? fallbackScopePath[2],
  )
  const policyVersion = normalizeString(
    sourcePayload.policy_version
    ?? sourcePayload.policyVersion
    ?? sourcePayload.policyVersionCode
    ?? fallbackPayload.policy_version
    ?? fallbackPayload.policyVersion
    ?? fallbackPayload.policyVersionCode,
  )

  const scopePath = examCategoryCode && jointExamGroupCode
    ? [examCategoryCode, jointExamGroupCode, ...(subjectCode ? [subjectCode] : [])]
    : []

  return {
    exam_category_code: examCategoryCode,
    joint_exam_group_code: jointExamGroupCode,
    subject_code: subjectCode,
    policy_version: policyVersion,
    examCategoryCode,
    jointExamGroupCode,
    subjectCode,
    policyVersion,
    scope_path: scopePath,
    scopePath,
  }
}
