# 软件上线成功率补齐路线图

## 结论

现有 skill 体系更强于：

- 全端一致性
- 接口/权限/状态/错误码/测试/文档收敛
- 组件复用与公共逻辑抽取

现有 skill 体系更弱于：

- 需求冻结与变更治理
- 技术方案评审与架构决策
- 数据库迁移安全
- 发布部署前检查
- 回滚能力与配置一致性
- 安全基线、性能基线、可观测性
- UAT / release readiness / Git 流程

一句话判断：
当前 skill 能防“开发做歪”，但还不够防“上线翻车”。

## 优先级路线图

### P0 必须补

1. `release-preflight-guard`
2. `rollback-readiness-guard`
3. `database-migration-safety-guard`
4. `deployment-config-alignment`
5. `app-security-baseline-guard`
6. `requirements-freeze-guard`

### P1 上线前补

1. `acceptance-criteria-builder`
2. `prd-ui-traceability-guard`
3. `ux-state-completeness-checker`
4. `release-quality-gate`
5. `uat-handoff-guard`
6. `observability-readiness-guard`
7. `git-flow-enforcer`
8. `release-branch-readiness-checker`

### P2 体系化建设

1. `architecture-decision-recorder`
2. `tech-stack-drift-guard`
3. `secret-config-leak-guard`
4. `performance-regression-guard`
5. `capacity-and-hotspot-review`
6. `incident-runbook-builder`

## P0 说明

### `release-preflight-guard`

- 解决问题：上线前遗漏配置、构建、回滚、监控、依赖、环境检查
- 最容易翻车点：代码没问题，但环境变量、证书、回调地址、数据库变更顺序出错
- 建议接入时机：发布前强制执行

```md
---
name: release-preflight-guard
description: 上线前统一检查专项技能。用于在发布前核对构建产物、环境变量、数据库变更、监控告警、回滚条件、配置差异与关键依赖，识别“代码能发但环境不能发”的高风险上线缺口。
---

# Release Preflight Guard

## 核心目标

- 在发布前给出统一门禁检查，阻断“缺配置、缺备份、缺监控、缺回滚”的上线风险。

## 触发场景

- 发布前检查
- 灰度前检查
- 正式上线前检查

## 默认检查项

1. 构建产物是否存在且版本一致
2. 环境变量 / 配置项是否齐全
3. 数据库脚本与应用版本是否匹配
4. 是否具备备份与回滚条件
5. 监控、日志、告警是否已开启
6. 域名、证书、回调地址、跨域配置是否正确

## 输出要求

- 输出 high/medium/low 风险清单
- 明确“是否允许上线”
- 对每个阻断项给出修复动作
```

### `rollback-readiness-guard`

- 解决问题：上线失败后无法快速恢复
- 最容易翻车点：应用可回滚、数据库不可回滚；配置改了但没版本化

```md
---
name: rollback-readiness-guard
description: 回滚就绪性专项技能。用于检查应用版本、数据库变更、配置切换、功能开关、静态资源与数据备份的回滚条件，识别“能上线但回不去”的高风险问题。
---

# Rollback Readiness Guard

## 核心目标

- 确认本次发布具备应用、配置、数据库三层回滚能力。

## 默认检查项

1. 应用版本是否可回退
2. 数据库变更是否可逆或可降级兼容
3. 配置变更是否可回滚
4. 功能开关是否可止血
5. 是否有明确回滚步骤与负责人

## 输出要求

- 输出回滚步骤
- 标识不可逆变更
- 对无回滚能力项给出阻断
```

### `database-migration-safety-guard`

- 解决问题：DDL、索引、回填、锁表、兼容迁移风险
- 最容易翻车点：上线时大表改结构、慢 SQL、无回滚、双写缺失

```md
---
name: database-migration-safety-guard
description: 数据库迁移安全专项技能。用于检查表结构变更、索引变更、数据回填、兼容迁移、执行顺序与回滚脚本，识别“DDL 可执行但线上高风险”的发布问题。
---

# Database Migration Safety Guard

## 核心目标

- 在数据库变更上线前识别锁表、长事务、回填、索引与兼容性风险。

## 默认检查项

1. 是否涉及大表 DDL
2. 是否缺少索引或新增查询路径无索引
3. 是否需要数据回填
4. 是否存在先发库/先发代码顺序要求
5. 是否支持双写、兼容读或灰度迁移
6. 是否有回滚脚本

## 输出要求

- 输出迁移顺序
- 输出回滚顺序
- 对高风险 DDL 给出阻断
```

### `deployment-config-alignment`

- 解决问题：dev/test/prod 配置漂移
- 最容易翻车点：测试能跑、生产缺 env；证书/域名/跨域/回调地址错误

```md
---
name: deployment-config-alignment
description: 环境配置对齐专项技能。用于对比开发、测试、生产环境的配置项、域名、证书、回调地址、跨域与外部依赖，识别“代码一致但环境不一致”的部署风险。
---

# Deployment Config Alignment

## 核心目标

- 保证多环境配置差异可见、可审计、可回滚。

## 默认检查项

1. env/config 是否齐全
2. dev/test/prod 差异是否符合预期
3. 域名、证书、回调地址是否正确
4. 外部服务地址与密钥是否已配置
5. 配置是否与代码解耦

## 输出要求

- 输出配置差异矩阵
- 输出缺失项与危险项
```

### `app-security-baseline-guard`

- 解决问题：上线前缺少统一安全基线
- 最容易翻车点：鉴权漏控、输入校验缺失、日志泄密、XSS/CSRF/重复提交

```md
---
name: app-security-baseline-guard
description: 应用安全基线专项技能。用于检查鉴权、输入校验、SQL 注入、XSS/CSRF、防重复提交、敏感日志与最小权限原则，识别“功能正确但安全不达标”的上线风险。
---

# App Security Baseline Guard

## 核心目标

- 把安全检查变成上线前必须过的基线门禁。

## 默认检查项

1. 鉴权与权限控制
2. 输入校验与输出转义
3. SQL 注入风险
4. XSS / CSRF 风险
5. 防重复提交与幂等
6. 敏感信息是否出现在代码、日志、错误信息

## 输出要求

- 输出安全风险分级
- 指出阻断项与修复建议
```

### `requirements-freeze-guard`

- 解决问题：需求变动无流程、验收口径不一致
- 最容易翻车点：边做边改，上线前才发现“不是这个意思”

```md
---
name: requirements-freeze-guard
description: 需求冻结与变更治理专项技能。用于检查需求是否明确、可验收、已评审、已冻结，识别“需求未冻结就进入设计/开发”的项目管理风险。
---

# Requirements Freeze Guard

## 核心目标

- 保证需求明确后再设计，设计明确后再开发。

## 默认检查项

1. 是否有正式需求文档
2. 是否有验收标准
3. 是否完成需求评审
4. 是否存在口头变更
5. 变更是否已评估影响面

## 输出要求

- 输出是否允许进入设计/开发
- 对未冻结需求给出阻断说明
```

## P1 / P2 骨架清单

以下 skill 建议先按精简骨架落地：

- `acceptance-criteria-builder`
- `prd-ui-traceability-guard`
- `ux-state-completeness-checker`
- `release-quality-gate`
- `uat-handoff-guard`
- `observability-readiness-guard`
- `git-flow-enforcer`
- `release-branch-readiness-checker`
- `architecture-decision-recorder`
- `tech-stack-drift-guard`
- `secret-config-leak-guard`
- `performance-regression-guard`
- `capacity-and-hotspot-review`
- `incident-runbook-builder`

统一骨架模板：

```md
---
name: <skill-name>
description: <一句话描述该 skill 解决的专项风险、适用场景和输出物>
---

# <Skill Title>

## 核心目标

- <解决什么上线/交付风险>

## 触发场景

- <什么时候用>

## 默认检查项

1. <检查项 1>
2. <检查项 2>
3. <检查项 3>

## 输出要求

- <要求输出的清单 / 矩阵 / 阻断项 / 修复建议>
```

## 推荐建设顺序

1. 先补 `P0`，尤其是 `release-preflight-guard`、`rollback-readiness-guard`、`database-migration-safety-guard`
2. 再补 `P1` 的上线门禁与验收链路
3. 最后补 `P2` 的架构、性能、可观测性与安全深水区

## 一句话建议

先把“能不能安全上线”补齐，再把“上线后能不能稳住”补齐，最后再做体系化治理。
