import { describe, expect, it } from 'vitest'
import {
  buildRadarDimensions,
  buildSubjectMetaById,
  computeSubjectMastery,
  normalizeMasteryScore,
  normalizeSubjectCode,
  resolveSubjectDimensionLabel,
} from './studentMastery'

describe('studentMastery', () => {
  it('normalizes percentage and ratio scores into 0-100 range', () => {
    expect(normalizeMasteryScore(0.82)).toBe(82)
    expect(normalizeMasteryScore(82)).toBe(82)
    expect(normalizeMasteryScore('bad')).toBe(0)
  })

  it('computes mastery with accuracy-weighted formula', () => {
    expect(computeSubjectMastery({
      accuracy: 0.8,
      speed: 0.5,
      frequency: 0.4,
    })).toBe(66)
  })

  it('prefers chinese subject names when building radar dimensions', () => {
    const subjectMetaMap = buildSubjectMetaById([
      {
        subjectId: 'subject-advanced-math-2',
        subjectCode: 'ADVANCED_MATH_2',
        subjectName: '高等数学（二）',
      },
    ])

    expect(resolveSubjectDimensionLabel('subject-advanced-math-2', subjectMetaMap)).toBe('高等数学（二）')
    expect(normalizeSubjectCode(subjectMetaMap['subject-advanced-math-2'].subjectCode, '', 0)).toBe('ADVANCED_MATH_2')

    expect(buildRadarDimensions([
      {
        subjectId: 'subject-advanced-math-2',
        accuracy: 0.8,
        speed: 0.5,
        frequency: 0.4,
      },
    ], subjectMetaMap)).toEqual([
      expect.objectContaining({
        label: '高等数学（二）',
        subjectCode: 'ADVANCED_MATH_2',
        mastery: 66,
      }),
    ])
  })

  it('falls back to readable subject text when chinese metadata is missing', () => {
    expect(resolveSubjectDimensionLabel('subject-english', {})).toBe('english')
    expect(resolveSubjectDimensionLabel('', {}, 1)).toBe('科目 2')
  })
})
