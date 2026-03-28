# PR 描述（学习方法模块收口）

## 背景
本次变更用于收敛学习方法模块在提测前的契约一致性问题，重点修复 API schema drift 并补齐发布证据。

## 主要改动
- 后端：`app/service_modules/learning_method.py`
  - 增加学习进度状态流守卫（`allowedTransitions/canTransition`）
  - 增加 `traceId` 与 `metricSnapshot` 上下文字段，提升可观测性证据
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
- `python3 /Users/shaotongli/.codex/skills/api-schema-drift-checker/scripts/schema_drift_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku ...`
  - 结果：`Drift issues: none`
- `python3 -m pytest -q tests/test_openapi_schema_scope.py`
  - 结果：`2 passed`
- `./tools/bin/run-tests.sh --suite integration`
  - 结果：`46 passed`
- `./tools/bin/run-acceptance.sh`
  - 结果：`120/120 checks passed`
- 交付守卫：`docs/release/delivery-guard-2026-03-25-final.md`
  - 结果：`可上线（ACCEPTABLE_TO_RELEASE）`

## 风险与回滚
- 当前阻断项：无。
- 回滚入口：`docs/release/learning-method-rollback-switch-2026-03-25.md`
- 异常触发：学习方法核心接口持续 5xx 或状态异常时执行回滚。

## 关联文档
- `docs/release/learning-method-test-handoff-2026-03-25.md`
- `docs/release/learning-method-release-evidence-2026-03-25.md`
- `docs/release/learning-method-config-checklist-2026-03-25.md`
