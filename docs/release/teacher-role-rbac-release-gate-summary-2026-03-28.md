# Teacher Role RBAC Release Gate Summary (2026-03-28)

- release: teacher-role-rbac
- status: READY_FOR_UAT
- action: FIX_THEN_RELEASE
- reason: 代码实现完成，需保持 release 分支干净后执行上线。

## key checks

- super admin 开通岗位后，teacher 端权限同步生效。
- recruit / teach / dual-role 三类账号权限显隐一致。
- managedStudentIds 数据范围过滤生效，无越权。

## evidence links

- acceptance: `docs/release/teacher-role-rbac-acceptance-2026-03-28.md`
- config checklist: `docs/release/teacher-role-rbac-config-checklist-2026-03-28.md`
- rollback switch: `docs/release/teacher-role-rbac-rollback-switch-2026-03-28.md`
