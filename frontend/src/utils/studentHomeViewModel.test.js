import { describe, expect, it } from 'vitest'
import {
  DAILY_MOTIVATIONAL_QUOTES,
  buildFocusedUrgentKnowledgeSuggestion,
  buildReferenceMastery,
  buildTodayExecutionRecommendation,
  buildUrgentKnowledgeSuggestion,
  derivePredictedScore,
  getDayOfYear,
  normalizeKnowledgeMastery,
  resolveDailyMotivationalQuote,
} from './studentHomeViewModel.js'

describe('studentHomeViewModel', () => {
  it('正常路径: derivePredictedScore 优先使用后端预测分', () => {
    expect(derivePredictedScore({
      backendScore: 268,
      hasPersonalMastery: true,
      averageMastery: 80,
      averageAccuracy: 82,
      coveragePercent: 76,
    })).toBe(268)
  })

  it('异常路径: buildUrgentKnowledgeSuggestion 在没有弱点数据时回退为空建议', () => {
    expect(buildUrgentKnowledgeSuggestion({
      weakKnowledgeCandidates: [],
      referenceGroupLabel: '理工3',
    })).toEqual(expect.objectContaining({
      tone: 'empty',
      actionLabel: '去做任务',
      target: null,
    }))
  })

  it('默认口径: buildUrgentKnowledgeSuggestion 不再写死专业组名称', () => {
    expect(buildUrgentKnowledgeSuggestion().detail).toContain('当前专业组')
  })

  it('前端联动: buildFocusedUrgentKnowledgeSuggestion 只返回当前科目的弱项建议', () => {
    const suggestion = buildFocusedUrgentKnowledgeSuggestion({
      currentSubjectCode: 'ENGLISH',
      weakKnowledgeCandidates: [
        {
          subjectCode: 'POLITICS',
          subjectName: '政治',
          label: '毛泽东思想',
          mastery: 28,
          questionCount: 18,
          subjectCoverage: 52,
        },
        {
          subjectCode: 'ENGLISH',
          subjectName: '英语',
          label: '阅读理解',
          mastery: 36,
          questionCount: 14,
          subjectCoverage: 61,
        },
      ],
    })

    expect(suggestion.target).toEqual(expect.objectContaining({
      subjectCode: 'ENGLISH',
      subjectName: '英语',
      label: '阅读理解',
    }))
  })

  it('边界路径: buildFocusedUrgentKnowledgeSuggestion 在当前科目没有弱项时不串到其他科目', () => {
    const suggestion = buildFocusedUrgentKnowledgeSuggestion({
      currentSubjectCode: 'ENGLISH',
      weakKnowledgeCandidates: [
        {
          subjectCode: 'POLITICS',
          subjectName: '政治',
          label: '毛泽东思想',
          mastery: 28,
          questionCount: 18,
          subjectCoverage: 52,
        },
      ],
      referenceGroupLabel: '理工 3',
    })

    expect(suggestion.tone).toBe('empty')
    expect(suggestion.target).toBeNull()
  })

  it('边界路径: normalizeKnowledgeMastery 会同时兼容比例值与百分比值并做截断', () => {
    expect(normalizeKnowledgeMastery(0.58)).toBe(58)
    expect(normalizeKnowledgeMastery(135)).toBe(100)
    expect(normalizeKnowledgeMastery(-4)).toBe(0)
  })

  it('推荐路径: buildTodayExecutionRecommendation 会在未打卡时优先推荐打卡', () => {
    expect(buildTodayExecutionRecommendation({
      checkInDone: false,
      streakDays: 3,
      nextDailyTask: {
        taskName: '章节刷题10道',
        actionLabel: '去做章节闯关',
        completed: 2,
        target: 10,
        isDone: false,
      },
      urgentKnowledgeSuggestion: null,
      dailyCompletionPercent: 33,
      currentSubjectName: '英语',
    })).toEqual(expect.objectContaining({
      kind: 'checkIn',
      actionLabel: '先完成打卡',
      helper: '已连续达成 3 天',
    }))
  })

  it('推荐路径: buildTodayExecutionRecommendation 会优先挑出极弱知识点', () => {
    expect(buildTodayExecutionRecommendation({
      checkInDone: true,
      streakDays: 5,
      nextDailyTask: {
        taskName: '章节刷题10道',
        actionLabel: '去做章节闯关',
        completed: 4,
        target: 10,
        isDone: false,
      },
      urgentKnowledgeSuggestion: {
        message: '英语：阅读理解 掌握偏弱，建议优先补强。',
        detail: '掌握度 32% · 关联题量 18',
        actionLabel: '立即补强',
        target: {
          subjectName: '英语',
          label: '阅读理解',
          mastery: 32,
          questionCount: 18,
        },
      },
      dailyCompletionPercent: 40,
      currentSubjectName: '英语',
    })).toEqual(expect.objectContaining({
      kind: 'weakness',
      actionLabel: '立即补强',
    }))
  })

  it('前端联动: 默认参考曲线与首页默认预测分可稳定生成', () => {
    expect(buildReferenceMastery({ subjectCode: 'POLITICS', subjectName: '政治' }, 0)).toBe(66)
    expect(derivePredictedScore({
      backendScore: 0,
      hasPersonalMastery: false,
      averageMastery: 0,
      averageAccuracy: 0,
      coveragePercent: 0,
    })).toBe(215)
  })

  it('首页主线: 2026年3月22日展示指定激励语', () => {
    const today = new Date(2026, 2, 22)
    expect(getDayOfYear(today)).toBe(81)
    expect(resolveDailyMotivationalQuote(today)).toBe('玉汝于成 功不唐捐')
  })

  it('文案轮换: 365条激励语在年内保持唯一', () => {
    expect(DAILY_MOTIVATIONAL_QUOTES).toHaveLength(365)
    expect(new Set(DAILY_MOTIVATIONAL_QUOTES).size).toBe(365)
  })
})
