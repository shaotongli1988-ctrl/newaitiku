import { describe, expect, it } from 'vitest'
import {
  clearPracticePathQuery,
  clearPracticeTransientFocusQuery,
  normalizePracticePercent,
  normalizePracticeSubjectOptions,
  resolvePracticeSubjectCode,
  sanitizePracticeQuery,
} from './practiceScope'

describe('practiceScope helpers', () => {
  it('covers normal frontend flow by normalizing practice subject options from dashboard payload', () => {
    const result = normalizePracticeSubjectOptions({
      coreSubjects: [
        {
          subjectCode: ' ADVANCED_MATH ',
          subjectId: ' subject-1 ',
          subjectName: ' 高等数学 ',
          subjectType: ' CORE ',
          progress: {
            answered: 12,
            total: 40,
            accuracy: 0.82,
          },
        },
        {
          subjectCode: '',
        },
      ],
    })

    expect(result).toEqual([
      {
        subjectCode: 'ADVANCED_MATH',
        subjectId: 'subject-1',
        subjectName: '高等数学',
        subjectType: 'CORE',
        answered: 12,
        total: 40,
        accuracy: 0.82,
      },
    ])
  })

  it('covers boundary flow by sanitizing empty query values and clearing downstream path fields', () => {
    const sanitized = sanitizePracticeQuery({
      examCategoryCode: 'SCIENCE_ENGINEERING',
      subjectCode: ' ',
      chapterCode: 'CH_001',
      pointCode: undefined,
      pathLabel: '高等数学 / 极限',
    })

    expect(sanitized).toEqual({
      examCategoryCode: 'SCIENCE_ENGINEERING',
      chapterCode: 'CH_001',
      pathLabel: '高等数学 / 极限',
    })

    expect(clearPracticePathQuery(sanitized)).toEqual({
      examCategoryCode: 'SCIENCE_ENGINEERING',
    })
  })

  it('covers error flow by clearing invalid adaptive trace state and normalizing bad percentages', () => {
    const cleared = clearPracticeTransientFocusQuery({
      adaptiveQuestionIds: 'q1,q2',
      adaptiveDimension: 'math',
      adaptiveMastery: '37.2',
      learningMethodCode: 'LM_TIME_BLOCK',
      learningMethodRecommendationId: 'lm-rec-001',
      learningMethodSessionId: 'lm-session-001',
      focusMode: 'RISK_REPAIR',
      focusQuestionId: 'question-1',
      subjectCode: 'ADVANCED_MATH',
    })

    expect(cleared).toEqual({
      subjectCode: 'ADVANCED_MATH',
    })
    expect(normalizePracticePercent(0.823)).toBe(82)
    expect(normalizePracticePercent(67)).toBe(67)
    expect(normalizePracticePercent('bad')).toBe(0)
  })

  it('resolves generic advanced math subject codes to the scoped concrete subject', () => {
    expect(resolvePracticeSubjectCode('ADVANCED_MATH', [
      { subjectCode: 'INFO_TECH_INTRO' },
      { subjectCode: 'ADVANCED_MATH_1' },
    ])).toBe('ADVANCED_MATH_1')

    expect(resolvePracticeSubjectCode('MATH', [
      { subjectCode: 'ADVANCED_MATH_2' },
    ])).toBe('ADVANCED_MATH_2')

    expect(resolvePracticeSubjectCode('POLITICS', [
      { subjectCode: 'POLITICS' },
      { subjectCode: 'ENGLISH' },
    ])).toBe('POLITICS')
  })
})
