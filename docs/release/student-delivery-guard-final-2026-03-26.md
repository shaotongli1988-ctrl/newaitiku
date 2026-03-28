# Delivery Governance Output

_Template Source: /Users/shaotongli/.codex/skills/software-delivery-unified-governance/references/delivery-governance-template.md_

## Release Scope
- Release / build: newaitiku
- Owner: TBD
- Environment: TBD

## Gate Summary
- Preflight: has blockers
- Quality gate: has gaps
- UAT handoff: review subguard outputs
- Rollback readiness: review release conclusion and rollback subguard
- Observability: review observability subguard
- Security: review security subguard

## Evidence Pack
- Release evidence bundle: use release-evidence-packager or release gate bundle
- Rollback material: check rollback readiness outputs
- UAT conclusion: check UAT handoff outputs
- Monitoring / replay / logs: check observability and replay artifacts

## Decision
- Status: 不建议上线
- Blocking items: release-preflight-guard 存在阻断项, rollback-readiness-guard 存在阻断项
- Governance follow-ups: performance-regression-guard 存在治理建设项, performance-regression-guard: 列表/表格改动未明显体现分页、虚拟列表或分段加载策略。 [/Users/shaotongli/Code/newaitiku/frontend/src/views/Student/LearningMethods.vue], performance-regression-guard: 疑似高频后端路径改动未明显体现缓存或降载策略。 [/Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py], incident-runbook-builder 存在治理建设项, incident-runbook-builder: 本次改动未发现 runbook / incident / playbook 文档更新。
- Recommended helpers: 推荐显式调用 `cutover-backfill-executor`，补齐切流、回填、审计和回滚资产后再发布。

## Recovery Plan
- Rollback trigger: any P0 blocker or post-release regression
- Rollback owner: TBD
- Post-release checks: fullstack-unified-development-standards 存在高风险或阻断项, fullstack-unified-development-standards: api-schema-drift-checker returned non-zero (1). Resolve schema drift or explicitly justify blocking issues.

## Template Reference

# Delivery Governance Template

## Release Scope

- Release / build:
- Owner:
- Environment:

## Gate Summary

- Preflight:
- Quality gate:
- UAT handoff:
- Rollback readiness:
- Observability:
- Security:

## Evidence Pack

- Release evidence bundle:
- Rollback material:
- UAT conclusion:
- Monitoring / replay / logs:

## Decision

- Status:
- Blocking items:
- Governance follow-ups:

## Recovery Plan

- Rollback trigger:
- Rollback owner:
- Post-release checks:
