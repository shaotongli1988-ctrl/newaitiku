# 全端统一交付清单

在首次编辑前、每个主要改动批次后、最终交付前都要执行本清单。

默认执行路径：

- `python3 scripts/unified_delivery_guard.py --phase start --task "<用户需求>"`
- `python3 scripts/unified_delivery_guard.py --phase batch`
- `python3 scripts/unified_delivery_guard.py --phase final`
- 推荐在 `batch/final` 补充统一报告输出：
  - `--report-md <path>`
  - `--report-json <path>`
- 如存在已批准的临时豁免，需补充：
  - `--waiver-file <json-file>`
- 推荐在 CI 中保存 Markdown / JSON 报告产物，便于评审与追溯。
- 阻断阈值默认 `--fail-on auto`：
  - `start` 不阻断
  - `batch/final` 对 `high` 阻断
- 主守卫默认自动调用：
  - `api-schema-drift-checker` 子守卫（API 契约防漂移）
  - `question-bank-contract-enforcer` 子守卫（题库固定契约校验）
  - `rbac-alignment-guard` 子守卫（RBAC 权限对齐校验）
  - `state-machine-alignment` 子守卫（状态流统一校验）
  - `error-code-governor` 子守卫（错误码统一治理校验）
  - `fullstack-test-matrix` 子守卫（全栈联动测试矩阵校验）
  - `delivery-doc-sync` 子守卫（交付文档同步校验）
- 守卫脚本任何告警都必须处理或说明阻塞原因。

## 目录

1. 分发闸门
2. 字段标准
3. 接口标准
4. 页面标准
5. 状态标准
6. 权限标准
7. 校验标准
8. 错误标准
9. 扩展标准
10. 文档标准
11. 测试标准
12. 最终闸门

## 1. 分发闸门

编辑前确认：

- 本技能是全端改动的默认单一入口。
- 先选择契约模式：题库模块用 `questionBank`，其他用 `global`。
- 题库模块限定为：`user`、`userAuth`、`knowledge`、`question`、`task`。
- 冲突优先级固定：用户要求 > `questionBank` 固定契约 > 本技能统一规则 > 已批准且带截止时间的阶段性兼容窗口或豁免规则。
- 读取治理与能力特性文档：
  - [skill-governance.md](skill-governance.md)
  - [capability-profiles.md](capability-profiles.md)
- 若为题库模块，额外读取：
  - [question-bank-fixed-contract.md](question-bank-fixed-contract.md)
  - [question-bank-alignment-checklist.md](question-bank-alignment-checklist.md)

## 2. 字段标准

- 字段命名统一为小驼峰并保持业务语义清晰。
- 数据库字段、实体属性、接口字段、前端模型、表单绑定、表格列键保持同名。
- 不允许同义别名字段并存。

## 3. 接口标准

- 请求和响应结构遵循当前契约模式。
- 分页键、排序键、方向值全链路一致。
- 列表、详情、新增、更新、删除、流程接口结构一致。

契约模式规则：

- `questionBank`：响应包固定 `{ code, message, data }`。
- `global`：遵循当前项目全局响应契约。

## 4. 页面标准

- 页面布局、按钮位置、弹窗结构保持项目统一规范。
- 表单项、表格列、详情展示与接口字段一一对应。
- 标签、占位文案、提示文案与后端语义一致。

## 5. 状态标准

- 状态集合有限且可枚举。
- 状态流转路径在数据库、后端、前端、测试、文档保持一致。
- 不允许临时状态或局部状态泄漏到正式契约。

## 6. 权限标准

- 角色名、权限键、鉴权表达式统一。
- 后端鉴权、路由守卫、按钮显隐、接口拦截规则保持一致。
- 未授权行为与提示保持一致。

## 7. 校验标准

- 必填、格式、长度、范围规则前后端一致。
- 唯一性与关联性校验规则在全链路一致。
- 不允许仅前端或仅后端单边校验。

## 8. 错误标准

- 错误码命名空间、错误文案、异常分类一致。
- 异常处理路径一致，日志字段与业务标识一致。
- 前端错误展示与后端语义一致。

## 9. 扩展标准

- 先使用预留扩展策略，再考虑结构性变更。
- 不能随意新增表、列、顶层结构。
- `questionBank` 模式下，契约外业务字段必须进入 `extJson`。

## 10. 文档标准

- 同步字段说明、接口说明、页面说明、状态说明。
- 注释、示例、文档描述必须与最终实现一致。
- 不允许遗留过期说明。

## 11. 测试标准

至少覆盖：

- 正常路径
- 异常路径
- 边界条件
- 权限场景
- 性能敏感场景（需求涉及热路径时）

并确认：

- 断言字段名、状态值、权限与校验规则与最终实现一致。
- 接口响应包断言符合当前契约模式。
- 主守卫增强能力（报告输出、模块摘要、豁免解析）具备单测或 smoke test。

## 12. 最终闸门

以下任一不满足都不能结束：

- 没有遗漏层（库、后端、接口、前端、文档、测试）。
- 没有字段漂移、类型漂移、规则漂移、状态漂移、权限漂移。
- 没有未经批准的结构扩展。
- 题库模块没有遗留旧契约结构。
- 最终守卫脚本无未解释告警。
- 最终报告中没有未说明的豁免项。
