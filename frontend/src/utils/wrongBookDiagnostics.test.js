import { describe, expect, it } from 'vitest'
import {
  buildWrongBookAiTutorPlan,
  buildWrongBookBreadcrumbTrail,
  buildWrongBookDiagnosticBoard,
  computeWrongBookPriorityAlertCount,
  resolveWrongBookPracticeSuggestionCount,
} from './wrongBookDiagnostics'

describe('wrongBookDiagnostics', () => {
  it('builds the dashboard for the normal subject flow', () => {
    const board = buildWrongBookDiagnosticBoard({
      effectiveSubjectCode: 'POLITICS',
      nowMs: Date.parse('2026-03-21T12:00:00Z'),
      questionInsights: [
        { subjectCode: 'POLITICS', submittedAt: '2026-03-20T12:00:00Z' },
        { subjectCode: 'POLITICS', submittedAt: '2026-03-18T13:00:00Z' },
        { subjectCode: 'ENGLISH', submittedAt: '2026-03-20T12:00:00Z' },
      ],
      currentSubject: {
        knowledgeCoverageRate: 0.56,
        practicedPointCount: 14,
        totalPointCount: 25,
        errorCoverageRate: 0.24,
        topChapters: [{ chapterName: '政治经济学', wrongCount: 5 }],
      },
    })

    expect(board).toMatchObject({
      knowledgeCoverageRate: 56,
      practicedPointCount: 14,
      totalPointCount: 25,
      recentNewWrongCount: 2,
      errorCoverageRate: 24,
      wrongCount: 2,
    })
    expect(board.hotspots).toHaveLength(1)
  })

  it('falls back to chapter and point labels when breadcrumb trail is incomplete', () => {
    expect(buildWrongBookBreadcrumbTrail([], '函数极限', '极限的定义')).toEqual([
      { level: 4, levelLabel: 'L4 章节', label: '函数极限' },
      { level: 5, levelLabel: 'L5 原子知识点', label: '极限的定义' },
    ])
  })

  it('handles missing repair matches and overdue warnings as an exception-style path', () => {
    const plan = buildWrongBookAiTutorPlan({
      chapterLabel: '导数应用',
      errorInducerLabel: '计算题',
      reviewStatusKey: 'fragile',
      isOverdue72h: true,
      wrongCount: 4,
      repairSuggestions: [],
      chapterSuggestions: [],
    })

    expect(plan.priorityLabel).toBe('72h 预警')
    expect(plan.diagnosisTitle).toBe('计算链路断点')
    expect(plan.chapterAction).toContain('导数应用')
    expect(plan.actionLabel).toContain('今天先回顾原题')
  })

  it('resolves suggestion and priority counts without fake fallback values', () => {
    expect(resolveWrongBookPracticeSuggestionCount({ questionCount: 6 })).toBe(6)
    expect(resolveWrongBookPracticeSuggestionCount({})).toBe(0)
    expect(
      computeWrongBookPriorityAlertCount({
        benchmarkAlertRows: [{ id: 'a' }, { id: 'b' }],
        reviewWarnings: [{ id: 'c' }],
        repairSuggestions: [{ id: 'd' }, { id: 'e' }],
      }),
    ).toBe(5)
  })

  it('keeps db data chain cutover counts stable for repository-backed wrong-book cards', () => {
    expect(resolveWrongBookPracticeSuggestionCount({ questionCount: '4' })).toBe(4)
    expect(
      computeWrongBookPriorityAlertCount({
        benchmarkAlertRows: [{ id: 'db-1' }],
        reviewWarnings: [],
        repairSuggestions: [{ id: 'repo-1' }],
      }),
    ).toBe(2)
  })
})
