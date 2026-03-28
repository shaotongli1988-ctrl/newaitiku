import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

function readContractsSource() {
  return readFileSync(new URL('./contracts.ts', import.meta.url), 'utf8')
}

describe('API contract alignment integration coverage', () => {
  it('keeps the questionBank backend contract envelope on BaseResponse', () => {
    const source = readContractsSource()

    expect(source).toContain('{ "code": "')
    expect(source).toContain('export interface BaseResponse')
    expect(source).toContain('code: string')
    expect(source).toContain('message: string')
    expect(source).toContain('data?: unknown')
  })

  it('guards error-prone KnowledgeNode contract drift fields', () => {
    const source = readContractsSource()

    expect(source).toContain('fullLabel?: string')
    expect(source).toContain('shortLabel?: string')
    expect(source).toContain('wrongCount?: number')
    expect(source).not.toContain('full_label?: string')
    expect(source).not.toContain('short_label?: string')
    expect(source).not.toContain('wrong_count?: number')
  })

  it('enforces camelCase-only submit request contracts', () => {
    const source = readContractsSource()

    expect(source).toContain('assignmentId?: string')
    expect(source).toContain('sourceType?: string')
    expect(source).toContain('attemptKey?: string')
    expect(source).not.toContain('assignment_id?: string')
    expect(source).not.toContain('attempt_key?: string')
    expect(source).not.toContain('source_type?: string')
  })

  it('keeps backend integration request schemas available for exam task and mock exam start flows', () => {
    const source = readContractsSource()

    expect(source).toContain('export interface ExamTaskCreateRequest')
    expect(source).toContain('taskName?: string')
    expect(source).toContain('studentIds?: string[]')
    expect(source).toContain('export interface StudentMockExamStartRequest')
    expect(source).toContain('subjectCode?: string')
  })

  it('maintains single entry contract declarations for canonical submit payload contracts', () => {
    const source = readContractsSource()

    expect(source).toContain('export interface StudentPracticeSubmitRequest')
    expect(source).toContain('assignmentId?: string')
    expect(source).toContain('export interface StudentAiMarkingSubmitRequest')
    expect(source).toContain('answerImageUrl?: string')
  })

  it('keeps question create/update request contracts aligned with camelCase scope fields', () => {
    const source = readContractsSource()

    expect(source).toContain('export interface QuestionCreateRequest')
    expect(source).toContain('examCategoryCode: string')
    expect(source).toContain('jointExamGroupCode: string')
    expect(source).toContain('subjectCode: string')
    expect(source).toContain('knowledgePoints: string[]')
    expect(source).toContain('export interface QuestionUpdateRequest')
    expect(source).toContain('examCategoryCode?: string')
    expect(source).toContain('jointExamGroupCode?: string')
    expect(source).toContain('subjectCode?: string')
    expect(source).toContain('knowledgePoints?: string[]')
    expect(source).not.toContain('exam_category_code')
    expect(source).not.toContain('joint_exam_group_code')
    expect(source).not.toContain('subject_code')
    expect(source).not.toContain('knowledge_points')
  })

  it('removes stale consumer-only task type enum contract', () => {
    const source = readContractsSource()

    expect(source).not.toContain('export enum TaskTypeEnum')
    expect(source).not.toContain('AI_MARKING =')
    expect(source).not.toContain('QUESTION_BATCH_PARSE =')
  })

  it('removes stale consumer-only task status enum contract', () => {
    const source = readContractsSource()

    expect(source).not.toContain('export enum TaskStatusEnum')
    expect(source).not.toContain('QUEUED =')
    expect(source).not.toContain('CANCELLED =')
  })
})
