# 数据库索引上线说明（2026-03-20）

## 文档信息

- 文档类型：发布配套说明
- 适用版本：2026-03-20 发布批次
- 适用环境：测试 / 生产
- 关联文件：[schema.sql](/Users/shaotongli/Documents/newaitiku/data/schema.sql)
- 责任角色：研发、运维、测试

## 一、目标

- 说明 `data/schema.sql` 中索引相关变更的上线策略，避免“索引存在但上线方式不明确”。

## 二、适用范围

- 文件：[schema.sql](/Users/shaotongli/Documents/newaitiku/data/schema.sql)
- 影响对象：
  - `user`
  - `userAuth`
  - `knowledge`
  - `question`
  - `task`

## 三、当前结论

- 当前 `schema.sql` 已移除破坏性 `DROP TABLE`。
- 本次剩余的数据库上线风险，主要在“索引构建如何执行”缺少正式说明。

### 本地验证结果

- 已在临时 SQLite 数据库中成功执行 `schema.sql`。
- 已成功创建以下业务索引：
  - `idx_user_status`
  - `idx_userauth_user_type`
  - `idx_knowledge_parent_sort`
  - `idx_question_knowledge_status`
  - `idx_question_owner_status`
  - `idx_question_policy`
  - `idx_question_joint_group`
  - `idx_question_subject`
  - `idx_task_user_status`
- 当前结论：
  - 技术上可在空库完成初始化
  - 生产是否允许执行，仍需 DBA / 运维确认执行窗口、备份和回滚策略

## 四、索引清单

1. `idx_user_status`
2. `idx_userauth_user_type`
3. `idx_knowledge_parent_sort`
4. `idx_question_knowledge_status`
5. `idx_question_owner_status`
6. `idx_question_policy`
7. `idx_question_joint_group`
8. `idx_question_subject`
9. `idx_task_user_status`

## 五、上线策略

### 1. 环境要求

- 仅允许在测试环境与生产变更窗口中执行。
- 禁止在业务高峰期执行。
- 执行前必须先备份数据库文件。

### 2. 执行顺序

1. 备份当前数据库。
2. 在测试环境先执行一次并验证启动与查询。
3. 生产环境执行前确认无破坏性 DDL。
4. 生产执行完成后验证：
   - 应用可正常启动
   - 题库列表可正常分页
   - 登录、题目查询、组卷、任务查询可正常访问

### 3. 执行前勾选项

- [ ] 已确认当前分支为发布分支，非 `main/master`
- [ ] 已备份当前数据库
- [ ] 已确认本次不执行任何破坏性删表
- [x] 已在本地临时库完成一次初始化验证
- [ ] 已在测试环境完成一次验证
- [ ] 已明确执行窗口与回滚负责人
- [ ] DBA 已确认允许执行
- [ ] 运维已确认执行与回滚方案

### 4. 回滚策略

- 索引新增失败：
  - 立即停止继续执行
  - 回滚到备份数据库
- 应用启动失败或查询异常：
  - 恢复数据库备份
  - 回滚应用版本

## 六、验收项

1. 应用启动正常
2. `question` 查询正常
3. `knowledge` 树加载正常
4. 登录、题库管理、组卷、学生练习路径可访问

## 七、责任归属

- 研发：确认索引语义和查询路径
- 运维：安排执行窗口、备份、回滚
- 测试：执行上线后关键路径验证

## 八、签收

- 研发确认：__________
- DBA 确认：__________
- 运维确认：__________
- 测试确认：__________
- 发布时间：__________
