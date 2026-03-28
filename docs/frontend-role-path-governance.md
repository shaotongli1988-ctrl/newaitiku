# Frontend Role Path Governance

## Canonical User Store Fields

- `role`: `super_admin | teacher | student`
- `permissions`: permission key list
- `examCategoryCode`
- `jointExamGroupCode`
- `availableExamCategories`
- `availableJointExamGroups`

## Initialize Strategy

- Student path (`/student/*`): initialize from `GET /api/question-bank/student/dashboard`.
- Management path (`/admin/*` and `/teacher/*`): initialize from `GET /api/question-bank/auth/me`.

## API Migration Note

- Legacy adapter `frontend/src/api/questionBank.js` has been removed.
- New code must import from `frontend/src/api/services/questionBank.js` directly.
- Removal window:
  - Deprecation grace period: 2026-03-18 to 2026-06-30.
  - Planned removal: first frontend release after 2026-07-01, once no imports remain.

## Role Prefix Isolation

- `/admin/*` only for `super_admin`
- `/teacher/*` only for `teacher`
- `/student/*` only for `student`

When role mismatch happens, router guard forces redirect to the role home route.
Example: student opens `/teacher/questions`, then redirects to `/student/home`.

## Permission-Driven Sidebar

`DefaultLayout` builds sidebar items from route metadata and hides unauthorized items.

- `question:manage` controls `题库管理`
- `analytics:view` controls `学情管理`

If a teacher has no `analytics:view`, `学情管理` is not rendered.

## Unified FilterPanel

Shared component: `src/components/common/BaseFilterPanel.vue`

- Collapsible panel layout
- Common fields: `keyword`, `examCategoryCode`, `jointExamGroupCode`, `subjectCode`
- Auto linkage: changing `examCategoryCode` updates available `jointExamGroupCode` options
- Subject filtering supports category/group linkage and PUBLIC subject compatibility
- Applied pages:
  - `教师 / 题库管理`
  - `教师 / 手动组卷选题抽屉`

## Teacher Real API Integration

- `教师 / 题库管理` now uses `GET /api/question-bank/questions` with server-side pagination.
- `教师 / 题库管理` supports edit and status transitions via:
  - `GET /api/question-bank/questions/{question_id}`
  - `PUT /api/question-bank/questions/{question_id}`
  - `POST /api/question-bank/questions/{question_id}/status/{target_status}`
- `教师 / 题库管理` detail drawer now includes:
  - Fixed field section
  - Status transition shortcuts
  - Options display
  - `extJson` overview and raw JSON
  - Review timeline and rejected-node pipeline (aligned with legacy static page behavior)
- `教师 / 学情管理` now uses:
  - `GET /api/question-bank/analytics/summary`
  - `GET /api/question-bank/analytics/records`
  - `GET /api/question-bank/analytics/export`
- `教师 / 学情管理` current toolbar and drill-down controls include:
  - `classId`
  - `studentUserId`
  - `subjectCodes / subjectCode`
  - `knowledgePathNodeId / knowledgeId`
- `教师 / 学情管理` current page does not depend on legacy static `analytics.js`; the active implementation lives in `frontend/src/views/Teacher/Analytics.vue`.
