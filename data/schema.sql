-- 安全说明：
-- 本文件仅用于初始化缺失表与索引，不再包含任何破坏性 DROP TABLE。
-- 如需重建本地数据库，请使用单独的开发重置脚本，禁止将重建脚本作为上线脚本执行。
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS "user" (
  id TEXT PRIMARY KEY,
  phone TEXT NOT NULL,
  password TEXT NOT NULL,
  status TEXT NOT NULL,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS userAuth (
  id TEXT PRIMARY KEY,
  userId TEXT NOT NULL,
  type TEXT NOT NULL,
  openid TEXT NOT NULL,
  unionid TEXT NOT NULL,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (userId) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS knowledge (
  id TEXT PRIMARY KEY,
  parentId TEXT,
  name TEXT NOT NULL,
  sort INTEGER NOT NULL,
  status TEXT NOT NULL,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (parentId) REFERENCES knowledge(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS question (
  id TEXT PRIMARY KEY,
  knowledgeId TEXT NOT NULL,
  userId TEXT NOT NULL,
  type TEXT NOT NULL,
  stem TEXT NOT NULL,
  optionsJson TEXT NOT NULL,
  answer TEXT NOT NULL,
  status TEXT NOT NULL,
  extJson TEXT NOT NULL,
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (knowledgeId) REFERENCES knowledge(id) ON DELETE RESTRICT,
  FOREIGN KEY (userId) REFERENCES "user"(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS task (
  id TEXT PRIMARY KEY,
  userId TEXT NOT NULL,
  type TEXT NOT NULL,
  status TEXT NOT NULL,
  progress INTEGER NOT NULL,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (userId) REFERENCES "user"(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS student_question_record (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  questionId TEXT NOT NULL,
  status TEXT NOT NULL,
  lastSubmittedAt TEXT NOT NULL DEFAULT '',
  lastAnswer TEXT NOT NULL DEFAULT '',
  lastIsCorrect INTEGER NOT NULL DEFAULT 0,
  answerCount INTEGER NOT NULL DEFAULT 0,
  correctCount INTEGER NOT NULL DEFAULT 0,
  wrongCount INTEGER NOT NULL DEFAULT 0,
  totalAnswerDurationSec INTEGER NOT NULL DEFAULT 0,
  latestSourceType TEXT NOT NULL DEFAULT '',
  latestPaperId TEXT NOT NULL DEFAULT '',
  wrongBookFlag INTEGER NOT NULL DEFAULT 0,
  wrongBookArchivedFlag INTEGER NOT NULL DEFAULT 0,
  wrongBookCollectedAt TEXT NOT NULL DEFAULT '',
  wrongBookLastWrongAt TEXT NOT NULL DEFAULT '',
  wrongBookReviewedAt TEXT NOT NULL DEFAULT '',
  wrongBookArchivedAt TEXT NOT NULL DEFAULT '',
  wrongBookRestoredAt TEXT NOT NULL DEFAULT '',
  wrongBookReviewCount INTEGER NOT NULL DEFAULT 0,
  wrongBookPostWrongAttemptCount INTEGER NOT NULL DEFAULT 0,
  wrongBookPostWrongCorrectCount INTEGER NOT NULL DEFAULT 0,
  wrongBookLastReasonCode TEXT NOT NULL DEFAULT '',
  wrongBookLastReasonLabel TEXT NOT NULL DEFAULT '',
  personalBankFlag INTEGER NOT NULL DEFAULT 0,
  personalBankCollectedAt TEXT NOT NULL DEFAULT '',
  personalBankSourceType TEXT NOT NULL DEFAULT '',
  personalBankSourceLabel TEXT NOT NULL DEFAULT '',
  profileAnchorFlag INTEGER NOT NULL DEFAULT 0,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  FOREIGN KEY (questionId) REFERENCES question(id) ON DELETE CASCADE,
  UNIQUE (studentUserId, questionId)
);

CREATE TABLE IF NOT EXISTS student_daily_progress (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  progressDate TEXT NOT NULL,
  checkInCount INTEGER NOT NULL DEFAULT 0,
  practiceAnswers INTEGER NOT NULL DEFAULT 0,
  papersCompleted INTEGER NOT NULL DEFAULT 0,
  wrongBookReviewed INTEGER NOT NULL DEFAULT 0,
  rewardedKeysJson TEXT NOT NULL DEFAULT '[]',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (studentUserId, progressDate)
);

CREATE TABLE IF NOT EXISTS student_points_ledger (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  eventKey TEXT NOT NULL,
  reason TEXT NOT NULL,
  points INTEGER NOT NULL DEFAULT 0,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (studentUserId, eventKey)
);

CREATE TABLE IF NOT EXISTS student_profile_state (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  examCategoryCode TEXT NOT NULL DEFAULT 'SCIENCE_ENGINEERING',
  jointExamGroupCode TEXT NOT NULL DEFAULT 'SCIENCE_ENGINEERING_3',
  points INTEGER NOT NULL DEFAULT 0,
  title TEXT NOT NULL DEFAULT '备考新星',
  unlockedTitlesJson TEXT NOT NULL DEFAULT '[]',
  checkInDatesJson TEXT NOT NULL DEFAULT '[]',
  aiDailyLimit INTEGER NOT NULL DEFAULT 20,
  aiUsedCount INTEGER NOT NULL DEFAULT 0,
  aiQuotaDate TEXT NOT NULL DEFAULT '',
  examAnsweredCount INTEGER NOT NULL DEFAULT 0,
  examElapsedSec INTEGER NOT NULL DEFAULT 0,
  examUpdateTime TEXT NOT NULL DEFAULT '',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (studentUserId)
);

CREATE TABLE IF NOT EXISTS student_review_plan (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  planType TEXT NOT NULL,
  planName TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  generatedAt TEXT NOT NULL DEFAULT '',
  startedAt TEXT NOT NULL DEFAULT '',
  completedAt TEXT NOT NULL DEFAULT '',
  lastExecutedAt TEXT NOT NULL DEFAULT '',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (studentUserId, planType)
);

CREATE TABLE IF NOT EXISTS student_review_plan_item (
  id TEXT PRIMARY KEY,
  planId TEXT NOT NULL,
  studentUserId TEXT NOT NULL,
  questionId TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  sort INTEGER NOT NULL DEFAULT 0,
  completedAt TEXT NOT NULL DEFAULT '',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (planId) REFERENCES student_review_plan(id) ON DELETE CASCADE,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  FOREIGN KEY (questionId) REFERENCES question(id) ON DELETE CASCADE,
  UNIQUE (planId, questionId)
);

CREATE TABLE IF NOT EXISTS paper_report (
  id TEXT PRIMARY KEY,
  reportId TEXT NOT NULL,
  studentUserId TEXT NOT NULL,
  paperId TEXT NOT NULL,
  subjectId TEXT NOT NULL DEFAULT '',
  subjectIdsJson TEXT NOT NULL DEFAULT '[]',
  score INTEGER NOT NULL DEFAULT 0,
  totalScore INTEGER NOT NULL DEFAULT 0,
  scoreRate REAL NOT NULL DEFAULT 0,
  totalElapsedSec INTEGER NOT NULL DEFAULT 0,
  submittedAt TEXT NOT NULL DEFAULT '',
  pendingSubjectiveCount INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (reportId)
);

CREATE TABLE IF NOT EXISTS exam_task (
  id TEXT PRIMARY KEY,
  taskName TEXT NOT NULL,
  taskType TEXT NOT NULL,
  subjectId TEXT NOT NULL DEFAULT '',
  examCategoryCode TEXT NOT NULL DEFAULT '',
  jointExamGroupCode TEXT NOT NULL DEFAULT '',
  subjectCode TEXT NOT NULL DEFAULT '',
  sourceType TEXT NOT NULL DEFAULT '',
  sourceId TEXT NOT NULL DEFAULT '',
  sourceLabel TEXT NOT NULL DEFAULT '',
  teacherUserId TEXT NOT NULL,
  teacherName TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  allowRedo INTEGER NOT NULL DEFAULT 0,
  dueAt TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'DRAFT',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (teacherUserId) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exam_task_target (
  id TEXT PRIMARY KEY,
  taskId TEXT NOT NULL,
  targetType TEXT NOT NULL,
  targetId TEXT NOT NULL,
  targetName TEXT NOT NULL DEFAULT '',
  createTime TEXT NOT NULL,
  FOREIGN KEY (taskId) REFERENCES exam_task(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exam_task_assignment (
  id TEXT PRIMARY KEY,
  taskId TEXT NOT NULL,
  studentUserId TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'NOT_STARTED',
  score INTEGER NOT NULL DEFAULT 0,
  totalScore INTEGER NOT NULL DEFAULT 0,
  startedAt TEXT NOT NULL DEFAULT '',
  submittedAt TEXT NOT NULL DEFAULT '',
  completedAt TEXT NOT NULL DEFAULT '',
  expiredAt TEXT NOT NULL DEFAULT '',
  lastPaperId TEXT NOT NULL DEFAULT '',
  redoCount INTEGER NOT NULL DEFAULT 0,
  maxRedoCount INTEGER NOT NULL DEFAULT 0,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (taskId) REFERENCES exam_task(id) ON DELETE CASCADE,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (taskId, studentUserId)
);

CREATE TABLE IF NOT EXISTS mock_exam_session (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  subjectCode TEXT NOT NULL,
  examCategoryCode TEXT NOT NULL DEFAULT '',
  jointExamGroupCode TEXT NOT NULL DEFAULT '',
  paperId TEXT NOT NULL,
  paperName TEXT NOT NULL DEFAULT '',
  questionCount INTEGER NOT NULL DEFAULT 0,
  totalScore INTEGER NOT NULL DEFAULT 0,
  durationMinutes INTEGER NOT NULL DEFAULT 0,
  syllabusVersion TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  ruleSnapshotJson TEXT NOT NULL DEFAULT '{}',
  degradeSummaryJson TEXT NOT NULL DEFAULT '{}',
  startedAt TEXT NOT NULL DEFAULT '',
  submittedAt TEXT NOT NULL DEFAULT '',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS challenge_point_event (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  questionId TEXT NOT NULL,
  subjectCode TEXT NOT NULL,
  attemptKey TEXT NOT NULL DEFAULT '',
  sourceType TEXT NOT NULL DEFAULT '',
  points INTEGER NOT NULL DEFAULT 1,
  awardedAt TEXT NOT NULL,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  FOREIGN KEY (questionId) REFERENCES question(id) ON DELETE CASCADE,
  UNIQUE (studentUserId, questionId, attemptKey)
);

CREATE TABLE IF NOT EXISTS challenge_point_subject (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  subjectCode TEXT NOT NULL,
  totalPoints INTEGER NOT NULL DEFAULT 0,
  lastAwardedAt TEXT NOT NULL DEFAULT '',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (studentUserId, subjectCode)
);

CREATE TABLE IF NOT EXISTS challenge_point_award (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  subjectCode TEXT NOT NULL,
  awardCode TEXT NOT NULL,
  awardName TEXT NOT NULL,
  unlockedAt TEXT NOT NULL,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (studentUserId, subjectCode, awardCode)
);

CREATE TABLE IF NOT EXISTS message_send_history (
  id TEXT PRIMARY KEY,
  traceId TEXT NOT NULL,
  scheduleId TEXT NOT NULL DEFAULT '',
  senderUserId TEXT NOT NULL,
  targetMode TEXT NOT NULL DEFAULT '',
  targetCount INTEGER NOT NULL DEFAULT 0,
  sentCount INTEGER NOT NULL DEFAULT 0,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  sendAt TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL,
  recalledAt TEXT NOT NULL DEFAULT '',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  extJson TEXT NOT NULL DEFAULT '{}',
  FOREIGN KEY (senderUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (traceId)
);

CREATE TABLE IF NOT EXISTS learning_method (
  id TEXT PRIMARY KEY,
  methodCode TEXT NOT NULL UNIQUE,
  methodName TEXT NOT NULL,
  oneLineIntro TEXT NOT NULL DEFAULT '',
  useWhenJson TEXT NOT NULL DEFAULT '[]',
  stepsJson TEXT NOT NULL DEFAULT '[]',
  commonMistakesJson TEXT NOT NULL DEFAULT '[]',
  questionBankActionsJson TEXT NOT NULL DEFAULT '[]',
  starterTask TEXT NOT NULL DEFAULT '',
  difficultyLevel TEXT NOT NULL DEFAULT 'L1',
  estimatedMinutes INTEGER NOT NULL DEFAULT 15,
  sort INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS student_learning_method_progress (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  methodCode TEXT NOT NULL,
  startCount INTEGER NOT NULL DEFAULT 0,
  completeCount INTEGER NOT NULL DEFAULT 0,
  lastPracticedAt TEXT NOT NULL DEFAULT '',
  lastAccuracy REAL NOT NULL DEFAULT 0,
  lastReviewSummary TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'NOT_STARTED',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  FOREIGN KEY (methodCode) REFERENCES learning_method(methodCode) ON DELETE CASCADE,
  UNIQUE (studentUserId, methodCode)
);

CREATE TABLE IF NOT EXISTS subscription_plan (
  id TEXT PRIMARY KEY,
  planCode TEXT NOT NULL UNIQUE,
  planName TEXT NOT NULL,
  durationDays INTEGER NOT NULL DEFAULT 30,
  listPriceFen INTEGER NOT NULL DEFAULT 0,
  salePriceFen INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  sort INTEGER NOT NULL DEFAULT 0,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS student_subscription (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL,
  currentPlanCode TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'INACTIVE',
  startTime TEXT NOT NULL DEFAULT '',
  endTime TEXT NOT NULL DEFAULT '',
  lastActivatedAt TEXT NOT NULL DEFAULT '',
  lastExpiredAt TEXT NOT NULL DEFAULT '',
  sourceType TEXT NOT NULL DEFAULT '',
  sourceOrderId TEXT NOT NULL DEFAULT '',
  sourceRedeemCode TEXT NOT NULL DEFAULT '',
  totalActivatedDays INTEGER NOT NULL DEFAULT 0,
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
  UNIQUE (studentUserId)
);

CREATE TABLE IF NOT EXISTS redeem_code_batch (
  id TEXT PRIMARY KEY,
  batchCode TEXT NOT NULL UNIQUE,
  batchName TEXT NOT NULL,
  channelCode TEXT NOT NULL DEFAULT '',
  planCode TEXT NOT NULL DEFAULT '',
  totalCount INTEGER NOT NULL DEFAULT 0,
  usedCount INTEGER NOT NULL DEFAULT 0,
  expiresAt TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  createdByUserId TEXT NOT NULL DEFAULT '',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS redeem_code (
  id TEXT PRIMARY KEY,
  batchId TEXT NOT NULL,
  code TEXT NOT NULL UNIQUE,
  planCode TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'UNUSED',
  expiresAt TEXT NOT NULL DEFAULT '',
  usedByUserId TEXT NOT NULL DEFAULT '',
  usedAt TEXT NOT NULL DEFAULT '',
  sourceOrderId TEXT NOT NULL DEFAULT '',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (batchId) REFERENCES redeem_code_batch(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS subscription_order (
  id TEXT PRIMARY KEY,
  orderNo TEXT NOT NULL UNIQUE,
  studentUserId TEXT NOT NULL,
  planCode TEXT NOT NULL DEFAULT '',
  amountFen INTEGER NOT NULL DEFAULT 0,
  channel TEXT NOT NULL DEFAULT 'MOCK',
  status TEXT NOT NULL DEFAULT 'CREATED',
  paidAt TEXT NOT NULL DEFAULT '',
  closedAt TEXT NOT NULL DEFAULT '',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payment_transaction_mock (
  id TEXT PRIMARY KEY,
  orderId TEXT NOT NULL,
  transactionNo TEXT NOT NULL UNIQUE,
  requestId TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'SUCCESS',
  payloadJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL,
  FOREIGN KEY (orderId) REFERENCES subscription_order(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversion_event_log (
  id TEXT PRIMARY KEY,
  studentUserId TEXT NOT NULL DEFAULT '',
  eventType TEXT NOT NULL,
  eventTime TEXT NOT NULL,
  eventDate TEXT NOT NULL DEFAULT '',
  sessionId TEXT NOT NULL DEFAULT '',
  planCode TEXT NOT NULL DEFAULT '',
  orderId TEXT NOT NULL DEFAULT '',
  redeemCode TEXT NOT NULL DEFAULT '',
  channelCode TEXT NOT NULL DEFAULT '',
  extJson TEXT NOT NULL DEFAULT '{}',
  createTime TEXT NOT NULL,
  updateTime TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_status
ON "user"(status);

CREATE INDEX IF NOT EXISTS idx_userauth_user_type
ON userAuth(userId, type);

CREATE INDEX IF NOT EXISTS idx_knowledge_parent_sort
ON knowledge(parentId, sort);

CREATE INDEX IF NOT EXISTS idx_question_knowledge_status
ON question(knowledgeId, status);

CREATE INDEX IF NOT EXISTS idx_question_owner_status
ON question(userId, status);

CREATE INDEX IF NOT EXISTS idx_question_policy
ON question(COALESCE(json_extract(extJson, '$.policyVersionCode'), ''));

CREATE INDEX IF NOT EXISTS idx_question_joint_group
ON question(COALESCE(json_extract(extJson, '$.jointExamGroupCode'), ''));

CREATE INDEX IF NOT EXISTS idx_question_subject
ON question(COALESCE(json_extract(extJson, '$.subjectCode'), ''));

CREATE INDEX IF NOT EXISTS idx_task_user_status
ON task(userId, status, type);

CREATE INDEX IF NOT EXISTS idx_student_question_record_user_status_update
ON student_question_record(studentUserId, status, updateTime);

CREATE INDEX IF NOT EXISTS idx_student_question_record_question_status
ON student_question_record(questionId, status);

CREATE INDEX IF NOT EXISTS idx_student_question_record_user_wrong_book_update
ON student_question_record(studentUserId, wrongBookFlag, updateTime);

CREATE INDEX IF NOT EXISTS idx_student_question_record_user_personal_bank_update
ON student_question_record(studentUserId, personalBankFlag, updateTime);

CREATE INDEX IF NOT EXISTS idx_student_question_record_user_submitted
ON student_question_record(studentUserId, lastSubmittedAt);

CREATE INDEX IF NOT EXISTS idx_student_daily_progress_user_date
ON student_daily_progress(studentUserId, progressDate DESC);

CREATE INDEX IF NOT EXISTS idx_student_points_ledger_user_time
ON student_points_ledger(studentUserId, createTime DESC, eventKey ASC);

CREATE INDEX IF NOT EXISTS idx_student_profile_state_user
ON student_profile_state(studentUserId);

CREATE INDEX IF NOT EXISTS idx_student_review_plan_user_status_update
ON student_review_plan(studentUserId, status, updateTime);

CREATE INDEX IF NOT EXISTS idx_student_review_plan_item_plan_status_sort
ON student_review_plan_item(planId, status, sort, updateTime);

CREATE INDEX IF NOT EXISTS idx_paper_report_student_submitted
ON paper_report(studentUserId, submittedAt DESC);

CREATE INDEX IF NOT EXISTS idx_paper_report_student_paper_submitted
ON paper_report(studentUserId, paperId, submittedAt DESC);

CREATE INDEX IF NOT EXISTS idx_paper_report_student_subject_submitted
ON paper_report(studentUserId, subjectId, submittedAt DESC);

CREATE INDEX IF NOT EXISTS idx_paper_report_paper_submitted
ON paper_report(paperId, submittedAt DESC);

CREATE INDEX IF NOT EXISTS idx_exam_task_teacher_status_due
ON exam_task(teacherUserId, status, dueAt DESC);

CREATE INDEX IF NOT EXISTS idx_exam_task_subject_status
ON exam_task(subjectCode, status, dueAt DESC);

CREATE INDEX IF NOT EXISTS idx_exam_task_target_task
ON exam_task_target(taskId, targetType, targetId);

CREATE INDEX IF NOT EXISTS idx_exam_task_assignment_student_status_due
ON exam_task_assignment(studentUserId, status, updateTime DESC);

CREATE INDEX IF NOT EXISTS idx_exam_task_assignment_task_status
ON exam_task_assignment(taskId, status, updateTime DESC);

CREATE INDEX IF NOT EXISTS idx_mock_exam_session_student_status
ON mock_exam_session(studentUserId, status, createTime DESC);

CREATE INDEX IF NOT EXISTS idx_mock_exam_session_student_subject_status
ON mock_exam_session(studentUserId, subjectCode, status, createTime DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mock_exam_session_active_unique
ON mock_exam_session(studentUserId, subjectCode)
WHERE status = 'ACTIVE';

/* online index rollout note: local SQLite schema keeps the target index definitions here, and release rollout follows the documented online/serial publish steps in docs/release/db-index-rollout-2026-03-20.md. */
CREATE INDEX IF NOT EXISTS idx_challenge_point_event_subject_awarded
ON challenge_point_event(subjectCode, awardedAt DESC);

CREATE INDEX IF NOT EXISTS idx_challenge_point_event_student_subject_awarded
ON challenge_point_event(studentUserId, subjectCode, awardedAt DESC);

CREATE INDEX IF NOT EXISTS idx_challenge_point_subject_subject_points
ON challenge_point_subject(subjectCode, totalPoints DESC, updateTime ASC);

CREATE INDEX IF NOT EXISTS idx_challenge_point_subject_student
ON challenge_point_subject(studentUserId, subjectCode);

CREATE INDEX IF NOT EXISTS idx_challenge_point_award_student_subject
ON challenge_point_award(studentUserId, subjectCode, unlockedAt DESC);

CREATE INDEX IF NOT EXISTS idx_message_send_history_sender_create
ON message_send_history(senderUserId, createTime DESC);

CREATE INDEX IF NOT EXISTS idx_message_send_history_sender_status_create
ON message_send_history(senderUserId, status, createTime DESC);

CREATE INDEX IF NOT EXISTS idx_message_send_history_schedule
ON message_send_history(scheduleId);

CREATE INDEX IF NOT EXISTS idx_message_send_history_send_at
ON message_send_history(sendAt);

CREATE INDEX IF NOT EXISTS idx_learning_method_status_sort
ON learning_method(status, sort, methodCode);

CREATE INDEX IF NOT EXISTS idx_student_learning_method_progress_user_status_update
ON student_learning_method_progress(studentUserId, status, updateTime);

CREATE INDEX IF NOT EXISTS idx_student_learning_method_progress_method_update
ON student_learning_method_progress(methodCode, updateTime);

CREATE INDEX IF NOT EXISTS idx_subscription_plan_status_sort
ON subscription_plan(status, sort, planCode);

CREATE INDEX IF NOT EXISTS idx_student_subscription_status_end
ON student_subscription(status, endTime, updateTime);

CREATE INDEX IF NOT EXISTS idx_redeem_code_batch_status_expire
ON redeem_code_batch(status, expiresAt, updateTime);

CREATE INDEX IF NOT EXISTS idx_redeem_code_batch_used
ON redeem_code(batchId, status, updateTime);

CREATE INDEX IF NOT EXISTS idx_redeem_code_status_expire
ON redeem_code(status, expiresAt, updateTime);

CREATE INDEX IF NOT EXISTS idx_redeem_code_used_by_user
ON redeem_code(usedByUserId, usedAt, updateTime);

CREATE INDEX IF NOT EXISTS idx_subscription_order_student_status_update
ON subscription_order(studentUserId, status, updateTime);

CREATE INDEX IF NOT EXISTS idx_subscription_order_status_paid
ON subscription_order(status, paidAt, updateTime);

CREATE INDEX IF NOT EXISTS idx_payment_transaction_mock_order
ON payment_transaction_mock(orderId, createTime);

CREATE INDEX IF NOT EXISTS idx_conversion_event_type_time
ON conversion_event_log(eventType, eventTime);

CREATE INDEX IF NOT EXISTS idx_conversion_event_student_time
ON conversion_event_log(studentUserId, eventTime);

CREATE INDEX IF NOT EXISTS idx_conversion_event_date_type
ON conversion_event_log(eventDate, eventType);
