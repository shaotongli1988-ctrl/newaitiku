# 发布群通知模板（2026-03-20）

## 一、发版前确认模板

```text
【发布前确认】
项目：题库系统
版本批次：2026-03-20
发布分支：codex/release-hardening

当前结论：基本可上线，建议补齐后上线

本次发布建议保留：
app/、frontend/（仅源码与构建配置）、static/、templates/、deploy/、data/schema.sql、requirements.txt、必要 scripts

明确不要带入发布：
tmp/、.shared-deps/、.codex-runtime/、tools/logs/、tests/、skills/、各类 .venv、frontend/node_modules/、frontend/dist/、本地 *.db、截图、日志、临时评审产物

已完成：
1. 超管 / 教师 / 学生关键路径自动化复核已通过（7/7）
2. 超管仍可通过 /login 正常登录
3. 发布文档、UAT 交接、可观测性说明、发布包清理说明已补齐

待最终确认：
1. DBA / 运维确认 schema.sql 索引执行窗口、备份与回滚
2. 产品 / 测试补最终验收结论
3. 运维确认发布后 30 分钟值班安排

请相关负责人确认是否允许进入正式发布窗口。
```

## 二、发布开始通知模板

```text
【发布开始】
项目：题库系统
版本批次：2026-03-20
发布时间：____
发布分支：codex/release-hardening

本次已进入发布窗口，请以下角色开始值班观察：
- 产品：____
- 研发：____
- 测试：____
- 运维：____

发布后 30 分钟重点观察链路：
1. 登录与鉴权
2. 学生首页与练习
3. 教师组卷与学情
4. 消息中心

若出现登录不可用、学生无法拉题/提交、教师组卷 5xx、数据库执行异常，请立即在群内同步并判断止血 / 回滚。
```

## 三、发布完成观察模板

```text
【发布完成，进入观察期】
项目：题库系统
版本批次：2026-03-20
发布完成时间：____

请按 30 分钟观察计划执行：
- 第 10 分钟结论：____
- 第 20 分钟结论：____
- 第 30 分钟结论：____

本轮重点确认：
1. /login 登录成功且跳转正确
2. /admin/home、/teacher/home、/student/home 可访问
3. 教师组卷页可打开列表与主要弹层
4. 学生练习页可拉题、可提交
5. 消息中心可查看未读消息
6. 无大面积 401 / 403 / 5xx

若 30 分钟内未出现阻断级问题，请同步最终放行结论。
```

## 四、放行 / 回滚结论模板

```text
【发布结论】
项目：题库系统
版本批次：2026-03-20
结论：____（放行 / 带风险放行 / 回滚）

产品结论：____
研发结论：____
测试结论：____
运维结论：____

补充说明：
1. ____
2. ____
```

## 五、参考文档

- [最终上线清单](/Users/shaotongli/Documents/newaitiku/docs/release/final-release-checklist-2026-03-20.md)
- [发布后 30 分钟值班安排](/Users/shaotongli/Documents/newaitiku/docs/release/release-watch-plan-2026-03-20.md)
- [数据库索引上线说明](/Users/shaotongli/Documents/newaitiku/docs/release/db-index-rollout-2026-03-20.md)
- [当前仓库可发布目录清单（简版）](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-brief-2026-03-20.md)
