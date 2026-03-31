# P0/P1 收口发布记录（2026-03-31）

## Before Starting
- Scope: 鉴权收口、全局超管口令治理、时间窗回归修复、门禁脚本依赖补齐。
- Non-goals: 不做数据库 schema 结构变更，不做业务功能扩展。
- Affected modules: `app/auth.py`、`app/db.py`、`frontend/src/api/request.js`、`frontend/src/utils/devLogin.js`、`tests/**`、`scripts/software_delivery_guard.py`。
- Acceptance criteria: 未登录业务 API 返回 `401`；仅 dev 显式开关允许 header actor；全局超管口令首启必填且重启不回刷；时间窗用例与日期解耦。
- Source of truth: 后端接口行为 + 回归测试结果 + 本文档发布与回滚说明。

## Config Alignment
| Config Item | Dev/Test | Prod | Notes |
| --- | --- | --- | --- |
| `QUESTION_BANK_SUPER_ADMIN_PASSWORD` | 必填，测试环境使用安全测试值 | 必填，生产必须强口令 | 首启缺失应阻断启动 |
| `QB_ALLOW_HEADER_ACTOR_FALLBACK` | 默认关闭，仅联调时显式 `true` | 固定关闭 | 仅允许开发联调，不作为生产身份来源 |
| `QB_COOKIE_SECURE` | 按环境配置 | 建议开启 | 与反向代理/HTTPS 对齐 |

## Feature Flag / Kill Switch
- Feature flag: `QB_ALLOW_HEADER_ACTOR_FALLBACK`
- Default: `false`
- Emergency mitigation:
  - 若联调流程受阻，可在 `dev` 临时开启；
  - 若发现越权风险，立即关闭并仅保留 token/cookie 登录态访问。

## Rollout / Rollback
- Rollout:
  1. 部署前注入 `QUESTION_BANK_SUPER_ADMIN_PASSWORD`。
  2. 执行回归：`unit/integration/regression`。
  3. 执行门禁：`python3 scripts/software_delivery_guard.py --phase final --task "smoke"`。
- Rollback:
  1. 回滚应用版本到上一稳定版本。
  2. 保持数据库不回滚（本次无 schema 变更）。
  3. 关闭 `QB_ALLOW_HEADER_ACTOR_FALLBACK`，恢复仅 token/cookie。

## Verification Evidence
- `./tools/bin/run-tests.sh --suite unit` 通过。
- `./tools/bin/run-tests.sh --suite integration` 通过。
- `./tools/bin/run-tests.sh --suite regression` 通过。
- `python3 scripts/software_delivery_guard.py --phase final --task "smoke"` 可执行并输出结构化结果。

## Residual Risk And Owner
- Residual item: `release-branch-readiness-checker` 会在脏工作区提示中风险。
- Owner: 研发负责人（当前分支 owner）。
- Mitigation: 发布前清理工作区并拆分无关改动后重跑门禁。
- Deadline: 2026-04-01 发布窗口前完成。
