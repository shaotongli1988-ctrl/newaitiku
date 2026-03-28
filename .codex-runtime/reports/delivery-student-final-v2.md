Software Delivery Guard: final
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
  - [MEDIUM] 发布涉及数据库或配置变更，但未发现功能开关/止血手段证据。 [rollback-readiness-guard]
  - [MEDIUM] 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。 [release-branch-readiness-checker]
Release Conclusion:
  - 结论: 基本可上线
  - 建议动作: 建议补齐后上线 (RECOMMEND_FIX_THEN_RELEASE)
  - 原因: 不存在阻断项，但仍有上线前建议补齐的中风险准备项。
  - 上线阻断项:
      - 无
  - 上线前必须补齐:
      - rollback-readiness-guard: 发布涉及数据库或配置变更，但未发现功能开关/止血手段证据。
      - release-branch-readiness-checker: 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
  - 可延期治理:
      - 无
  - P2 治理项:
      - 无
  - 责任归属:
      - 研发:
          - release-branch-readiness-checker: 当前工作区存在未提交或未跟踪改动，请确认 release 分支是否干净。
      - 运维:
          - rollback-readiness-guard: 发布涉及数据库或配置变更，但未发现功能开关/止血手段证据。
Layered Summary:
  P0 阻断项:
    - 无
  P1 准备不足项:
    - 无
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/fullstack-unified-development-standards/scripts/unified_delivery_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Unified Delivery Guard: final
      Working directory: /Users/shaotongli/Code/newaitiku
      Git root: /Users/shaotongli/Code/newaitiku
      Fail threshold: high
      Matched triggers: none
      Changed files: 13
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
      Detected ten-standard coverage:
        - Field standards: no evidence
        - API standards: no evidence
        - Page standards: yes
        - Status standards: yes
        - Permission standards: yes
        - Validation standards: yes
        - Error standards: yes
        - Extension standards: yes
        - Documentation standards: yes
        - Test standards: yes
      Detected surfaces:
        - persistence: no evidence
        - backend: yes
        - frontend: yes
        - docs: yes
        - tests: yes
      Warnings: none
      Conditional tooling pilot:
        - name: test-code-generator
        - enabled: no
        - reason: No missing-test signal detected.
        - output:
            Skipped
      Conditional tooling pilot:
        - name: auto-install-missing-deps
        - enabled: no
        - reason: No dependency-failure signal detected.
        - output:
            Skipped
      Conditional tooling pilot:
        - name: ci-failure-triager
        - enabled: no
        - reason: No CI-failure signal detected.
        - output:
            Skipped
      Conditional tooling pilot:
        - name: cutover-backfill-executor
        - enabled: no
        - reason: No cutover/backfill signal detected.
        - output:
            Skipped
      Conditional tooling pilot:
        - name: release-evidence-packager
        - enabled: no
        - reason: No release-evidence packaging signal detected.
        - output:
            Skipped
      Integrated sub-guard:
        - name: api-schema-drift-checker
        - enabled: yes
        - script: /Users/shaotongli/Code/newaitiku/docs/skills/api-schema-drift-checker/scripts/schema_drift_guard.py
        - returncode: 0
        - command:
            /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/api-schema-drift-checker/scripts/schema_drift_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --max-files 6000 --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
        - output:
            API Schema Drift Guard: final
            Working directory: /Users/shaotongli/Code/newaitiku
            Git root: /Users/shaotongli/Code/newaitiku
            Fail threshold: high
            Inputs: openapi=1 producer-model-files=20 consumer-files=91
            Extracted: producer-schemas=185 consumer-schemas=72 openapi-endpoints=157 consumer-endpoints=146
            Drift issues:
              [MEDIUM] 64
                - (field) Optional fields missing in consumer (AdaptivePracticeRequest -> AdaptivePracticeRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: knowledge_id, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AdaptivePracticeResponse -> AdaptivePracticeResponse): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AdaptivePracticeResult -> AdaptivePracticeResult): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, question_ids
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AdminManagedUserSaveRequest -> AdminManagedUserSaveRequest): Producer has 6 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: exam_category_code, joint_exam_group_code, model_config, prep_stage, user_id, vocational_major
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AdminStudentsImportRequest -> AdminStudentsImportRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: csv_text, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AdminSyllabusVersionCreateRequest -> AdminSyllabusVersionCreateRequest): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: copy_from_version_id, model_config, version_name
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AdminSyllabusWeightItemRequest -> AdminSyllabusWeightItemRequest): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: knowledge_id, model_config, target_weight
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AdminSyllabusWeightsSaveRequest -> AdminSyllabusWeightsSaveRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: knowledge_weights, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AdminSystemSettingsSaveRequest -> AdminSystemSettingsSaveRequest): Producer has 11 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: ai_daily_limit, daily_check_in_points, default_exam_minutes, mock_exam_rule_profiles, model_config, paper_reward_points, platform_name, practice_reward_points, practice_reward_threshold, wrong_book_reward_points
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AuthLoginPasswordRequest -> AuthLoginPasswordRequest): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AuthLoginSmsRequest -> AuthLoginSmsRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, sms_code
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AuthPasswordResetRequest -> AuthPasswordResetRequest): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, new_password, sms_code
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AuthRegisterRequest -> AuthRegisterRequest): Producer has 7 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: employee_no, exam_category_code, joint_exam_group_code, model_config, prep_stage, sms_code, vocational_major
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (AuthSmsCodeRequest -> AuthSmsCodeRequest): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (BaseResponse -> BaseResponse): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (BatchQuestionCreateRequest -> BatchQuestionCreateRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, source_task_id
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (ExamTaskCreateRequest -> ExamTaskCreateRequest): Producer has 15 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: allow_redo, class_ids, due_at, exam_category_code, joint_exam_group_code, model_config, source_id, source_label, source_type, student_ids
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (KnowledgeGraphEnvelopeResponse -> KnowledgeGraphEnvelopeResponse): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (KnowledgeGraphResponse -> KnowledgeGraphResponse): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (KnowledgeLayoutNodeRequest -> KnowledgeLayoutNodeRequest): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (KnowledgeLayoutSaveRequest -> KnowledgeLayoutSaveRequest): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (KnowledgeLink -> KnowledgeLink): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (KnowledgeNode -> KnowledgeNode): Producer has 8 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: create_time, full_label, model_config, module_code, parent_id, question_count, short_label, wrong_count
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (KnowledgePrerequisiteUpdateRequest -> KnowledgePrerequisiteUpdateRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, source_id
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (KnowledgeWriteRequest -> KnowledgeWriteRequest): Producer has 9 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: create_time, exam_category_code, ext_json, joint_exam_group_code, model_config, parent_id, policy_version, subject_code, update_time
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (LearningMethodAdminSaveRequest -> LearningMethodAdminSaveRequest): Producer has 11 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: common_mistakes, difficulty_level, estimated_minutes, ext_json, method_code, method_name, model_config, one_line_intro, question_bank_actions, starter_task
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (LearningMethodAdminSortRequest -> LearningMethodAdminSortRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: method_codes, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (LearningMethodAdminUpdateRequest -> LearningMethodAdminUpdateRequest): Producer has 10 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: common_mistakes, difficulty_level, estimated_minutes, ext_json, method_name, model_config, one_line_intro, question_bank_actions, starter_task, use_when
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (LearningMethodPracticeCompleteRequest -> LearningMethodPracticeCompleteRequest): Producer has 4 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: duration_sec, model_config, review_summary, session_id
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (LearningMethodPracticeStartRequest -> LearningMethodPracticeStartRequest): Producer has 4 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, practice_strategy, session_id, source_type
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (ManualPaperCreateRequest -> ManualPaperCreateRequest): Producer has 16 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: duration_minutes, exam_category_code, joint_exam_group_code, model_config, paper_id, paper_name, paper_status, paper_type, policy_version, publish_class_ids
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (MessagesReadBatchRequest -> MessagesReadBatchRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: message_ids, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (MessagesSendRequest -> MessagesSendRequest): Producer has 7 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: exam_category_code, joint_exam_group_code, model_config, send_at, subject_code, target_mode, user_ids
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (MessagesSettingsSaveRequest -> MessagesSettingsSaveRequest): Producer has 7 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: allow_ai_tutor, allow_points_notice, allow_review_notice, allow_study_reminder, allow_system_notice, allow_weekly_report, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (PaperAiGenerateRequest -> PaperAiGenerateRequest): Producer has 9 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: class_ids, exam_category_code, joint_exam_group_code, knowledge_scope, model_config, policy_version, subject_code, subject_id, total_count
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (PaperAutoRuleRequest -> PaperAutoRuleRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, question_score
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (PaperAutoSaveRequest -> PaperAutoSaveRequest): Producer has 14 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: duration_minutes, exam_category_code, joint_exam_group_code, model_config, paper_id, paper_name, paper_status, paper_type, policy_version, subject_code
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (PaperTemplateSaveRequest -> PaperTemplateSaveRequest): Producer has 12 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: duration_minutes, exam_category_code, joint_exam_group_code, model_config, paper_type, policy_version, subject_code, subject_id, template_id, template_name
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (ProfessionalTreeExamCategory -> ProfessionalTreeExamCategory): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, sort_no
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (ProfessionalTreeJointExamGroup -> ProfessionalTreeJointExamGroup): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: major_list_text, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (ProfessionalTreeResponse -> ProfessionalTreeResponse): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (ProfessionalTreeSubject -> ProfessionalTreeSubject): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, subject_slot, subject_type
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (QuestionCreateRequest -> QuestionCreateRequest): Producer has 11 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: exam_category_code, ext_json, joint_exam_group_code, knowledge_points, model_config, module_code, policy_version, source_type, subject_code, subject_type
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (QuestionDeleteBatchRequest -> QuestionDeleteBatchRequest): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, policy_version, question_ids
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (QuestionOptionItem -> QuestionOptionItem): Producer has 1 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (QuestionStatusBatchTransitionRequest -> QuestionStatusBatchTransitionRequest): Producer has 4 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, policy_version, question_ids, target_status
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (QuestionTransitionRequest -> QuestionTransitionRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, policy_version
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (QuestionUpdateRequest -> QuestionUpdateRequest): Producer has 13 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: create_time, exam_category_code, ext_json, joint_exam_group_code, knowledge_points, model_config, module_code, policy_version, source_type, subject_code
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentAiMarkingSubmitRequest -> StudentAiMarkingSubmitRequest): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: answer_image_url, assignment_id, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentAiTutorAskRequest -> StudentAiTutorAskRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, prompt_image_url
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentDiagnosisQuickStartRequest -> StudentDiagnosisQuickStartRequest): Producer has 4 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, question_count, source_type, subject_code
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentDiagnosisQuickSubmitAnswerItem -> StudentDiagnosisQuickSubmitAnswerItem): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: elapsed_sec, model_config, question_id
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentDiagnosisQuickSubmitRequest -> StudentDiagnosisQuickSubmitRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, source_type
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentMockExamStartRequest -> StudentMockExamStartRequest): Producer has 5 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: exam_category_code, joint_exam_group_code, model_config, subject_code, subject_id
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentPaperAnswerRequest -> StudentPaperAnswerRequest): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: elapsed_sec, model_config, question_id
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentPaperSubmitRequest -> StudentPaperSubmitRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, total_elapsed_sec
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentPersonalBankToggleRequest -> StudentPersonalBankToggleRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: is_collected, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentPracticeSubmitRequest -> StudentPracticeSubmitRequest): Producer has 5 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: assignment_id, attempt_key, elapsed_sec, model_config, source_type
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentProfileUpdateRequest -> StudentProfileUpdateRequest): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: exam_category_code, joint_exam_group_code, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentSessionSubmitRequest -> StudentSessionSubmitRequest): Producer has 3 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: answered_count, elapsed_sec, model_config
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentSubscriptionMockOrderConfirmRequest -> StudentSubscriptionMockOrderConfirmRequest): Producer has 4 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, paid_at, request_id, transaction_no
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentSubscriptionMockOrderCreateRequest -> StudentSubscriptionMockOrderCreateRequest): Producer has 4 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, plan_code, session_id, source_type
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (field) Optional fields missing in consumer (StudentSubscriptionRedeemRequest -> StudentSubscriptionRedeemRequest): Producer has 2 additional optional fields; potential stale typing. Match rule: exact.
                  evidence: model_config, request_id
                  fix: Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.
                - (schema) Producer schemas not matched by consumer: Some producer models cannot be mapped to frontend types, causing blind spots.
                  evidence: AdminRedeemCodeBatchCreateRequest, AiMarkingSubmitModel, AiTutorAskModel, AuthLoginPasswordModel, AuthLoginSmsModel, AuthPasswordResetModel, AuthRegisterModel, BatchQuestionDeleteModel, BatchQuestionStatusModel, ImportResultModel
                  fix: Add alias mapping via --alias-map or define corresponding consumer type models.
              [LOW] 1
                - (endpoint) Documented APIs not referenced by consumer: Some OpenAPI endpoints are not detected in frontend call sites.
                  evidence: GET /api/question-bank/admin/conversion/overview, GET /api/question-bank/admin/learning-methods, GET /api/question-bank/admin/redeem-code/batches, GET /api/question-bank/learning-methods, GET /api/question-bank/learning-methods/{param}, POST /api/question-bank/admin/learning-methods, POST /api/question-bank/admin/learning-methods/sort, POST /api/question-bank/admin/redeem-code/batches, POST /api/question-bank/learning-methods/{param}/complete, POST /api/question-bank/learning-methods/{param}/start
                  fix: If APIs are valid but unused, keep as low priority; if deprecated, clean docs/contracts.
      Integrated sub-guard:
        - name: question-bank-contract-enforcer
        - enabled: yes
        - script: /Users/shaotongli/Code/newaitiku/docs/skills/question-bank-contract-enforcer/scripts/question_bank_contract_guard.py
        - returncode: 0
        - command:
            /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/question-bank-contract-enforcer/scripts/question_bank_contract_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
        - output:
            题库契约守卫: final
            工作目录: /Users/shaotongli/Code/newaitiku
            Git 根目录: /Users/shaotongli/Code/newaitiku
            校验阈值: high
            题库上下文: 开启 (path-hint)
            改动文件数: 13
            目标模块: 未指定
            触达模块: question
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
            问题: 无
      Integrated sub-guard:
        - name: rbac-alignment-guard
        - enabled: yes
        - script: /Users/shaotongli/Code/newaitiku/docs/skills/rbac-alignment-guard/scripts/rbac_alignment_guard.py
        - returncode: 0
        - command:
            /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/rbac-alignment-guard/scripts/rbac_alignment_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
        - output:
            RBAC 对齐守卫: final
            工作目录: /Users/shaotongli/Code/newaitiku
            Git 根目录: /Users/shaotongli/Code/newaitiku
            校验阈值: high
            RBAC 上下文: 跳过 (no-rbac-evidence)
            改动文件数: 13
            扫描统计: backend_files=0 frontend_files=0 backend_perm_keys=0 frontend_perm_keys=0
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
            备注:
              - 未检测到 RBAC 相关上下文，本次跳过严格阻断。
            问题: 无
      Integrated sub-guard:
        - name: state-machine-alignment
        - enabled: yes
        - script: /Users/shaotongli/Code/newaitiku/docs/skills/state-machine-alignment/scripts/state_machine_guard.py
        - returncode: 0
        - command:
            /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/state-machine-alignment/scripts/state_machine_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
        - output:
            状态流守卫: final
            工作目录: /Users/shaotongli/Code/newaitiku
            Git 根目录: /Users/shaotongli/Code/newaitiku
            校验阈值: high
            状态上下文: 跳过 (no-state-machine-evidence)
            改动文件数: 13
            扫描统计: backend_files=0 frontend_files=0 backend_states=0 frontend_states=0 backend_transitions=0 frontend_transitions=0
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
            备注:
              - 未检测到状态流上下文，本次跳过严格阻断。
            问题: 无
      Integrated sub-guard:
        - name: error-code-governor
        - enabled: yes
        - script: /Users/shaotongli/Code/newaitiku/docs/skills/error-code-governor/scripts/error_code_guard.py
        - returncode: 0
        - command:
            /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/error-code-governor/scripts/error_code_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
        - output:
            错误码治理守卫: final
            工作目录: /Users/shaotongli/Code/newaitiku
            Git 根目录: /Users/shaotongli/Code/newaitiku
            校验阈值: high
            错误码上下文: 跳过 (no-error-code-evidence)
            改动文件数: 13
            扫描统计: backend_files=0 frontend_files=0 backend_codes=0 frontend_codes=0
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
            备注:
              - 未检测到错误码相关上下文，本次跳过严格阻断。
            问题: 无
      Integrated sub-guard:
        - name: fullstack-test-matrix
        - enabled: yes
        - script: /Users/shaotongli/Code/newaitiku/docs/skills/fullstack-test-matrix/scripts/fullstack_test_matrix_guard.py
        - returncode: 0
        - command:
            /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/fullstack-test-matrix/scripts/fullstack_test_matrix_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
        - output:
            全栈测试矩阵守卫: final
            工作目录: /Users/shaotongli/Code/newaitiku
            Git 根目录: /Users/shaotongli/Code/newaitiku
            校验阈值: high
            测试矩阵上下文: 开启 (test-path-hint)
            改动文件数: 13
            扫描统计: impl_files=3 test_files=2 required_scenarios=6
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
            测试矩阵:
              - 正常路径: required=yes covered=yes
                reason: 检测到实现改动，需验证主流程可用
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
              - 异常路径: required=yes covered=yes
                reason: 检测到实现改动，需验证异常分支
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
              - 边界路径: required=yes covered=yes
                reason: 检测到实现改动，需验证边界条件
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
              - 后端联动: required=yes covered=yes
                reason: 检测到后端相关改动
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
              - 前端联动: required=yes covered=yes
                reason: 检测到前端相关改动
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
              - 接口契约: required=yes covered=yes
                reason: 检测到接口契约相关改动
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
              - 数据链路: required=no covered=yes
                reason: 当前改动未强制要求
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
              - 权限场景: required=no covered=yes
                reason: 当前改动未强制要求
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
              - 状态流场景: required=no covered=yes
                reason: 当前改动未强制要求
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
              - 切流回归: required=no covered=yes
                reason: 当前改动未强制要求
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
              - 单入口回归: required=no covered=yes
                reason: 当前改动未强制要求
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py
              - 性能场景: required=no covered=yes
                reason: 当前改动未强制要求
                evidence: /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py, /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py
            问题: 无
      Integrated sub-guard:
        - name: delivery-doc-sync
        - enabled: yes
        - script: /Users/shaotongli/Code/newaitiku/docs/skills/delivery-doc-sync/scripts/delivery_doc_sync_guard.py
        - returncode: 0
        - command:
            /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/delivery-doc-sync/scripts/delivery_doc_sync_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
        - output:
            交付文档同步守卫: final
            工作目录: /Users/shaotongli/Code/newaitiku
            Git 根目录: /Users/shaotongli/Code/newaitiku
            校验阈值: high
            文档同步上下文: 开启 (task-hint)
            改动文件数: 13
            扫描统计: impl_files=3 doc_files=8 test_files=2 required_sections=6
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
            文档同步矩阵:
              - 交付总览: required=yes covered=yes
                reason: 检测到实现改动，需同步交付总览
                evidence: /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
              - 接口说明: required=yes covered=yes
                reason: 检测到 API 相关改动
                evidence: /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json, /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
              - 数据说明: required=yes covered=yes
                reason: 检测到正式表/回填/切读切写相关改动
                evidence: /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json, /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
              - 前端说明: required=yes covered=yes
                reason: 检测到前端相关改动
                evidence: /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
              - 权限说明: required=no covered=yes
                reason: 当前改动未强制要求
                evidence: /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json, /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
              - 状态流说明: required=no covered=yes
                reason: 当前改动未强制要求
                evidence: /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
              - 错误处理说明: required=no covered=yes
                reason: 当前改动未强制要求
                evidence: /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json
              - 测试说明: required=yes covered=yes
                reason: 检测到实现改动，需同步测试章节
                evidence: /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json, /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md
              - 发布说明: required=yes covered=yes
                reason: 任务描述包含发布/上线关键词
                evidence: /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md, /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md
            问题: 无
      Integrated sub-guard:
        - name: component-reuse-shared-logic-guard
        - enabled: yes
        - script: /Users/shaotongli/Code/newaitiku/docs/skills/component-reuse-shared-logic-guard/scripts/component_reuse_guard.py
        - returncode: 0
        - command:
            /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/component-reuse-shared-logic-guard/scripts/component_reuse_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
        - output:
            Component Reuse Guard: final
            Working directory: /Users/shaotongli/Code/newaitiku
            Changed files: 13
            Fail threshold: high
            Summary: 0 high, 0 medium, 0 low across 1 frontend and 1 backend files.
            Detected reusable layers: AiGenerationDialog(1), BaseFilterPanel(2), QuestionCard(1), QuestionSelectionDrawer(1), request(0), useAiMarking(1)
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
            Findings: none
      Integrated sub-guard:
        - name: cache-consistency-guard
        - enabled: no
        - output:
            Skipped because no cache or cutover-related context was detected.
      Final gate: pass
Integrated sub-guard:
  - name: requirements-freeze-guard
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/requirements-freeze-guard/scripts/requirements_freeze_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Requirements Freeze Guard: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/release-preflight-guard/scripts/release_preflight_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md --report-json .codex-runtime/reports/preflight-student-final-v2.json
  - returncode: 0
  - output:
      Release Preflight Guard: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/rollback-readiness-guard/scripts/rollback_readiness_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Rollback Readiness Guard: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/database-migration-safety-guard/scripts/database_migration_safety_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Database Migration Safety Guard: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/deployment-config-alignment/scripts/deployment_config_alignment_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Deployment Config Alignment: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/app-security-baseline-guard/scripts/app_security_baseline_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      App Security Baseline Guard: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/acceptance-criteria-builder/scripts/acceptance_criteria_builder_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Acceptance Criteria Builder: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/prd-ui-traceability-guard/scripts/prd_ui_traceability_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      PRD UI Traceability Guard: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/ux-state-completeness-checker/scripts/ux_state_completeness_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      UX State Completeness Checker: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/release-quality-gate/scripts/release_quality_gate.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Release Quality Gate: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/uat-handoff-guard/scripts/uat_handoff_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      UAT Handoff Guard: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/observability-readiness-guard/scripts/observability_readiness_guard.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Observability Readiness Guard: final
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
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/git-flow-enforcer/scripts/git_flow_enforcer.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md
  - returncode: 0
  - output:
      Git Flow Enforcer: final
      Working directory: /Users/shaotongli/Code/newaitiku
      Changed files: 0
      Fail threshold: high
      Summary: 0 high, 0 medium, 0 low
      Warnings: none
Integrated sub-guard:
  - name: release-branch-readiness-checker
  - enabled: yes
  - command: /opt/homebrew/opt/python@3.14/bin/python3.14 /Users/shaotongli/Code/newaitiku/docs/skills/release-branch-readiness-checker/scripts/release_branch_readiness_checker.py --phase final --cwd /Users/shaotongli/Code/newaitiku --fail-on high --task 学生端兑换码与订阅发布门禁复验 --changed-file /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py --changed-file /Users/shaotongli/Code/newaitiku/tests/integration/test_question_bank_core_api_pytest_suite.py --changed-file /Users/shaotongli/Code/newaitiku/app/service_modules/student_monetization.py --changed-file /Users/shaotongli/Code/newaitiku/frontend/src/views/Student/OnboardingDiagnosis.vue --changed-file /Users/shaotongli/Code/newaitiku/scripts/export_openapi.py --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-config-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-checklist-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-mvp-retrospective-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-operations-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/release/student-conversion-customer-support-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/contracts/current/openapi.json --changed-file /Users/shaotongli/Code/newaitiku/docs/system-function-manual-2026-03-26.md --changed-file /Users/shaotongli/Code/newaitiku/docs/question-bank-contract.md --report-json .codex-runtime/reports/release-branch-student-final-v2.json
  - returncode: 0
  - output:
      Release Branch Readiness Checker: final
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