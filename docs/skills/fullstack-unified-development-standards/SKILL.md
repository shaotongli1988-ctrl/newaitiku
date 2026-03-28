---
name: fullstack-unified-development-standards
description: 开发中全端统一交付单一入口技能。适用于开发实施阶段的数据库、后端、接口、前端、权限、状态、校验、错误、文档、测试统一改动；内置题库模块子契约与自动守卫流程，负责在开发中持续防跑偏，并把设计阶段约定的高并发、数据一致性、性能容量、部署稳定性与安全权限控制点真正落地，适合“开发中别跑偏”，通常由 `$three-stage-skill-orchestrator` 路由进入本阶段。
---

# 全端统一交付（单一入口）

## 定位

- 本技能已合并并接管以下能力：严格对齐、统一新增、零漂移、实现层收敛、题库对齐。
- 本技能是三阶段体系中的“开发中总技能”，负责把已定义好的需求稳定落成代码与文档。
- 所有项目默认直接调用本技能，不再并行叠加其他通用全端技能。
- 统一治理说明见 [references/skill-governance.md](references/skill-governance.md)。

## 能力特性（已合并）

- 严格对齐特性：14 个影响面必须逐项核对，文案/图标/按钮/注释/测试同样纳入对齐。
- 统一新增特性：按“名字 -> 类型 -> 权限 -> 状态 -> 接口 -> 页面 -> 校验 -> 文档 -> 自检”的顺序执行。
- 零漂移特性：字段、状态、权限、异常、目录结构、文档与测试全链路一致。
- 实现层收敛特性：重复实现优先抽取为公共组件/Hook/工具/request/基础模块，避免页面直写请求与结构各自为政。
- 正确实现优先特性：禁止通过补丁式兼容、外围胶水、双轨并存来迁就旧坏实现；已有更正确的公共层、模型或组件时，应直接替换旧实现并完成收敛。
- 单入口收敛特性：发现前端/服务/脚本存在双入口、双实现、双读写时，默认删除旧入口并收敛到唯一主入口，不保留长期并存分支。
- 样式变量统一特性：CSS 变量、设计 token、主题变量、颜色/间距/圆角/阴影等前端样式基线应在开发中统一收敛，避免页面各写一套样式常量。
- 题库特性：固定 5 模块契约、`extJson` 扩展规则、ID 关联规则、`{ code, message, data }` 响应包。
- 热状态拆表特性：命中高频状态、报告型数据、撤回历史、发送历史、学习记录等场景时，按“建表/索引 -> 双写 -> 正式表优先读 -> 删除 legacy 写入 -> 下线 fallback”顺序收口。
- 风险落地特性：设计阶段已经定义的并发、一致性、性能、部署、安全控制点必须在代码、配置、文档与测试中一并落地，不能只写在方案里。

能力细则见 [references/capability-profiles.md](references/capability-profiles.md)。

## 实施阶段必须做实的五类问题

以下问题在本阶段不是“提醒一下”，而是要通过真实实现、测试与守卫证据落地。

1. 高并发、超卖、重复下单
   - 实施要求：落地幂等键/防重机制、库存扣减一致性、热点隔离、限流降级、压测或基准验证证据
2. 数据错误、事务不对
   - 实施要求：落地事务边界、状态流、异常回滚、补偿逻辑、接口与数据模型一致性测试
3. 慢查询、数据库崩掉
   - 实施要求：落地索引、分页、缓存、慢 SQL 优化、批量查询治理、容量验证证据
4. 部署不上、线上环境炸
   - 实施要求：落地配置解耦、环境变量模板、版本/脚本匹配、监控埋点、回滚与止血文档
5. 安全漏洞、越权
   - 实施要求：落地后端鉴权、前端权限显隐、输入校验、输出转义、敏感信息治理与权限回归测试

共享口径见 [/Users/shaotongli/.codex/skills/three-stage-skill-orchestrator/references/five-risk-three-stage-control-template.md](/Users/shaotongli/.codex/skills/three-stage-skill-orchestrator/references/five-risk-three-stage-control-template.md)。本阶段只取其中“开发中控制点”和“阻断规则”。

## 触发场景

- 任何涉及数据库、后端、接口、前端页面、权限、状态、校验、错误、文档、测试的全端变更。
- 需要把并发、一致性、性能、部署、安全方案变成真实实现与测试证据。
- 常见触发词：`一键开发`、`全端统一`、`前后端一致`、`零漂移`、`统一新增`、`新增字段`、`新增接口`、`新增页面`、`新增按钮`、`新增状态`、`所有端完全一致`、`九端对齐检查`、`十端对齐检查`、`自动对齐检查`、`开发中别跑偏`、`实现阶段总入口`、`边开发边校验`、`CSS 变量统一`、`design token 统一`、`样式变量统一`、`主题变量统一`。

## 快速调用

- 推荐说法：`用开发中总技能开始做，边开发边对齐，别跑偏。`
- 推荐说法：`用开发中总技能处理这个需求，按全端统一方式落地。`
- 推荐说法：`开始真实实现和联调，进入开发中阶段。`
- 推荐说法：`把 CSS 变量、design token、主题样式统一都放到开发中总技能里收敛。`
- 路由说法：`让 $three-stage-skill-orchestrator 先判断阶段，再进入开发中实施。`
- 阶段切换信号：如果还在定义范围、验收和方案，先回到 `software-development-readiness-governance`；如果代码已基本完成并准备提测，切到 `$software-delivery-unified-governance`。

统一三阶段调用模板见 [/Users/shaotongli/.codex/skills/software-development-readiness-governance/references/stage-invocation-templates.md](/Users/shaotongli/.codex/skills/software-development-readiness-governance/references/stage-invocation-templates.md)。

## 契约模式（先选后改）

1. `questionBank` 模式
   - 仅用于题库新架构模块：`user`、`userAuth`、`knowledge`、`question`、`task`。
   - 响应包固定为 `{ code, message, data }`。
   - 只允许修改用户指定模块，额外业务字段统一进入 `extJson`。
2. `global` 模式
   - 适用于其他项目或非题库模块。
   - 响应包、状态流、角色体系遵循当前项目全局契约。

## 冲突优先级

1. 用户在当前任务中的明确要求。
2. `questionBank` 固定契约。
3. 本技能统一编排规则。
4. 已批准且带截止时间的阶段性兼容窗口或豁免规则。

## 数据建模非协商规则

- `extJson` 不再承载高频业务状态。
- 任何需要并发写安全的状态必须入表。
- 任何需要幂等的写接口必须有数据库唯一约束。
- 任何报告型数据如果要分页、统计、筛选，不能只存 JSON。
- 任何撤回、发送历史、报告详情、学习记录等热路径数据，不允许长期依赖 legacy JSON fallback。
- 发现双入口时，不允许以“先保留旧入口再说”作为默认方案；应明确唯一入口并同步清理旧路由、旧模板、旧构建入口与旧文档。

实现要求：

- 命中上述场景时，优先修改表结构、索引、唯一键、Repository 和事务边界。
- 不允许仅通过 if/else、内存缓存、先查再写、额外 JSON 字段来替代正式建模。
- 兼容期允许双写，但最终读路径必须切回正式表，不得长期依赖热状态 JSON。
- 兼容期必须同时具备 backfill/审计方案；没有一致性校验脚本的双写，不算完整迁移方案。
- 进入“去双入口”或“去双读写”收口阶段后，应同步删除 seed/default/fallback 里对旧入口的隐式依赖。

## 正确实现优先规则

- 不允许为了少改存量代码，采用补丁式兼容、外围适配、额外别名、双轨分支、胶水层包裹等方式继续堆在旧坏实现之上。
- 已有更正确的公共层、统一模型、标准接口、标准组件或更干净的旧实现时，本次改动应直接迁移并替换旧路径，不得新旧并挂继续扩散。
- 发现存量实现本身方向错误、抽象过时或明显劣于当前统一方案时，应优先修正旧实现，而不是让新代码反向兼容旧问题。
- 任何“先兼容一下后面再收”都必须被视为例外，不得作为默认开发策略。

仅以下场景允许阶段性兼容：

- 数据库迁移、灰度切流、双写切读等有明确收口方案的过渡窗口。
- 外部依赖、第三方接口、历史客户端短期内无法同步切换的受限窗口。
- 紧急故障止血、线上回滚保护等必须先恢复服务的临时窗口。

命中例外时，仍必须同时满足：

- 有明确最终正确方案，而不是无限期保留临时实现。
- 有负责人、范围、截止时间和清理动作。
- 在豁免或报告中显式记录，不能静默留下。
- 一旦窗口结束，优先删除兼容代码并完成替换收敛。

## 守卫脚本（强制）

1. 首次编辑前运行：
`python3 scripts/unified_delivery_guard.py --phase start --task "<用户需求>"`
2. 每个主要批次后运行：
`python3 scripts/unified_delivery_guard.py --phase batch`
3. 最终交付前运行：
`python3 scripts/unified_delivery_guard.py --phase final`

主守卫统一阻断阈值：

- 默认 `--fail-on auto`：`start` 不阻断，`batch/final` 对 `high` 阻断。
- 可按需覆盖：`--fail-on none|high|medium|low`。

主守卫会自动联动同级子技能：

- `api-schema-drift-checker`（`scripts/schema_drift_guard.py`）：API 契约防漂移检查。
- `question-bank-contract-enforcer`（`scripts/question_bank_contract_guard.py`）：题库固定契约检查（五模块、响应包、extJson、模块边界）。
- `rbac-alignment-guard`（`scripts/rbac_alignment_guard.py`）：RBAC 权限对齐检查（角色、权限键、后端鉴权、前端显隐）。
- `state-machine-alignment`（`scripts/state_machine_guard.py`）：状态流统一检查（状态集合、流转边、按钮策略、前后端映射）。
- `error-code-governor`（`scripts/error_code_guard.py`）：错误码统一治理检查（命名空间、异常映射、前后端错误语义、错误键一致性）。
- `fullstack-test-matrix`（`scripts/fullstack_test_matrix_guard.py`）：全栈联动测试矩阵检查（必测场景生成、漏测识别、补测建议）。
- `delivery-doc-sync`（`scripts/delivery_doc_sync_guard.py`）：交付文档同步检查（README/接口/状态/权限/测试/发布说明同步与漂移拦截）。
- `component-reuse-shared-logic-guard`（`scripts/component_reuse_guard.py`）：实现层收敛检查（公共组件/Hook/工具/request/分页/基础实体统一与重复实现抽取）。

命中以下主题时，默认把对应控制点纳入实现清单，不需要再次确认：

- 命中“高并发 / 超卖 / 重复下单”时，自动把幂等、防重、库存一致性与限流降级纳入必做项
- 命中“事务 / 数据错误 / 一致性”时，自动把事务边界、状态流、回滚语义与补偿逻辑纳入必做项
- 命中“慢查询 / 热点 SQL / 数据库风险”时，自动把索引、分页、缓存、批量化与性能验证纳入必做项
- 命中“部署 / 环境 / 发布 / 回滚”时，自动把配置模板、脚本匹配、监控埋点与回滚资料纳入必做项
- 命中“安全 / 越权 / 权限”时，自动把后端鉴权、前端显隐、校验与安全回归纳入必做项

如需显式传参给子守卫，可在主命令追加：

- `--fail-on <auto|none|high|medium|low>`
- `--api-openapi <path-or-glob>`
- `--api-producer <path-or-glob>`
- `--api-consumer <path-or-glob>`
- `--api-alias-map <json-file>`
- `--api-strip-prefix <prefix>`
- `--api-report-md <path>`
- `--api-report-json <path>`
- `--qb-module <module>`
- `--qb-force`
- `--qb-report-md <path>`
- `--qb-report-json <path>`
- `--rbac-role <role>`
- `--rbac-permission-key <key>`
- `--rbac-force`
- `--rbac-report-md <path>`
- `--rbac-report-json <path>`
- `--sm-state <state>`
- `--sm-transition <from>><to>`
- `--sm-force`
- `--sm-report-md <path>`
- `--sm-report-json <path>`
- `--ec-code <error-code>`
- `--ec-namespace <namespace>`
- `--ec-force`
- `--ec-report-md <path>`
- `--ec-report-json <path>`
- `--tm-scenario <scenario>`
- `--tm-force`
- `--tm-report-md <path>`
- `--tm-report-json <path>`
- `--ds-doc-target <target>`
- `--ds-force`
- `--ds-report-md <path>`
- `--ds-report-json <path>`
- `--cr-force`
- `--cr-report-md <path>`
- `--cr-report-json <path>`

仅在紧急排障时可临时跳过子守卫：

- `--skip-api-schema-guard`
- `--skip-question-bank-guard`
- `--skip-rbac-guard`
- `--skip-state-machine-guard`
- `--skip-error-code-guard`
- `--skip-test-matrix-guard`
- `--skip-delivery-doc-sync-guard`
- `--skip-component-reuse-guard`

守卫告警必须处理或明确说明阻塞原因，不能静默忽略。

## 告警闭环规则

- 守卫告警不区分 `high / medium / low` 默认放过；凡命中本次改动面的告警，都应优先做真实修复并在本阶段收口。
- “压告警 / 跳过检查 / 降级阈值 / 保留低优先级不管”不算解决问题，默认视为技术债继续累积。
- 告警必须优先归类到以下真实动作之一：
  - 修实现：修源码、修调用、修字段、修状态、修权限、修测试。
  - 修契约：修 OpenAPI、修后端模型、修前端类型、修文档口径。
  - 清理旧入口：删除历史别名、兼容路由、旧文档、旧 schema、旧双入口。
  - 升级守卫：当告警来自检测能力缺陷时，应优先补脚本识别能力，避免业务代码长期迁就工具。
- 对“工具识别不到模板字符串 / 常量前缀 / 标准占位符替换”这类问题，默认优先升级守卫能力，而不是要求业务代码无限制改写成守卫特供格式。
- 只有满足“负责人 + 范围 + 截止时间 + 清理动作”的显式豁免，才允许临时保留未清零告警；没有豁免信息时，不得以备注代替修复。

## 实施顺序

1. 选择并冻结契约模式、字段语义和状态规则。
2. 更新数据库、实体、DTO/VO、服务、接口契约。
3. 更新前端页面、表单、表格、按钮、弹窗、状态绑定。
4. 对齐权限、校验、异常、错误码与日志。
5. 对齐文档、注释、示例、测试与运行手册。
6. 执行统一清单并修复全部漂移。
7. 对命中数据建模非协商规则的改动，补齐迁移脚本、双写方案、切读方案和回滚说明。
8. 对命中“热状态拆表”或“去双入口”的改动，补齐 legacy 清理、backfill 审计、文档口径更新和回归测试证据。

详细清单见 [references/unified-delivery-checklist.md](references/unified-delivery-checklist.md)。
题库模式额外清单见 [references/question-bank-alignment-checklist.md](references/question-bank-alignment-checklist.md)。
题库固定契约见 [references/question-bank-fixed-contract.md](references/question-bank-fixed-contract.md)。

## 与其他总技能的边界

- 开发前准备阶段：优先使用 `software-development-readiness-governance`，先冻结需求、ADR、技术栈边界与五类高风险问题的设计基线。
- 进入真实实现和联调阶段：切换到本技能，负责数据库、后端、接口、前端、权限、状态、校验、错误、文档、测试与风险控制点的统一收敛。
- 发布上线阶段：切换到 `software-delivery-unified-governance`，负责检查这些设计与实现控制点是否真的完成，并执行发布门禁。
- 同一阶段不要并行双开多个总技能；应按“开发前准备 -> 全端统一交付 -> 软件交付”的顺序串行衔接。

## 统一报告输出

主守卫支持输出统一交付报告：

- `--mode <auto|global|questionBank>`
- `--report-md <path>`
- `--report-json <path>`
- `--waiver-file <json-file>`

统一报告至少应包含：

- 执行阶段与任务摘要
- 契约模式
- 十域检查汇总
- 未处理漂移清单
- 已批准豁免清单
- `questionBank` 模式下的五模块结果摘要
- 是否允许继续联调 / 提测 / 交付 的结论

`questionBank` 模式下，报告需额外按模块输出：

- `user`
- `userAuth`
- `knowledge`
- `question`
- `task`

每个模块至少给出：固定字段、响应契约、`extJson`、状态/权限/页面/测试的收敛状态。

## 守卫脚本测试

主守卫及其增强能力应至少具备 smoke tests：

- 报告输出
- `questionBank` 模块级摘要
- 豁免文件解析
- 失败项与豁免项分类

如项目内存在测试目录，优先以单测形式校验这些能力，避免规则升级后误报回归。

## CI 接入

推荐在 CI 中执行：

- `python3 scripts/unified_delivery_guard.py --phase final --report-md <path> --report-json <path>`

CI 至少应做到：

- 守卫失败时阻断
- 报告产物可下载
- 与测试步骤一起执行，避免“脚本通过但测试缺席”

## 漂移豁免机制

仅在紧急排障或明确的阶段性兼容窗口内允许使用豁免。

豁免文件应至少记录：

- `name`：检查项或域名
- `reason`：豁免原因
- `owner`：负责人
- `expiresAt`：到期时间
- `scope`：影响范围

使用豁免后仍需：

- 在统一报告中显式列出
- 说明为什么当前不能立即修复
- 给出清理计划和截止时间

示例见 [references/waiver-file.example.json](references/waiver-file.example.json)。

禁止长期、静默、无限期豁免。

## 非协商规则

- 同一模块不允许混用两套响应包。
- 同一交付不允许混用两套状态流。
- 不允许长期保留别名字段或兼容字段。
- 不允许以小修小补兼容、外围胶水或双轨并存代替正确实现。
- 已有更优实现时，应在本次改动范围内直接替换旧实现，不得继续叠加新旧两套写法。
- 不能安全收敛时必须暂停并向用户确认。

## 输出要求

- 优先输出可直接落地的改动，不只给建议。
- 如有阻塞，必须明确阻塞层与原因。
