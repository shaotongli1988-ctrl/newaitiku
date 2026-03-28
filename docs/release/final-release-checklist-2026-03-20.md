# 最终上线清单（2026-03-20）

## 当前结论

- 当前状态：**基本可上线**
- 当前建议：**建议补齐后上线**
- 当前工作分支：`codex/release-hardening`
- 发布材料统一入口：
  - [发布入口索引](/Users/shaotongli/Documents/newaitiku/docs/release/release-index-2026-03-20.md)

## 一、已完成

- [x] 数据库初始化脚本已移除破坏性 `DROP TABLE`
- [x] 超管公开自动登录页已移除明文账号密码
- [x] 后端核心仓储层 `SELECT *` 已收敛到显式字段
- [x] 已从 `main` 切换到发布修复分支
- [x] 已补充发布总说明：
  - [发布就绪说明](/Users/shaotongli/Documents/newaitiku/docs/release/release-readiness-2026-03-20.md)
- [x] 已补充数据库上线说明：
  - [数据库索引上线说明](/Users/shaotongli/Documents/newaitiku/docs/release/db-index-rollout-2026-03-20.md)
- [x] 已补充 UAT 交接说明：
  - [UAT 交接说明](/Users/shaotongli/Documents/newaitiku/docs/release/uat-handoff-2026-03-20.md)
- [x] 已补充可观测性说明：
  - [可观测性说明](/Users/shaotongli/Documents/newaitiku/docs/release/observability-readiness-2026-03-20.md)
- [x] 静态页 `innerHTML` 风险已完成一轮集中收敛

## 二、上线前最后确认

### 数据库

- [ ] 确认 [schema.sql](/Users/shaotongli/Documents/newaitiku/data/schema.sql) 中索引执行方式已被 DBA/运维认可
- [ ] 确认执行窗口、备份方式、回滚方式已明确
- [ ] 确认不再通过任何方式执行破坏性重建脚本

### 前端与安全

- [x] 已复核当前仓库 `innerHTML` 使用点；未检出可追踪的前端源码命中，历史 `analytics.js` 保留说法已失效，不再作为可接受例外
- [x] 已确认 [frontend/public/auto-super-admin-login.html](/Users/shaotongli/Documents/newaitiku/frontend/public/auto-super-admin-login.html) 不再暴露凭据
- [x] 已确认超管通过 `/login` 正常登录

### 测试与验收

- [x] 已按 [UAT 交接说明](/Users/shaotongli/Documents/newaitiku/docs/release/uat-handoff-2026-03-20.md) 完成一轮超管 / 教师 / 学生关键路径自动化复核
- [ ] 补齐最终验收结论
- [x] 已确认当前关键路径无阻断级 Bug

### 可观测性

- [ ] 按 [发布后 30 分钟值班安排](/Users/shaotongli/Documents/newaitiku/docs/release/release-watch-plan-2026-03-20.md) 确认责任人与值班方式
- [x] 登录、题库、组卷、学生练习链路监控方式已说明

### Git 与发布包

- [x] 已确认当前工作分支仍为 `codex/release-hardening`
- [ ] 按 [发布包清理检查](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-cleanup-2026-03-20.md)、[发布包执行说明](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-execution-2026-03-20.md) 与 [发布包保留 / 排除名单](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-manifest-2026-03-20.md) 整理工作区，避免将临时文件、日志、测试数据库一起带入发布包
- [ ] 如需发群或同步运维，直接使用 [当前仓库可发布目录清单（简版）](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-brief-2026-03-20.md)
- [ ] 如需同步发布群，直接使用 [发布群通知模板](/Users/shaotongli/Documents/newaitiku/docs/release/release-group-message-template-2026-03-20.md)

## 三、可延期治理

- [ ] 继续系统性清理所有静态页脚本的历史 DOM 拼接写法
- [ ] 继续增强后端与前端可观测性证据
- [ ] 将本次上线材料模板化，作为后续版本固定使用

## 四、责任归属

### 产品

- [ ] 最终确认验收口径
- [ ] 确认是否允许进入正式上线流程

### 研发

- [ ] 最终确认数据库索引上线说明
- [ ] 最终确认剩余静态页风险是否可接受

### 测试

- [x] 已完成 UAT 关键路径自动化复核
- [ ] 输出最终验收结论

### 运维

- [ ] 确认执行窗口、备份与回滚
- [ ] 确认发布后值班与观察方式

## 五、最终决策栏

- 发布结论：__________
- 产品确认：__________
- 研发确认：__________
- 测试确认：__________
- 运维确认：__________
- 发布时间：__________
