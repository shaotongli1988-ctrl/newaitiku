# Delivery Governance Output

_Template Source: /Users/shaotongli/.codex/skills/software-delivery-unified-governance/references/delivery-governance-template.md_

## Release Scope
- Release / build: newaitiku
- Owner: TBD
- Environment: TBD

## Gate Summary
- Preflight: done
- Quality gate: done
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
- Status: 可上线
- Blocking items: none
- Governance follow-ups: none
- Recommended helpers: 推荐显式调用 `release-evidence-packager`，把 gate、rollback、UAT、replay 与关键日志收敛成统一发布证据包。

## Recovery Plan
- Rollback trigger: any P0 blocker or post-release regression
- Rollback owner: TBD
- Post-release checks: review responsibility summary

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
