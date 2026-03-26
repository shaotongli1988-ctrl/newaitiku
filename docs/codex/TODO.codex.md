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
| P1-02 | P1 | docs | 沉淀阻塞问题模板和决策 SLA | Blockers 表至少含 1 条示例和处理规则 | P1-01 | done | `docs/codex/blocker-decision-sla.md` |
| P1-03 | P1 | chore | 收敛守卫高优先告警（API 契约漂移与复用守卫噪音） | 在不依赖 break-glass 的情况下通过 `unified_delivery_guard --phase batch/final` | P0-03 | done | `frontend/src/api/contracts.ts`、`tests/test_openapi_schema_scope.py`、`docs/codex/unified-delivery-p1-03-batch.md`、`docs/codex/unified-delivery-p1-03-final.md` |
| P1-04 | P1 | docs | 清算遗留阻塞并固化微小改动门槛 | 全量 API 漂移复验为 0 且 Blockers/Run Log 回填治理证据 | P1-03 | done | `docs/codex/api-schema-drift-p1-04-final.md`、`docs/codex/blocker-decision-sla.md`、`docs/codex/three-stage-routing-p1-04.md` |
| P1-05 | P1 | docs | 收敛文档治理场景的守卫路径误报 | `unified_delivery_guard --phase final` 在文档治理样本中无 LOW 误报 | P1-04 | done | `docs/codex/three-stage-handoff-p1-05.md`、`docs/codex/drift-baseline-p1-05-final.md`、`docs/codex/unified-delivery-p1-05-final.md` |
| P1-06 | P1 | test | 复验全局 DoD 基线命令稳定性 | DoD 5 条命令在同一轮执行全部通过并形成证据 | P1-05 | done | `docs/codex/dod-baseline-p1-06.md`、`docs/codex/unified-delivery-p1-06-final.md` |
| P1-07 | P1 | docs | 阻塞清单显式归档并关闭存量项 | Blockers 表含状态列且历史阻塞全部标记为 `closed` | P1-06 | done | `docs/codex/blocker-archive-p1-07.md`、`docs/codex/TODO.codex.md`、`docs/codex/unified-delivery-p1-07-final.md` |

状态只允许使用: `todo` / `doing` / `blocked` / `done`

## 4) 阻塞清单 (Blockers)
| 时间 | 任务ID | 阻塞描述 | 需要谁决策 | 临时假设 | 到期时间 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-03-26 07:39 | P1-03 | `api-schema-drift-checker` 报告历史 API 漂移，与本轮 onboarding util 修复不直接相关 | 项目Owner | 已在 `P1-04` 执行全量复验，`docs/codex/api-schema-drift-p1-04-final.md` 显示 `Drift issues: none`（2026-03-26 11:52） | 2026-03-27 | closed |
| 2026-03-26 07:39 | P1-03 | `delivery-doc-sync` 与 `fullstack-test-matrix` 对“小改动”要求完整交付章节与场景标签，当前模板未沉淀豁免规则 | 项目Owner | 已在 `docs/codex/blocker-decision-sla.md` 新增“微小改动门槛（治理补充）”并落地执行规则（2026-03-26 11:52） | 2026-03-27 | closed |
| 2026-03-26 07:46 | P1-03 | `python3 -m pytest -q tests/test_openapi_schema_scope.py` 失败，断言 `/api/question-bank/knowledge/{knowledge_id}` 不在 OpenAPI paths | 项目Owner | 已修复为 camelCase 路径参数断言并补齐异常路径测试，`2026-03-26 11:40` 验证通过 | 2026-03-27 | closed |
| 2026-03-26 07:50 | P1-03 | `P1-01` 的 `unified_delivery_guard batch/final` 需临时 `BG-304` 跳过 API schema 子守卫 | 项目Owner | 已在 `P1-03` 真实修复后完成替代验证，`2026-03-26 11:40` 可撤销豁免 | 2026-03-27 | closed |
| 2026-03-26 08:04 | P1-03 | `P1-02` 的 `unified_delivery_guard batch/final` 需临时 `BG-305` 跳过 API schema 子守卫 | 项目Owner | 已在 `P1-03` 真实修复后完成替代验证，`2026-03-26 11:40` 可撤销豁免 | 2026-03-27 | closed |
| 2026-03-26 11:53 | P1-04 | 文档治理任务执行 `unified_delivery_guard final` 时出现 2 条 LOW 级跨层提醒（前端/扩展证据） | 项目Owner | 已在 `P1-05` 通过中性证据命名收敛误报，`2026-03-26 13:52` 复验 `final` 为 `Warnings: none` | 2026-03-27 | closed |

## 5) 运行日志 (Run Log)
| 时间 | 本轮选择任务 | 改动文件 | 验证命令 | 结果 | 下一步 |
| --- | --- | --- | --- | --- | --- |
| 2026-03-26 07:39 | P0-01 | `docs/codex/codex-continuous-dev-prompt.md` | `n/a` | pass | P0-02 |
| 2026-03-26 07:39 | P0-02 | `docs/codex/TODO.codex.template.md`, `docs/codex/TODO.codex.md` | `n/a` | pass | P0-03 |
| 2026-03-26 07:40 | P0-03 | `frontend/src/utils/studentOnboarding.js`, `frontend/src/utils/studentOnboarding.test.js` | `npm --prefix /Users/shaotongli/Code/newaitiku/frontend run test -- /Users/shaotongli/Code/newaitiku/frontend/src/utils/studentOnboarding.test.js` | pass(8/8) | P1-01 |
| 2026-03-26 07:41 | P0-03 | `docs/codex/three-stage-routing-p0-03.md`, `docs/codex/unified-delivery-p0-03-start.md`, `docs/codex/unified-delivery-p0-03-batch.md`, `docs/codex/unified-delivery-p0-03-final.md` | `three_stage_orchestrator + unified_delivery_guard(start/batch/final)` | pass(使用 break-glass: BG-303) | P1-03 |
| 2026-03-26 07:46 | P1-01 | `docs/codex/TODO.codex.md` | `npm --prefix frontend run build` + `python3 -m compileall app` + `python3 -m pytest -q tests/test_question_bank.py -k "knowledge_tree_response_allows_wrong_count_field"` + `python3 -m pytest -q tests/test_question_bank.py -k "dashboard_filtering"` | pass | P1-02 |
| 2026-03-26 07:50 | P1-01 | `docs/codex/three-stage-routing-p1-01.md`, `docs/codex/unified-delivery-p1-01-start.md`, `docs/codex/unified-delivery-p1-01-batch.md`, `docs/codex/unified-delivery-p1-01-final.md` | `three_stage_orchestrator + unified_delivery_guard(start/batch/final)` | pass(使用 break-glass: BG-304) | P1-02 |
| 2026-03-26 08:04 | P1-02 | `docs/codex/blocker-decision-sla.md`, `docs/codex/TODO.codex.md`, `docs/codex/three-stage-routing-p1-02.md`, `docs/codex/unified-delivery-p1-02-start.md`, `docs/codex/unified-delivery-p1-02-batch.md`, `docs/codex/unified-delivery-p1-02-final.md` | `three_stage_orchestrator + unified_delivery_guard(start/batch/final)` | pass(使用 break-glass: BG-305) | P1-03 |
| 2026-03-26 11:40 | P1-03 | `frontend/src/api/contracts.ts`, `tests/test_openapi_schema_scope.py`, `docs/codex/three-stage-routing-p1-03.md`, `docs/codex/unified-delivery-p1-03-batch.md`, `docs/codex/unified-delivery-p1-03-final.md`, `docs/codex/TODO.codex.md` | `python3 -m pytest -q tests/test_openapi_schema_scope.py` + `unified_delivery_guard --phase batch/final` | pass(无 break-glass) | 等待下一条任务 |
| 2026-03-26 11:53 | P1-04 | `docs/codex/three-stage-routing-p1-04.md`, `docs/codex/api-schema-drift-p1-04-final.md`, `docs/codex/blocker-decision-sla.md`, `docs/codex/unified-delivery-p1-04-batch.md`, `docs/codex/unified-delivery-p1-04-final.md`, `docs/codex/TODO.codex.md` | `schema_drift_guard --phase final --report-md docs/codex/api-schema-drift-p1-04-final.md` + `unified_delivery_guard --phase batch/final` | warn(2 条 LOW 提醒已解释，`frontend: n/a`, `extJson: n/a`) | 等待下一条任务 |
| 2026-03-26 13:52 | P1-05 | `docs/codex/three-stage-handoff-p1-05.md`, `docs/codex/drift-baseline-p1-05-final.md`, `docs/codex/blocker-decision-sla.md`, `docs/codex/unified-delivery-p1-05-batch.md`, `docs/codex/unified-delivery-p1-05-final.md`, `docs/codex/TODO.codex.md` | `schema_drift_guard --phase final --report-md docs/codex/drift-baseline-p1-05-final.md` + `unified_delivery_guard --phase batch/final` | pass(无 warnings) | 等待下一条任务 |
| 2026-03-26 13:58 | P1-06 | `docs/codex/three-stage-handoff-p1-06.md`, `docs/codex/dod-baseline-p1-06.md`, `docs/codex/unified-delivery-p1-06-batch.md`, `docs/codex/unified-delivery-p1-06-final.md`, `docs/codex/TODO.codex.md` | `npm --prefix frontend run build` + `python3 -m pytest -q tests/test_question_bank.py -k "knowledge_tree_response_allows_wrong_count_field"` + `python3 -m pytest -q tests/test_question_bank.py -k "dashboard_filtering"` + `npm --prefix frontend run test -- frontend/src/utils/studentOnboarding.test.js` + `python3 -m compileall app` + `unified_delivery_guard --phase batch/final` | pass(DoD 全量复验通过) | 等待下一条任务 |
| 2026-03-26 14:05 | P1-07 | `docs/codex/three-stage-handoff-p1-07.md`, `docs/codex/blocker-archive-p1-07.md`, `docs/codex/unified-delivery-p1-07-batch.md`, `docs/codex/unified-delivery-p1-07-final.md`, `docs/codex/TODO.codex.md` | `unified_delivery_guard --phase batch/final` | pass(Blockers 全量 `closed`) | 等待下一条任务 |

## 6) 提交规范
- Commit 格式: `<type>(<scope>): <subject>`
- 每次提交必须原子化: 一个任务一条提交
- 提交前必须回填任务状态、验证证据、运行日志
