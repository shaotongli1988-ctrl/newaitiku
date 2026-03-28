---
name: software-development-readiness-governance
description: 开发前准备总技能。用于在进入开发前统一冻结需求边界、验收标准、PRD/UI 追踪关系、技术方案与非功能基线，并把高并发、数据一致性、性能容量、部署稳定性与安全权限等高风险问题前置到设计阶段解决，避免“还没定义清楚就开始做”；通常由 `$three-stage-skill-orchestrator` 路由进入本阶段。
---

# 开发前准备总技能

## 定位

- 本技能是三阶段体系中的“开发前总技能”，负责把需求、设计、方案和验收一次性定义清楚。
- 本技能优先解决“方向没定就开工”“做到一半才补规则”“UI、接口、权限、状态口径不一致”的问题。
- 本技能的输出是后续 `$fullstack-unified-development-standards` 的实施基线。
- 开发完成后的全面终检与上线门禁，交由 `$software-delivery-unified-governance` 处理。

## 能力特性（已编排）

- 需求冻结特性：进入开发前先确认范围、边界、角色、约束和变更口径。
- 验收定义特性：把模糊需求转成 Given/When/Then、正常/异常/边界、权限/状态验收标准。
- PRD/UI 追踪特性：确保页面、按钮、弹窗、文案、流程与 PRD/原型一一对应。
- 技术方案特性：关键选型、替代方案、影响范围和风险必须沉淀为 ADR。
- 开发蓝图特性：明确字段、接口、状态、权限、测试、文档的首版实施边界，避免开发中反复返工。
- 高风险前置设计特性：高并发、超卖、重复下单、事务一致性、慢查询、部署稳定性、安全越权等问题必须在设计阶段先明确方案、边界和验收口径。
- 数据建模治理特性：高频业务状态、并发写安全、幂等唯一键、报告型数据建模必须在设计阶段一次性定清，不允许把结构性问题留给实现阶段兜底。

## 数据建模非协商规则

- `extJson` 不再承载高频业务状态。
- 任何需要并发写安全的状态必须入表。
- 任何需要幂等的写接口必须有数据库唯一约束。
- 任何报告型数据如果要分页、统计、筛选，不能只存 JSON。

设计阶段至少要输出：

- 哪些字段允许留在 `extJson`
- 哪些状态必须拆表
- 哪些接口需要唯一键保障幂等
- 哪些报告类数据必须使用关系表而不是 JSON 聚合

如以上四项没有明确结论，则视为“方案未冻结”，不得进入开发。

## 设计阶段必须前置定义的五类问题

以下问题在本阶段不是“先记着，开发后再看”，而是必须先形成可实施基线，再允许进入开发。

1. 高并发、超卖、重复下单
   - 设计输出：幂等策略、库存扣减模型、并发控制方案、限流降级策略、压测目标
2. 数据错误、事务不对
   - 设计输出：事务边界、状态流转规则、一致性约束、补偿/回滚语义、异常口径
3. 慢查询、数据库崩掉
   - 设计输出：核心查询路径、索引/分页策略、缓存策略、容量假设、扩容与告警基线
4. 部署不上、线上环境炸
   - 设计输出：环境清单、配置解耦方案、发布顺序、回滚策略、依赖与监控要求
5. 安全漏洞、越权
   - 设计输出：角色权限模型、接口鉴权原则、输入校验要求、敏感数据处理规则、最小权限边界

如以上任一问题没有形成明确方案、边界或验收条件，则视为“未定义完成”，不得直接进入开发。

共享口径见 [/Users/shaotongli/.codex/skills/three-stage-skill-orchestrator/references/five-risk-three-stage-control-template.md](/Users/shaotongli/.codex/skills/three-stage-skill-orchestrator/references/five-risk-three-stage-control-template.md)。本阶段只取其中“开发前控制点”和“阻断规则”。

## 触发场景

- 开发前想先把一切定义清楚。
- 需求评审、技术方案评审、开发排期前。
- 需要在设计阶段先把并发、事务、性能、部署、安全等高风险问题定义清楚。
- 常见触发词：`开发前定义好一切`、`开发前准备`、`先把需求冻结`、`先出验收标准`、`先对齐 PRD 和 UI`、`先做技术方案`、`进入开发前检查`。

## 快速调用

- 推荐说法：`用开发前总技能，先把需求、验收、PRD/UI、技术方案一次性定义清楚。`
- 推荐说法：`开发前定义好一切，先别开工。`
- 推荐说法：`进入开发前，先冻结范围、状态、权限、接口和页面。`
- 路由说法：`让 $three-stage-skill-orchestrator 先判断阶段，再进入开发前。`
- 阶段切换信号：一旦开始写真实实现、联调接口、改数据库或页面代码，切到 `$fullstack-unified-development-standards`。

统一三阶段调用模板见 [references/stage-invocation-templates.md](references/stage-invocation-templates.md)。

## 守卫脚本（强制）

1. 首次定义前运行：
`python3 scripts/software_development_readiness_guard.py --phase start --task "<用户需求>"`
2. 需求或方案发生主要调整后运行：
`python3 scripts/software_development_readiness_guard.py --phase batch`
3. 正式进入开发前运行：
`python3 scripts/software_development_readiness_guard.py --phase final`

默认 `--fail-on auto`：

- `start` 不阻断，先暴露缺口。
- `batch/final` 对 `high` 阻断。

主守卫会自动联动：

- `requirements-freeze-guard`：需求是否明确、已评审、已冻结。
- `acceptance-criteria-builder`：验收标准、UAT 与 Given/When/Then 是否成型。
- `prd-ui-traceability-guard`：PRD/原型/页面追踪关系是否完整。
- `architecture-decision-recorder`：关键方案是否形成 ADR 与风险说明。
  - 支持直接生成 ADR 草案模板，便于在评审前先把背景、决策、替代方案和风险填完整。
- `readiness-evidence-packager`：当任务明确进入“开发前材料整理 / 开发启动包 / readiness evidence”语义，且显式提供 `--readiness-evidence-source` 时，自动在 `.codex-runtime/readiness-evidence-pilot/` 生成 runtime scoped 准备包预演产物。

命中以下主题时，默认要求在设计结果中显式落版，不需要再次确认：

- 命中“高并发 / 超卖 / 重复下单”时，必须补齐幂等、库存一致性、限流降级与压测口径
- 命中“事务 / 数据错误 / 一致性”时，必须补齐事务边界、状态机和补偿语义
- 命中“慢查询 / 数据库风险 / 容量”时，必须补齐查询路径、索引、分页、缓存和容量假设
- 命中“部署 / 环境 / 发布 / 回滚”时，必须补齐配置矩阵、发布顺序和回滚预案
- 命中“安全 / 越权 / 权限”时，必须补齐角色、权限点、鉴权和输入校验原则

如需显式传参给子守卫，可在主命令追加：

- `--fail-on <auto|none|high|medium|low>`
- `--requirements-report-md <path>`
- `--requirements-report-json <path>`
- `--acceptance-report-md <path>`
- `--acceptance-report-json <path>`
- `--prd-ui-report-md <path>`
- `--prd-ui-report-json <path>`
- `--architecture-report-md <path>`
- `--architecture-report-json <path>`
- `--readiness-evidence-source <path>` 可重复传入多个开发前材料目录或文件
- `--readiness-evidence-project <name>`
- `--readiness-evidence-owner <owner>`
- `--readiness-evidence-milestone <name>`

仅在紧急场景可临时跳过：

- `--skip-requirements-freeze-guard`
- `--skip-acceptance-criteria-builder`
- `--skip-prd-ui-traceability-guard`
- `--skip-architecture-decision-recorder`

## 实施顺序

1. 冻结需求目标、角色边界、范围和不做什么。
2. 产出可签收的验收标准与测试口径。
3. 建立 PRD、原型、页面、按钮、文案、流程的追踪矩阵。
4. 确定关键技术方案、替代方案、约束与风险。
5. 输出开发蓝图：字段、接口、状态、权限、测试、文档与五类高风险控制点的首版边界。
6. 评估是否允许进入开发；未冻结项必须先补齐。
7. 对涉及 `extJson`、并发状态、幂等接口、报告数据的需求，明确表结构、唯一键、索引与事务边界。

统一治理说明见 [references/skill-governance.md](references/skill-governance.md)。

## 输出要求

- 输出是否允许进入开发。
- 输出“未定义清楚项”与责任归属。
- 输出后续交给 `$fullstack-unified-development-standards` 的实施基线，明确哪些并发、一致性、性能、部署、安全控制点必须在开发中落地。
