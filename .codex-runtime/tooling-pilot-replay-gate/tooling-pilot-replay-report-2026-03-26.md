# Tooling Pilot Replay Report (2026-03-26)

## Snapshot
- Cases replayed: 34
- Passed: 34
- Failed: 0

| Skill | Case | Type | Expected | Actual | Runtime Output | Result |
| --- | --- | --- | --- | --- | --- | --- |
| test-code-generator | tp-impl-without-tests | true_positive | auto-run | auto-run | present | pass |
| test-code-generator | skip-start-phase | guarded_skip | skip | skip | missing | pass |
| test-code-generator | fp-docs-only-test-language | false_positive_replay | skip | skip | missing | pass |
| auto-install-missing-deps | tp-missing-module-with-command | true_positive | auto-run | auto-run | present | pass |
| auto-install-missing-deps | skip-signal-without-command | guarded_skip | skip | skip | missing | pass |
| auto-install-missing-deps | fp-replay-command-without-signal | false_positive_replay | skip | skip | missing | pass |
| auto-install-missing-deps | fp-unsafe-dep-command | false_positive_replay | skip | skip | missing | pass |
| auto-install-missing-deps | fp-missing-dependency-manifest | false_positive_replay | skip | skip | missing | pass |
| auto-install-missing-deps | skip-start-phase-with-command | guarded_skip | skip | skip | missing | pass |
| auto-install-missing-deps | fp-unsafe-sudo-dep-command | false_positive_replay | skip | skip | missing | pass |
| auto-install-missing-deps | fp-unsafe-inline-python-dep-command | false_positive_replay | skip | skip | missing | pass |
| auto-install-missing-deps | fp-absolute-replay-command | false_positive_replay | skip | skip | missing | pass |
| ci-failure-triager | tp-ci-log-with-signal | true_positive | auto-run | auto-run | present | pass |
| ci-failure-triager | skip-start-phase | guarded_skip | skip | skip | missing | pass |
| ci-failure-triager | fp-postmortem-without-log | false_positive_replay | skip | skip | missing | pass |
| cutover-backfill-executor | tp-cutover-signal-with-spec | true_positive | auto-run | auto-run | present | pass |
| cutover-backfill-executor | skip-signal-without-spec | guarded_skip | skip | skip | missing | pass |
| cutover-backfill-executor | fp-spec-without-cutover-signal | false_positive_replay | skip | skip | missing | pass |
| cutover-backfill-executor | fp-spec-missing-idempotency | false_positive_replay | skip | skip | missing | pass |
| cutover-backfill-executor | fp-unsafe-cutover-spec | false_positive_replay | skip | skip | missing | pass |
| cutover-backfill-executor | fp-spec-target-mismatch | false_positive_replay | skip | skip | missing | pass |
| cutover-backfill-executor | fp-spec-missing-target | false_positive_replay | skip | skip | missing | pass |
| cutover-backfill-executor | skip-start-phase-with-cutover-spec | guarded_skip | skip | skip | missing | pass |
| cutover-backfill-executor | fp-weak-migration-semantics-with-spec | false_positive_replay | skip | skip | missing | pass |
| cutover-backfill-executor | fp-nested-live-runmode-spec | false_positive_replay | skip | skip | missing | pass |
| cutover-backfill-executor | fp-prod-target-environment-spec | false_positive_replay | skip | skip | missing | pass |
| readiness-evidence-packager | tp-readiness-evidence-with-source | true_positive | auto-run | auto-run | present | pass |
| readiness-evidence-packager | tp-readiness-evidence-auto-discovery | true_positive | auto-run | auto-run | present | pass |
| readiness-evidence-packager | fp-readiness-doc-with-source | false_positive_replay | skip | skip | missing | pass |
| readiness-evidence-packager | fp-readiness-evidence-source-outside | false_positive_replay | skip | skip | missing | pass |
| release-evidence-packager | tp-release-evidence-with-source | true_positive | auto-run | auto-run | present | pass |
| release-evidence-packager | tp-release-evidence-auto-discovery | true_positive | auto-run | auto-run | present | pass |
| release-evidence-packager | fp-release-notes-with-source | false_positive_replay | skip | skip | missing | pass |
| release-evidence-packager | fp-release-evidence-source-outside | false_positive_replay | skip | skip | present | pass |

## Guardrail
Synthetic replay is the promotion check above unit trigger tests: it verifies that the real unified guard still respects explicit-input gates and writes into runtime-scoped output paths.
