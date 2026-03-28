# 全端技能治理一页版

本文是本技能的治理总则。

## 一、决策表

| 场景 | 默认模式 | 备注 |
| --- | --- | --- |
| 通用全端改动（库/后端/接口/前端/权限/状态/校验/文档/测试） | `global` | 守卫脚本执行 `start/batch/final`，并自动联动 `api-schema-drift-checker`、`rbac-alignment-guard`、`state-machine-alignment`、`error-code-governor`、`fullstack-test-matrix`、`delivery-doc-sync` 与 `component-reuse-shared-logic-guard` |
| 题库模块改动（`user`、`userAuth`、`knowledge`、`question`、`task`） | `questionBank` | 响应包固定 `{ code, message, data }`，并自动联动 `question-bank-contract-enforcer` 与 `component-reuse-shared-logic-guard`（同时按上下文自动执行其他子守卫） |
| 用户明确指定特殊校验重点（严格对齐/统一新增/零漂移/实现层收敛） | 在当前模式下增加对应检查项 | 仍由本技能统一执行 |

## 二、冲突收敛顺序

1. 用户在当前任务中的明确要求
2. `questionBank` 固定契约
3. 本技能统一规则
4. 本技能能力特性细则
5. 项目局部习惯

## 三、实现层治理边界

- 实现层收敛规则只约束公共组件、公共 Hook、公共函数、统一 `request`、分页结构、基础实体与重复实现抽取。
- 实现层守卫不替代接口契约、题库边界、权限语义、状态流、错误码、测试与文档子守卫。
- 实现层默认按“正确实现优先”执行，不允许为了兼容旧坏写法而长期保留补丁层、胶水层或双轨实现。
- 如实现层抽取会扩大到多个模块或超出用户授权范围，必须暂停并确认边界。

## 四、与其他总技能的切换表

| 阶段 | 默认总技能 | 说明 |
| --- | --- | --- |
| 开发前准备 | `software-development-readiness-governance` | 先统一需求、验收、ADR、技术栈与非功能基线 |
| 实现与联调 | `fullstack-unified-development-standards` | 负责字段、接口、页面、权限、状态、错误、文档、测试零漂移 |
| 发布与上线 | `software-delivery-unified-governance` | 负责发布前检查、回滚、安全、配置、UAT 与上线门禁 |

## 五、统一报告与豁免规则

- 主守卫输出优先使用统一报告，至少包含：模式、任务、十域结果、失败项、豁免项、结论。
- `questionBank` 模式必须额外输出五模块摘要。
- 豁免必须显式落在豁免文件中，并在报告中可见。
- 豁免只能用于时间受限、范围明确、责任明确的漂移。

## 六、不可违背项

- 同一模块不允许混用不同响应包。
- 同一批交付不允许混用不同状态流。
- 不允许长期保留别名字段或兼容字段。
- 不允许以小修小补兼容、外围适配或双轨并存代替正确实现。
- 已存在更优公共层、标准模型或统一方案时，应直接替换旧实现并完成收敛。
- 无法安全收敛时必须暂停并向用户确认。
