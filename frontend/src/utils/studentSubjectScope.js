function toText(value) {
  return String(value || '').trim()
}

export const DEFAULT_STUDENT_SUBJECT_SCOPE = Object.freeze({
  examCategoryName: '理工类',
  jointExamGroupName: '理工 3',
  subjectName: '未选择科目',
})

export function buildStudentSubjectScope({
  examCategoryName = '',
  jointExamGroupName = '',
  subjectName = '',
} = {}) {
  return {
    examCategoryName: toText(examCategoryName) || DEFAULT_STUDENT_SUBJECT_SCOPE.examCategoryName,
    jointExamGroupName: toText(jointExamGroupName) || DEFAULT_STUDENT_SUBJECT_SCOPE.jointExamGroupName,
    subjectName: toText(subjectName) || DEFAULT_STUDENT_SUBJECT_SCOPE.subjectName,
  }
}
