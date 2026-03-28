# 当前仓库可发布目录清单（简版，2026-03-20）

## 结论

- 本次发布建议采用：`源码 + 配置 + schema.sql`
- 不要携带任何本地数据库、日志、缓存、截图、临时评审产物

## 建议保留进发布

- `app/`
- `frontend/`
  - 仅保留源码与构建配置
- `static/`
- `templates/`
- `deploy/`
- `data/schema.sql`
- `requirements.txt`
- `scripts/`
  - 仅保留实际发布或运维需要的脚本
- `.dockerignore`
- `.gitignore`

## 明确不要带进发布

- `tmp/`
- `.shared-deps/`
- `.codex-runtime/`
- `tools/logs/`
- `tests/`
- `skills/`
- `.venv/`
- `.venv-e2e/`
- `.venv313/`
- `frontend/node_modules/`
- `frontend/dist/`
- `frontend/.screenshots/`
- `frontend/.vscode/`
- `tmp_test.db`
- `tmp_test2.db`
- `tmp_test3.db`
- `tmp_test4.db`
- `tmp_verify_super.db`
- `data/question_bank.db`
- `data/question_bank.backup-*.db`
- 所有本地截图、日志、调试文件、临时 JSON / MD / TXT 产物

## 当前发布特别注意

1. 前端 Docker 构建上下文已通过 [`.dockerignore`](/Users/shaotongli/Documents/newaitiku/.dockerignore) 做了排除。
2. 后端当前仍通过 [docker-compose.prod.yml](/Users/shaotongli/Documents/newaitiku/deploy/docker-compose.prod.yml) 挂载整个仓库目录运行。
3. 所以正式发布前，仍需人工确认工作区中没有本地临时工件。

## 发群可直接复制版

```text
本次发布包建议只保留：
app/、frontend/（仅源码与构建配置）、static/、templates/、deploy/、data/schema.sql、requirements.txt、必要 scripts

本次明确不要带入发布：
tmp/、.shared-deps/、.codex-runtime/、tools/logs/、tests/、skills/、各类 .venv、frontend/node_modules/、frontend/dist/、本地 *.db、截图、日志、临时评审产物

注意：
前端构建上下文已加 .dockerignore；
后端当前仍挂载整个仓库目录，发布前请人工确认工作区干净。
```

## 参考文档

- [发布包清理检查](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-cleanup-2026-03-20.md)
- [发布包执行说明](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-execution-2026-03-20.md)
- [发布包保留 / 排除名单](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-manifest-2026-03-20.md)
