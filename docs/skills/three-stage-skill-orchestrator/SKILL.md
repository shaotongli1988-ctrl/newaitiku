---
name: three-stage-skill-orchestrator
description: 三阶段总技能统一入口。用于根据当前任务语义和上下文状态，把需求自动路由到开发前准备、开发中实施或开发后终检阶段，解决“三阶段总技能只有口令、没有真正分发器”的问题。
---

# 三阶段总技能统一入口

## 定位

- 本技能是三阶段体系的唯一万能入口，只负责路由，不直接替代阶段总技能本身。
- 本技能接收统一口令：`三阶段总技能`。
- 本技能把请求分发到以下阶段总技能：
  - 开发前：`software-development-readiness-governance`
  - 开发中：`fullstack-unified-development-standards`
  - 开发后：`software-delivery-unified-governance`

## 触发场景

- 用户说 `三阶段总技能`。
- 用户不想手动判断当前应该进入哪个阶段。
- 需求在多阶段之间切换，需要系统给出当前最合理的阶段建议。

## 路由规则

1. 出现“冻结需求 / 验收 / PRD / 原型 / 技术方案 / 开发前”等词，优先路由到开发前。
2. 出现“实现 / 联调 / 新增字段 / 新增接口 / 前后端对齐 / 开发中”等词，优先路由到开发中。
3. 出现“提测 / 上线 / 门禁 / 终检 / 回滚 / 发布 / 开发后”等词，优先路由到开发后。
4. 如果提供了当前阶段状态，则优先结合状态判断，而不是只看关键字。
5. 如果多个阶段信号冲突明显，则输出“无法安全自动路由”，提示确认。

## 五类高风险问题的阶段化路由

以下问题不能被默认理解成“只在开发后排查”，必须结合当前语义判断所处阶段：

- 高并发、超卖、重复下单
- 数据错误、事务不对
- 慢查询、数据库崩掉
- 部署不上、线上环境炸
- 安全漏洞、越权

阶段化解释规则：

1. 如果用户在讨论“方案 / 设计 / 规则 / 验收 / 口径”，路由到 `software-development-readiness-governance`，要求先定义控制点。
2. 如果用户在讨论“实现 / 联调 / 落地 / 改代码 / 加测试”，路由到 `fullstack-unified-development-standards`，要求把控制点做实。
3. 如果用户在讨论“提测 / 发布 / 上线 / 检查 / 门禁”，路由到 `software-delivery-unified-governance`，要求检查控制点是否兑现。
4. 仅凭出现上述问题名词，不得直接默认路由到开发后阶段。

统一控制点模板见 [references/five-risk-three-stage-control-template.md](references/five-risk-three-stage-control-template.md)。

如用户讨论以下规则，默认视为“数据一致性 / 并发安全 / 建模治理”问题，优先按当前语义路由到开发前或开发中，而不是开发后：

- `extJson` 不再承载高频业务状态
- 任何需要并发写安全的状态必须入表
- 任何需要幂等的写接口必须有数据库唯一约束
- 任何报告型数据如果要分页、统计、筛选，不能只存 JSON

详细规则见 [references/routing-rules.md](references/routing-rules.md)。
阶段输入输出契约见 [references/stage-contract.md](references/stage-contract.md)。
模板能力索引见 [references/template-capability-catalog.md](references/template-capability-catalog.md)。
近期技能治理变更清单见 [references/skill-governance-change-checklist-2026-03-22.md](references/skill-governance-change-checklist-2026-03-22.md)。

## 守卫脚本

1. 统一路由前运行：
`python3 scripts/three_stage_orchestrator.py --task "<用户需求>"`
2. 若已有阶段状态，可显式传入：
`python3 scripts/three_stage_orchestrator.py --task "<用户需求>" --current-stage <none|readiness|implementation|delivery>`

## 输出要求

- 输出推荐阶段。
- 输出推荐阶段对应的总技能名。
- 输出路由原因与命中信号。
- 输出下一步建议话术。
- 无法安全路由时必须明确说明原因。

## 告警治理路由原则

- 任何“告警治理 / 漂移收敛 / 技术债消减 / 守卫误报收敛”类任务，不得以“先压告警”作为默认完成标准。
- 如果任务语义是“改代码、改契约、改文档、补测试、升级守卫能力”，默认路由到 `fullstack-unified-development-standards`，要求先做真实修复。
- 如果任务语义是“提测前、上线前、门禁复验”，默认路由到 `software-delivery-unified-governance`，要求检查告警是否已被真实消除，而不是被跳过。
- 仅当用户明确要求讨论方案且尚未进入实现时，才回到开发前阶段定义治理口径。
