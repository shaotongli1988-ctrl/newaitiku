# 学习方法模块 PR 最终文案（可直接复制）

```markdown
## 背景
本次变更用于收敛学习方法模块在提测前的契约一致性问题，重点修复 API schema drift 并补齐发布证据。

## 主要改动
- 后端：`app/service_modules/learning_method.py`
  - 增加学习进度状态流守卫（`allowedTransitions/canTransition`）
  - 增加 `traceId` 与 `metricSnapshot` 上下文字段，补齐可观测性证据
- 前端契约：`frontend/src/api/contracts.ts`
  - `AiMarkingSubmitModel` 新增 `assignment_id/assignmentId`
  - 新增学习方法请求模型：
    - `LearningMethodPracticeStartRequest`
    - `LearningMethodPracticeCompleteRequest`
    - `LearningMethodAdminSaveRequest`
    - `LearningMethodAdminUpdateRequest`
    - `LearningMethodAdminSortRequest`
- 文档：补齐发布/配置/回滚/提测交接文档

## 验证结果
- API schema drift：`none`
- OpenAPI 范围测试：`2 passed`
- 集成测试：`46 passed`
- 十域验收门禁：`120/120 checks passed`
- 交付守卫：`可上线（ACCEPTABLE_TO_RELEASE）`

## 风险与回滚
- 当前阻断项：无
- 回滚入口：`docs/release/learning-method-rollback-switch-2026-03-25.md`
- 异常触发：学习方法核心接口持续 5xx 或状态异常

## 关联文档
- `docs/release/learning-method-test-handoff-2026-03-25.md`
- `docs/release/learning-method-ops-release-brief-2026-03-25.md`
- `docs/release/delivery-guard-2026-03-25-final.md`
```
