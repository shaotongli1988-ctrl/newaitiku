# 专升本题库系统功能说明（学生转化闭环版）

- 文档版本：v1.0
- 日期：2026-03-26
- 适用范围：产品、研发、测试、运营、客服

## 1. 文档目标

本说明用于统一“系统有什么功能、谁可以用、如何判断是否正常”，重点覆盖学生端转化闭环（快诊、兑换码、订阅、模拟支付）以及三端核心能力边界。

## 2. 角色与权限边界

### 2.1 学生

- 可访问：学生首页、知识诊断、刷题升本、错题中心、沉淀题库、积分段位、消息中心、快诊与订阅开通。
- 不可访问：教师端管理页面、超管配置页面。

### 2.2 教师

- 可访问：题目管理、试卷管理、考试任务、学情管理、消息发送、学生数据查看。
- 不可访问：学生订阅接口、学生首登转化页面。

### 2.3 超级管理员

- 可访问：系统设置、账号权限、内容基线、兑换码批次管理、转化看板。
- 具备全局兜底权限，但需遵循认证与 CSRF 安全策略。

## 3. 学生端核心流程

### 3.1 首登与分流

- 学生登录后进入学生入口。
- 若未完成首登引导，路由分流到 ` /student/onboarding/diagnosis `。
- 分流优先依据后端 `dashboard.onboarding.completed`，本地缓存仅兜底。

### 3.2 AI 快诊

- 学生完成 3-5 题快诊。
- 系统返回：答题数、正确数、正确率、建议动作。
- 快诊完成后写入 onboarding 快照，供首页和路由守卫使用。

### 3.3 订阅开通

- 两种方式：兑换码开通、模拟支付开通。
- 订阅状态统一：`INACTIVE / ACTIVE / EXPIRED`。
- 权益生效后进入“今日任务”主线。

### 3.4 首页权益态

- 首页显示三态：
  - 已开通：建议直接进入今日任务。
  - 已快诊未开通：建议去开通页。
  - 未快诊：建议先快诊。
- 首页提供 CTA：快诊、开通、权益状态、今日任务。

## 4. 教师端核心功能

- 题目全生命周期：草稿、提审、审核、发布、驳回。
- 试卷与考试任务：创建、下发、提交、评阅、统计。
- 学情看板：按科目/章节/知识点查看表现与趋势。
- 消息中心：对学生群体定向触达与追踪。

## 5. 超管端核心功能

- 系统配置：平台参数、AI 配额、奖励规则。
- 权限治理：账号角色、菜单权限、接口权限。
- 转化运营：兑换码批次、核销统计、转化漏斗。
- 发布治理：发布检查、证据归档、回滚资料。

## 6. 学生转化闭环接口（MVP）

- `GET /api/question-bank/student/subscription/status`
- `GET /api/question-bank/student/subscription/plans`
- `POST /api/question-bank/student/subscription/redeem`
- `POST /api/question-bank/student/subscription/mock-orders`
- `POST /api/question-bank/student/subscription/mock-orders/{orderId}/confirm`
- `POST /api/question-bank/student/diagnosis/quick/start`
- `POST /api/question-bank/student/diagnosis/quick/{sessionId}/submit`
- `GET /api/question-bank/student/dashboard`（含 `onboarding` 快照）

统一响应包：`{ code, message, data }`

## 7. 指标与口径

- 兑换成功率 = `redeem_success / redeem_submit`
- 模拟支付转化率 = `mock_payment_success / 结果页到达人数`
- 订阅开通率 = `subscription_activated / 注册成功人数`
- 次日留存 = `D+1 活跃注册用户 / D日注册用户`

## 8. 客服与运营处理口径

### 8.1 常见问题

- 兑换失败：优先核对“是否已兑换过、码是否过期、码是否已使用”。
- 权益未生效：核对订阅状态接口与订单/兑换日志。
- 页面跳转异常：核对登录角色与入口类型（学生/教师）。

### 8.2 升级路径

- 一级客服无法判定时，提交工单并附：userId、请求时间、接口路径、错误信息。
- 研发侧按“日志 -> 订单/兑换记录 -> 订阅状态 -> 路由行为”顺序排查。

## 9. 发布与回滚口径

- 发布前必须完成：构建、关键测试、守卫脚本 batch/final。
- 回滚触发条件：核心接口不可用、订阅状态错误、大面积分流异常。
- 回滚后必须复核：订阅状态查询、快诊提交、首页权益态展示。

## 10. 配套手册

- 客服手册：`docs/release/student-conversion-customer-support-manual-2026-03-26.md`
- 运营手册：`docs/release/student-conversion-operations-manual-2026-03-26.md`
- 发布复盘：`docs/release/student-conversion-mvp-retrospective-2026-03-26.md`

## 11. 术语表

- 快诊：首登 3-5 题的快速评估流程。
- 兑换码：运营发放的权益开通码，受规则限制。
- 模拟支付：用于联调与验收的支付闭环，不对接真实资金渠道。
- 权益态：学生是否具备订阅能力的当前状态。
