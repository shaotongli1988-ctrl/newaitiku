---
name: architecture-decision-recorder
description: 架构决策记录专项技能。用于沉淀技术选型、替代方案、约束与影响范围，识别“技术方案做了但没有决策记录”的长期维护风险。
---

# 架构决策记录

## 核心目标

- 把重要技术选型变成可追溯的 ADR。
- 在技术栈、架构边界、基础设施或核心模块改动时，沉淀背景、决策、替代方案和风险。

## 触发场景

- 技术方案评审
- 新技术引入
- 架构变更
- 中间件、部署链路或数据库架构调整

## 默认检查项

1. 是否记录问题背景
2. 是否记录选型与替代方案
3. 是否记录影响范围与风险
4. 是否明确决策状态、负责人和后续动作

## 输出要求

- 输出 ADR 草案
- 输出风险与取舍说明
- 输出是否允许按当前方案继续推进

## 守卫脚本

- 守卫检查：`python3 scripts/architecture_decision_recorder_guard.py --phase final --cwd <repo>`
- 生成 ADR：`python3 scripts/architecture_decision_recorder_guard.py --decision-title "<标题>" --owner "<负责人>" --output-md <path>`

## 参考资料

- 检查清单见 [references/checklist.md](references/checklist.md)
- ADR 模板见 [references/adr-template.md](references/adr-template.md)
