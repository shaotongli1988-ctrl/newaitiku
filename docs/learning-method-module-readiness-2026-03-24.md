# Readiness Governance Output

_Template Source: /Users/shaotongli/.codex/skills/software-development-readiness-governance/references/readiness-governance-template.md_

## Scope
- Feature / request: 题库新增学习方法模块，首批包含费曼学习法并梳理可上架学习方法内容
- Owner: TBD
- Target milestone: TBD

## Frozen Inputs
- Requirement boundary: defined
- Acceptance criteria: TBD
- PRD / UI references: README.md, alignment-self-check.md, api-permission-mapping.md, click-replay-report-template.md, click-replay-result-schema.md, contract.md, module-summary.md, test-plan.md, core-business-components-vue.md, extjson-hot-state-readiness-2026-03-22.md, frontend-role-path-governance.md, knowledge-module.md, question-bank-contract.md, auth-session-expiry-recovery-2026-03-24.md, db-index-rollout-2026-03-20.md, error-book-ui-refactor-2026-03-21.md, feature-chain-test-matrix-2026-03-21.md, final-release-checklist-2026-03-20.md, observability-readiness-2026-03-20.md, p0-e2e-task-backlog-2026-03-21.md, practice-points-acceptance-2026-03-23.md, practice-ui-refactor-2026-03-21.md, release-group-message-template-2026-03-20.md, release-index-2026-03-20.md, release-package-brief-2026-03-20.md, release-package-cleanup-2026-03-20.md, release-package-execution-2026-03-20.md, release-package-manifest-2026-03-20.md, release-readiness-2026-03-20.md, release-watch-plan-2026-03-20.md, student-analysis-readable-weak-points-2026-03-23.md, student-analysis-redesign-spec-2026-03-22.md, student-analysis-tasks-regression-checklist-2026-03-23.md, student-analysis-tasks-remediation-plan-2026-03-23.md, student-copy-baseline-acceptance-2026-03-23.md, student-fixed-scope-subject-switch-2026-03-22.md, student-frontend-delivery-2026-03-22.md, student-frontend-redesign-task-breakdown-2026-03-22.md, student-home-subject-sync-2026-03-24.md, student-question-bank-syllabus-2026-03-23.md, student-question-bank-syllabus-implementation-notes-2026-03-23.md, student-question-bank-syllabus-redesign-spec-2026-03-23.md, student-retained-question-bank-remediation-plan-2026-03-23.md, student-subject-switcher-recovery-2026-03-24.md, subject-diagnostic-standardization-2026-03-22.md, uat-handoff-2026-03-20.md, manifest.md, checklist.md, teacher-click-replay-report-2026-03-19.md, SKILL.md, checklist.md, SKILL.md, detection-tuning.md, schema-drift-checklist.md, SKILL.md, checklist.md, SKILL.md, adr-template.md, checklist.md, SKILL.md, SKILL.md, fullstack-integration-checklist.md, reuse-extraction-checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, capability-profiles.md, question-bank-alignment-checklist.md, question-bank-fixed-contract.md, skill-governance.md, unified-delivery-checklist.md, SKILL.md, checklist.md, SKILL.md, SKILL.md, checklist.md, SKILL.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, software-delivery-skill-roadmap.md, SKILL.md, capability-profiles.md, skill-governance.md, subskill-roadmap.md, SKILL.md, capability-profiles.md, shared-contract-package.md, skill-governance.md, stage-invocation-templates.md, SKILL.md, checklist.md, SKILL.md, five-risk-three-stage-control-template.md, routing-rules.md, skill-governance-change-checklist-2026-03-22.md, stage-contract.md, template-capability-catalog.md, SKILL.md, checklist.md, SKILL.md, checklist.md, student-click-replay-report-2026-03-18.md, student-click-replay-report-2026-03-21.md, student-ui-design-token-sync-2026-03-22.md, super_admin-click-replay-report-2026-03-18.md, teacher-click-replay-report-2026-03-18.md, teacher-manual-click-checklist-2026-03-18.md, three-end-click-replay-summary-2026-03-18.md, three-end-true-click-checklist.md, three-role-feature-inventory.md, README.md, README.md
- ADR / technical plan: follow mode-specific governance

## Risk Baseline
- Concurrency / idempotency: review before implementation
- Data consistency / transaction: review before implementation
- Performance / capacity: review before implementation
- Deployment / rollback: define readiness expectations early
- Security / permission: confirm guard coverage before coding

## Delivery Contract
- Ready to enter implementation: 建议补齐后进入开发
- Required documents: README.md, alignment-self-check.md, api-permission-mapping.md, click-replay-report-template.md, click-replay-result-schema.md, contract.md, module-summary.md, test-plan.md, core-business-components-vue.md, extjson-hot-state-readiness-2026-03-22.md, frontend-role-path-governance.md, knowledge-module.md, question-bank-contract.md, auth-session-expiry-recovery-2026-03-24.md, db-index-rollout-2026-03-20.md, error-book-ui-refactor-2026-03-21.md, feature-chain-test-matrix-2026-03-21.md, final-release-checklist-2026-03-20.md, observability-readiness-2026-03-20.md, p0-e2e-task-backlog-2026-03-21.md, practice-points-acceptance-2026-03-23.md, practice-ui-refactor-2026-03-21.md, release-group-message-template-2026-03-20.md, release-index-2026-03-20.md, release-package-brief-2026-03-20.md, release-package-cleanup-2026-03-20.md, release-package-execution-2026-03-20.md, release-package-manifest-2026-03-20.md, release-readiness-2026-03-20.md, release-watch-plan-2026-03-20.md, student-analysis-readable-weak-points-2026-03-23.md, student-analysis-redesign-spec-2026-03-22.md, student-analysis-tasks-regression-checklist-2026-03-23.md, student-analysis-tasks-remediation-plan-2026-03-23.md, student-copy-baseline-acceptance-2026-03-23.md, student-fixed-scope-subject-switch-2026-03-22.md, student-frontend-delivery-2026-03-22.md, student-frontend-redesign-task-breakdown-2026-03-22.md, student-home-subject-sync-2026-03-24.md, student-question-bank-syllabus-2026-03-23.md, student-question-bank-syllabus-implementation-notes-2026-03-23.md, student-question-bank-syllabus-redesign-spec-2026-03-23.md, student-retained-question-bank-remediation-plan-2026-03-23.md, student-subject-switcher-recovery-2026-03-24.md, subject-diagnostic-standardization-2026-03-22.md, uat-handoff-2026-03-20.md, manifest.md, checklist.md, teacher-click-replay-report-2026-03-19.md, SKILL.md, checklist.md, SKILL.md, detection-tuning.md, schema-drift-checklist.md, SKILL.md, checklist.md, SKILL.md, adr-template.md, checklist.md, SKILL.md, SKILL.md, fullstack-integration-checklist.md, reuse-extraction-checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, capability-profiles.md, question-bank-alignment-checklist.md, question-bank-fixed-contract.md, skill-governance.md, unified-delivery-checklist.md, SKILL.md, checklist.md, SKILL.md, SKILL.md, checklist.md, SKILL.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, checklist.md, SKILL.md, software-delivery-skill-roadmap.md, SKILL.md, capability-profiles.md, skill-governance.md, subskill-roadmap.md, SKILL.md, capability-profiles.md, shared-contract-package.md, skill-governance.md, stage-invocation-templates.md, SKILL.md, checklist.md, SKILL.md, five-risk-three-stage-control-template.md, routing-rules.md, skill-governance-change-checklist-2026-03-22.md, stage-contract.md, template-capability-catalog.md, SKILL.md, checklist.md, SKILL.md, checklist.md, student-click-replay-report-2026-03-18.md, student-click-replay-report-2026-03-21.md, student-ui-design-token-sync-2026-03-22.md, super_admin-click-replay-report-2026-03-18.md, teacher-click-replay-report-2026-03-18.md, teacher-manual-click-checklist-2026-03-18.md, three-end-click-replay-summary-2026-03-18.md, three-end-true-click-checklist.md, three-role-feature-inventory.md, README.md, README.md
- Required evidence before coding: FIX_THEN_START
- Reason: 已发现应在编码前补齐的关键缺口，建议先收口再开工。

## Open Items
- Pending confirmation: acceptance-criteria-builder: 任务描述中未明显体现验收标准或 Given/When/Then 口径。
- Pending confirmation: acceptance-criteria-builder: 检测到改动，但未发现验收说明或 UAT 文档更新。
- Pending confirmation: tech-stack-drift-guard: tech-stack-drift-guard 返回非零退出码 (1)。
- Pending confirmation: tech-stack-drift-guard: 检测到基础设施或交付链路变更，但未发现方案说明或风险评审证据。
- Pending confirmation: question-bank-contract-enforcer: question-bank-contract-enforcer 返回非零退出码 (2)。
- Deferred decisions with owner and deadline: none

## Template Reference

# Readiness Governance Template

## Scope

- Feature / request:
- Owner:
- Target milestone:

## Frozen Inputs

- Requirement boundary:
- Acceptance criteria:
- PRD / UI references:
- ADR / technical plan:

## Risk Baseline

- Concurrency / idempotency:
- Data consistency / transaction:
- Performance / capacity:
- Deployment / rollback:
- Security / permission:

## Delivery Contract

- Ready to enter implementation:
- Required documents:
- Required evidence before coding:

## Open Items

- Pending confirmation:
- Deferred decisions with owner and deadline:
