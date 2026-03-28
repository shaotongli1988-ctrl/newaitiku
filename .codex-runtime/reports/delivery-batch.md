Software Delivery Guard: batch
Working directory: /Users/shaotongli/Code/newaitiku
Fail threshold: medium
Changed files: 29
  - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
  - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
  - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
  - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
  - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
  - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
  - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
  - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
Warnings:
  - [HIGH] fullstack-unified-development-standards 返回非零退出码 (2)。 [fullstack-unified-development-standards]
  - [HIGH] release-preflight-guard 返回非零退出码 (1)。 [release-preflight-guard]
  - [MEDIUM] 实现改动存在，但未发现部署/发布相关证据。 [release-preflight-guard]
  - [HIGH] release-branch-readiness-checker 返回非零退出码 (1)。 [release-branch-readiness-checker]
  - [MEDIUM] 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。 [release-branch-readiness-checker]
Suggested explicit skills:
  - 推荐显式调用 `release-evidence-packager`，把 gate、rollback、UAT、replay 与关键日志收敛成统一发布证据包。
Release Conclusion:
  - 结论: 不建议上线
  - 建议动作: 立即阻断 (BLOCK_NOW)
  - 原因: 存在 P0 阻断项，当前版本不满足安全上线条件。
  - 上线阻断项:
      - release-preflight-guard 存在阻断项
  - 上线前必须补齐:
      - fullstack-unified-development-standards 存在上线前准备不足
      - release-branch-readiness-checker 存在上线前准备不足
      - release-preflight-guard: 实现改动存在，但未发现部署/发布相关证据。
      - release-branch-readiness-checker: 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
  - 可延期治理:
      - 无
  - P2 治理项:
      - 无
  - 责任归属:
      - 研发:
          - fullstack-unified-development-standards 存在高风险或阻断项
          - release-branch-readiness-checker 存在高风险或阻断项
          - release-branch-readiness-checker: 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
      - 运维:
          - release-preflight-guard 存在高风险或阻断项
          - release-preflight-guard: 实现改动存在，但未发现部署/发布相关证据。
Layered Summary:
  P0 阻断项:
    - release-preflight-guard 存在阻断项
  P1 准备不足项:
    - fullstack-unified-development-standards 存在上线前准备不足
    - release-branch-readiness-checker 存在上线前准备不足
  建议上线前补齐:
    - release-preflight-guard: 实现改动存在，但未发现部署/发布相关证据。
    - release-branch-readiness-checker: 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
  可延期治理:
    - 无
  P2 治理项:
    - 无
Integrated sub-guard:
  - name: fullstack-unified-development-standards
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/fullstack-unified-development-standards/scripts/unified_delivery_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md --report-json .codex-runtime/reports/fullstack-batch.json
  - returncode: 2
  - warnings:
      - fullstack-unified-development-standards 返回非零退出码 (2)。
Integrated sub-guard:
  - name: requirements-freeze-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/requirements-freeze-guard/scripts/requirements_freeze_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      Requirements Freeze Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: release-preflight-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/release-preflight-guard/scripts/release_preflight_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md --report-json .codex-runtime/reports/preflight-batch.json
  - returncode: 1
  - output:
      Release Preflight Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 1 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings:
        - [MEDIUM] 实现改动存在，但未发现部署/发布相关证据。
  - warnings:
      - release-preflight-guard 返回非零退出码 (1)。
Integrated sub-guard:
  - name: rollback-readiness-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/rollback-readiness-guard/scripts/rollback_readiness_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      Rollback Readiness Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: database-migration-safety-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/database-migration-safety-guard/scripts/database_migration_safety_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      Database Migration Safety Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: deployment-config-alignment
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/deployment-config-alignment/scripts/deployment_config_alignment_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      Deployment Config Alignment: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: app-security-baseline-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/app-security-baseline-guard/scripts/app_security_baseline_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      App Security Baseline Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: acceptance-criteria-builder
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/acceptance-criteria-builder/scripts/acceptance_criteria_builder_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      Acceptance Criteria Builder: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: prd-ui-traceability-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/prd-ui-traceability-guard/scripts/prd_ui_traceability_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      PRD UI Traceability Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: ux-state-completeness-checker
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/ux-state-completeness-checker/scripts/ux_state_completeness_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      UX State Completeness Checker: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: release-quality-gate
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/release-quality-gate/scripts/release_quality_gate.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      Release Quality Gate: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: uat-handoff-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/uat-handoff-guard/scripts/uat_handoff_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      UAT Handoff Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: observability-readiness-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/observability-readiness-guard/scripts/observability_readiness_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      Observability Readiness Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 29
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
      Warnings: none
Integrated sub-guard:
  - name: git-flow-enforcer
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/git-flow-enforcer/scripts/git_flow_enforcer.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md
  - returncode: 0
  - output:
      Git Flow Enforcer: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 0
      Fail threshold: medium
      Summary: 0 high, 0 medium, 0 low
      Warnings: none
Integrated sub-guard:
  - name: release-branch-readiness-checker
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/release-branch-readiness-checker/scripts/release_branch_readiness_checker.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on auto --task 第8批：全量发布与文档冻结 --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_learning_method_api.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/learning_method.py --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/module-summary.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/test-plan.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-announcement-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-final-copy-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-group-message-template-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-pr-description-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-ops-release-brief-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-test-handoff-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-rollback-switch-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-config-checklist-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-evidence-2026-03-25.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/waivers.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/contract.json --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-final.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-batch.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/unified-delivery-p1-01-start.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing-p1-01.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-dev-prompt.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/TODO.codex.template.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/codex-continuous-readiness.md --changed-file /Users/shaotongli/Code/newaitiku/docs/codex/three-stage-routing.md --report-json .codex-runtime/reports/release-branch-batch.json
  - returncode: 1
  - output:
      Release Branch Readiness Checker: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 0
      Fail threshold: medium
      Summary: 0 high, 1 medium, 0 low
      Warnings:
        - [MEDIUM] 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
  - warnings:
      - release-branch-readiness-checker 返回非零退出码 (1)。
Integrated sub-guard:
  - name: tooling-pilot-replay-gate
  - enabled: no
  - output:
      Skipped because no tooling-pilot governance context was detected.