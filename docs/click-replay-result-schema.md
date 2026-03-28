# 真点击结果 JSON Schema

- Schema 文件：`docs/click-replay-result-schema.json`
- 结果产物命名：`<role>-click-replay-result-YYYY-MM-DD.json`
- 报告产物命名：`<role>-click-replay-report-YYYY-MM-DD.md`

## 固定字段
- `mode`：固定为 `python-playwright-true-click-replay`
- `role`：`student|teacher|super_admin`
- `steps[]`：固定包含
  - `name`
  - `status`
  - `startedAt`
  - `endedAt`
  - `artifacts`
  - `error`
- `issues` + `totalIssues`：统一问题聚合
- `linkageMatrix`：统一三端联调矩阵
  - `superAdminToTeacher`
  - `teacherToStudent`
  - `studentToTeacher`

## 判定口径
- 任一步骤 `FAIL` 即视为该角色回放失败。
- 联调矩阵任一链路非 `PASS`，汇总报告判定为“联调未收口”。
