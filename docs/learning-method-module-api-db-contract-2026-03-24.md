# 学习方法模块 API / DB 合同草案（V1）

## 1. 路由结论与阶段

- 三阶段路由：开发前（`readiness`）。
- 当前产物目标：把内容方案转换为可实现合同，供开发阶段直接落地。

## 2. 设计原则

- 学习方法主数据属于稳定配置，使用正式表存储，不放 `extJson`。
- 学生学习方法进度属于高频状态，使用正式表存储，不放 `extJson`。
- `extJson` 仅用于低频扩展字段，不承载核心检索与统计条件。
- API 响应保持题库统一包结构：`{ code, message, data }`。

## 3. 数据模型（建议新增两张表）

### 3.1 `learning_method`

用途：存储方法主数据（管理端维护，学生端读取）。

建议字段：
- `id` TEXT PRIMARY KEY
- `methodCode` TEXT NOT NULL UNIQUE
- `methodName` TEXT NOT NULL
- `oneLineIntro` TEXT NOT NULL
- `useWhenJson` TEXT NOT NULL DEFAULT '[]'
- `stepsJson` TEXT NOT NULL DEFAULT '[]'
- `commonMistakesJson` TEXT NOT NULL DEFAULT '[]'
- `questionBankActionsJson` TEXT NOT NULL DEFAULT '[]'
- `starterTask` TEXT NOT NULL DEFAULT ''
- `difficultyLevel` TEXT NOT NULL DEFAULT 'L1'
- `estimatedMinutes` INTEGER NOT NULL DEFAULT 15
- `sort` INTEGER NOT NULL DEFAULT 0
- `status` TEXT NOT NULL DEFAULT 'ACTIVE'
- `extJson` TEXT NOT NULL DEFAULT '{}'
- `createTime` TEXT NOT NULL
- `updateTime` TEXT NOT NULL

建议索引：
- `idx_learning_method_status_sort(status, sort)`

### 3.2 `student_learning_method_progress`

用途：记录学生对学习方法的练习与完成状态。

建议字段：
- `id` TEXT PRIMARY KEY
- `studentUserId` TEXT NOT NULL
- `methodCode` TEXT NOT NULL
- `startCount` INTEGER NOT NULL DEFAULT 0
- `completeCount` INTEGER NOT NULL DEFAULT 0
- `lastPracticedAt` TEXT NOT NULL DEFAULT ''
- `lastAccuracy` REAL NOT NULL DEFAULT 0
- `lastReviewSummary` TEXT NOT NULL DEFAULT ''
- `status` TEXT NOT NULL DEFAULT 'NOT_STARTED'
- `extJson` TEXT NOT NULL DEFAULT '{}'
- `createTime` TEXT NOT NULL
- `updateTime` TEXT NOT NULL

约束与索引：
- `UNIQUE(studentUserId, methodCode)`
- `FOREIGN KEY(studentUserId) REFERENCES "user"(id) ON DELETE CASCADE`
- 建议索引：`idx_student_learning_method_progress_user_status(studentUserId, status, updateTime)`

## 4. API 草案（学生端）

### 4.1 获取学习方法列表

- `GET /api/question-bank/learning-methods`
- 入参：
  - `status`（可选，默认 `ACTIVE`）
- 出参 `data`：
  - `items`: `[{ methodCode, methodName, oneLineIntro, difficultyLevel, estimatedMinutes, sort }]`

### 4.2 获取学习方法详情

- `GET /api/question-bank/learning-methods/{method_code}`
- 出参 `data`：
  - `method`: 完整方法卡字段
  - `progress`: 当前用户进度（未开始时返回默认结构）

### 4.3 开始一次方法练习

- `POST /api/question-bank/learning-methods/{method_code}/start`
- 入参：
  - `practiceStrategy`（可选，如 `INTERLEAVE`, `WRONG_BOOK_RETRY`）
- 出参 `data`：
  - `sessionId`
  - `recommendedQuestionPack`

### 4.4 提交一次方法练习结果

- `POST /api/question-bank/learning-methods/{method_code}/complete`
- 入参：
  - `sessionId`
  - `accuracy`
  - `reviewSummary`
  - `durationSec`
- 出参 `data`：
  - `updatedProgress`

## 5. API 草案（管理端）

### 5.1 学习方法列表（管理）

- `GET /api/question-bank/admin/learning-methods`

### 5.2 新增学习方法

- `POST /api/question-bank/admin/learning-methods`

### 5.3 编辑学习方法

- `PUT /api/question-bank/admin/learning-methods/{method_code}`

### 5.4 学习方法排序

- `POST /api/question-bank/admin/learning-methods/sort`

## 6. 首版验收补充（技术口径）

- 列表接口返回顺序与 `sort` 一致，默认只展示 `ACTIVE`。
- 详情接口必须携带当前用户 `progress`，前端无需二次拼装。
- `start` 和 `complete` 操作后，`student_learning_method_progress` 可被正确更新且幂等。
- 统计字段（开始次数、完成次数、最近正确率）可直接用于后续学情页面，不依赖 `extJson` 二次解析。

## 7. 与现有题库合同的对齐要求

- 不修改既有题库固定响应包结构。
- 不在 `question.extJson`、`knowledge.extJson` 塞入学习方法高频状态。
- 学习方法模块可与错题中心、沉淀题库联动，但联动数据通过正式字段或独立表读取。

## 8. 实施顺序建议

1. 先导入 `data/learning_method_seed_v1.json` 到 `learning_method`。
   - 命令：`python3 scripts/import_learning_method_seed.py`
2. 完成学生端 4 个接口（列表、详情、开始、完成）。
3. 完成管理端 4 个接口（增删改查 + 排序）。
4. 前端接入“学习方法”页卡片列表与详情页，最后打通“开始练习”跳题库链路。
