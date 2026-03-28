# 技能治理变更清单（2026-03-22）

## 1. 变更目标

- 把“`extJson` 热状态拆表、正式表切流、backfill/一致性审计、去双入口、去 fallback”从一次性项目经验，收敛为可复用的现有技能能力。
- 不新建同类技能，优先并入已有总技能、专项技能、守卫脚本与技能元数据。
- 让技能能力形成统一的 5 层结构：
  - `SKILL.md`
  - `references/checklist.md`
  - `references/detection-tuning.md`
  - `scripts/*.py`
  - `agents/openai.yaml`

## 2. 本次并入范围

### 2.1 已更新技能

- `fullstack-unified-development-standards`
- `question-bank-contract-enforcer`
- `delivery-doc-sync`
- `fullstack-test-matrix`

### 2.2 变更能力主题

- 热状态拆表
- 正式表优先读
- legacy JSON fallback 清理
- backfill / 一致性审计
- 单入口收敛
- 去双入口 / 去双读写

## 3. 各技能变更面

### 3.1 fullstack-unified-development-standards

#### 已更新层

- `SKILL.md`
- `agents/openai.yaml`

#### 新增能力

- 单入口收敛特性
- 热状态拆表特性
- 数据建模非协商规则补充：
  - 报告详情、发送历史、撤回历史、学习记录等热路径数据不得长期依赖 legacy JSON fallback
  - 去双入口默认进入收口阶段，不允许“先保留旧入口再说”
- 实施顺序补充：
  - 命中热状态拆表或去双入口时，必须补齐 legacy 清理、backfill 审计、文档口径更新、回归证据

#### review 要点

- 是否只保留了“稳定复用规则”，没有写入项目私有表名或路径
- 是否仍与三阶段总入口的开发中阶段定位一致

### 3.2 question-bank-contract-enforcer

#### 已更新层

- `SKILL.md`
- `references/question-bank-contract-checklist.md`
- `references/detection-tuning.md`
- `scripts/question_bank_contract_guard.py`
- `agents/openai.yaml`

#### 新增能力

- 热状态约束
- 正式表约束
- 收口约束
- 审计约束
- questionBank 额外红线：
  - 学习态不能长期堆在 `user.extJson` 根级 map
  - 报告/发送历史/撤回历史不能只存系统状态 JSON
  - `json_each(...)`、整块 JSON map 回写、整块系统状态回写按高风险处理
- 守卫脚本新增识别：
  - 热状态 JSON 命中
  - 正式表/唯一约束证据
  - legacy fallback
  - backfill / 一致性审计证据
  - 非生产代码误报收敛（如 `docs/skills`、`tools`）

#### review 要点

- 守卫是否优先识别生产代码，而不是把技能文档和治理脚本误判为业务实现
- “热状态改动但未见正式表证据”“legacy fallback 未清理”“缺少 backfill/审计”的分级是否合理

### 3.3 delivery-doc-sync

#### 已更新层

- `SKILL.md`
- `references/delivery-doc-checklist.md`
- `references/detection-tuning.md`
- `scripts/delivery_doc_sync_guard.py`
- `agents/openai.yaml`

#### 新增能力

- 文档检查新增：
  - 热状态拆表/切流时检查正式模型、兼容窗口、legacy 清理口径
  - 去双入口/去双读写时检查唯一入口与旧入口删除说明
- detection-tuning 新增：
  - 热状态拆表时优先命中 `overview/data/test`
  - 单入口收敛时优先命中 `overview/frontend/test`
  - 文档误报收敛建议
- 守卫脚本新增识别：
  - 热状态切流关键词
  - 单入口收敛关键词
  - 根据命中内容自动提高相关章节要求

#### review 要点

- 文档守卫是否真的会在“切流/收口”任务里要求对应章节，而不是仍只按通用 API/数据/前端规则处理
- 是否避免要求重复开新章节，优先鼓励补充已有章节

### 3.4 fullstack-test-matrix

#### 已更新层

- `SKILL.md`
- `references/fullstack-test-checklist.md`
- `references/detection-tuning.md`
- `scripts/fullstack_test_matrix_guard.py`
- `agents/openai.yaml`

#### 新增能力

- 新增场景：
  - `cutover`
  - `single_entry`
- checklist 新增：
  - 热状态切流回归
  - 单入口回归
- detection-tuning 新增：
  - 什么时候显式追加 `--scenario cutover`
  - 什么时候显式追加 `--scenario single_entry`
  - 两类场景的误报收敛建议
- 守卫脚本新增：
  - 场景别名
  - 关键词命中
  - required 场景推断
  - 参数提示文案更新

#### review 要点

- 新场景是否足够清晰，不会与 `data` / `frontend` 现有场景混淆
- `cutover` 是否只用于运行时主路径切换，不会误伤普通数据改动
- `single_entry` 是否只用于入口收敛，不会误伤普通前端改动

## 4. 建议 review 顺序

1. 先看 `SKILL.md`
   - 判断规则是否值得长期复用
2. 再看 `references/checklist.md`
   - 判断检查项是否完整
3. 再看 `references/detection-tuning.md`
   - 判断命中策略和误报收敛是否合理
4. 最后看 `scripts/*.py`
   - 判断自动化守卫是否真的落地了新增规则
5. 最后看 `agents/openai.yaml`
   - 判断技能列表元数据是否和正文能力一致

## 5. 本次可直接验收的结果

- 现有技能已不再只在正文层面描述热状态拆表和单入口收口
- 题库契约、文档同步、测试矩阵 3 个专项技能都已具备对应的检查清单、检测调优说明和脚本级支撑
- 技能元数据已经同步更新，技能列表和默认 prompt 能体现新增能力

## 6. 后续可选增强项

- 给新增守卫能力补对应 smoke tests，避免后续规则演化时回归
- 统一各守卫里的“忽略非生产代码目录”策略，减少多处重复维护
- 如后续还会持续出现类似问题，可再评估是否需要单独抽出“热状态拆表专项技能”
