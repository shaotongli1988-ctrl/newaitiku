# 学生转化闭环 MVP 运营手册

- 版本：v1.0（冻结）
- 日期：2026-03-26
- 适用角色：运营、增长、数据运营

## 1. 目标与指标

- 目标：提升“首登完成快诊并开通权益”的链路完成率。
- 核心指标：
  - `quickDiagnosisStartCount`
  - `quickDiagnosisCompleteCount`
  - `redeemSubmitCount`
  - `redeemSuccessCount`
  - `mockOrderCreatedCount`
  - `mockPaymentSuccessCount`
  - `subscriptionActivatedCount`

## 2. 日常运营动作

### 2.1 发码运营

- 在管理端创建兑换码批次：渠道、数量、有效期。
- 每次活动码必须有唯一 `channelCode`，便于复盘归因。
- 发码后 24h 内跟踪核销速度，异常时及时补充引导文案。

### 2.2 路径优化

- 重点观察断点：
  - 快诊开始 -> 快诊完成
  - 快诊完成 -> 兑换/模拟支付提交
  - 提交 -> 开通成功
- 若断点异常，优先调整文案与 CTA 顺序，再考虑改流程。

## 3. 观测与预警阈值（MVP）

- 兑换成功率（`redeemSuccess / redeemSubmit`）连续 2 个时段低于 30%：告警。
- 模拟支付成功率（`mockPaymentSuccess / mockOrderCreated`）低于 95%：告警。
- 快诊完成率（`quickDiagnosisComplete / quickDiagnosisStart`）低于 60%：告警。

## 4. 活动复盘模板

- 活动名称：
- 观察时间窗：
- 触达用户数：
- 关键漏斗：
  - 快诊开始：
  - 快诊完成：
  - 兑换提交：
  - 兑换成功：
  - 模拟支付成功：
  - 开通成功：
- 结论：
- 下轮优化动作：

## 5. 数据口径约束

- 所有运营看板口径与 `admin/conversion/overview` 保持一致。
- 不允许单独定义冲突口径覆盖系统主口径。
- 报表截图需保留日期范围与导出时间。

## 6. 版本冻结声明

- 本手册冻结于 2026-03-26，用于 MVP 发布期。
- 后续真实支付接入时，需新增渠道对账、退款、异常回调处置章节。
