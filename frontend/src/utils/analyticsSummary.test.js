import { describe, expect, it } from 'vitest'
import { createEmptyAnalyticsSummary, normalizeAnalyticsSummary } from './analyticsSummary'

describe('analyticsSummary', () => {
  it('creates a stable empty summary schema', () => {
    expect(createEmptyAnalyticsSummary()).toEqual({
      timeRangeLabel: '全部时间',
      studentCount: 0,
      activeStudentCount: 0,
      inactiveStudentCount: 0,
      coverageRate: 0,
      questionCount: 0,
      averageAccuracy: 0,
      averageAnswerDurationSec: 0,
      masteredStudentCount: 0,
      atRiskStudentCount: 0,
      chapterRankings: [],
      weakKnowledgeTags: [],
      lowActivityStudents: [],
      mastery: [],
      studentRankings: [],
      aiReport: '',
    })
  })

  it('normalizes summary collections into chart-safe arrays', () => {
    const summary = normalizeAnalyticsSummary({
      studentCount: 2,
      mastery: [{ studentUserId: 'student-1', mastery: '0.8' }],
      studentRankings: [{ studentUserId: 'student-2', subjectCount: '3' }],
      lowActivityStudents: [{ studentUserId: 'student-3', activityCount: '1' }],
      weakKnowledgeTags: null,
    })

    expect(summary.studentCount).toBe(2)
    expect(summary.mastery).toEqual([
      expect.objectContaining({ studentUserId: 'student-1', mastery: 0.8 }),
    ])
    expect(summary.studentRankings).toEqual([
      expect.objectContaining({ studentUserId: 'student-2', subjectCount: 3 }),
    ])
    expect(summary.lowActivityStudents).toEqual([
      expect.objectContaining({ studentUserId: 'student-3', activityCount: 1 }),
    ])
    expect(summary.weakKnowledgeTags).toEqual([])
    expect(summary.chapterRankings).toEqual([])
  })
})
