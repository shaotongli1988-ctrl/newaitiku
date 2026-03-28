# 学习方法模块运维发布说明（2026-03-25）

## 发布目标
- 发布内容：学习方法模块契约对齐与提测前收口。
- 目标结果：学习方法相关接口可稳定提供；发布门禁与验收全绿。

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

## 发布前检查
- 确认 seed 导入脚本可用：`scripts/import_learning_method_seed.py`
- 确认配置核对文档：`docs/release/learning-method-config-checklist-2026-03-25.md`
- 确认回滚/止血方案：`docs/release/learning-method-rollback-switch-2026-03-25.md`

## 验证基线
- 集成测试：`./tools/bin/run-tests.sh --suite integration`（46 passed）
- OpenAPI 范围：`python3 -m pytest -q tests/test_openapi_schema_scope.py`（2 passed）
- 十域验收：`./tools/bin/run-acceptance.sh`（120/120 passed）
- 开发后总守卫：`docs/release/delivery-guard-2026-03-25-final.md`（可上线，无阻断）

## 发布后观测
- 重点观测项：
  - 学习方法 `start/complete` 接口 5xx 比例
  - 学习进度状态是否出现非法跳转
  - 关键响应耗时与错误码分布
- 若异常持续：执行回滚文档中的止血与回退流程。
