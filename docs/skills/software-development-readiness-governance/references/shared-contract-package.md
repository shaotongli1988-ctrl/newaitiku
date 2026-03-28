# 三阶段共享合同包规范

本规范用于把“开发前准备 -> 开发中统一交付 -> 开发后发布治理”串成同一条合同链。

目标不是让三个总技能各自再推断一套规则，而是：

- 开发前总技能负责定义并冻结
- 开发中总技能负责按冻结约束实现
- 开发后总技能负责按同一份冻结约束验收、发布、回滚与交付

## 一、核心原则

### 1. 唯一合同源

- 三阶段都只认同一份合同包。
- 开发中与开发后不得各自重解释字段、权限、状态、校验、错误码与交互规则。

### 2. 先冻结再执行

- 开发前总技能产出合同包后，才允许进入开发中阶段。
- 任何会改变合同含义的事项，都必须回到开发前阶段重新冻结。

### 3. 项目差异只放在适配层

- 三阶段主流程不因项目不同而变化。
- 项目差异只体现在目录路径、语言栈、框架发现方式、环境配置发现方式。

### 4. 合同优先于实现

- 代码必须服从合同。
- 测试、文档、发布说明也必须服从合同。

### 5. 正确实现优先于补丁兼容

- 进入开发中阶段后，默认按“正确实现优先”执行，不允许把补丁式兼容、外围胶水、双轨并存作为常规开发策略。
- 已存在更优公共层、统一模型、标准组件或标准接口时，应直接替换旧实现并完成收敛，不得继续新旧并挂扩散。
- 仅数据库迁移、灰度切流、外部依赖短期受限、紧急止血等明确过渡窗口允许临时兼容，且必须记录负责人、截止时间和清理动作。

## 二、建议目录结构

建议在项目内固定放在：

`docs/contracts/current/`

推荐结构：

```text
docs/contracts/current/
├── contract.md
├── contract.json
├── module-summary.md
├── test-plan.md
├── waivers.json
└── history/
    └── 2026-03-21-contract-v1/
        ├── contract.md
        ├── contract.json
        ├── module-summary.md
        ├── test-plan.md
        └── waivers.json
```

说明：

- `contract.md`
  面向人读的冻结说明。
- `contract.json`
  面向守卫脚本、测试生成器、发布流程消费的结构化合同。
- `module-summary.md`
  题库模式或复杂项目下的模块级对齐摘要。
- `test-plan.md`
  由合同直接映射出的测试矩阵与自动化建议。
- `waivers.json`
  临时豁免，不允许散落在其他文档里。
- `history/`
  存档已冻结版本，避免后续覆盖丢失。

## 三、contract.json 顶层字段规范

建议结构：

```json
{
  "contractVersion": "v1",
  "contractId": "dr-2026-03-21-001",
  "generatedAt": "2026-03-21T10:00:00+08:00",
  "generatedBy": "software-development-readiness-governance",
  "phase": "development-readiness",
  "mode": "questionBank",
  "projectProfile": {},
  "scope": {},
  "contracts": {},
  "governance": {},
  "testPlan": {},
  "releaseReadiness": {},
  "waivers": []
}
```

### 1. `contractVersion`

- 合同结构版本。
- 用于脚本兼容与升级。

### 2. `contractId`

- 本次冻结合同的唯一标识。
- 推荐包含日期与流水号。

### 3. `generatedAt`

- 合同冻结时间。

### 4. `generatedBy`

- 默认记录来源总技能。

### 5. `phase`

- 固定记录当前来源阶段。
- 开发前总技能产出时建议固定为 `development-readiness`。

### 6. `mode`

- `global` 或 `questionBank`。

## 四、projectProfile 字段

用于保存项目级适配信息。

建议包含：

```json
{
  "name": "newaitiku",
  "repoRoot": "/Users/shaotongli/Documents/newaitiku",
  "backendStack": "python-fastapi",
  "frontendStack": "vue-vite",
  "database": "sqlite",
  "primaryGuard": "fullstack-unified-development-standards"
}
```

## 五、scope 字段

用于冻结本轮范围。

建议包含：

```json
{
  "businessGoal": "教师题目管理与学生练习链路统一收敛",
  "inScopeModules": ["question", "knowledge"],
  "outOfScopeModules": ["messages", "system"],
  "affectedLayers": ["database", "backend", "api", "frontend", "docs", "tests"],
  "actors": ["super_admin", "teacher", "student"]
}
```

## 六、contracts 字段

这是核心区域。

建议拆成：

### 1. `fieldDictionary`

- 字段名
- 类型
- 是否必填
- 默认值
- 枚举
- 说明
- 所属模块
- 是否允许进入 `extJson`

### 2. `database`

- 表名
- 字段
- 主键
- 外键
- 索引
- 唯一性
- 历史兼容策略

### 3. `api`

- 路径
- 方法
- 请求字段
- 响应包
- 分页结构
- 错误语义

### 4. `permissions`

- 角色
- 权限键
- 菜单显隐
- 按钮显隐
- 接口鉴权
- 数据作用域

### 5. `stateMachines`

- 状态集合
- 流转边
- 合法操作
- 非法操作提示

### 6. `validation`

- 前端校验
- 后端校验
- 服务层补充校验
- 错误提示文案

### 7. `errorSemantics`

- 错误码
- HTTP 状态
- 错误文案
- 是否可重试
- 责任归属

### 8. `uiStandards`

- 页面骨架
- 筛选规则
- 抽屉/弹窗规范
- 按钮层级
- Toast/消息反馈
- 状态标签
- 空态/加载态/错误态

## 七、governance 字段

用于冻结开发过程规则。

建议包含：

```json
{
  "adrRefs": ["docs/architecture/adr-001.md"],
  "techStackPolicy": {
    "allowNewDependency": false,
    "allowNewFramework": false
  },
  "gitPolicy": {
    "branchPrefix": "codex/",
    "requiredChecks": ["unified_delivery_guard", "tests"]
  }
}
```

## 八、testPlan 字段

开发前总技能冻结后，开发中与开发后都应直接消费。

建议包含：

- 正常场景
- 异常场景
- 边界场景
- 权限场景
- 状态流场景
- API 场景
- 前端交互场景
- 建议自动化类型
  - `pytest-unit`
  - `pytest-integration`
  - `pytest-regression`
  - `playwright-e2e`

## 九、releaseReadiness 字段

虽然最终由开发后总技能消费，但应在开发前先冻结最低口径。

建议包含：

- 回滚要求
- 配置要求
- 数据迁移要求
- 监控要求
- 值班要求

## 十、waivers 字段

用于结构化记录本轮豁免。

建议每项至少包含：

```json
{
  "name": "validation:legacy-alias-window",
  "reason": "灰度兼容窗口",
  "owner": "teacher-platform-owner",
  "expiresAt": "2026-04-01",
  "scope": "teacher question APIs only"
}
```

## 十一、三阶段如何消费

### 1. 开发前总技能

输出：

- `contract.md`
- `contract.json`
- `test-plan.md`
- `waivers.json`

职责：

- 定义并冻结合同
- 给出是否允许进入开发结论

### 2. 开发中总技能

输入：

- 读取 `docs/contracts/current/contract.json`

职责：

- 不重新定义规则
- 只检查实现是否偏离合同
- 输出实现漂移报告

### 3. 开发后总技能

输入：

- 读取同一份 `docs/contracts/current/contract.json`

职责：

- 检查是否满足发布、回滚、UAT、监控与交付要求
- 不允许重新发明验收口径

## 十二、变更闸门

以下任意一项变化，都必须回到开发前总技能重新冻结：

- 字段名、类型、枚举变化
- 状态集合或流转边变化
- 权限键或数据作用域变化
- 错误码语义变化
- 页面交互标准变化
- 引入新依赖或新框架
- 非功能基线变化

## 十三、落地建议

建议按下面顺序推进：

1. 先让开发前总技能产出 `contract.json`
2. 再让开发中总技能强制读取它
3. 最后让开发后总技能读取同一份合同
4. 任何规则变化都通过重新冻结合同进入三阶段
