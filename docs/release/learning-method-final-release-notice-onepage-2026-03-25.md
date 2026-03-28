# 学习方法模块最终发布通知单页（2026-03-25）

## 发布结论
- 状态：可提测，可上线。
- 当前门禁：
  - API schema drift：none
  - 集成测试：46 passed
  - OpenAPI 范围：2 passed
  - 十域验收：120/120 passed
  - Delivery Guard：ACCEPTABLE_TO_RELEASE

## @角色确认清单
- `@产品`：确认提测范围与验收口径
- `@测试`：确认提测执行窗口与回归排期
- `@研发`：确认变更冻结、值班响应人
- `@运维`：确认发布窗口、观察与回滚执行人

## 发布批次信息
- 模块：学习方法（learning_method）
- 批次：2026-03-25
- 计划提测时间：____
- 计划发布时间：____
- 值班群：____

## 影响接口
- 学生端：
  - `GET /api/question-bank/learning-methods`
  - `GET /api/question-bank/learning-methods/{method_code}`
  - `POST /api/question-bank/learning-methods/{method_code}/start`
  - `POST /api/question-bank/learning-methods/{method_code}/complete`
- 管理端：
  - `GET /api/question-bank/admin/learning-methods`
  - `POST /api/question-bank/admin/learning-methods`
  - `PUT /api/question-bank/admin/learning-methods/{method_code}`
  - `POST /api/question-bank/admin/learning-methods/sort`

## 发布窗口动作
1. 提测开始前：
   - 确认 `docs/release/learning-method-test-handoff-2026-03-25.md`
2. 发布开始前：
   - 确认 `docs/release/learning-method-ops-release-brief-2026-03-25.md`
3. 发布后 30 分钟：
   - 观察学习方法核心接口错误率、耗时和状态流异常

## 回滚与止血
- 回滚文档：`docs/release/learning-method-rollback-switch-2026-03-25.md`
- 触发条件：学习方法核心接口持续 5xx 或状态流异常。
- 止血策略：按回滚文档先关闭写入口，再执行版本回退。

## 附件索引
- 发布包索引：`docs/release/learning-method-release-index-2026-03-25.md`
- 提测交接：`docs/release/learning-method-test-handoff-2026-03-25.md`
- 运维发布说明：`docs/release/learning-method-ops-release-brief-2026-03-25.md`
- 企业群公告（Markdown）：`docs/release/learning-method-enterprise-announcement-2026-03-25.md`
- PR 最终文案：`docs/release/learning-method-pr-final-copy-2026-03-25.md`
