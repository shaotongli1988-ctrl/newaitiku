# 学科诊断标准化补齐说明

## 目标

- 补齐高数（一）的知识树与示例数据，让学生端知识诊断层次与政治保持一致。
- 同时把其他学科按同一标准收口，避免再次出现“某些学科可诊断、某些学科层级稀疏”的差异。

## 本次实现

- 在数据库初始化阶段新增“诊断标准化 backfill”。
- 对缺少 L5 节点的学科，按章节自动补齐最小诊断点，保证每个 L4 章节至少有 1 个 L5 节点。
- 对示例题不足的学科，自动补齐最少 4 道已发布示例题，保证知识诊断和练习入口可用。
- 保持实现幂等；对新库和已有库都会生效。

## 影响范围

- 后端初始化与种子逻辑：`app/db.py`
- 学生端知识诊断、刷题路径的数据基础：`knowledge`、`question` 种子数据

## 验证

- `python3 -m pytest -q tests/test_question_bank.py -k "backfills_l5_diagnostic_nodes_for_sparse_subjects or backfills_minimum_published_demo_questions_per_subject"`
- 验证结果：2 条新增回归测试通过

