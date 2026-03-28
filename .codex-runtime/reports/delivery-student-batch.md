Software Delivery Guard: batch
Working directory: /Users/shaotongli/Code/newaitiku
Fail threshold: high
Changed files: 13
  - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
  - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
  - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
  - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
  - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
  - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
  - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
  - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
  - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
  - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
  - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
  - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
Warnings:
  - [HIGH] fullstack-unified-development-standards 返回非零退出码 (2)。 [fullstack-unified-development-standards]
  - [MEDIUM] 发布涉及数据库或配置变更，但未发现功能开关/止血手段证据。 [rollback-readiness-guard]
  - [MEDIUM] 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。 [release-branch-readiness-checker]
Release Conclusion:
  - 结论: 有条件上线
  - 建议动作: 补齐后上线 (FIX_THEN_RELEASE)
  - 原因: 不存在 P0 阻断项，但存在 P1 准备不足，原则上应补齐后再上线。
  - 上线阻断项:
      - 无
  - 上线前必须补齐:
      - fullstack-unified-development-standards 存在上线前准备不足
      - rollback-readiness-guard: 发布涉及数据库或配置变更，但未发现功能开关/止血手段证据。
      - release-branch-readiness-checker: 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
  - 可延期治理:
      - 无
  - P2 治理项:
      - 无
  - 责任归属:
      - 研发:
          - fullstack-unified-development-standards 存在高风险或阻断项
          - release-branch-readiness-checker: 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
      - 运维:
          - rollback-readiness-guard: 发布涉及数据库或配置变更，但未发现功能开关/止血手段证据。
Layered Summary:
  P0 阻断项:
    - 无
  P1 准备不足项:
    - fullstack-unified-development-standards 存在上线前准备不足
  建议上线前补齐:
    - rollback-readiness-guard: 发布涉及数据库或配置变更，但未发现功能开关/止血手段证据。
    - release-branch-readiness-checker: 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
  可延期治理:
    - 无
  P2 治理项:
    - 无
Integrated sub-guard:
  - name: fullstack-unified-development-standards
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/fullstack-unified-development-standards/scripts/unified_delivery_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md --report-json .codex-runtime/reports/fullstack-student-batch-subguard.json
  - returncode: 2
  - warnings:
      - fullstack-unified-development-standards 返回非零退出码 (2)。
Integrated sub-guard:
  - name: requirements-freeze-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/requirements-freeze-guard/scripts/requirements_freeze_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Requirements Freeze Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: release-preflight-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/release-preflight-guard/scripts/release_preflight_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md --report-json .codex-runtime/reports/preflight-student-batch.json
  - returncode: 0
  - output:
      Release Preflight Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: rollback-readiness-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/rollback-readiness-guard/scripts/rollback_readiness_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Rollback Readiness Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 1 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings:
        - [MEDIUM] 发布涉及数据库或配置变更，但未发现功能开关/止血手段证据。
Integrated sub-guard:
  - name: database-migration-safety-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/database-migration-safety-guard/scripts/database_migration_safety_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Database Migration Safety Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: deployment-config-alignment
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/deployment-config-alignment/scripts/deployment_config_alignment_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Deployment Config Alignment: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: app-security-baseline-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/app-security-baseline-guard/scripts/app_security_baseline_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      App Security Baseline Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: acceptance-criteria-builder
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/acceptance-criteria-builder/scripts/acceptance_criteria_builder_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Acceptance Criteria Builder: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: prd-ui-traceability-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/prd-ui-traceability-guard/scripts/prd_ui_traceability_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      PRD UI Traceability Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: ux-state-completeness-checker
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/ux-state-completeness-checker/scripts/ux_state_completeness_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      UX State Completeness Checker: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: release-quality-gate
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/release-quality-gate/scripts/release_quality_gate.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Release Quality Gate: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: uat-handoff-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/uat-handoff-guard/scripts/uat_handoff_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      UAT Handoff Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: observability-readiness-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/observability-readiness-guard/scripts/observability_readiness_guard.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Observability Readiness Guard: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 13
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
        - /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
        - /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
        - /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py
        - /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue
        - /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
        - /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
        - /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
      Warnings: none
Integrated sub-guard:
  - name: git-flow-enforcer
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/git-flow-enforcer/scripts/git_flow_enforcer.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Git Flow Enforcer: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 0
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
      Warnings: none
Integrated sub-guard:
  - name: release-branch-readiness-checker
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/release-branch-readiness-checker/scripts/release_branch_readiness_checker.py --phase batch --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md --report-json .codex-runtime/reports/release-branch-student-batch.json
  - returncode: 0
  - output:
      Release Branch Readiness Checker: batch
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 0
      Fail threshold: high
      Summary: 0 high, 1 medium, 0 low
      Warnings:
        - [MEDIUM] 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
Integrated sub-guard:
  - name: tooling-pilot-replay-gate
  - enabled: no
  - output:
      Skipped because no tooling-pilot governance context was detected.