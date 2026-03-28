---
name: software-delivery-unified-governance
description: 开发后终检与软件交付总技能。适用于开发完成后的全面检查、提测评审、发布门禁、回滚准备与上线治理；统一调度全端终检、发布前检查、回滚就绪、数据库迁移安全、配置对齐、安全基线、UAT、可观测性与 Git 流程等子技能，并对设计阶段、实施阶段已经约定的高并发、数据一致性、性能容量、部署稳定性与安全权限控制点做最终验收，适合“开发后检查一切”，通常由 `$three-stage-skill-orchestrator` 路由进入本阶段。
---

# 软件交付全流程总技能

## 定位

- 本技能是“成功上线软件”的终检入口，负责对前两阶段产出的方案与实现做交付前验收和门禁。
- 本技能是三阶段体系中的“开发后总技能”，重点负责开发完成后的终检、提测与上线门禁。
- 本技能优先解决“已经设计过、也已经开发过，但还不能证明能安全上线”的问题。
- 本技能默认按风险优先级调度子技能，并在终检阶段自动联动 `$fullstack-unified-development-standards` 做一次实现一致性收口。
- 统一治理说明见 [references/skill-governance.md](references/skill-governance.md)。

## 能力特性（已合并）

- 需求冻结特性：需求必须明确、可验收、可量化，变更必须评估影响面。
- 发布前检查特性：构建、配置、数据库、监控、日志、告警与回滚条件统一核对。
- 回滚就绪特性：应用、配置、数据库三层回滚能力统一确认。
- 迁移安全特性：DDL、索引、回填、兼容迁移与发布顺序统一检查。
- 配置对齐特性：dev/test/prod 配置差异、域名、证书、回调地址统一核对。
- 安全基线特性：鉴权、校验、注入防护、敏感日志与最小权限统一检查。
- 高并发一致性特性：并发下单、超卖、重复提交、幂等、事务边界与状态一致性风险统一识别。
- 性能容量特性：慢查询、热点 SQL、缓存缺失、容量瓶颈、降级与限流准备统一评估。
- 线上稳定性特性：部署失败、环境炸裂、配置缺失、监控缺口、止血与回滚准备统一收敛。

能力细则见 [references/capability-profiles.md](references/capability-profiles.md)。

## 默认覆盖的五类高风险问题

以下问题一旦在任务描述中出现，默认纳入本技能范围；本阶段应检查设计阶段是否已定义、实施阶段是否已落地，而不是把问题当成上线前才第一次发现。

1. 高并发、超卖、重复下单
   - 默认联动：`fullstack-unified-development-standards`、`app-security-baseline-guard`、`capacity-and-hotspot-review`、`performance-regression-guard`、`observability-readiness-guard`
   - 必看项：幂等、防重复提交、库存扣减一致性、热点隔离、限流降级、压测与监控证据
2. 数据错误、事务不对
   - 默认联动：`fullstack-unified-development-standards`、`state-machine-alignment`、`fullstack-test-matrix`、`database-migration-safety-guard`
   - 必看项：事务边界、回滚语义、状态流一致性、接口与数据模型一致性、补偿与回归测试证据
3. 慢查询、数据库崩掉
   - 默认联动：`performance-regression-guard`、`capacity-and-hotspot-review`、`database-migration-safety-guard`、`observability-readiness-guard`
   - 必看项：慢 SQL、N+1、索引与分页、热点 SQL、缓存命中、DDL 风险、容量与告警证据
4. 部署不上、线上环境炸
   - 默认联动：`release-preflight-guard`、`deployment-config-alignment`、`rollback-readiness-guard`、`observability-readiness-guard`、`incident-runbook-builder`
   - 必看项：构建产物、环境变量、配置差异、数据库脚本匹配、监控告警、回滚与止血路径
5. 安全漏洞、越权
   - 默认联动：`app-security-baseline-guard`、`rbac-alignment-guard`、`secret-config-leak-guard`
   - 必看项：鉴权、RBAC、输入校验、SQL 注入、XSS/CSRF、敏感日志、密钥泄漏、最小权限

如任务同时命中以上多类问题，按“先阻断线上事故，再核验设计与实现缺口，再收敛数据一致性与性能容量，最后补体系化建设”的顺序给出建议。

共享口径见 [/Users/shaotongli/.codex/skills/three-stage-skill-orchestrator/references/five-risk-three-stage-control-template.md](/Users/shaotongli/.codex/skills/three-stage-skill-orchestrator/references/five-risk-three-stage-control-template.md)。本阶段只取其中“开发后控制点”和“阻断规则”。

## 子技能分层

### P0 必须补

- `requirements-freeze-guard`
- `release-preflight-guard`
- `rollback-readiness-guard`
- `database-migration-safety-guard`
- `deployment-config-alignment`
- `app-security-baseline-guard`

### P1 上线前补

- `fullstack-unified-development-standards`
- `acceptance-criteria-builder`
- `prd-ui-traceability-guard`
- `ux-state-completeness-checker`
- `release-quality-gate`
- `uat-handoff-guard`
- `observability-readiness-guard`
- `git-flow-enforcer`
- `release-branch-readiness-checker`

### P2 体系化建设

- `architecture-decision-recorder`
- `tech-stack-drift-guard`
- `secret-config-leak-guard`
- `performance-regression-guard`
- `capacity-and-hotspot-review`
- `incident-runbook-builder`

P2 默认作为治理建设项维护；如需在开发后总技能中一并体检，可通过 `--include-p2` 纳入本轮执行。

## 触发场景

- 需要对“成功上线”做全流程治理。
- 开发已经完成，想做一次“检查一切”。
- 需要补齐需求、测试、发布、回滚、安全、性能、运维短板。
- 需要统一处理高并发、超卖、重复下单、事务错误、慢查询、数据库风险、部署失败或越权漏洞。
- 需要做项目交付门禁、上线前检查、上线后风险兜底。
- 需要验证设计阶段和实施阶段对这 5 类风险的承诺是否都已兑现。
- 常见触发词：`开发后检查一切`、`提测前总检查`、`上线前总检查`、`终检总技能`、`发布门禁`、`交付终检`。

## 快速调用

- 推荐说法：`用开发后总技能检查一切，给我提测前结论。`
- 推荐说法：`用开发后总技能检查一切，给我上线前结论。`
- 推荐说法：`代码做完了，现在进入开发后终检阶段。`
- 路由说法：`让 $three-stage-skill-orchestrator 先判断阶段，再进入开发后终检。`
- 阶段切换信号：只要核心实现已完成、开始准备提测、验收或上线，就切到本技能。

统一三阶段调用模板见 [/Users/shaotongli/.codex/skills/software-development-readiness-governance/references/stage-invocation-templates.md](/Users/shaotongli/.codex/skills/software-development-readiness-governance/references/stage-invocation-templates.md)。

## 实施顺序

1. 先冻结需求与验收标准。
2. 再做产品/技术方案与架构评审。
3. 开发阶段对齐代码、接口、数据库与测试。
4. 开发完成后先执行 `$fullstack-unified-development-standards` 的 `final` 终检，收口实现层漂移。
5. 上线前执行发布前检查、配置对齐、迁移安全、安全基线。
6. 上线时确认回滚条件、监控、告警、UAT 与 release readiness。
7. 上线后补齐 runbook、性能、容量、可观测性与持续治理。

## 冲突优先级

1. 用户在当前任务中的明确要求
2. 发布安全与回滚安全
3. 需求冻结与验收口径
4. 本技能统一规则
5. 项目局部习惯

## 输出要求

- 优先输出阻断上线的高风险缺口。
- 对每个缺口明确归属阶段、影响范围、推荐子技能。
- 对重要风险给出“先补什么、后补什么”的顺序。
- 不能安全上线时必须明确阻断原因。

## 数据建模验收门禁

对以下规则必须做终检，不满足时应作为阻断项：

- `extJson` 不再承载高频业务状态。
- 任何需要并发写安全的状态必须入表。
- 任何需要幂等的写接口必须有数据库唯一约束。
- 任何报告型数据如果要分页、统计、筛选，不能只存 JSON。

终检至少应回答：

- 是否仍存在高频热状态写入 `extJson`
- 是否仍存在只靠代码判断幂等、没有唯一键的写接口
- 是否仍存在需要分页/统计/筛选却只存在于 JSON 的报告数据
- 是否已有迁移、双写、切读、回滚证据

## 守卫脚本（P0 编排）

1. 首次排查前运行：
`python3 scripts/software_delivery_guard.py --phase start --task "<用户需求>"`
2. 每个主要批次后运行：
`python3 scripts/software_delivery_guard.py --phase batch`
3. 最终上线前运行：
`python3 scripts/software_delivery_guard.py --phase final`

默认自动联动：

- `fullstack-unified-development-standards`
- `requirements-freeze-guard`
- `release-preflight-guard`
- `rollback-readiness-guard`
- `database-migration-safety-guard`
- `deployment-config-alignment`
- `app-security-baseline-guard`
- `acceptance-criteria-builder`
- `prd-ui-traceability-guard`
- `ux-state-completeness-checker`
- `release-quality-gate`
- `uat-handoff-guard`
- `observability-readiness-guard`
- `git-flow-enforcer`
- `release-branch-readiness-checker`

命中以下主题时，额外默认联动，不需要再次询问：

- 命中“高并发 / 超卖 / 重复下单 / 慢查询 / 热点 / 容量”时，自动纳入 `performance-regression-guard` 与 `capacity-and-hotspot-review`
- 命中“线上炸了 / 部署不上 / 环境不一致 / 发布失败”时，自动纳入 `incident-runbook-builder`
- 命中“越权 / 权限漏洞”时，自动按 `app-security-baseline-guard` 之外补跑 `rbac-alignment-guard`

按需可追加联动：

- `architecture-decision-recorder`
- `tech-stack-drift-guard`
- `secret-config-leak-guard`
- `performance-regression-guard`
- `capacity-and-hotspot-review`
- `incident-runbook-builder`

启用方式：

- `python3 scripts/software_delivery_guard.py --phase final --include-p2`
- P2 项默认输出为治理项，不直接改变 P0/P1 的上线阻断判定。

统一阻断阈值：

- 默认 `--fail-on auto`：`start` 不阻断，`batch/final` 对 `high` 阻断。

如需显式传参给子守卫，可在主命令追加：

- `--report-md <path>`
- `--report-json <path>`
- `--fullstack-report-md <path>`
- `--fullstack-report-json <path>`
- `--requirements-report-md <path>`
- `--requirements-report-json <path>`
- `--preflight-report-md <path>`
- `--preflight-report-json <path>`
- `--rollback-report-md <path>`
- `--rollback-report-json <path>`
- `--db-migration-report-md <path>`
- `--db-migration-report-json <path>`
- `--config-report-md <path>`
- `--config-report-json <path>`
- `--security-report-md <path>`
- `--security-report-json <path>`
- `--acceptance-report-md <path>`
- `--acceptance-report-json <path>`
- `--prd-ui-report-md <path>`
- `--prd-ui-report-json <path>`
- `--ux-state-report-md <path>`
- `--ux-state-report-json <path>`
- `--quality-gate-report-md <path>`
- `--quality-gate-report-json <path>`
- `--uat-report-md <path>`
- `--uat-report-json <path>`
- `--observability-report-md <path>`
- `--observability-report-json <path>`
- `--git-flow-report-md <path>`
- `--git-flow-report-json <path>`
- `--release-branch-report-md <path>`
- `--release-branch-report-json <path>`

仅在紧急排障时可临时跳过子守卫：

- `--skip-fullstack-unified-development-standards`
- `--skip-requirements-freeze-guard`
- `--skip-release-preflight-guard`
- `--skip-rollback-readiness-guard`
- `--skip-database-migration-safety-guard`
- `--skip-deployment-config-alignment`
- `--skip-app-security-baseline-guard`
- `--skip-acceptance-criteria-builder`
- `--skip-prd-ui-traceability-guard`
- `--skip-ux-state-completeness-checker`
- `--skip-release-quality-gate`
- `--skip-uat-handoff-guard`
- `--skip-observability-readiness-guard`
- `--skip-git-flow-enforcer`
- `--skip-release-branch-readiness-checker`
- `--skip-architecture-decision-recorder`
- `--skip-tech-stack-drift-guard`
- `--skip-secret-config-leak-guard`
- `--skip-performance-regression-guard`
- `--skip-capacity-and-hotspot-review`
- `--skip-incident-runbook-builder`

## 告警验收门禁

- 开发后终检发现的告警，不能默认解释为“低优先级可忽略”；凡与本次交付面相关的告警，默认要求清零后再给通过结论。
- 若开发阶段已判断告警来自守卫识别能力不足，终检阶段必须验证守卫能力是否已补齐，不能接受“人工知道没问题但工具还在报”的长期状态。
- 仅以下情况允许不清零交付：
  - 已确认是未被任何消费者引用、且已进入明确下线窗口的废弃契约。
  - 已获批准的阶段性豁免，且包含负责人、清理时间和回收动作。
- 未满足上述条件时，终检应把未清零告警视为交付缺口，而不是记录性提醒。
