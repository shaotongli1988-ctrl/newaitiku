# Development Readiness Contract

- Contract ID: `dr-2026-03-26-074557`
- Generated At: `2026-03-26T07:45:57+08:00`
- Mode: `questionBank`
- Business Goal: skills platform release gate final guard (readiness)
- In Scope Modules: `user, knowledge, question, task`
- Out Of Scope Modules: `userAuth`
- Affected Layers: `database, backend, frontend, docs, tests, api`
- Readiness Status: `不建议进入开发`
- Action: `BLOCK_BEFORE_CODING`
- Reason: 存在 P0 高风险缺口，当前不满足安全开工条件。

## Implementation Baselines
- Roles: `super_admin, teacher, student`
- Permission Keys: `question:manage, paper:manage, analytics:view, student:manage, settings:manage, message:send`
- Question Error Codes: `QUESTION_NOT_FOUND, QUESTION_FORBIDDEN, QUESTION_VALIDATION_FAILED, QUESTION_INVALID_STATUS, QUESTION_DATABASE_ERROR`
- UI Feedback: `Toast, message-box`
- Automation Targets: `pytest-unit, pytest-integration, pytest-regression, playwright-e2e`

## questionBank Modules
- `user`: `IN_SCOPE` / extJson=`contract-outside-fields-go-to-extJson`
- `userAuth`: `OUT_OF_SCOPE` / extJson=`contract-outside-fields-go-to-extJson`
- `knowledge`: `IN_SCOPE` / extJson=`contract-outside-fields-go-to-extJson`
- `question`: `IN_SCOPE` / extJson=`contract-outside-fields-go-to-extJson`
- `task`: `IN_SCOPE` / extJson=`contract-outside-fields-go-to-extJson`