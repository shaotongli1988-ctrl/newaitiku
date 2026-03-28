# 学习方法模块发布文档归档（2026-03-25）

## 归档结论
- 模块状态：可提测，可上线。
- 门禁结果：`delivery-guard` 无阻断，`acceptance` 120/120 通过。
- 归档目的：为提测、发布、回滚、群通知、PR 提供单入口检索。

## 0. 总入口
- `docs/release/learning-method-release-index-2026-03-25.md`
- `docs/release/learning-method-final-release-notice-onepage-2026-03-25.md`

## 1. 提测与交接
- `docs/release/learning-method-test-handoff-2026-03-25.md`
- `docs/release/learning-method-group-message-template-2026-03-25.md`

## 2. 发布与运维
- `docs/release/learning-method-ops-release-brief-2026-03-25.md`
- `docs/release/learning-method-release-evidence-2026-03-25.md`
- `docs/release/learning-method-config-checklist-2026-03-25.md`
- `docs/release/learning-method-rollback-switch-2026-03-25.md`
- `docs/release/delivery-guard-2026-03-25-final.md`

## 3. 群公告材料
- Markdown 版：`docs/release/learning-method-enterprise-announcement-2026-03-25.md`
- 纯文本版：`docs/release/learning-method-enterprise-final-plain-2026-03-25.txt`

## 4. PR 文案材料
- 工作版：`docs/release/learning-method-pr-description-2026-03-25.md`
- 最终复制版：`docs/release/learning-method-pr-final-copy-2026-03-25.md`

## 5. 建议使用顺序
1. 提测前：先看 `learning-method-test-handoff`。
2. 发布前：看 `learning-method-ops-release-brief` + `learning-method-config-checklist`。
3. 群通知：使用 `enterprise-final-plain` 直接发送。
4. PR 合并：使用 `pr-final-copy` 直接粘贴。
5. 异常处置：按 `learning-method-rollback-switch` 执行止血与回滚。

## 6. 归档时间
- 归档日期：2026-03-25
- 归档人：Codex
