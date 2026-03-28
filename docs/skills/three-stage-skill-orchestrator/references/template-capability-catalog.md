# 三阶段模板能力索引

## 共享模板

- `five-risk-three-stage-control-template`
  - 用于统一高并发、事务一致性、性能容量、部署稳定性、安全权限五类高风险问题在开发前、开发中、开发后的控制点口径
  - 参考文件：`references/five-risk-three-stage-control-template.md`

## 开发前

- `architecture-decision-recorder`
  - `python3 scripts/architecture_decision_recorder_guard.py --decision-title "<标题>" --owner "<负责人>" --output-md <path>`
- `requirements-freeze-guard`
  - `python3 scripts/requirements_freeze_guard.py --requirement-title "<标题>" --owner "<负责人>" --output-md <path>`
- `acceptance-criteria-builder`
  - `python3 scripts/acceptance_criteria_builder_guard.py --story-title "<标题>" --owner "<负责人>" --output-md <path>`
- `prd-ui-traceability-guard`
  - `python3 scripts/prd_ui_traceability_guard.py --feature-name "<功能>" --owner "<负责人>" --output-md <path>`

## 开发中

- 当前开发中子守卫以契约校验为主，模板产出主要通过开发前与开发后相关技能补齐。

## 开发后

- `deployment-config-alignment`
  - `python3 scripts/deployment_config_alignment_guard.py --service-name "<服务>" --owner "<负责人>" --output-md <path>`
- `observability-readiness-guard`
  - `python3 scripts/observability_readiness_guard.py --service-name "<服务>" --owner "<负责人>" --output-md <path>`
- `release-quality-gate`
  - `python3 scripts/release_quality_gate.py --release-name "<版本>" --owner "<负责人>" --output-md <path>`
- `git-flow-enforcer`
  - `python3 scripts/git_flow_enforcer.py --branch-policy "<策略>" --owner "<负责人>" --output-md <path>`
- `release-branch-readiness-checker`
  - `python3 scripts/release_branch_readiness_checker.py --release-name "<版本>" --owner "<负责人>" --output-md <path>`
- `uat-handoff-guard`
  - `python3 scripts/uat_handoff_guard.py --feature-name "<功能>" --owner "<负责人>" --output-md <path>`
- `ux-state-completeness-checker`
  - `python3 scripts/ux_state_completeness_guard.py --page-name "<页面>" --owner "<负责人>" --output-md <path>`
- `incident-runbook-builder`
  - `python3 scripts/incident_runbook_builder.py --service-name "<服务>" --owner "<负责人>" --output-md <path>`
