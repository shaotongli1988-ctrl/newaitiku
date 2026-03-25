# Codex 持续开发任务池

## 1) 项目上下文
- 项目名: `newaitiku`
- 目标里程碑: `2026-03-31`
- 目标分支: `codex/continuous-dev-loop`
- 关键约束:
  - 高风险改动(数据库迁移/权限/删除逻辑)先暂停确认
  - 每轮必须回填任务状态和验证证据
  - 每次提交保持原子化

## 2) 全局验收门槛 (Definition of Done)
- 构建通过: `npm --prefix /Users/shaotongli/Code/newaitiku/frontend run build`
- 单元测试通过:
  - `python3 -m pytest -q /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py -k "knowledge_tree_response_allows_wrong_count_field"`
  - `python3 -m pytest -q /Users/shaotongli/Code/newaitiku/tests/test_question_bank.py -k "dashboard_filtering"`
  - `npm --prefix /Users/shaotongli/Code/newaitiku/frontend run test -- /Users/shaotongli/Code/newaitiku/frontend/src/utils/studentOnboarding.test.js`
- 静态检查通过: `python3 -m compileall /Users/shaotongli/Code/newaitiku/app`
- 文档同步完成: `docs/codex/TODO.codex.md` 已更新

## 3) 任务池 (按优先级排序)
| ID | 优先级 | 类型 | 任务描述 | 可执行验收标准 | 依赖 | 状态 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0-01 | P0 | docs | 固化持续开发主提示词并完成首次演练记录 | `docs/codex/codex-continuous-dev-prompt.md` 存在且可直接粘贴使用 | none | done | `docs/codex/codex-continuous-dev-prompt.md` |
| P0-02 | P0 | docs | 建立任务池模板与可执行任务池文件 | `docs/codex/TODO.codex.template.md` 与 `docs/codex/TODO.codex.md` 存在 | P0-01 | done | `docs/codex/TODO.codex.template.md` |
| P0-03 | P0 | chore | 在 codex 分支启动首次连续循环(至少完成 1 个真实代码任务) | 至少 1 条任务状态从 `todo/doing` 变为 `done` 且附验证证据 | P0-02 | done | `frontend/src/utils/studentOnboarding.js`、`frontend/src/utils/studentOnboarding.test.js`、`npm --prefix frontend run test -- frontend/src/utils/studentOnboarding.test.js` |
| P1-01 | P1 | test | 为连续循环补充标准验证命令清单 | 在 TODO 的 DoD 中填充项目可执行命令 | P0-03 | done | `npm --prefix frontend run build`、`python3 -m compileall app`、2 条后端最小回归用例 |
| P1-02 | P1 | docs | 沉淀阻塞问题模板和决策 SLA | Blockers 表至少含 1 条示例和处理规则 | P1-01 | todo | 待补充 |
| P1-03 | P1 | chore | 收敛守卫高优先告警（API 契约漂移与复用守卫噪音） | 在不依赖 break-glass 的情况下通过 `unified_delivery_guard --phase batch/final` | P0-03 | todo | `BG-303`、`BG-304` 临时豁免记录 |

状态只允许使用: `todo` / `doing` / `blocked` / `done`

## 4) 阻塞清单 (Blockers)
| 时间 | 任务ID | 阻塞描述 | 需要谁决策 | 临时假设 | 到期时间 |
| --- | --- | --- | --- | --- | --- |
| 2026-03-26 07:39 | P1-03 | `api-schema-drift-checker` 报告历史 API 漂移，与本轮 onboarding util 修复不直接相关 | 项目Owner | 作为独立治理任务处理，不阻塞本轮小修复收口 | 2026-03-27 |
| 2026-03-26 07:39 | P1-03 | `delivery-doc-sync` 与 `fullstack-test-matrix` 对“小改动”要求完整交付章节与场景标签，当前模板未沉淀豁免规则 | 项目Owner | 先在 P1-03 增加“微小改动门槛”治理策略 | 2026-03-27 |
| 2026-03-26 07:46 | P1-03 | `python3 -m pytest -q tests/test_openapi_schema_scope.py` 失败，断言 `/api/question-bank/knowledge/{knowledge_id}` 不在 OpenAPI paths | 项目Owner | 先不纳入 P1-01 基线，归入 P1-03 做契约漂移收敛 | 2026-03-27 |
| 2026-03-26 07:50 | P1-03 | `P1-01` 的 `unified_delivery_guard batch/final` 需临时 `BG-304` 跳过 API schema 子守卫 | 项目Owner | 保留豁免记录并在 P1-03 完成后撤销 | 2026-03-27 |

## 5) 运行日志 (Run Log)
| 时间 | 本轮选择任务 | 改动文件 | 验证命令 | 结果 | 下一步 |
| --- | --- | --- | --- | --- | --- |
| 2026-03-26 07:39 | P0-01 | `docs/codex/codex-continuous-dev-prompt.md` | `n/a` | pass | P0-02 |
| 2026-03-26 07:39 | P0-02 | `docs/codex/TODO.codex.template.md`, `docs/codex/TODO.codex.md` | `n/a` | pass | P0-03 |
| 2026-03-26 07:40 | P0-03 | `frontend/src/utils/studentOnboarding.js`, `frontend/src/utils/studentOnboarding.test.js` | `npm --prefix /Users/shaotongli/Code/newaitiku/frontend run test -- /Users/shaotongli/Code/newaitiku/frontend/src/utils/studentOnboarding.test.js` | pass(8/8) | P1-01 |
| 2026-03-26 07:41 | P0-03 | `docs/codex/three-stage-routing-p0-03.md`, `docs/codex/unified-delivery-p0-03-start.md`, `docs/codex/unified-delivery-p0-03-batch.md`, `docs/codex/unified-delivery-p0-03-final.md` | `three_stage_orchestrator + unified_delivery_guard(start/batch/final)` | pass(使用 break-glass: BG-303) | P1-03 |
| 2026-03-26 07:46 | P1-01 | `docs/codex/TODO.codex.md` | `npm --prefix frontend run build` + `python3 -m compileall app` + `python3 -m pytest -q tests/test_question_bank.py -k "knowledge_tree_response_allows_wrong_count_field"` + `python3 -m pytest -q tests/test_question_bank.py -k "dashboard_filtering"` | pass | P1-02 |
| 2026-03-26 07:50 | P1-01 | `docs/codex/three-stage-routing-p1-01.md`, `docs/codex/unified-delivery-p1-01-start.md`, `docs/codex/unified-delivery-p1-01-batch.md`, `docs/codex/unified-delivery-p1-01-final.md` | `three_stage_orchestrator + unified_delivery_guard(start/batch/final)` | pass(使用 break-glass: BG-304) | P1-02 |

## 6) 提交规范
- Commit 格式: `<type>(<scope>): <subject>`
- 每次提交必须原子化: 一个任务一条提交
- 提交前必须回填任务状态、验证证据、运行日志
