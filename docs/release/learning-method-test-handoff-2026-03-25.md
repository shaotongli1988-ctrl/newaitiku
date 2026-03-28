# 学习方法模块提测交接摘要（2026-03-25）

## 1. 交付范围
- 模块：学习方法（learning_method）
- 本轮目标：
  - 补齐学习方法模块 API 契约与前端 consumer 类型对齐
  - 修复 schema drift 告警
  - 完成提测前门禁复验

## 2. 代码与契约改动
- 后端状态流与可观测补强：
  - `app/service_modules/learning_method.py`
  - 增加学习进度状态流守卫（allowedTransitions/canTransition）
  - 增加 trace/metric 语义上下文（`traceId`、`metricSnapshot`）
- 前端契约补齐：
  - `frontend/src/api/contracts.ts`
  - `AiMarkingSubmitModel` 补齐 `assignment_id/assignmentId`
  - 新增类型：
    - `LearningMethodPracticeStartRequest`
    - `LearningMethodPracticeCompleteRequest`
    - `LearningMethodAdminSaveRequest`
    - `LearningMethodAdminUpdateRequest`
    - `LearningMethodAdminSortRequest`

## 3. 发布证据文档
- 发布证据：`docs/release/learning-method-release-evidence-2026-03-25.md`
- 配置核对：`docs/release/learning-method-config-checklist-2026-03-25.md`
- 回滚与止血：`docs/release/learning-method-rollback-switch-2026-03-25.md`
- 开发后总守卫报告：`docs/release/delivery-guard-2026-03-25-final.md`

## 4. 验证结果
- API schema drift：`none`
  - 命令：`schema_drift_guard.py --phase final`
- OpenAPI 范围测试：`2 passed`
  - 命令：`python3 -m pytest -q tests/test_openapi_schema_scope.py`
- 集成测试：`46 passed`
  - 命令：`./tools/bin/run-tests.sh --suite integration`
- 十域验收门禁：`120/120 checks passed`
  - 命令：`./tools/bin/run-acceptance.sh`
- 开发后总守卫结论：`可上线（ACCEPTABLE_TO_RELEASE）`

## 5. 提测结论
- 结论：可提测。
- 阻断项：无。
- 上线前必须补齐：无。
- 备注：如需统一归档发布证据包，可后续按需执行 `release-evidence-packager`。

## 6. 回滚入口
- 见：`docs/release/learning-method-rollback-switch-2026-03-25.md`
- 回滚触发：学习方法核心接口出现持续 5xx 或进度状态异常。
