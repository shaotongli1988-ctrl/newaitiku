# 学生端转化闭环 MVP 实施计划拆解（兑换码 + 订阅 + 模拟支付）

- 日期：2026-03-25
- 对应设计：`docs/superpowers/specs/2026-03-25-student-conversion-redeem-subscription-mvp-design.md`
- 目标周期：6-8 周
- 主指标：订阅开通率、兑换码核销率、模拟支付转化率

## 1. 目标与约束

### 1.1 本期必须交付

1. 学生端首登转化主链路：`登录 -> 快诊 -> 结果页 -> 兑换/模拟支付 -> 权益生效 -> 今日任务`。
2. 单套餐订阅能力：`AI提分30天`。
3. 兑换码系统（拉新体验码）：一码一次、一号一次、过期失效、顺延规则。
4. 模拟支付闭环：下单、成功回调、幂等保障、异常补偿。
5. 功能说明文档可用于产品/研发/运营/客服统一口径。

### 1.2 技术与流程约束

1. 路由层禁止 `payload: dict`，必须新增 Pydantic 请求模型（`app/contracts.py`）。
2. 时间字段统一 `createTime/updateTime`，不引入 `createdAt/updatedAt`。
3. 前端请求必须经过 `frontend/src/api/services/questionBank.js`。
4. 保持固定响应包：`{ code, message, data }`。

## 2. 代码落点与模块分工

## 2.1 后端

1. `data/schema.sql`
: 新增订阅/兑换码/模拟支付相关表和索引。
2. `app/db.py`
: 增加 `ensure_subscription_redeem_schema(connection)`，纳入 `init_db()` 执行链。
3. `app/repository.py`
: 增加新表字段常量、CRUD 方法、幂等查询方法。
4. `app/contracts.py`
: 增加兑换码、模拟支付、订阅状态、快诊会话请求模型。
5. `app/service_modules/student_monetization.py`（新增）
: 承接订阅权益、兑换、模拟支付业务编排。
6. `app/service.py`
: 组合 `StudentMonetizationServiceMixin`。
7. `app/main.py`
: 新增学生端与管理端 API 路由。

## 2.2 前端

1. `frontend/src/api/services/questionBank.js`
: 增加兑换码、模拟支付、订阅状态、快诊相关 API 封装。
2. `frontend/src/api/services/student.js`
: 暴露学生端聚合接口（适配页面调用）。
3. `frontend/src/router/studentRoutes.js`
: 增加首登转化路由与结果页路由。
4. `frontend/src/stores/userStore.js`
: 登录后首登分流逻辑（是否进入引导链路）。
5. `frontend/src/views/Student/`（新增）
: `OnboardingDiagnosis.vue`、`SubscriptionCheckout.vue`、`SubscriptionSuccess.vue`。
6. `frontend/src/views/Student/Home.vue`
: 权益态入口（已开通 vs 未开通）联动。

## 2.3 测试与文档

1. `tests/test_question_bank.py`
: 新增核心业务测试（兑换、顺延、幂等、权限）。
2. `tests/integration/test_question_bank_core_api_pytest_suite.py`
: 新增核心 API 契约回归。
3. `tests/e2e/test_student_interaction_acceptance.py`
: 新增学生主链路真点击验收场景。
4. `docs/question-bank-contract.md`
: 新增 API 合同与字段说明。
5. `docs/` 下新增系统功能说明（见第 8 节交付物）。

## 3. 数据模型拆解（MVP 最小集）

## 3.1 新增表

1. `subscription_plan`
: 订阅商品定义（本期仅 1 条：`AI提分30天`）。
2. `student_subscription`
: 学生订阅状态真相源（`inactive/active/expired` + `startTime/endTime`）。
3. `redeem_code_batch`
: 发码批次（渠道、有效期、数量）。
4. `redeem_code`
: 兑换码实体（码值、状态、过期、已使用账号、使用时间）。
5. `subscription_order`
: 模拟支付订单（订单号、金额、状态、来源）。
6. `payment_transaction_mock`
: 模拟支付回调与幂等日志。
7. `conversion_event_log`
: 关键转化事件审计（注册、快诊、兑换提交、兑换成功、支付成功、开通成功）。

## 3.2 兼容与迁移策略

1. 通过 `app/db.py` 的 `ensure_*` 方式保证历史库可升级。
2. 不做破坏性 DDL，不删除旧字段。
3. 订阅权益判定以后端 `student_subscription` 为准，不依赖前端本地缓存。

## 4. API 计划（第一版）

## 4.1 学生端

1. `GET /api/question-bank/student/subscription/status`
: 获取当前订阅状态与到期时间。
2. `GET /api/question-bank/student/subscription/plans`
: 获取可购买套餐（本期返回单套餐）。
3. `POST /api/question-bank/student/subscription/redeem`
: 提交兑换码。
4. `POST /api/question-bank/student/subscription/mock-orders`
: 创建模拟支付订单。
5. `POST /api/question-bank/student/subscription/mock-orders/{orderId}/confirm`
: 确认模拟支付成功（幂等）。
6. `POST /api/question-bank/student/diagnosis/quick/start`
: 创建快诊会话。
7. `POST /api/question-bank/student/diagnosis/quick/{sessionId}/submit`
: 提交快诊答案并回传结果。

## 4.2 管理端（最小运维能力）

1. `POST /api/question-bank/admin/redeem-code/batches`
: 创建发码批次。
2. `GET /api/question-bank/admin/redeem-code/batches`
: 查询批次核销统计。
3. `GET /api/question-bank/admin/conversion/overview`
: 拉取核心转化指标。

## 5. 周粒度执行计划（可直接排期）

### 周 1：基建与可观测性

1. 数据表与索引落地（`schema.sql + db.py + repository.py`）。
2. 事件日志统一接口（`conversion_event_log` 写入能力）。
3. 指标查询草版 API（`admin/conversion/overview`）。

### 周 2：订阅权益内核

1. 单套餐数据初始化与读取接口。
2. `student_subscription` 生命周期实现。
3. 权益判定中间层（一个函数供所有 AI 入口复用）。

### 周 3：兑换码系统

1. 发码批次与码生成（管理端）。
2. 学生端兑换接口、限制规则、审计日志。
3. 顺延策略与冲突处理。

### 周 4：模拟支付系统

1. 下单接口、订单状态机。
2. 模拟回调接口与幂等处理。
3. 支付成功后复用“权益发放引擎”。

### 周 5：学生端首登链路页面

1. 快诊引导页与结果页。
2. 结果页接入兑换码与模拟支付入口。
3. 开通成功页与“今日任务”跳转。

### 周 6：联调与全链路回归

1. 登录后分流策略接入。
2. 首页权益态联动。
3. API/页面/指标一致性校验。

### 周 7：灰度优化

1. 灰度人群发布（小流量）。
2. 重点优化转化断点（文案、按钮、路径）。
3. 监控错误码与核心漏斗。

### 周 8：全量与文档冻结

1. 全量发布。
2. 功能说明、客服手册、运营手册冻结。
3. 发布复盘与下阶段真实支付接入输入。

## 6. 测试矩阵（MVP 必测）

1. 兑换码：一码一次、一号一次、过期码、空码、错误码、重复提交。
2. 订阅：新开通、顺延、过期、状态展示一致。
3. 模拟支付：重复回调幂等、失败补偿、订单状态流转。
4. 权限：学生可用，教师/超管禁止访问学生订阅接口。
5. 链路：登录 -> 快诊 -> 兑换/支付 -> 开通 -> 今日任务。
6. 指标：关键事件均可落库，计算公式结果正确。

## 7. 风险与应对

1. 风险：一次引入页面+后端+数据改动较大。
: 应对：按“后端先稳定 -> 前端接入 -> 灰度放量”推进。
2. 风险：规则复杂导致状态冲突。
: 应对：先冻结状态机，再做接口；所有写路径统一走 service 层。
3. 风险：转化效果不明显。
: 应对：周 7 预留 A/B 文案与入口实验窗口。

## 8. 本阶段交付物清单

1. 实施计划文档（本文）。
2. API 清单与字段合同（更新 `docs/question-bank-contract.md`）。
3. 系统功能说明文档（新增 `docs/system-function-manual-2026-xx.md`）。
4. 发布验收清单（新增 `docs/release/student-conversion-mvp-checklist-2026-xx.md`）。

## 9. 立即执行（T+3 天）

1. 先完成后端数据层骨架：`schema.sql / db.py / repository.py`。
2. 同步落第一批契约：`contracts.py + main.py`（仅订阅状态、兑换、模拟下单/确认）。
3. 补 8 条核心后端测试用例（兑换、顺延、幂等、权限）。
4. 前端先接最小闭环页面（结果页 + 兑换弹窗 + 模拟支付按钮）。

