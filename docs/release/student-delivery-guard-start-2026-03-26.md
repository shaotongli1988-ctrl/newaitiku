# Delivery Governance Output

_Template Source: /Users/shaotongli/.codex/skills/software-delivery-unified-governance/references/delivery-governance-template.md_

## Release Scope
- Release / build: newaitiku
- Owner: TBD
- Environment: TBD

## Gate Summary
- Preflight: done
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
- Status: 基本可上线
- Blocking items: none
- Governance follow-ups: none
- Recommended helpers: 推荐显式调用 `cutover-backfill-executor`，补齐切流、回填、审计和回滚资产后再发布。

## Recovery Plan
- Rollback trigger: any P0 blocker or post-release regression
- Rollback owner: TBD
- Post-release checks: fullstack-unified-development-standards: No explicit auto-trigger phrase was detected in the task text. Confirm this skill is the right orchestrator if the request is not clearly full-stack., fullstack-unified-development-standards: This file contains a repeatable request state machine that fits a shared hook better than page-local state. [/Users/shaotongli/Code/newaitiku/frontend/src/views/Student/LearningMethods.vue]

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
