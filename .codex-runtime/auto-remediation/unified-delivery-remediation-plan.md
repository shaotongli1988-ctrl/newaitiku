# Unified Delivery Auto Remediation Plan

- Phase: `final`
- Mode: `auto`
- Warning count: `5`
- Blocking warnings: `5`
- Detail JSON: `/Users/shaotongli/Code/newaitiku/.codex-runtime/auto-remediation/unified-delivery-remediation-plan.json`

## Actions

1. `api-schema-drift-checker-warning` (high) [api-schema-drift-checker]
   - owner: `backend-api-owner`
   - skill: `api-schema-drift-checker`
   - fix: 先修复 `api-schema-drift-checker` 告警，再回跑该守卫并更新关联证据。
   - auto-fix eligible: `no`
2. `rbac-alignment-guard-warning` (high) [rbac-alignment-guard]
   - owner: `rbac-owner`
   - skill: `rbac-alignment-guard`
   - fix: 先修复 `rbac-alignment-guard` 告警，再回跑该守卫并更新关联证据。
   - auto-fix eligible: `no`
3. `delivery-doc-sync-warning` (high) [delivery-doc-sync]
   - owner: `docs-owner`
   - skill: `delivery-doc-sync`
   - fix: 先修复 `delivery-doc-sync` 告警，再回跑该守卫并更新关联证据。
   - auto-fix eligible: `no`
4. `component-reuse-shared-logic-guard-warning` (high) [component-reuse-shared-logic-guard]
   - owner: `frontend-owner`
   - skill: `component-reuse-shared-logic-guard`
   - fix: 先修复 `component-reuse-shared-logic-guard` 告警，再回跑该守卫并更新关联证据。
   - auto-fix eligible: `no`
5. `cache-consistency-guard-warning` (high) [cache-consistency-guard]
   - owner: `runtime-owner`
   - skill: `cache-consistency-guard`
   - fix: 先修复 `cache-consistency-guard` 告警，再回跑该守卫并更新关联证据。
   - auto-fix eligible: `no`

## Loop

1. Apply fixes based on this plan.
2. Re-run `unified_delivery_guard.py` to verify warning convergence.
3. Sync evidence artifacts for delivery handoff.
