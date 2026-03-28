import { describe, expect, it } from 'vitest'
import {
  buildPersonalBankQuestionMeta,
  buildPersonalBankSearchText,
  buildWrongBookQuestionMeta,
  formatQuestionBankDateTime,
} from './studentQuestionBankMeta'

describe('studentQuestionBankMeta', () => {
  it('formats empty and iso datetimes safely', () => {
    expect(formatQuestionBankDateTime('')).toBe('-')
    expect(formatQuestionBankDateTime('2026-03-22T10:20:30Z')).toBe('2026-03-22 10:20:30')
  })

  it('builds personal bank meta from row and semantic map', () => {
    const meta = buildPersonalBankQuestionMeta(
      {
        knowledgeId: 'k-1',
        extJson: {
          subjectCode: 'POLITICS',
          subjectId: 'subject-1',
          chapter: '马克思主义',
          chapter_code: 'CH_001',
          point_code: 'PT_001_001',
          analysis: '重做解析',
          studentState: {
            personalBank: { isCollected: true, sourceLabel: '已斩获归档' },
            wrongBook: {
              archivedAt: '2026-03-22T08:00:00Z',
              reasonStats: [{ reasonLabel: '概念混淆' }],
            },
          },
        },
      },
      {
        knowledgeSemanticMap: {
          'k-1': {
            levelLabel: 'L5 原子知识点',
            fullPathLabel: '政治 / 马原 / 实践与认识',
            semanticTrail: [
              { id: 'l3', level: 3, label: '马原' },
              { id: 'l4', level: 4, label: '马克思主义' },
              { id: 'l5', level: 5, label: '实践与认识' },
            ],
          },
        },
      },
    )

    expect(meta.subjectCode).toBe('POLITICS')
    expect(meta.pointLabel).toBe('实践与认识')
    expect(meta.semanticPath).toContain('实践与认识')
    expect(meta.reasons).toEqual(['概念混淆'])
    expect(meta.isCollected).toBe(true)
    expect(meta.isArchived).toBe(true)
    expect(meta.sourceType).toBe('')
    expect(meta.stateLabels).toContain('已进入沉淀题库')
    expect(meta.stateLabels).toContain('已斩获归档')
    expect(meta.archivedAt).toBe('2026-03-22 08:00:00')
  })

  it('builds searchable personal bank text', () => {
    const text = buildPersonalBankSearchText(
      { stem: '题干文本', answer: 'A' },
      {
        analysis: '解析内容',
        semanticPath: '政治 / 马原',
        level3Label: '马原',
        chapter: '章节',
        chapterCode: 'CH_001',
        chapterLabel: '马克思主义',
        pointCode: 'PT_001',
        pointLabel: '实践',
        sourceLabel: '已斩获归档',
        reasons: ['概念混淆'],
      },
    )

    expect(text).toContain('题干文本'.toLowerCase())
    expect(text).toContain('概念混淆'.toLowerCase())
  })

  it('builds wrong-book meta with insight fallback and ai plan', () => {
    const meta = buildWrongBookQuestionMeta(
      {
        id: 'q-1',
        knowledgeId: 'k-9',
        extJson: {
          chapter: '导数',
          chapter_code: 'CH_009',
          point_code: 'PT_009_001',
          analysis: '错在步骤变形',
          studentState: {
            chapterPractice: {
              lastAnswer: 'A',
              submitCount: 4,
              correctCount: 1,
              answerDurationSec: 36,
            },
            wrongBook: {
              reviewCount: 2,
              postWrongAttemptCount: 3,
              postWrongCorrectCount: 1,
              lastReasonLabel: '概念混淆',
            },
          },
        },
      },
      {
        knowledgeSemanticMap: {
          'k-9': {
            levelLabel: 'L5 原子知识点',
            fullPathLabel: '数学 / 导数 / 单调性',
            semanticTrail: [
              { id: 'c1', level: 4, levelLabel: 'L4 章节', label: '导数' },
              { id: 'p1', level: 5, levelLabel: 'L5 原子知识点', label: '单调性' },
            ],
          },
        },
        insightMap: {
          'q-1': {
            pointName: '单调性',
            masteryScore: 28,
            jointGroupAccuracyGap: 0.35,
            wrongCount: 3,
            reviewStatusLabel: '生疏',
            reviewStatusKey: 'fragile',
          },
        },
        similarQuestionsMap: {
          'q-1': [{ id: 'q-2' }],
        },
        currentRepairSuggestions: ['回看定义'],
        currentChapterInducerSuggestions: ['检查导数符号'],
        buildWrongBookBreadcrumbTrail: (trail, chapterLabel, pointLabel) => [trail.length, chapterLabel, pointLabel],
        buildWrongBookAiTutorPlan: (payload) => ({ planFor: payload.pointName, wrongCount: payload.wrongCount }),
      },
    )

    expect(meta.chapterLabel).toBe('导数')
    expect(meta.pointLabel).toBe('单调性')
    expect(meta.benchmarkTagType).toBe('danger')
    expect(meta.benchmarkRiskBadgeText).toBe('同组高风险')
    expect(meta.similarQuestions).toEqual([{ id: 'q-2' }])
    expect(meta.aiTutorPlan).toEqual({ planFor: '单调性', wrongCount: 3 })
    expect(meta.lastAnswer).toBe('A')
    expect(meta.reviewCount).toBe(2)
    expect(meta.postWrongAttemptCount).toBe(3)
    expect(meta.lastReasonLabel).toBe('概念混淆')
  })

  it('prefers formal personal-bank and wrong-book state fields when building personal bank meta', () => {
    const meta = buildPersonalBankQuestionMeta(
      {
        knowledgeId: 'k-formal',
        extJson: {
          studentState: {
            personalBank: {
              isCollected: true,
              collectedAt: '2026-03-23T08:30:00Z',
              sourceType: 'HARVESTED_ARCHIVE',
              sourceLabel: '',
            },
            wrongBook: {
              isArchived: true,
              archivedAt: '2026-03-23T09:00:00Z',
              restoredAt: '2026-03-23T10:00:00Z',
              reviewedAt: '2026-03-23T11:00:00Z',
              reviewCount: 3,
              lastReasonLabel: '步骤跳跃',
            },
          },
        },
      },
      {
        knowledgeSemanticMap: {},
      },
    )

    expect(meta.sourceType).toBe('HARVESTED_ARCHIVE')
    expect(meta.sourceLabel).toBe('已斩获归档')
    expect(meta.collectedAt).toBe('2026-03-23 08:30:00')
    expect(meta.archivedAt).toBe('2026-03-23 09:00:00')
    expect(meta.restoredAt).toBe('2026-03-23 10:00:00')
    expect(meta.reviewedAt).toBe('2026-03-23 11:00:00')
    expect(meta.reviewCount).toBe(3)
    expect(meta.lastReasonLabel).toBe('步骤跳跃')
    expect(meta.stateLabels).toContain('已恢复到错题中心')
    expect(meta.stateLabels).toContain('已有复习记录')
  })

  it('handles invalid wrong-book payloads without throwing on error-like missing data', () => {
    const meta = buildWrongBookQuestionMeta(
      {
        id: 'q-error',
        knowledgeId: 'k-error',
        extJson: {
          chapter: '',
          analysis: '',
          studentState: null,
          studentRecord: {
            extJson: '{"wrongBook": "invalid", "chapterPractice": null}',
          },
        },
      },
      {
        knowledgeSemanticMap: {},
        insightMap: {},
        similarQuestionsMap: {},
      },
    )

    expect(meta.chapterLabel).toBe('-')
    expect(meta.analysis).toBe('-')
    expect(meta.lastAnswer).toBe('')
    expect(meta.reviewCount).toBe(0)
    expect(meta.similarQuestions).toEqual([])
  })

  it('hydrates wrong-book meta from repository db record extJson data chain fallback', () => {
    const meta = buildWrongBookQuestionMeta(
      {
        id: 'q-db',
        knowledgeId: 'k-db',
        extJson: {
          studentRecord: {
            extJson: JSON.stringify({
              chapterPractice: {
                lastAnswer: 'C',
                submitCount: 5,
                correctCount: 2,
                answerDurationSec: 48,
              },
              wrongBook: {
                reviewCount: 4,
                postWrongAttemptCount: 6,
                postWrongCorrectCount: 3,
                lastReasonLabel: '公式遗漏',
              },
            }),
          },
        },
      },
      {
        knowledgeSemanticMap: {},
        insightMap: {},
        similarQuestionsMap: {},
      },
    )

    expect(meta.lastAnswer).toBe('C')
    expect(meta.submitCount).toBe(5)
    expect(meta.correctCount).toBe(2)
    expect(meta.answerDurationSec).toBe(48)
    expect(meta.reviewCount).toBe(4)
    expect(meta.postWrongAttemptCount).toBe(6)
    expect(meta.postWrongCorrectCount).toBe(3)
    expect(meta.lastReasonLabel).toBe('公式遗漏')
  })
})
