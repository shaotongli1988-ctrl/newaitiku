import { describe, expect, it } from 'vitest'
import {
  DEFAULT_STUDENT_SUBJECT_SCOPE,
  buildStudentSubjectScope,
} from './studentSubjectScope.js'

describe('studentSubjectScope helpers', () => {
  it('uses provided scope labels and preserves the selected subject name', () => {
    expect(buildStudentSubjectScope({
      examCategoryName: '理工类',
      jointExamGroupName: '理工 3',
      subjectName: '高等数学（一）',
    })).toEqual({
      examCategoryName: '理工类',
      jointExamGroupName: '理工 3',
      subjectName: '高等数学（一）',
    })
  })

  it('falls back cleanly when scope labels or subject are empty', () => {
    expect(DEFAULT_STUDENT_SUBJECT_SCOPE).toEqual({
      examCategoryName: '理工类',
      jointExamGroupName: '理工 3',
      subjectName: '未选择科目',
    })
    expect(buildStudentSubjectScope({
      examCategoryName: ' ',
      jointExamGroupName: '',
      subjectName: '   ',
    })).toEqual({
      examCategoryName: '理工类',
      jointExamGroupName: '理工 3',
      subjectName: '未选择科目',
    })
  })
})
