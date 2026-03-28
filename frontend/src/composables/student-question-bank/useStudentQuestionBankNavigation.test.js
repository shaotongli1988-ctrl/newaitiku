import { describe, expect, it } from 'vitest'
import {
  buildKnowledgePracticeLocation,
  buildWrongBookPracticeLocation,
} from './useStudentQuestionBankNavigation'

describe('student question bank navigation helpers', () => {
  it('builds wrong-book weakest practice location', () => {
    const location = buildWrongBookPracticeLocation({
      subjectCode: 'POLITICS',
      questionIds: ['q1', 'q2'],
      adaptiveDimension: 'POLITICS',
      adaptiveMastery: 62,
    })

    expect(location.path).toBe('/student/practice/chapter')
    expect(location.query.subjectCode).toBe('POLITICS')
    expect(location.query.adaptiveQuestionIds).toBe('q1,q2')
    expect(location.query.adaptiveMastery).toBe('62')
    expect(location.query.module).toBe('chapter')
    expect(location.query.practiceSource).toBe('WRONG_BOOK')
  })

  it('builds wrong-book focused repair location from row meta', () => {
    const location = buildWrongBookPracticeLocation({
      subjectCode: 'POLITICS',
      knowledgePathNodeId: 'l5-001',
      chapterCode: 'CH_ROUTE',
      chapterName: '路由章节',
      pointCode: 'PT_ROUTE',
      pointName: '路由考点',
      pathLabel: '政治 / 路由章节 / 路由考点',
      questionIds: 'q9',
      focusMode: 'RISK_REPAIR',
      focusQuestionId: 'q9',
      row: {
        knowledgeId: 'k-1',
        _meta: {
          chapterCode: 'CH_001',
          chapterLabel: '马克思主义',
          pointCode: 'PT_001_001',
          pointLabel: '实践与认识',
          semanticPath: '政治 / 马原 / 实践与认识',
          masteryScore: 33,
        },
      },
    })

    expect(location.query.knowledgeId).toBe('k-1')
    expect(location.query.knowledgePathNodeId).toBe('l5-001')
    expect(location.query.chapterCode).toBe('CH_ROUTE')
    expect(location.query.chapterName).toBe('路由章节')
    expect(location.query.focusMode).toBe('RISK_REPAIR')
    expect(location.query.focusQuestionId).toBe('q9')
    expect(location.query.pointName).toBe('路由考点')
    expect(location.query.pathLabel).toBe('政治 / 路由章节 / 路由考点')
  })

  it('builds knowledge practice location with semantic fallback', () => {
    const location = buildKnowledgePracticeLocation({
      subjectCode: 'ENGLISH',
      row: {
        knowledgeId: 'kp-2',
        _meta: {
          chapterCode: 'CH_201',
          chapterLabel: '阅读理解',
          pointCode: 'PT_201_003',
          pointLabel: '细节定位',
          semanticPath: '英语 / 阅读理解 / 细节定位',
        },
      },
    })

    expect(location.query.subjectCode).toBe('ENGLISH')
    expect(location.query.knowledgeId).toBe('kp-2')
    expect(location.query.practiceSource).toBe('KNOWLEDGE')
    expect(location.query.pointName).toBe('细节定位')
  })
})
