import { describe, expect, it } from 'vitest'
import { resolveManualDraftScope } from './paperDraftScope'

describe('resolveManualDraftScope', () => {
  it('parses scope fields from snake_case payload and builds scope_path', () => {
    const result = resolveManualDraftScope({
      exam_category_code: 'SCIENCE_ENGINEERING',
      joint_exam_group_code: 'SCIENCE_ENGINEERING_3',
      subject_code: 'INFO_TECH_INTRO',
      policy_version: 'HB_ZSB_2026',
    })

    expect(result.examCategoryCode).toBe('SCIENCE_ENGINEERING')
    expect(result.jointExamGroupCode).toBe('SCIENCE_ENGINEERING_3')
    expect(result.subjectCode).toBe('INFO_TECH_INTRO')
    expect(result.scope_path).toEqual(['SCIENCE_ENGINEERING', 'SCIENCE_ENGINEERING_3', 'INFO_TECH_INTRO'])
    expect(result.policyVersion).toBe('HB_ZSB_2026')
  })

  it('falls back to scope_path values when explicit scope fields are missing', () => {
    const result = resolveManualDraftScope({
      scope_path: ['SCIENCE_ENGINEERING', 'SCIENCE_ENGINEERING_3', 'POLITICS'],
    })

    expect(result.exam_category_code).toBe('SCIENCE_ENGINEERING')
    expect(result.joint_exam_group_code).toBe('SCIENCE_ENGINEERING_3')
    expect(result.subject_code).toBe('POLITICS')
    expect(result.scope_path).toEqual(['SCIENCE_ENGINEERING', 'SCIENCE_ENGINEERING_3', 'POLITICS'])
  })

  it('uses fallback payload when source payload does not carry scope fields', () => {
    const result = resolveManualDraftScope(
      {},
      {
        examCategoryCode: 'SCIENCE_ENGINEERING',
        jointExamGroupCode: 'SCIENCE_ENGINEERING_3',
        subjectCode: 'ADVANCED_MATH_1',
        policyVersion: 'HB_ZSB_2026',
      },
    )

    expect(result.exam_category_code).toBe('SCIENCE_ENGINEERING')
    expect(result.joint_exam_group_code).toBe('SCIENCE_ENGINEERING_3')
    expect(result.subject_code).toBe('ADVANCED_MATH_1')
    expect(result.scope_path).toEqual(['SCIENCE_ENGINEERING', 'SCIENCE_ENGINEERING_3', 'ADVANCED_MATH_1'])
    expect(result.policy_version).toBe('HB_ZSB_2026')
  })
})
