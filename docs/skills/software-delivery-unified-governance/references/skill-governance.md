# 软件交付总技能治理说明

## 一、决策表

| 场景 | 默认层级 | 备注 |
| --- | --- | --- |
| 开发完成后想做一次“检查一切” | `P1 + 全端终检` | 先联动 `fullstack-unified-development-standards` 的实现终检，再汇总交付门禁 |
| 发布前检查、上线评审、灰度前确认 | `P0` | 自动联动需求冻结、发布前检查、回滚、迁移安全、配置对齐、安全基线 |
| 需求不明确、验收标准模糊、设计与实现追踪不清 | `P1` | 优先补验收与追踪，再推进开发与发布 |
| 架构治理、容量评估、性能回归、runbook 沉淀 | `P2` | 面向中长期治理，默认不阻断紧急修复 |

## 二、分层原则

### P0 必须补

- 直接决定“能不能安全上线”
- 默认优先于 P1/P2
- 任一 P0 出现高风险阻断项，应暂停上线

### P1 上线前补

- 决定“上线前是否准备充分”
- 出现高风险项时，原则上不建议上线

### P2 体系化建设

- 决定“长期是否可维护、可扩展、可追踪”
- 以中长期治理为主，不默认阻断紧急发布

## 三、冲突优先级

1. 用户当前任务中的明确要求
2. 发布与回滚安全
3. 需求冻结与验收口径
4. 本技能统一编排规则
5. 项目局部习惯

## 四、默认编排顺序

1. `fullstack-unified-development-standards`
2. `requirements-freeze-guard`
3. `release-preflight-guard`
4. `rollback-readiness-guard`
5. `database-migration-safety-guard`
6. `deployment-config-alignment`
7. `app-security-baseline-guard`
8. `acceptance-criteria-builder`
9. `prd-ui-traceability-guard`
10. `ux-state-completeness-checker`
11. `release-quality-gate`
12. `uat-handoff-guard`
13. `observability-readiness-guard`
14. `git-flow-enforcer`
15. `release-branch-readiness-checker`

## 五、阻断规则

- `start` 阶段默认不阻断，只提示风险。
- `batch/final` 阶段出现 `high` 风险时默认阻断。
- 无法安全收敛时必须明确阻断原因。
