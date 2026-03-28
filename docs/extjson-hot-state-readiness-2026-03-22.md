# extJson 热状态治理现状（2026-03-22）

## 1. 当前结论

- 三阶段定位：本文当前作为“开发中已落地结果 + 剩余治理边界”说明使用。
- 主业务路径已完成收口：`studentRecords`、`paperReports`、`messageSendHistory` 不再作为正式业务热状态保存在 `user/system extJson` 根级。
- 当前仓库默认执行规则是：
  - 低频扩展数据进入 `extJson`
  - 高频状态、报告型数据、并发写状态、需要唯一约束的数据进入正式业务表

统一合同以 [question-bank-contract.md](/Users/shaotongli/Documents/newaitiku/docs/question-bank-contract.md) 为准。

## 2. 已完成状态

当前正式表承接关系如下：

- `student_question_record`
  - 承接学生题目学习热状态
  - 主业务路径已按 `studentUserId + questionId` 读取与写入
- `paper_report`
  - 承接学生交卷报告
  - 报告列表、详情、AI 批改联动已走正式表
- `message_send_history`
  - 承接消息发送历史
  - 发送历史分页、撤回校验、发送落账已走正式表

当前 `user/system extJson` 已不再作为以下数据的正式存储位置：

- `studentRecords`
- `paperReports`
- `messageSendHistory`

系统保存状态时会主动剔除 `paperReports`、`messageSendHistory`，避免旧热状态重新落回系统记录。

## 3. extJson 当前允许范围

### 3.1 允许进入 `extJson`

- 低频扩展字段
- 不参与分页、筛选、聚合、唯一约束、并发控制的补充明细
- 需要保留原始上下文、展示摘要、附加说明，但不作为主查询键的结构化补充

### 3.2 不允许继续进入 `extJson`

- 高频业务状态
- 报告型主数据
- 需要并发写安全的状态
- 需要唯一约束的数据
- 需要分页、统计、筛选的数据

## 4. 各表 extJson 边界

### 4.1 `question.extJson`

继续承接题目扩展元数据，例如：

- `subjectId`, `chapter`, `difficulty`, `analysis`, `knowledgeTags`
- `policyVersionCode`, `examCategoryCode`, `jointExamGroupCode`, `subjectCode`, `subjectType`, `moduleCode`, `sourceType`, `applicableGroups`
- `paperBindings`, `practiceConfig`, `reviewRecords`, `reviewSummary`

这部分仍是主合同允许的扩展区。

### 4.2 `user.extJson`

普通用户继续承接：

- `role`
- `name`
- `permissions`
- `examCategoryCode`
- `jointExamGroupCode`
- `vocationalMajor`
- `prepStage`

系统用户继续承接低频系统扩展：

- `systemSettings`
- `messages`
- `messageSettingsByUser`
- `paperTemplates`
- `undoSnapshots`

### 4.3 `student_question_record.extJson`

允许承接：

- `chapterPractice` 展示补充字段
- 最近一次答题原始 payload
- `aiMarking` 摘要
- `aiTutor` 非检索型上下文
- `studentProfile` 的题目态局部快照（如业务确有展示需要）

不允许把可查询主字段重新塞回 `extJson` 代替正式列。

### 4.4 `paper_report.extJson`

允许承接：

- `typeAccuracy`
- `wrongQuestionIds`
- `pendingSubjectiveTaskIds`
- `reportDetail`

主查询字段仍以正式列为准：`reportId`、`studentUserId`、`paperId`、`subjectId`、`submittedAt`、`score` 等。

### 4.5 `message_send_history.extJson`

允许承接：

- `targetUserIds`
- 筛选快照
- 发送结果摘要
- 失败明细

主查询字段仍以正式列为准：`traceId`、`senderUserId`、`targetCount`、`sentCount`、`status`、`sendAt` 等。

## 5. 仍保留的 legacy 能力

当前仓库仍保留一项明确的离线 legacy 能力：

- [scripts/extjson_hot_state_backfill.py](/Users/shaotongli/Documents/newaitiku/scripts/extjson_hot_state_backfill.py)

用途限定为：

- 审计历史 legacy 快照与正式表是否一致
- 在需要处理历史旧库或旧快照时，执行一次性离线导入

它不是常规运行路径，也不应被当成主业务依赖。

## 6. 与历史方案的关系

2026-03-22 当天的原始目标包括：

- 建表
- 切读
- 回填
- 下线 legacy 依赖

目前这些目标在主业务路径上已经完成，本文不再把仓库描述为“仍处于双写 / 切读阶段”。

如果后续需要处理历史旧库，只能走离线迁移工具，不允许重新把双写、兼容读、系统态 JSON 热状态带回常规实现。

## 7. 剩余治理项

以下内容仍可继续收敛，但不影响“主链路已完成收口”这一事实：

- 文档中仍引用旧迁移背景的表述
- 守卫脚本中针对旧写法的检测说明
- 离线 backfill 工具的长期保留策略

## 8. 当前判断

- `extJson` 仍然是项目里的重要扩展容器，但已经被限制在“低频扩展 / 补充明细”边界内使用。
- 以 `studentRecords`、`paperReports`、`messageSendHistory` 为代表的热状态，当前不应再被视为 `extJson` 的合法承载范围。
- 如果未来再次出现“先写进 extJson，后面再拆”的方案，应直接视为偏离当前治理基线。
