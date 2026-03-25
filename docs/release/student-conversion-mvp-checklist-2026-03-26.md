# 学生转化闭环 MVP 发布验收清单

- 版本：v1.0
- 日期：2026-03-26
- 范围：快诊 + 兑换码 + 订阅 + 模拟支付 + 首页权益态

## 1. 发布前检查（必须全部通过）

### 1.1 接口可用性

- [ ] `GET /api/question-bank/student/dashboard` 返回 `onboarding` 快照。
- [ ] `POST /api/question-bank/student/diagnosis/quick/start` 可正常发起会话。
- [ ] `POST /api/question-bank/student/diagnosis/quick/{sessionId}/submit` 支持幂等。
- [ ] `POST /api/question-bank/student/subscription/redeem` 正常核销并返回权益状态。
- [ ] `POST /api/question-bank/student/subscription/mock-orders` 正常创建订单。
- [ ] `POST /api/question-bank/student/subscription/mock-orders/{orderId}/confirm` 重复确认不重复发放权益。

### 1.2 规则正确性

- [ ] 兑换码规则满足“一码一次、一号一次、过期不可用”。
- [ ] 订阅状态流转满足 `INACTIVE -> ACTIVE -> EXPIRED`。
- [ ] 学生首登未完成引导时会分流到快诊页。
- [ ] 首页权益态可区分“待快诊/待开通/已开通”。

### 1.3 权限与安全

- [ ] 教师/超管无法访问学生订阅与快诊接口。
- [ ] 认证与角色隔离符合现有合同口径。
- [ ] 日志不包含敏感凭据（token、明文密码等）。

## 2. 测试与构建证据

- [ ] 前端单测通过：`npm run test -- src/utils/studentOnboarding.test.js src/stores/userStore.test.js`
- [ ] 前端构建通过：`npm run build`
- [ ] 后端关键用例通过：
  - `python3 -m pytest tests/test_question_bank.py -k "dashboard_filtering or student_subscription_redeem_once_limit or student_quick_diagnosis_start_submit_and_idempotent"`
- [ ] 接口合同回归通过：`python3 -m pytest tests/integration/test_http_contracts.py`

## 3. 守卫与门禁

- [ ] `python3 scripts/unified_delivery_guard.py --phase batch`
- [ ] `python3 scripts/unified_delivery_guard.py --phase final`
- [ ] 无高风险阻断告警。

## 4. 灰度观察项（上线后 24h）

- [ ] 快诊开始数与完成数趋势稳定。
- [ ] 兑换提交与兑换成功比值在预期范围。
- [ ] 模拟支付确认成功率稳定，无幂等重复发放异常。
- [ ] 首页分流异常率（跳错页、死循环）为 0。

## 5. 回滚判定与动作

### 5.1 触发条件

- [ ] 学生大面积无法完成快诊或开通。
- [ ] 订阅状态错误导致权益误判。
- [ ] 首登分流出现循环跳转或阻断主流程。

### 5.2 回滚后复核

- [ ] 学生可正常进入首页主流程。
- [ ] 订阅状态接口返回正确。
- [ ] 快诊接口可发起并提交。
- [ ] 关键日志与告警恢复正常。

## 6. 验收结论

- 验收负责人：__________
- 验收时间：__________
- 结论：`通过 / 有条件通过 / 不通过`
- 备注：________________________________
