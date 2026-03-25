// questionBank API envelope: { "code": "...", "message": "...", "data": {} }
export interface BaseResponse {
  code: string
  message: string
  data?: unknown
}

export interface AuthLoginPasswordRequest {
  phone: string
  password: string
}

export interface AuthLoginSmsRequest {
  phone: string
  smsCode?: string
}

export interface AuthSmsCodeRequest {
  phone: string
  purpose: string
}

export interface AuthRegisterRequest {
  phone: string
  smsCode?: string
  password: string
  role: string
  name: string
  examCategoryCode?: string
  jointExamGroupCode?: string
  vocationalMajor?: string
  prepStage?: string
  employeeNo?: string
}

export interface AuthPasswordResetRequest {
  phone: string
  smsCode?: string
  newPassword?: string
}

export interface QuestionTransitionRequest {
  policyVersion?: string
  reason?: string
}

export interface KnowledgePrerequisiteUpdateRequest {
  sourceId?: string
}

export interface KnowledgeLayoutNodeRequest {
  id: string
  x: number
  y: number
}

export interface KnowledgeLayoutSaveRequest {
  nodes: KnowledgeLayoutNodeRequest[]
}

export interface KnowledgeNode {
  id: string
  label: string
  fullLabel?: string
  shortLabel?: string
  parentId?: string | null
  level: number
  sort: number
  createTime?: string
  moduleCode?: string
  mastery: number
  wrongCount?: number
  size: number
  questionCount?: number
  x?: number | null
  y?: number | null
}

export interface KnowledgeLink {
  source: string
  target: string
  type: string
}

export interface KnowledgeGraphResponse {
  nodes: KnowledgeNode[]
  links: KnowledgeLink[]
}

export interface KnowledgeGraphEnvelopeResponse {
  code: string
  message: string
  data: KnowledgeGraphResponse
}

export interface AdaptivePracticeRequest {
  count?: number
  knowledgeId?: string
}

export interface AdaptivePracticeResult {
  questionIds?: string[]
}

export interface AdaptivePracticeResponse {
  code: string
  message: string
  data: AdaptivePracticeResult
}

export interface AdminSyllabusVersionCreateRequest {
  versionName?: string
  copyFromVersionId?: string
}

export interface AdminSyllabusWeightItemRequest {
  knowledgeId?: string
  targetWeight?: number
}

export interface AdminSyllabusWeightsSaveRequest {
  knowledgeWeights?: AdminSyllabusWeightItemRequest[]
}

export type SyllabusWeightsSaveModel = AdminSyllabusWeightsSaveRequest

export interface AdminSystemSettingsSaveRequest {
  platformName?: string
  defaultExamMinutes?: number
  dailyCheckInPoints?: number
  practiceRewardThreshold?: number
  practiceRewardPoints?: number
  paperRewardPoints?: number
  wrongBookRewardThreshold?: number
  wrongBookRewardPoints?: number
  aiDailyLimit?: number
  mockExamRuleProfiles?: Record<string, unknown>
}

export type SystemSettingsModel = AdminSystemSettingsSaveRequest

export interface AdminManagedUserSaveRequest {
  userId?: string
  role: string
  name: string
  mobile: string
  enabled?: boolean
  permissions?: string[]
  examCategoryCode?: string
  jointExamGroupCode?: string
  vocationalMajor?: string
  prepStage?: string
}

export interface AdminStudentsImportRequest {
  csvText?: string
}

export interface BatchQuestionCreateRequest {
  items: unknown[]
  sourceTaskId?: string
}

export type KnowledgeGraphNode = KnowledgeNode
export type KnowledgeGraphLink = KnowledgeLink
export type KnowledgeLayoutNodeItem = KnowledgeLayoutNodeRequest

export enum KnowledgeLinkTypeEnum {
  parent = 'parent',
  prerequisite = 'prerequisite',
}

export enum KnowledgeStatusEnum {
  ENABLED = 'ENABLED',
  DISABLED = 'DISABLED',
}

export interface KnowledgeWriteRequest {
  id?: string | null
  parentId?: string | null
  policyVersion?: string
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  name: string
  sort: number
  status: string
  extJson?: Record<string, unknown>
  createTime?: string | null
  updateTime?: string | null
}

export interface ValidationError {
  loc: Array<string | number>
  msg: string
  type: string
  input?: unknown
  ctx?: Record<string, unknown>
}

export interface HTTPValidationError {
  detail?: ValidationError[]
}

export interface Body_import_template_api_question_bank_imports_template_post {
  knowledgeId: string
  selectedIndexes?: number[] | null
  file: unknown
}

export interface Body_preview_template_import_api_question_bank_imports_template_preview_post {
  knowledgeId: string
  file: unknown
}

export interface Body_batch_parse_questions_api_question_bank_batch_parse_post {
  file: unknown
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  policyVersion?: string
}

export interface Body_parse_knowledge_graph_from_word_api_knowledge_graph_parse_from_word_post {
  file: unknown
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  parseMode?: string
  policyVersion?: string
}

export interface Body_ai_parse_admin_syllabus_api_question_bank_admin_syllabus__versionId__ai_parse_post {
  file: unknown
}

export interface Body_create_teacher_qa_thread_api_question_bank_messages_teacher_qa_threads_post {
  subjectCode: string
  title: string
  content?: string
  attachments?: File[] | null
}

export interface Body_reply_teacher_qa_thread_api_question_bank_messages_teacher_qa_threads__threadId__reply_post {
  content?: string
  attachments?: File[] | null
}

export interface MessagesReadBatchRequest {
  messageIds?: string[]
}

export interface MessagesSettingsSaveRequest {
  allowAiTutor?: boolean
  allowSystemNotice?: boolean
  allowReviewNotice?: boolean
  allowStudyReminder?: boolean
  allowWeeklyReport?: boolean
  allowPointsNotice?: boolean
}

export interface MessagesSendRequest {
  targetMode?: string
  userIds?: string[]
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  sendAt?: string
  category: string
  title: string
  content: string
}

export type MessageCategoryEnum =
  | 'AI_TUTOR'
  | 'AI_MARKING'
  | 'SYSTEM_NOTICE'
  | 'REVIEW_NOTICE'
  | 'STUDY_REMINDER'
  | 'WEEKLY_REPORT'
  | 'POINTS_NOTICE'
  | 'TEACHER_QA'

export interface ManualPaperCreateRequest {
  paperId?: string | null
  paperName?: string
  policyVersion?: string
  subjectId?: string
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  paperType?: string
  paperStatus?: string
  durationMinutes?: number
  totalScore?: number
  visibleToStudents?: boolean
  publishClassIds?: string[]
  questionIds?: string[]
  questionScores?: Record<string, number>
}

export interface PaperAiGenerateRequest {
  policyVersion?: string
  subjectId?: string
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  difficulty: number
  classIds?: string[]
  totalCount?: number
  knowledgeScope?: string[]
}

export type PageActor = Record<string, unknown>
export type PageBootstrapResponse = Record<string, unknown>

export interface ProfessionalTreeSubject {
  code: string
  name: string
  subjectType: string
  subjectSlot: string
  score: number
}

export interface ProfessionalTreeJointExamGroup {
  code: string
  name: string
  majorListText?: string
  children: ProfessionalTreeSubject[]
}

export interface ProfessionalTreeExamCategory {
  code: string
  name: string
  sortNo: number
  enabled?: boolean
  children: ProfessionalTreeJointExamGroup[]
}

export interface ProfessionalTreeResponse {
  code: string
  message: string
  data: ProfessionalTreeExamCategory[]
}

export interface PaperAutoRuleRequest {
  type: string
  count: number
  questionScore: number
}

export interface PaperAutoSaveRequest {
  paperId?: string | null
  policyVersion?: string
  paperName: string
  paperType: string
  paperStatus: string
  durationMinutes: number
  totalScore: number
  visibleToStudents?: boolean
  subjectId: string
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  chapter?: string
  difficulty?: string
  typeRules: PaperAutoRuleRequest[]
}

export interface PaperTemplateSaveRequest {
  templateId?: string | null
  policyVersion?: string
  templateName: string
  paperType: string
  subjectId: string
  chapter?: string
  difficulty?: string
  totalScore: number
  durationMinutes: number
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  typeRules: PaperAutoRuleRequest[]
}

export interface QuestionCreateRequest {
  id?: string | null
  policyVersion?: string
  userId?: string
  title: string
  content: string
  type: string
  examCategoryCode: string
  jointExamGroupCode: string
  subjectCode: string
  knowledgePoints: string[]
  options?: unknown[]
  answer: string
  analysis?: string
  score?: number
  subjectType?: string
  moduleCode?: string
  sourceType?: string
  difficulty?: string
  status?: string
  extJson?: Record<string, unknown>
}

export interface QuestionDeleteBatchRequest {
  policyVersion?: string
  questionIds?: string[]
}

export interface QuestionOptionItem {
  key: string
  content: string
}

export interface QuestionStatusBatchTransitionRequest {
  policyVersion?: string
  questionIds?: string[]
  targetStatus?: string
  reason?: string
}

export enum QuestionStatusEnum {
  DRAFT = 'DRAFT',
  QA_IN_PROGRESS = 'QA_IN_PROGRESS',
  REVIEW_PENDING = 'REVIEW_PENDING',
  PUBLISHED = 'PUBLISHED',
  REJECTED = 'REJECTED',
}

export enum QuestionTypeEnum {
  single_choice = 'single_choice',
  multiple_choice = 'multiple_choice',
  judge = 'judge',
  subjective = 'subjective',
}

export interface QuestionUpdateRequest {
  id?: string | null
  policyVersion?: string
  userId?: string
  createTime?: string
  updateTime?: string
  title?: string
  content?: string
  type?: string
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  knowledgePoints?: string[]
  options?: unknown[]
  answer?: string
  analysis?: string
  score?: number
  subjectType?: string
  moduleCode?: string
  sourceType?: string
  difficulty?: string
  status?: string
  extJson?: Record<string, unknown>
}

export interface StudentAiMarkingSubmitRequest {
  answer: string
  answerImageUrl?: string
  assignmentId?: string
}

export interface StudentAiTutorAskRequest {
  prompt: string
  promptImageUrl?: string
}

export interface StudentSubscriptionRedeemRequest {
  code: string
  requestId?: string
}

export interface StudentSubscriptionMockOrderCreateRequest {
  planCode?: string
  sourceType?: string
  sessionId?: string
}

export interface StudentSubscriptionMockOrderConfirmRequest {
  transactionNo: string
  requestId?: string
  paidAt?: string
}

export interface StudentDiagnosisQuickStartRequest {
  questionCount?: number
  subjectCode?: string
  sourceType?: string
}

export interface StudentDiagnosisQuickSubmitAnswerItem {
  questionId: string
  answer: string
  elapsedSec?: number
}

export interface StudentDiagnosisQuickSubmitRequest {
  answers: StudentDiagnosisQuickSubmitAnswerItem[]
  sourceType?: string
}

export type AiMarkingSubmitModel = StudentAiMarkingSubmitRequest
export type AiTutorAskModel = StudentAiTutorAskRequest
export type AuthLoginPasswordModel = AuthLoginPasswordRequest
export type AuthLoginSmsModel = AuthLoginSmsRequest
export type AuthPasswordResetModel = AuthPasswordResetRequest
export type AuthRegisterModel = AuthRegisterRequest
export type BatchQuestionDeleteModel = QuestionDeleteBatchRequest
export type BatchQuestionStatusModel = QuestionStatusBatchTransitionRequest
export type ImportResultModel = Record<string, unknown>
export type KnowledgeWriteModel = KnowledgeWriteRequest
export type ManagedUserModel = AdminManagedUserSaveRequest
export type MessageSettingsModel = MessagesSettingsSaveRequest
export type PaperAutoRuleModel = PaperAutoRuleRequest

export type PracticeSubmitModel = StudentPracticeSubmitRequest

export interface ExamTaskCreateRequest {
  taskName?: string
  taskType?: string
  subjectId?: string
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
  sourceType?: string
  sourceId?: string
  sourceLabel?: string
  description?: string
  allowRedo?: boolean
  targetQuestionCount?: number
  dueAt?: string
  status?: string
  classIds?: string[]
  studentIds?: string[]
}

export type PaperManualModel = ManualPaperCreateRequest

export type PaperAutoModel = PaperAutoSaveRequest
export type PaperAnswerModel = StudentPaperAnswerRequest

export type PaperSubmitModel = StudentPaperSubmitRequest
export type PaperTemplateModel = PaperTemplateSaveRequest
export type QuestionWriteModel = QuestionCreateRequest
export type SendMessageModel = MessagesSendRequest
export type SmsCodeRequestModel = AuthSmsCodeRequest

export type StatusTransitionModel = QuestionStatusBatchTransitionRequest
export type StatusTransitionPayloadModel = QuestionTransitionRequest
export type StudentProfileModel = StudentProfileUpdateRequest
export type StudentSubmitModel = StudentSessionSubmitRequest
export type SyllabusVersionCreateModel = AdminSyllabusVersionCreateRequest
export type SyllabusWeightItemModel = AdminSyllabusWeightItemRequest

export interface LearningMethodPracticeStartRequest {
  practiceStrategy?: string
  sourceType?: string
  sessionId?: string
}

export interface LearningMethodPracticeCompleteRequest {
  sessionId?: string
  accuracy: number
  reviewSummary?: string
  durationSec?: number
}

export interface LearningMethodAdminSaveRequest {
  methodCode?: string
  methodName?: string
  oneLineIntro?: string
  useWhen?: string[]
  steps?: string[]
  commonMistakes?: string[]
  questionBankActions?: string[]
  starterTask?: string
  difficultyLevel?: string
  estimatedMinutes?: number
  sort?: number
  status?: string
  extJson?: Record<string, unknown>
}

export interface LearningMethodAdminUpdateRequest {
  methodName?: string
  oneLineIntro?: string
  useWhen?: string[]
  steps?: string[]
  commonMistakes?: string[]
  questionBankActions?: string[]
  starterTask?: string
  difficultyLevel?: string
  estimatedMinutes?: number
  sort?: number
  status?: string
  extJson?: Record<string, unknown>
}

export interface LearningMethodAdminSortRequest {
  methodCodes?: string[]
}

export interface StudentPaperAnswerRequest {
  questionId?: string
  answer: string
  elapsedSec?: number
  marked?: boolean
}

export interface StudentPaperSubmitRequest {
  answers: StudentPaperAnswerRequest[]
  totalElapsedSec?: number
}

export interface StudentPersonalBankToggleRequest {
  isCollected?: boolean
}

export interface StudentPracticeSubmitRequest {
  answer: string
  elapsedSec?: number
  assignmentId?: string
  sourceType?: string
  attemptKey?: string
}

export interface StudentMockExamStartRequest {
  subjectId?: string
  examCategoryCode?: string
  jointExamGroupCode?: string
  subjectCode?: string
}

export interface StudentProfileUpdateRequest {
  examCategoryCode?: string
  jointExamGroupCode?: string
}

export interface StudentSessionSubmitRequest {
  answeredCount?: number
  elapsedSec?: number
}

export enum SubjectKindEnum {
  PUBLIC = 'PUBLIC',
  PROFESSIONAL = 'PROFESSIONAL',
}

export enum QuestionDifficultyEnum {
  easy = 'easy',
  medium = 'medium',
  hard = 'hard',
}
