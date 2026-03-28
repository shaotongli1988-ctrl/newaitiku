# 子技能分层一览

## P0 必须补

- `requirements-freeze-guard`
- `release-preflight-guard`
- `rollback-readiness-guard`
- `database-migration-safety-guard`
- `deployment-config-alignment`
- `app-security-baseline-guard`

## P1 上线前补

- `fullstack-unified-development-standards`
- `acceptance-criteria-builder`
- `prd-ui-traceability-guard`
- `ux-state-completeness-checker`
- `release-quality-gate`
- `uat-handoff-guard`
- `observability-readiness-guard`
- `git-flow-enforcer`
- `release-branch-readiness-checker`

## P2 体系化建设

- `architecture-decision-recorder`
- `tech-stack-drift-guard`
- `secret-config-leak-guard`
- `performance-regression-guard`
- `capacity-and-hotspot-review`
- `incident-runbook-builder`

说明：

- P2 主要用于治理补强与能力建设，默认不作为上线阻断链路。
- 如需在开发后总技能中一并跑一轮，可使用 `--include-p2`。
