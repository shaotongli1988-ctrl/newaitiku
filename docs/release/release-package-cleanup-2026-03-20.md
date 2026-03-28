# 发布包清理检查（2026-03-20）

## 一、目标

- 用于发布前确认不将本地临时文件、日志、测试数据库、依赖缓存带入发布包。

## 二、当前发现的本地非发布工件

### 临时数据库

- `tmp_test.db`
- `tmp_test2.db`
- `tmp_test3.db`
- `tmp_test4.db`
- `tmp_verify_super.db`
- `data/question_bank.db`
- `data/question_bank.backup-2026-03-17-1773703724170665410.db`
- `data/question_bank.backup-4821d67a.db`
- `data/question_bank.backup-be39ad29.db`
- `tmp/test_index_plan.db`
- `tmp/tmp_ai_parser_debug.db`
- `tmp/adaptive_poison.db`
- `tmp/debug_ui_case.db`

### 临时输出与评审产物

- `tmp/`
- `tmp/reuse-blueprints/`
- `tmp/skill-sync/`
- `tmp/teacher_preview_20260320/`
- `tmp/*.md`
- `tmp/*.json`
- `tmp/*.txt`
- `tmp/*.log`

### 本地依赖缓存

- `.shared-deps/`

### 本地日志

- `tools/logs/`

### 本地运行态目录

- `.codex-runtime/`

## 三、发布建议

1. 构建或打包时仅包含真正交付目录：
   - `app/`
   - `frontend/`
   - `static/`
   - `templates/`
   - `data/schema.sql`
   - `deploy/`
   - `scripts/` 中确需发布的脚本
2. 不要将 `tmp/`、`.shared-deps/`、`tools/logs/`、本地 `.db` 一并拷入产物。
3. 若发布方式依赖仓库工作区，请先人工确认忽略规则和打包清单。
4. 当前 Docker / compose 发布方式请同时参考 [发布包执行说明](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-execution-2026-03-20.md)。
5. 实际打包时请直接参考 [发布包保留 / 排除名单](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-manifest-2026-03-20.md)。

## 四、发布前确认项

- [ ] 不携带 `tmp/`
- [ ] 不携带 `.shared-deps/`
- [ ] 不携带 `tools/logs/`
- [ ] 不携带任何本地测试数据库或备份数据库
- [ ] 不携带 `.codex-runtime/`
- [ ] 仅保留正式交付所需目录和配置

## 五、责任归属

- 研发：确认打包目录与忽略规则
- 运维：确认发布产物内容
- 测试：确认未误带测试工件

## 六、签收

- 研发确认：__________
- 运维确认：__________
- 测试确认：__________
- 发布包检查结论：__________
