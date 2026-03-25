# 题库固定合同

本项目当前按统一五表合同运行，数据库、后端、API、前端、测试使用同一套字段命名与响应口径。

## 1. 固定表

- `user`
  - `id`, `phone`, `password`, `status`, `extJson`, `createTime`, `updateTime`
- `userAuth`
  - `id`, `userId`, `type`, `openid`, `unionid`, `extJson`, `createTime`, `updateTime`
- `knowledge`
  - `id`, `parentId`, `name`, `sort`, `status`, `extJson`, `createTime`, `updateTime`
- `question`
  - `id`, `knowledgeId`, `userId`, `type`, `stem`, `optionsJson`, `answer`, `status`, `extJson`, `createTime`, `updateTime`
- `task`
  - `id`, `userId`, `type`, `status`, `progress`, `extJson`, `createTime`, `updateTime`

## 2. 全局规则

- 成功响应固定为 `{ code, message, data }`
- 分页固定为 `{ items, page, size, total }`
- 所有关系仅保留 ID 字段
- 合同外业务数据统一进入 `extJson`
- 高频状态、报告型数据、并发写状态、需要唯一约束的数据不得继续进入 `extJson`
- 高频状态、报告型数据、并发写状态、需要唯一约束的数据必须入正式业务表
- 不再使用 `subjects`、`questions`、`question_reviews`、`student_question_bank`、`question_vectors`

## 3. question 合同

固定字段顺序：

`id`, `knowledgeId`, `userId`, `type`, `stem`, `optionsJson`, `answer`, `status`, `extJson`, `createTime`, `updateTime`

扩展数据统一放入 `question.extJson`，包括但不限于：

- `subjectId`, `chapter`, `difficulty`, `analysis`, `knowledgeTags`
- `policyVersionCode`, `examCategoryCode`, `jointExamGroupCode`, `subjectCode`, `subjectType`, `moduleCode`, `sourceType`, `applicableGroups`
- `paperBindings`, `practiceConfig`, `reviewRecords`, `reviewSummary`

## 4. user 承接范围

- 普通用户行继续承接 `role`、`name`、`permissions`、`examCategoryCode`、`jointExamGroupCode`、`vocationalMajor`、`prepStage`
- 学生用户题目学习态统一进入 `student_question_record` 正式表，按 `studentUserId + questionId` 管理：
  - `studentProfile`
  - `chapterPractice`
  - `simulationAttempts`
  - `wrongBook`
  - `personalBank`
  - `aiMarking`
  - `aiTutor`
- `student_question_record` 中沉淀题库相关正式列至少固定包含：
  - `personalBankFlag`
  - `personalBankCollectedAt`
  - `personalBankSourceType`
  - `personalBankSourceLabel`
  - `wrongBookArchivedFlag`
  - `wrongBookArchivedAt`
  - `wrongBookRestoredAt`
- 学生复习计划为正式业务，不再由 `summary.reviewPlan` 临时拼装，统一入正式表：
  - `student_review_plan`
  - `student_review_plan_item`
- 系统用户 `user.id="__system__"` 承接以下低频系统扩展：
  - `systemSettings`
  - `messages`
  - `messageSettingsByUser`
  - `paperTemplates`
- 报告与消息发送历史统一入正式表：
  - `paper_report`
  - `message_send_history`
- `extJson` 不再承接 `studentRecords`、`paperReports`、`messageSendHistory` 这三类热状态；迁移基线见 [docs/extjson-hot-state-readiness-2026-03-22.md](/Users/shaotongli/Documents/newaitiku/docs/extjson-hot-state-readiness-2026-03-22.md)

## 4.1 沉淀题库与复习计划合同

- 沉淀题库正式语义统一为“沉淀题库”，不再以 `personal-bank` 作为产品语义扩散。
- 沉淀题库列表、汇总、导出统一基于 `student_question_record` 正式列筛选。
- `summary.reviewPlan` 仅作为正式复习计划的摘要投影，不再作为计划真相源。
- 复习计划正式接口固定为：
  - `GET /api/question-bank/student/personal-bank/review-plans`
  - `GET /api/question-bank/student/personal-bank/review-plans/{plan_id}`
  - `POST /api/question-bank/student/personal-bank/review-plans/{plan_id}/start`
  - `POST /api/question-bank/student/personal-bank/review-plans/{plan_id}/questions/{question_id}/complete`
- 复习计划固定状态至少包含：
  - `PENDING`
  - `IN_PROGRESS`
  - `COMPLETED`

## 4.2 学习方法与练习进度合同

- 学习方法主数据为正式业务，不进入 `extJson`，统一入表：
  - `learning_method`
- 学生学习方法练习进度为正式高频状态，不进入 `extJson`，统一入表：
  - `student_learning_method_progress`
- 学习方法主数据至少固定包含：
  - `id`
  - `methodCode`
  - `methodName`
  - `oneLineIntro`
  - `useWhenJson`
  - `stepsJson`
  - `commonMistakesJson`
  - `questionBankActionsJson`
  - `starterTask`
  - `difficultyLevel`
  - `estimatedMinutes`
  - `sort`
  - `status`
  - `extJson`
  - `createTime`
  - `updateTime`
- 学生练习进度至少固定包含：
  - `id`
  - `studentUserId`
  - `methodCode`
  - `status`
  - `practiceCount`
  - `lastSessionId`
  - `lastPracticedAt`
  - `lastAccuracy`
  - `lastReviewSummary`
  - `lastDurationSec`
  - `extJson`
  - `createTime`
  - `updateTime`
- 学生端固定接口：
  - `GET /api/question-bank/learning-methods`
  - `GET /api/question-bank/learning-methods/{method_code}`
  - `POST /api/question-bank/learning-methods/{method_code}/start`
  - `POST /api/question-bank/learning-methods/{method_code}/complete`
- 管理端固定接口：
  - `GET /api/question-bank/admin/learning-methods`
  - `POST /api/question-bank/admin/learning-methods`
  - `PUT /api/question-bank/admin/learning-methods/{method_code}`
  - `POST /api/question-bank/admin/learning-methods/sort`
- 学生练习状态固定包含：
  - `NOT_STARTED`
  - `IN_PROGRESS`
  - `COMPLETED`

## 5. task 合同

固定字段顺序：

`id`, `userId`, `type`, `status`, `progress`, `extJson`, `createTime`, `updateTime`

`task.extJson` 统一承接：

- `questionId`
- `requestPayload`
- `result`
- `resultSummary`
- `errorMessage`
- `queue`

任务接口包含：

- `GET /api/question-bank/tasks`
- `GET /api/question-bank/tasks/{task_id}`
- `POST /api/question-bank/tasks/{task_id}/cancel`

考试任务为独立正式业务，不复用通用 `task` 表承接学习任务状态：

- 教师端接口：
  - `GET /api/question-bank/exam-tasks`
  - `POST /api/question-bank/exam-tasks`
  - `GET /api/question-bank/exam-tasks/{task_id}`
- 学生端接口：
  - `GET /api/question-bank/student/exam-tasks`
  - `GET /api/question-bank/student/exam-tasks/{assignment_id}`
  - `POST /api/question-bank/student/exam-tasks/{assignment_id}/start`
  - `POST /api/question-bank/student/exam-tasks/{assignment_id}/submit`

考试任务学生状态固定为：

- `NOT_STARTED`
- `IN_PROGRESS`
- `SUBMITTED`
- `PENDING_REVIEW`
- `COMPLETED`
- `EXPIRED`

章节练习 / 专项练习 / 主观题批改任务允许配置 `targetQuestionCount`：

- 学生完成进度按 `completedQuestionIds` 去重累计
- 进度字段固定落在 assignment 的正式扩展数据中：
  - `progressCount`
  - `targetQuestionCount`
  - `completedQuestionIds`
  - `pendingReviewQuestionIds`
- 客观题提交后可直接累计进度
- 主观题提交后先累计进度并进入 `PENDING_REVIEW`
- 当 `progressCount >= targetQuestionCount` 且不存在待批改题目时，任务进入 `COMPLETED`

## 6. 导入模板规则

- 正式导入固定使用 `POST /api/question-bank/imports/template`
- 导入预览固定使用 `POST /api/question-bank/imports/template/preview`
- 示例模板固定使用 `GET /api/question-bank/imports/template/example`
- 请求字段固定为 `knowledgeId` + `file`
- 预览确认导入允许额外提交可选 `selectedIndexes`，索引口径固定对应 `preview.items` 的有效题目顺序
- 模板文件仅支持 `txt` / `docx`
- 每题必须包含 `【题干】`、`【答案】`、`【解析】`、`【知识点】`
- 客观题必须包含 `【选项】`
- 多题固定用 `---` 分隔
- `【知识点】` 逗号分隔，最多 3 个，最终写入 `question.extJson.knowledgeTags`
- 预览返回 `items`、`errors`、`validCount`、`invalidCount`
- 预览和导入结果在有错误时返回 `errorLog`、`errorLogFileName`，用于下载失败日志后重试
- `preview.items` 使用最终 `question` 合同字段，保证预览结果与真实落库口径一致
- 前端默认勾选全部有效预览题目，支持逐题勾选、全选、清空后再确认导入

## 7. 题目页交互规则

- 题目弹窗固定绑定 `knowledgeId`、`userId`、`type`、`stem`、`optionsJson`、`answer`、`status`、`extJson`
- `optionsJson` 在前端和后端都按 JSON 数组校验
- `extJson` 在前端和后端都按 JSON 对象校验
- `extJson.difficulty` 仅支持 `easy` / `medium` / `hard`
- `extJson.knowledgeTags` 仅支持 1-3 个标签
- 页面提供 `格式化 optionsJson`、`格式化 extJson` 按钮，但不会引入兼容别名字段
- 导入页提供 `预览校对 -> 逐题勾选 -> 确认导入当前预览` 流程，预览题目可直接载入单题录入弹窗复核
- 详情弹窗固定展示“固定字段 / 状态流转快捷操作 / optionsJson / extJson 摘要 / 审核轨迹”五段结构
- 快捷流转按钮只复用 `POST /api/question-bank/questions/{questionId}/status/{targetStatus}`，不新增并行状态接口
- 顶部筛选区固定支持 `examCategoryCode`、`jointExamGroupCode`、`subjectCode`，与接口参数同名
- 顶部筛选区补充 `keyword`，统一按题干与扩展字段关键字检索
- 教师题目列表固定提供 `全部题目 / 我的题目 / 待我审核` 视图页签，前端按接口返回的 `question.extJson.reviewSummary.latestStatus` 自动分类：
  - `我的题目`：`question.userId == 当前教师 userId`
  - `待我审核`：`latestStatus in {QA_IN_PROGRESS, REVIEW_PENDING}` 且 `question.userId != 当前教师 userId`
- 教师题目列表排序固定为 `updateTime desc -> createTime desc -> id desc`
- 教师筛选区的 `examCategoryCode`、`jointExamGroupCode` 固定使用下拉选择，选项必须来自 `GET /api/question-bank/content/baseline`：
  - `examCategoryCode`：10 个学科门类
  - `jointExamGroupCode`：40 个联考专业组，且按 `examCategoryCode` 联动过滤
- 题目列表状态标签颜色固定为：
  - `DRAFT` 灰色
  - `QA_IN_PROGRESS` 蓝色
  - `REVIEW_PENDING` 橙色
  - `PUBLISHED` 绿色
  - `REJECTED` 红色
- 题目流转按钮固定执行权限：
  - 当 `latestStatus == QA_IN_PROGRESS` 且 `question.userId == 当前教师 userId` 时，“提审”按钮必须置灰，不可执行
  - “通过/驳回”按钮仅在 `role == teacher` 且 `question.userId != 当前教师 userId` 时展示
- 题目编辑与详情固定使用右侧 `Drawer`，禁止整页跳转；抽屉内必须展示 `reviewRecords` 轨迹与审核流水线

## 7.1 审核轨迹扩展

- 审核记录新增 `createTime` 字段，详情弹窗与接口统一可追踪审核时间
- `question.extJson.reviewSummary` 固定维护：
  - `reviewCount`
  - `latestReviewId`
  - `latestStatus`
  - `latestReviewerUserId`
  - `latestReviewedAt`
- 题目详情弹窗右侧固定展示“审核流水线”视图，基于 `reviewRecords + reviewSummary` 渲染状态节点与驳回节点，且驳回节点必须展示审核人、审核时间、驳回原因
- 所有管理页筛选项超过 3 个时，前端自动折叠为 `Advanced Filter`，默认仅展示 `keyword` 输入；其余筛选项需展开后显示
- 所有 `POST` 操作统一通过全局 `Toast` 反馈处理结果，优先展示 `reviewSummary.latestStatus / latestStatus / status`；禁止使用浏览器原生 `alert/confirm/prompt`

## 7.2 页面入口与路由隔离

- 渲染层必须剔除非当前角色的直达入口按钮，避免学生/教师看到超管入口操作按钮
- 页面访问鉴权在 `auth` 层统一执行：当角色访问非本角色页面时，必须 302 重定向到该角色首页，而非继续渲染错误页面

## 8. 页面与接口范围

当前页面与接口仍覆盖：

- 注册登录页
- 题库管理
- 知识点 L1-L5 五级树
- 超管控制台
- 消息中心
- 内容体系字典
- 专属学习台
- 学生端刷题
- 我的题库（错题中心 / 沉淀题库 / 考试大纲）
- 试卷管理
- 学情页

补充说明：

- 当前学生端页面入口语义已统一收口到“我的题库”。
- 历史接口与内部服务中仍保留 `wrong-book / personal-bank` 命名，作为兼容契约继续存在。
- 错题中心列表与汇总统一采用同一套筛选作用域：`subjectCode / chapterCode / pointCode / knowledgeId / knowledgePathNodeId`。
- 错题中心“完成回顾”仅记录复盘行为，不直接推进 `reviewStatusLabel`；`熟悉 / 已斩获` 仍由错后再练结果驱动。
- 错题修复卷需要遵守当前错题中心筛选范围，避免出现“当前筛选”和“实际出卷”口径不一致。
- `student_question_record` 作为错题中心正式热状态表，至少承接 `wrongBookFlag / wrongBookArchivedFlag / wrongBookCollectedAt / wrongBookReviewedAt / wrongBookReviewCount / wrongBookPostWrongAttemptCount / wrongBookPostWrongCorrectCount / wrongBookLastReasonCode` 等高频字段；`extJson.wrongBook` 仅作兼容与回填来源。
- 错题中心页面当前页支持批量勾选与批量打印；题目详情需展示最近答案、累计作答、最近作答耗时、最近错因与错后再练统计，作为前端复盘最小证据集。

knowledge 模块补充接口：

- `POST /api/question-bank/knowledge/{knowledge_id}/sort/{direction}`
- `POST /api/question-bank/knowledge/layout`（教师拖拽知识星系节点后保存布局坐标）

知识星系交互口径：

- 教师端：右键选择前置节点，再右键目标节点，调用 `POST /api/question-bank/knowledge/{knowledge_id}/prerequisites`
- 学生端：`GET /api/question-bank/knowledge/tree` 开放学生读访问，灰色节点（低掌握度）点击后触发弱项强化

超管接口补充口径：

- `GET /api/question-bank/admin/users` 统一返回分页结构 `data.items / data.page / data.size / data.total`
- 查询参数固定为 `page`、`size`、`role`、`keyword`

试卷状态与撤销接口补充：

- 试卷状态流转固定为：
  - `DRAFT -> REVIEW_PENDING`
  - `REVIEW_PENDING -> DRAFT / PUBLISHED`
  - `PUBLISHED -> OFFLINE`
  - `OFFLINE -> REVIEW_PENDING`
- 题目删除返回 `undoSnapshotId`，并支持 `POST /api/question-bank/questions/deleted/{snapshotId}/restore`
- 试卷删除返回 `undoSnapshotId`，并支持 `POST /api/question-bank/papers/deleted/{snapshotId}/restore`
- 撤销快照统一保存在系统记录 `extJson.undoSnapshots`

消息中心补充接口：

- `POST /api/question-bank/messages/read/batch`
- 请求体固定为 `{ "messageIds": ["..."] }`

## 9. 认证与学习约束（第一批）

认证接口固定为：

- `POST /api/question-bank/auth/sms-code`
- `POST /api/question-bank/auth/register`
- `POST /api/question-bank/auth/login/password`
- `POST /api/question-bank/auth/login/sms`
- `POST /api/question-bank/auth/password/reset`
- `POST /api/question-bank/auth/logout`
- `GET /api/question-bank/auth/me`

认证约束：

- 登录接口在响应体返回 `accessToken`，同时下发 `HttpOnly` Cookie：`qbAccessToken`
- 登录接口同步下发可读 Cookie：`qbCsrfToken`，用于超管写接口 CSRF 双提交校验
- 认证优先读取 `Authorization: Bearer <token>`，缺省时回退读取 `qbAccessToken` Cookie
- `POST /api/question-bank/admin/*` 在 Cookie 会话下必须携带 `X-CSRF-Token` 且与 `qbCsrfToken` 一致
- Cookie 安全策略按环境收口：生产默认 `Secure=true` 且 `SameSite=Strict`（可通过环境变量覆盖）
- 令牌失效后访问受保护接口返回 `QUESTION_FORBIDDEN`
- `super_admin` 角色访问（含 `/api/question-bank/admin/*`）仅允许基于登录态 Token（Bearer 或 Cookie）
- 未登录访问 `/admin/home`、`/admin/control-center`、`/admin/syllabus` 固定 302 跳转 `/login`
- 三角色门户中的超管入口统一先跳转 `/login`，不再提供 query 直达超管页
- 手机号、密码强度、短信验证码用途统一由后端模型校验
- 密码登录按手机号与 IP 做失败限流，触发阈值后锁定 10 分钟

章节闯关约束：

- 学生练习题列表仅返回已解锁章节题目
- 非首章节要求上一章节正确率 `>= 0.8` 才解锁
- 未解锁章节提交返回 `QUESTION_VALIDATION_FAILED`

计时约束：

- 练习提交超过 `question.extJson.practiceConfig.timeLimitSec` 即判错
- 超时结果写回 `studentState.chapterPractice.isTimeout=true`
- 学生端模拟卷页面展示倒计时，时间归零自动交卷

## 10. 章节树与模拟任务（第二批）

章节树状态接口：

- `GET /api/question-bank/student/practice/chapters`

章节树状态口径：

- 返回章节列表时携带 `answered`、`total`、`accuracy`、`isUnlocked`、`isCurrent`、`statusLabel`
- `statusLabel` 仅允许 `未解锁`、`已解锁`、`正在闯关`
- 学生端章节树需展示章节状态与正确率，未解锁章节不可进入作答

模拟交卷口径：

- 未作答题目按答错处理（计入 `wrongQuestionIds`）
- 客观题即时判分，主观题提交后生成 `AI_MARKING` 任务异步批改
- 交卷响应额外返回 `pendingSubjectiveTaskIds` 与 `pendingSubjectiveCount`
- 学生作答记录 `simulationAttempts` 持续保留 `isPendingAiMarking` 与 `aiMarkingTaskId`
- 同一学生同一试卷当日重复提交按幂等返回，不重复生成成绩记录
- 同一学生同一科目每日最多完成 1 次全真模拟考试
- 新增报告查询接口 `GET /api/question-bank/student/papers/reports`，用于回看历史模拟报告
- 新增报告详情接口 `GET /api/question-bank/student/papers/reports/{reportId}`，用于回看单次模拟详情
- 报告记录固定包含 `reportId`，同一试卷不同日期成绩保留历史，不覆盖旧记录
- 报告列表每条记录补充 `subjectiveMarking` 汇总：
  - `total`、`pendingCount`、`queuedCount`、`runningCount`
  - `completedCount`、`failedCount`、`cancelledCount`
  - `averageScore`、`latestCompletedAt`
- 报告详情固定补充：
  - `typeAccuracy`
  - `questionResults`
  - `summary`

模拟考试交互约束：

- 模拟考试入口改为“点击开始考试后即时组卷”，未点击开始前不得生成正式试卷
- 新增开始接口 `POST /api/question-bank/student/mock-exams/start`
- 新增会话详情接口 `GET /api/question-bank/student/mock-exams/{session_id}`
- 开始接口成功后固定返回 `sessionId/id`、`paperId`、`paperName`、`questionCount`、`totalScore`、`durationMinutes`
- 同一学生同一科目存在未提交 `ACTIVE` 会话时，重复点击开始按幂等返回同一会话
- 即时组卷固定按官方大纲/知识树权重选题；题库不足时允许降级补邻近考点和重复旧题，并在会话中保留降级摘要
- 组卷规则优先按 `systemSettings.mockExamRuleProfiles[subjectCode]` 读取；未命中时回退到总分档默认规则
- 规则配置最少包含：
  - `durationMinutes`
  - `typeRules`
  - `difficultyRatio`
- 支持暂停/恢复，单场最多暂停 3 次
- 每次暂停上限 10 分钟，超时自动恢复考试
- 模拟答题过程实时写入本地草稿，异常关闭后可自动恢复未交卷进度

## 11. 学生转化闭环（第5批）

学生端转化链路固定为：

- `登录 -> 快诊 -> 结果 -> 兑换/模拟支付 -> 权益生效 -> 今日任务`

学生转化接口固定为：

- `GET /api/question-bank/student/subscription/status`
- `GET /api/question-bank/student/subscription/plans`
- `POST /api/question-bank/student/subscription/redeem`
- `POST /api/question-bank/student/subscription/mock-orders`
- `POST /api/question-bank/student/subscription/mock-orders/{orderId}/confirm`
- `POST /api/question-bank/student/diagnosis/quick/start`
- `POST /api/question-bank/student/diagnosis/quick/{sessionId}/submit`

学生首页与仪表盘字段补充口径：

- `GET /api/question-bank/student/dashboard` 的 `data` 固定新增 `onboarding`：
  - `completed`：`boolean`，是否完成首登转化闭环关键动作
  - `completionSource`：`NONE | QUICK_DIAGNOSIS | SUBSCRIPTION`
  - `quickDiagnosisCompleted`：`boolean`
  - `subscriptionActive`：`boolean`
  - `latestQuickDiagnosisSession`：`{ sessionId, status, submittedAt, answeredCount, correctCount, accuracy }`
- `data.studentState` 固定补充 `onboardingCompleted`（布尔值），用于页面快速判定。

快诊会话与状态口径：

- 快诊会话状态固定：
  - `STARTED`
  - `COMPLETED`
- `submit` 接口重复提交按幂等返回，不重复写事件日志与积分侧状态。

订阅与兑换口径：

- 订阅状态固定：
  - `INACTIVE`
  - `ACTIVE`
  - `EXPIRED`
- 兑换码规则固定：
  - 一码一次
  - 一账号一次（拉新体验码）
  - 过期不可用
- 模拟支付确认接口固定做幂等，重复确认不得重复发放权益。

前端路由与页面口径：

- 学生首登分流固定优先依据后端 `dashboard.onboarding.completed` 判定；
- 本地 `qbStudentOnboardingCompleted` 仅作兜底缓存，不作为最终真相源；
- 首页必须展示权益态入口（已开通 / 待开通 / 待快诊）并提供对应 CTA。
