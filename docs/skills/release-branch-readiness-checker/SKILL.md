---
name: release-branch-readiness-checker
description: 发布分支就绪性专项技能。用于检查 release 分支的未合并项、脏提交、风险 cherry-pick、版本差异与发布完整性，识别“分支能发但内容不稳”的发布风险。
---

# 发布分支就绪性

## 核心目标

- 确认 release 分支具备可发布性与可追踪性。

## 触发场景

- release 分支创建后
- 上线前分支检查

## 默认检查项

1. 是否存在未合并必需改动
2. 是否存在脏提交或风险 cherry-pick
3. 版本差异是否可解释

## 输出要求

- 输出分支就绪报告
- 输出阻断项
