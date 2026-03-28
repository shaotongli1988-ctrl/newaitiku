# 接口与权限映射（落地版）

## 1. 学生学习台 Dashboard（轻量返回）

接口：`GET /api/question-bank/student/dashboard`

统一响应壳：`{ code, message, data }`

`data` 字段：

- `policyVersionCode`
- `examCategoryCode`
- `jointExamGroupCode`
- `examCategoryName`
- `jointExamGroupName`
- `availableExamCategories`
- `coreSubjects`
- `points`
- `title`
- `streakDays`
- `dailyTasks`
- `aiQuota`
- `recentPointsLedger`
- `unlockedTitles`
- `personalBankCount`
- `messageUnreadCount`
- `studentState`
- `chapterPracticeTree`

### 轻量化约束

- `availableExamCategories` 仅返回学习台下拉框必需字段：
  - `examCategoryCode`
  - `examCategoryName`
  - `sortNo`
  - `jointExamGroups`（每项仅 `jointExamGroupCode`、`jointExamGroupName`）
- `availableJointExamGroups` 仅返回当前 `examCategoryCode` 下合法联考专业组子集：
  - `jointExamGroupCode`
  - `jointExamGroupName`
  - `examCategoryCode`
- `aiQuota` 仅返回页面渲染必需字段：
  - `dailyLimit`
  - `usedCount`
- 不再返回页面未消费的冗余字段（例如顶层 `checkInDates`、`aiQuota.quotaDate`）。
- 不再在 `dashboard` 中重复返回每个大类下完整 `subjects/professionalSubjects/score/majorListText` 深层结构，避免首页 payload 过大。

## 2. 权限点与页面/按钮映射

### 2.1 角色可配置权限

- `super_admin`：`student:manage`、`settings:manage`
- `teacher`：`question:manage`、`paper:manage`、`analytics:view`、`message:send`

### 2.2 页面与接口权限

- `question:manage`
  - 页面：`/teacher/questions`、`/teacher/knowledge`
  - API：`/api/question-bank/questions*`、`/api/question-bank/knowledge*`、题目导入相关接口
- `paper:manage`
  - 页面：`/teacher/papers`、`/teacher/content-system`
  - API：`/api/question-bank/papers*`、`/api/question-bank/content/baseline`
- `analytics:view`
  - 页面：`/teacher/analytics`
  - API：`/api/question-bank/analytics*`
- `student:manage`
  - API：`/api/question-bank/admin/users`、`/api/question-bank/admin/students/import`、`/api/question-bank/admin/students/export`
- `settings:manage`
  - 页面：`/admin/control-center`
  - API：`/api/question-bank/admin/console`、`/api/question-bank/admin/settings`
- `message:send`
  - API：`/api/question-bank/messages/send`、`/api/question-bank/messages/send-history*`

### 2.3 前端显隐规则（新增）

- 新增通用 Vue 指令：`v-permission`
  - 字符串写法：`v-permission="'question:manage'"`
  - 组合写法：`v-permission="{ anyOf: ['settings:manage', 'student:manage'] }"`
  - 初始化时通过 `/api/question-bank/auth/me` 同步当前账号 `permissions`
  - 无权限元素不渲染或自动隐藏
- 已接入范围：
  - 教师端各工作台左侧菜单（题库/知识点/内容体系/试卷/学情）
  - 消息中心教师端“发送提醒”“发送历史”区块
  - 超管控制台中“系统设置”“学生管理相关区块”的权限显隐标记

## 3. 设计原则

- 页面入口和 API 必须双重校验（后端为准）。
- 前端显隐只做体验优化，不替代后端鉴权。
- 首页聚合接口只返回“当前页真的会渲染”的字段，重型字典走独立接口。
