import { describe, expect, it } from 'vitest'
import {
  buildMockExamPreviewRows,
  isMockExamPreviewPaper,
  listMockExamPreviewQuestions,
} from './studentMockExamPreview'

describe('studentMockExamPreview helpers', () => {
  it('builds preview paper rows that can drive the mock paper deck', () => {
    const rows = buildMockExamPreviewRows({
      subjectCode: 'ADVANCED_MATH',
      subjectName: '高等数学',
    })

    expect(rows.length).toBeGreaterThan(0)
    expect(isMockExamPreviewPaper(rows[0].id)).toBe(true)
    expect(rows[0].extJson).toContain('paperBindings')
    expect(rows[0].extJson).toContain('ADVANCED_MATH')
  })

  it('returns stable preview questions for the selected preview paper', () => {
    const rows = buildMockExamPreviewRows({
      subjectCode: 'ENGLISH',
      subjectName: '英语',
    })
    const firstPaperBinding = JSON.parse(rows[0].extJson).paperBindings[0]
    const questions = listMockExamPreviewQuestions(firstPaperBinding.paperId, {
      subjectCode: 'ENGLISH',
      subjectName: '英语',
    })

    expect(isMockExamPreviewPaper(firstPaperBinding.paperId)).toBe(true)
    expect(questions.length).toBeGreaterThan(0)
    expect(questions[0].stem).toContain('预览卷')
    expect(questions[0].optionsJson).toContain('A')
  })
})
