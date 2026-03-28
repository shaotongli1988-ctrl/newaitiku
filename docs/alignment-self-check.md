# 对齐自检记录

日期：2026-03-17

## 七项检查结果

1. 请求边界
   - 本轮仅继续收紧 `question` 模块体验层，新增“导入预览逐题勾选导入”和“结构化详情弹窗状态快捷流转”
   - 未新增业务表、兼容列、别名字段

2. 数据库字段 ↔ 固定合同
   - `questions` 固定字段保持 `id`, `knowledgeId`, `userId`, `type`, `stem`, `optionsJson`, `answer`, `status`, `extJson`, `createTime`, `updateTime`
   - 导入预览不落库，只复用现有 `question` 合同做预演
   - 正式导入仅增加可选 `selectedIndexes`，未扩张 `question` 顶层字段
   - 审核轨迹、学生做题态、向量状态仍分别落在 `question_reviews`、`student_question_bank`、`question_vectors`

3. 数据库字段 ↔ 后端字段 ↔ API 字段
   - 新增 `POST /api/question-bank/imports/template/preview`
   - `POST /api/question-bank/imports/template` 正式接收可选 `selectedIndexes`，该字段已纳入当前导入合同，不引入别名参数或双轨入参
   - 详情弹窗快捷动作继续复用 `POST /api/question-bank/questions/{questionId}/status/{targetStatus}`
   - 预览响应使用统一 `{ code, message, data }`
   - `preview.items` 直接返回最终 `question` 合同字段，保证预览结果与实际落库一致

4. API 字段 ↔ 前端字段 ↔ 页面渲染
   - 题目弹窗继续只绑定合同字段，不新增派生字段
   - 导入页新增 `预览校对 -> 逐题勾选 / 全选 / 清空 -> 确认导入当前预览` 流程
   - 详情弹窗改为“固定字段 / 状态流转快捷操作 / optionsJson / extJson 摘要 / 审核轨迹”五段结构化展示

5. 扩展数据 ↔ `extJson`
   - 题目扩展信息继续只保留在 `questions.extJson`
   - 模板原文继续写入 `questions.extJson.rawTemplate`
   - 预览和详情摘要仅消费已有 `extJson` 数据，不发明新持久字段
   - 状态流转说明仍只写回既有 `extJson.reviewRemark`

6. 关系 ↔ ID-only
   - 题目与知识点继续仅通过 `knowledgeId` 关联
   - 审核、学生记录、任务继续仅通过 `questionId`、`studentUserId`、`userId` 关联
   - 未引入嵌套表结构和跨表冗余字段

7. 响应包裹 ↔ 测试
   - 新增统一测试分层：`unit`、`integration`、`regression`、`e2e`
   - 新增 `tools/python/test_suite_runner.py` 统一编排四类测试，并支持按变更路径自动选套件
   - 新增 watcher 对新增文件、修改文件、删除文件的自动触发校验
   - 新增测试覆盖模板预览接口、逐题勾选导入、越界勾选拦截、页面预览入口、结构化详情弹窗、教师发布到学生作答的完整链路
   - 现有试卷、学情、AI 任务、学生成长链路回归通过

## 自测命令

```bash
python3 scripts/unified_delivery_guard.py --phase start --task "继续往生产态推，直接做导入预览里的逐题勾选导入和详情弹窗里的状态流转快捷操作"
python3 scripts/unified_delivery_guard.py --phase batch
python3 scripts/unified_delivery_guard_scoped.py --phase batch
./tools/bin/check-alignment.sh
./tools/bin/run-unit-tests.sh
./tools/bin/run-integration-tests.sh
./tools/bin/run-regression-tests.sh
./tools/bin/run-e2e-tests.sh
./.venv/bin/python -m pytest tests/test_question_bank.py -q
./.venv/bin/python -m py_compile app/*.py
python3 scripts/unified_delivery_guard.py --phase final
python3 scripts/unified_delivery_guard_scoped.py --phase final
```

## 自测结果

- 统一守卫与四类测试套件全通过（以最新命令输出为准，不在文档固化通过数量）。
