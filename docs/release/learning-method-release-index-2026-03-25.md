# 学习方法模块发布包索引（2026-03-25）

## 一句话结论
- 当前状态：可提测，可上线。
- 门禁状态：开发后总守卫无阻断；十域验收 120/120 通过。

## 推荐阅读顺序
1. 提测交接：`docs/release/learning-method-test-handoff-2026-03-25.md`
2. 运维发布说明：`docs/release/learning-method-ops-release-brief-2026-03-25.md`
3. 发布证据：`docs/release/learning-method-release-evidence-2026-03-25.md`
4. 配置核对：`docs/release/learning-method-config-checklist-2026-03-25.md`
5. 回滚止血：`docs/release/learning-method-rollback-switch-2026-03-25.md`
6. 终检报告：`docs/release/delivery-guard-2026-03-25-final.md`

## 核心验证结果
- API schema drift：none
- OpenAPI 范围测试：2 passed
- 集成测试：46 passed
- 十域验收：120/120 checks passed
- 开发后总守卫：可上线（ACCEPTABLE_TO_RELEASE）

## 发布关注接口
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

## 回滚入口
- 文档：`docs/release/learning-method-rollback-switch-2026-03-25.md`
- 触发条件：学习方法核心接口出现持续 5xx 或状态异常。

## 发布群材料
- 群公告模板：`docs/release/learning-method-group-message-template-2026-03-25.md`
- PR 最终文案：`docs/release/learning-method-pr-final-copy-2026-03-25.md`
