# 核心业务组件化与 AI 交互沉浸化改造说明

## 本次范围

- 路由分区：`/teacher` 与 `/student`
- 前端目录：`frontend/src`
- 组件新增：
  - `components/core/QuestionCard.vue`
  - `components/core/KnowledgeTree.vue`
  - `components/core/AIAssistant.vue`
  - `components/core/AnalyticsCharts.vue`

## 统一契约对齐

- 题目模块：继续使用 `question` 固定字段（`id/knowledgeId/userId/type/stem/optionsJson/answer/status/extJson/createTime/updateTime`）。
- 知识点模块：继续使用 `knowledge` 固定字段（`id/parentId/name/sort/status/extJson/createTime/updateTime`）。
- 任务模块：继续使用 `task` 固定字段（`id/userId/type/status/progress/extJson/createTime/updateTime`）。
- API 响应：前端统一从 `{ code, message, data }` 中读取 `data`，分页接口读取 `data.items/page/size/total`。

## 组件能力

## 1) QuestionCard

- 全题型渲染：单选、多选、判断、主观题统一在卡片中渲染。
- 审核状态标签：根据 `status` 输出统一标签与颜色。
- 提审显隐逻辑：当 `status=QA_IN_PROGRESS` 且 `question.userId===currentUserId` 时，自动隐藏“提审”按钮。
- 抽屉查看审核轨迹：点击卡片打开右侧抽屉，加载 `GET /api/question-bank/questions/{id}/reviews`。

## 2) KnowledgeTree

- 基于 `el-tree-v2` 虚拟树渲染海量节点。
- 支持关键词过滤（ID/名称）。
- 支持拖拽排序：拖拽后将位移转换为 `up/down` 多次调用，落到 `POST /api/question-bank/knowledge/{id}/sort/{direction}`。
- 与题目列表双向联动：选中节点更新 `knowledgeId` 筛选，外部可回写当前选中节点。

## 3) AIAssistant

- 学生端从固定表单改为悬浮对话球（FAB）。
- 打开后展示对话区 + AI 任务队列。
- 支持两类异步任务：
  - `AI_TUTOR`: `POST /api/question-bank/student/practice/questions/{id}/ai-tutor`
  - `AI_MARKING`: `POST /api/question-bank/student/practice/questions/{id}/ai-marking`
- 任务可视化：轮询 `GET /api/question-bank/tasks`，实时展示 `status/progress/resultSummary`，避免刷新页面。

## 4) AnalyticsCharts

- 引入 ECharts。
- 教师端图表：
  - 知识点覆盖率雷达图（基于 `weakKnowledgeTags` 推导覆盖得分）
  - 风险学生分布散点图（基于 `studentRankings + lowActivityStudents`）
- 数据来源：`GET /api/question-bank/analytics/summary`。

## 表单字典化改造

- 教师端与学生端筛选表单移除手工输入 `subjectCode` / `subjectId` / `chapter`。
- 全部改为 `el-select` 下拉来源：
  - 教师端：`GET /api/question-bank/content/baseline`
  - 学生端：`GET /api/question-bank/student/dashboard`（其 `availableExamCategories/coreSubjects/chapterPracticeTree` 均基于 content baseline 同步）

## 请求头统一

- 在 `frontend/src/api/request.js` 中统一注入：
  - `X-Role`
  - `X-User-Id`
- 来源于本地缓存键：`qbUserRole`、`qbUserId`。

## 验证记录

- `npm run build` 通过。
- `python3 scripts/unified_delivery_guard.py --phase batch` 通过。
