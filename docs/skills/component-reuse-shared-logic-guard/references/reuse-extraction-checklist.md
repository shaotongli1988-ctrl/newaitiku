# 组件复用与公共逻辑提取检查清单

## 一、职责边界

本守卫只检查实现层收敛，不替代以下专项守卫：

- API 契约一致性：交给 `api-schema-drift-checker`
- 题库固定契约：交给 `question-bank-contract-enforcer`
- 权限：交给 `rbac-alignment-guard`
- 状态流：交给 `state-machine-alignment`
- 错误码：交给 `error-code-governor`
- 测试矩阵：交给 `fullstack-test-matrix`
- 文档同步：交给 `delivery-doc-sync`

## 二、前端检查项

### 1. 公共组件

- 列表页优先复用 `BaseTable`、`BasePagination`、`PageContainer`、`BaseSearch`
- 表单页优先复用 `BaseForm`、`BaseFormItem`、`BaseDialog`、`BaseDrawer`
- 通用交互优先复用 `BaseButton`、`StatusTag`、`EmptyState`、`LoadingWrapper`
- 已有组件不足以支撑新需求时，先扩展公共组件能力，再决定是否新增组件

判定为问题的信号：

- 两个及以上页面存在高相似度模板结构和交互逻辑
- 业务页内出现大段表格列、分页、搜索栏、弹窗壳子复制
- 公共组件缺少 `props`、事件、默认值、插槽其中之一，导致只能单页使用
- 公共组件内部硬编码接口、权限键、状态值、业务文案

### 2. 公共 Hook 与工具

- 查询、分页、搜索、重置逻辑优先归入 `useTable`、`usePagination`
- 请求执行态优先归入 `useRequest`
- 弹窗开关优先归入 `useModal`
- 表单提交、校验、重置优先归入 `useForm`
- 权限判断优先归入 `usePermission`
- 时间、校验、存储、下载、树形处理优先复用公共工具

判定为问题的信号：

- 多个页面重复维护 `loading/error/retry`
- 多个页面重复拼接分页参数和查询参数
- 页面内散落手机号校验、非空校验、长度校验
- 工具函数依赖外部可变状态，难以单测

### 3. request 与结构统一

- Vue 侧统一走 `frontend/src/api/request.js`
- 页面内禁止直接写裸 `axios`
- 静态页局部 `request` 不应作为常驻例外继续保留
- 仅明确过渡窗口允许短期保留局部 `request`，且必须进入迁移清单并写明负责人、截止时间、替换目标
- 返回结构固定 `{ code, message, data }`
- 分页结构固定 `{ items, page, size, total }`
- 时间字段统一使用 `createTime/updateTime`
- `extJson` 必须保持对象语义

判定为问题的信号：

- 页内直接 import `axios`
- 同模块同时出现 `list/records/rows` 等多套分页字段
- `createdAt/updatedAt` 与 `createTime/updateTime` 混用
- `extJson` 在新增代码中被序列化成字符串再传递

## 三、后端检查项

- 统一返回继续复用 `Result` 或现有 `BaseResponse`
- 分页继续复用 `PageResult` 与 `PageParam`
- 公共异常、参数校验、日志、拦截器优先复用全局能力
- 新增实体优先继承 `BaseEntity`
- `id/createTime/updateTime/extJson` 为核心固定字段
- `isDelete/remark` 作为新增表强制项和存量迁移目标

判定为问题的信号：

- 新接口单独定义一套返回体
- 控制器/服务层大量重复 try-catch、参数校验、日志模板
- 新表绕开公共实体字段约束
- 工具类带业务副作用或直接耦合具体模块

## 四、风险分级建议

### `high`

- 同构实现重复 3 次及以上
- 新页面直接写裸请求
- 同交付混用多套分页或返回结构
- 新增公共层写死业务逻辑导致不可复用

### `medium`

- 同构实现重复 2 次
- 已有公共层可复用但未使用
- 存量例外未登记迁移清单

### `low`

- 命名、注释、常量、默认值定义零散不统一
- 组件或工具可继续纯化与抽象，但不影响本次主流程

## 五、修复动作模板

1. 判断是否已存在可复用公共层
2. 若存在，优先迁移业务代码到公共层，并替换旧实现，不新增兼容胶水层
3. 若不存在，先补最小可复用公共抽象
4. 给公共层补充 `props`、事件、默认值、插槽或参数对象
5. 发现旧实现方向错误、抽象过时或明显劣于统一方案时，直接改旧实现，不在外围追加补丁式兼容
6. 把页面中的裸请求、分页拼装、时间格式、校验逻辑迁入公共层
7. 对暂不迁移的存量代码补迁移清单；仅明确过渡窗口允许临时兼容，且必须写截止时间

## 六、迁移清单建议字段

- 模块
- 页面或接口位置
- 当前重复点
- 目标公共层
- 风险等级
- 是否阻断本次交付
- 后续迁移批次
