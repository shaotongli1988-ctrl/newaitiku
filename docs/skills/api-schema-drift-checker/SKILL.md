---
name: api-schema-drift-checker
description: 防止 API 契约漂移的专项技能。用于对齐后端模型、OpenAPI/Swagger、前端类型与请求调用，输出高/中/低风险漂移清单并给出修复方向。遇到新增字段、字段改名、接口改动、状态枚举改动、返回结构改动、前后端不一致、联调报错、批量重构接口、上线前回归检查时使用。
---

# API Schema Drift Checker

## 核心目标

- 执行可重复的 schema drift 扫描，尽早发现“后端改了但前端没跟”与“前端假设和契约不一致”。
- 统一输出可落地问题清单，避免只说“可能有问题”。

## 标准流程（强制）

1. 首次编辑前运行：
`python3 scripts/schema_drift_guard.py --phase start --task "<用户需求>"`
2. 每个主要改动批次后运行：
`python3 scripts/schema_drift_guard.py --phase batch`
3. 最终交付前运行：
`python3 scripts/schema_drift_guard.py --phase final`

`final` 阶段若存在高风险漂移会返回非零退出码，必须修复或明确阻塞原因。

## 默认检查面

- Producer（服务端契约源）：
  - `openapi*.json|yaml` / `swagger*.json|yaml`
  - 后端模型文件（DTO/VO/Entity/Schema，支持 TS/Java/Python 基础解析）
- Consumer（消费端契约）：
  - 前端类型文件（`interface/type/enum`）
  - 前端请求调用（`axios/fetch/request`）

## 漂移分级

- `high`
  - OpenAPI 必填字段在前端类型缺失
  - 前端请求方法/路径无法在 OpenAPI 匹配
  - 已匹配同名枚举但成员缺失
- `medium`
  - 可选字段不一致
  - 存在明显过时字段（消费端多出 producer 不再提供的字段）
  - 大量模型无法匹配
- `low`
  - 信息性提醒（如 YAML 解析依赖缺失、扫描范围过大被截断）

## 常用命令

全量扫描：

```bash
python3 scripts/schema_drift_guard.py --phase final --cwd "$(pwd)"
```

指定契约源与消费端目录：

```bash
python3 scripts/schema_drift_guard.py \
  --phase final \
  --openapi docs/openapi.yaml \
  --producer backend/src \
  --consumer frontend/src
```

输出报告文件：

```bash
python3 scripts/schema_drift_guard.py \
  --phase batch \
  --report-md reports/schema-drift.md \
  --report-json reports/schema-drift.json
```

处理命名差异（DTO/VO/Response 等）：

```bash
python3 scripts/schema_drift_guard.py \
  --phase final \
  --alias-map references/alias-map.example.json
```

## 修复协议

1. 先修 `high`，再处理 `medium`，最后清理 `low`。
2. 对每条漂移给出单一真实来源（OpenAPI 或后端 DTO），避免双向猜测。
3. 字段改名优先一次性迁移，不长期保留双字段别名。
4. 接口路径和方法冲突先收敛契约，再修前端调用与类型。
5. 若业务必须保留临时兼容，必须标注移除计划与截止版本。

## 告警闭环要求

- 本技能输出的问题清单默认要求进入“真实修复”闭环，不得把“压告警”视为完成。
- `Documented APIs not referenced by consumer` 这类告警，必须先判断根因属于哪一类：
  - 前端确实未消费：清理废弃 OpenAPI/别名契约。
  - 前端已消费但写法未被识别：升级守卫脚本识别能力。
  - 前端路径或方法错误：修消费者实现。
  - OpenAPI 契约脏数据：修契约并重新导出。
- 对模板字符串、常量前缀、`replace('{id}', ...)` 等标准表达式，不应长期要求业务代码迁就检测器；守卫脚本应具备识别能力。
- 只有当接口明确进入废弃窗口时，才允许把“文档存在但消费者未引用”保留为低优先级；否则应推动代码、契约或脚本能力之一完成收口。

## 资源

- [references/schema-drift-checklist.md](references/schema-drift-checklist.md)：漂移类型与修复动作对照。
- [references/detection-tuning.md](references/detection-tuning.md)：扫描范围、别名映射、误报收敛方法。
- [scripts/schema_drift_guard.py](scripts/schema_drift_guard.py)：自动扫描与闸门脚本。
