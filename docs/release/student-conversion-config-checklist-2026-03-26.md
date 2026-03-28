# 学生端兑换码与订阅发布配置核对清单（2026-03-26）

## 1. 环境与配置

- 环境范围：`dev` / `test` / `prod`
- 核对项：学生端兑换码、订阅状态查询、快诊入口、Mock 订单确认接口
- 结论：本批次不新增环境变量，不修改既有配置键；沿用现有题库服务配置

## 2. 接口与部署证据

- OpenAPI：已更新 `docs/contracts/current/openapi.json`
- 发布检查：学生端发布清单已同步到 `docs/release/student-conversion-mvp-checklist-2026-03-26.md`
- 运维操作说明：已同步到 `docs/release/student-conversion-operations-manual-2026-03-26.md`
- 客服与回访说明：已同步到 `docs/release/student-conversion-customer-support-manual-2026-03-26.md`

## 3. 风险与回滚

- 风险：兑换码重复使用、订阅状态延迟、快诊会话过期
- 监控观察：重点观察兑换成功率、订阅激活事件、快诊提交完成率
- 回滚策略：回退到上一版服务逻辑，保留新增数据字段，按运维手册执行验证

## 4. 发布前确认

- [x] 配置项无新增无变更
- [x] 接口契约与文档已同步
- [x] 测试与权限回归已完成
- [x] 发布与回滚证据已归档
