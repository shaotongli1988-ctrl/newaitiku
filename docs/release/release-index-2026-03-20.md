# 发布入口索引（2026-03-20）

## 一、这份文件是干什么的

- 这是本次发布的统一入口页。
- 如果只想打开一个文件完成本次上线准备、执行和收尾，就先看这里。

## 二、推荐阅读顺序

### 1. 先看最终结论和待办

- [最终上线清单](/Users/shaotongli/Documents/newaitiku/docs/release/final-release-checklist-2026-03-20.md)

适用场景：
- 想知道当前到底能不能上
- 想知道还差哪几项没签
- 想知道该谁确认

### 2. 再看发布总说明

- [发布就绪说明](/Users/shaotongli/Documents/newaitiku/docs/release/release-readiness-2026-03-20.md)

适用场景：
- 要开发布评审会
- 要给产品 / 测试 / 运维统一讲当前状态

### 3. 数据库相关只看这一组

- [数据库索引上线说明](/Users/shaotongli/Documents/newaitiku/docs/release/db-index-rollout-2026-03-20.md)

适用场景：
- DBA / 运维确认执行窗口
- 确认备份和回滚

### 4. 验收和测试只看这一组

- [UAT 交接说明](/Users/shaotongli/Documents/newaitiku/docs/release/uat-handoff-2026-03-20.md)
- [功能链路测试矩阵](/Users/shaotongli/Documents/newaitiku/docs/release/feature-chain-test-matrix-2026-03-21.md)
- [P0 E2E 补测任务清单](/Users/shaotongli/Documents/newaitiku/docs/release/p0-e2e-task-backlog-2026-03-21.md)

适用场景：
- 测试要组织 UAT
- 产品要补最终验收结论
- 想快速知道哪些链路已经自动化、哪些还要补测
- 想把 P0 缺口直接拆成可执行开发任务

### 5. 发布后观察只看这一组

- [可观测性说明](/Users/shaotongli/Documents/newaitiku/docs/release/observability-readiness-2026-03-20.md)
- [发布后 30 分钟值班安排](/Users/shaotongli/Documents/newaitiku/docs/release/release-watch-plan-2026-03-20.md)

适用场景：
- 开始发版前排值班
- 发版后 30 分钟盯盘

### 6. 打包和发布产物只看这一组

- [发布包清理检查](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-cleanup-2026-03-20.md)
- [发布包执行说明](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-execution-2026-03-20.md)
- [发布包保留 / 排除名单](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-manifest-2026-03-20.md)
- [当前仓库可发布目录清单（简版）](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-brief-2026-03-20.md)

适用场景：
- 运维确认打包目录
- 发布群同步“该带什么、不该带什么”

### 7. 群通知直接看这里

- [发布群通知模板](/Users/shaotongli/Documents/newaitiku/docs/release/release-group-message-template-2026-03-20.md)

适用场景：
- 发版前确认
- 发布开始通知
- 观察期同步
- 放行 / 回滚结论

### 8. 学习方法发布专题（2026-03-25）

- [学习方法发布文档归档](/Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-archive-2026-03-25.md)
- [学习方法发布包索引](/Users/shaotongli/Code/newaitiku/docs/release/learning-method-release-index-2026-03-25.md)
- [学习方法最终发布通知单页](/Users/shaotongli/Code/newaitiku/docs/release/learning-method-final-release-notice-onepage-2026-03-25.md)
- [学习方法企业群最终公告（纯文本）](/Users/shaotongli/Code/newaitiku/docs/release/learning-method-enterprise-final-plain-2026-03-25.txt)

适用场景：
- 需要直接进入学习方法模块提测/发布材料
- 希望产品、测试、研发、运维按角色快速拿到对应文档
- 需要可直接复制发送的企业群公告文本

## 三、当前最关键的待确认项

1. DBA / 运维确认 [数据库索引上线说明](/Users/shaotongli/Documents/newaitiku/docs/release/db-index-rollout-2026-03-20.md) 中的执行窗口、备份与回滚。
2. 产品 / 测试在 [最终上线清单](/Users/shaotongli/Documents/newaitiku/docs/release/final-release-checklist-2026-03-20.md) 中补最终验收结论。
3. 运维按 [发布后 30 分钟值班安排](/Users/shaotongli/Documents/newaitiku/docs/release/release-watch-plan-2026-03-20.md) 确认值班责任人。
4. 发布前按 [发布包保留 / 排除名单](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-manifest-2026-03-20.md) 做一次人工核对。

## 四、当前一句话结论

- 当前状态：**基本可上线**
- 当前建议：**建议补齐后上线**
- 当前分支：`codex/release-hardening`

## 五、以后怎么复用

- 下次上线时，优先复制这套 `docs/release/` 文档结构。
- 再按当次日期替换文件名和结论即可。
