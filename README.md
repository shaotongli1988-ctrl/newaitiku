# 题库初步构建

本目录已按需求文档中题库初版范围完成一套可运行的全端对齐实现，包含：

- 字段冻结与共享合同
- SQLite 建表脚本
- FastAPI 接口与后端服务
- 管理后台题库页面
- 知识点三级树页面
- 超管控制台
- 消息中心
- 内容体系字典页
- 专属学习台
- 学生端刷题页
- 我的题库统一页（错题中心 / 沉淀题库 / 考试大纲）
- 试卷管理页
- 学情页
- 校验、权限、异常处理
- 文档与自测

## ⚠️ 开发者守则 (Architecture Gourdrail)

严禁 在路由函数中使用 `payload: dict`，必须定义 Pydantic 模型。  
严禁 使用 `createdAt/updatedAt`，全站统一使用 `createTime/updateTime`。  
严禁 在前端直接调用 `axios`，所有请求必须经过 `services/questionBank.js`。  
必须 在提交代码前运行 `python3 scripts/unified_delivery_guard.py --phase final`。  
涉及题库 API 合同、OpenAPI 导出、前后端契约对齐的批次，优先运行 `python3 scripts/unified_delivery_guard_scoped.py --phase final`，避免无关目录扫描放大误报。

## 总技能统一入口

- 开发前准备总守卫：`python3 scripts/development_readiness_guard.py --phase start --task "<需求>"`
- 全端统一交付总守卫：`python3 scripts/unified_delivery_guard.py --phase final`
- 全端统一交付总守卫（题库 API scoped 入口）：`python3 scripts/unified_delivery_guard_scoped.py --phase final`
- 软件交付总守卫：`python3 scripts/software_delivery_guard.py --phase final`

## 三角色隔离口径

- 超管端（`super_admin`）：仅承接账号开设、账号启停、权限分配、系统设置。
- 教师端（`teacher`）：仅承接题库内容管理、知识点管理、试卷管理、学情监控与教学消息触达。
- 学生端（`student`）：仅承接学习台、刷题、我的题库与学习成长功能。
- 页面与接口均按角色守卫做强隔离，不提供跨端子功能入口。
- 三端功能梳理清单见：[docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md)

当前 question 模块固定字段为：

`id`, `knowledgeId`, `userId`, `type`, `stem`, `optionsJson`, `answer`, `status`, `extJson`, `createTime`, `updateTime`

当前题库运行基座使用以下表：

- `user`
- `userAuth`
- `knowledge`
- `question`
- `task`

历史表 `subjects`、`questions`、`question_reviews`、`student_question_bank`、`question_vectors` 已完成清理，不再作为运行时依赖。

当前前端唯一运行入口已统一为 `frontend/` 下的 Vue + Vite SPA 源码；历史 `static/`、`templates/` 页面源码已下线，不再作为运行时依赖。

## 启动

```bash
./tools/bin/bootstrap-python.sh
./tools/bin/run-dev.sh
./tools/bin/run-frontend-dev.sh
```

启动后访问：

- 前端单入口（开发态）：[http://127.0.0.1:5173/](http://127.0.0.1:5173/)
- 注册登录页：[http://127.0.0.1:5173/login](http://127.0.0.1:5173/login)
- 专属学习台：[http://127.0.0.1:5173/student/home](http://127.0.0.1:5173/student/home)
- 学生端刷题页：[http://127.0.0.1:5173/student/practice](http://127.0.0.1:5173/student/practice)
- 我的题库错题中心页：[http://127.0.0.1:5173/student/question-bank/repair](http://127.0.0.1:5173/student/question-bank/repair)
- 我的题库「沉淀题库」子页：[http://127.0.0.1:5173/student/question-bank/archive](http://127.0.0.1:5173/student/question-bank/archive)
- 我的题库考试大纲页：[http://127.0.0.1:5173/student/question-bank/syllabus](http://127.0.0.1:5173/student/question-bank/syllabus)
- 教师工作台：[http://127.0.0.1:5173/teacher/home](http://127.0.0.1:5173/teacher/home)
- 题库页面：[http://127.0.0.1:5173/teacher/questions](http://127.0.0.1:5173/teacher/questions)
- 超管控制台：[http://127.0.0.1:5173/admin/control-center](http://127.0.0.1:5173/admin/control-center)
- 消息中心：[http://127.0.0.1:5173/messages](http://127.0.0.1:5173/messages)
- 后端 API / 鉴权 / 文件服务：[http://127.0.0.1:8000](http://127.0.0.1:8000)

开发态单入口说明：

- 浏览器页面统一进入前端单入口，不再使用 `student.html` / `teacher.html` 双入口。
- 后端 `8000` 仅承接 API、登录态、文件下载和前端壳桥接；开发态浏览器访问旧页面 URL 时会自动跳转到 `5173` 对应前端路由。
- 生产部署由 Nginx 统一把非 `/api` 路由回退到 `index.html`，浏览器仍然只进入同一套前端 SPA。
- 学生端页面入口已统一到 `/student/question-bank/*`；旧的 `/student/wrong-book` 与 `/student/personal-bank` 当前仅保留重定向兼容。

错题中心当前实现口径：

- 错题中心列表使用真实分页；前端默认按页加载，不再只取前 100 条。
- `GET /api/question-bank/student/wrong-book/questions` 与 `GET /api/question-bank/student/wrong-book/summary` 统一支持 `subjectCode / chapterCode / pointCode / knowledgeId / knowledgePathNodeId` 作用域参数。
- `POST /api/question-bank/student/wrong-book/questions/{question_id}/review` 仅记录“回顾行为”，不再直接把题目标记为“熟悉/已斩获”。
- `POST /api/question-bank/student/wrong-book/papers` 会遵守当前错题中心筛选范围生成修复卷。
- `student_question_record` 现已扩展承接错题热状态；错题中心读取时优先使用正式列，`extJson.wrongBook` 退回兼容镜像。
- 错题中心当前页支持“全选当前页 / 清空勾选 / 批量打印已选题”；详情区补充展示最近答案、作答次数、错后再练和最近错因，便于复盘。

## 学习首页补充说明

- 学生端学习首页的“掌握度雷达”现在统一使用中文科目名展示维度，不再直接暴露 `subjectId` 英文代码。
- 雷达图用于“科目层总览”，按正确率、速度分、训练频次聚合出掌握度；点击任一维度会跳转到自由练习并自动带上对应科目。
- “知识星系”用于“章节与考点下钻”，默认展示 L3-L4 结构，展开后查看 L5 考点，因此与雷达存在弱项定位上的关联，但不是重复页面。
- 前端自测建议至少覆盖：
  - 中文科目名映射优先于 `subjectId`
  - 英文/空值兜底标签仍可正常渲染
  - 雷达掌握度计算口径保持 `正确率 0.6 + 速度分 0.2 + 训练频次 0.2`

## 2026 学生端视觉重构说明

- 全站主题变量已统一收敛到 `frontend/src/style/main.css`，主色为 `#2F54EB`，成功色为 `#52C41A`，系统底色为 `#F0F2F5`，卡片圆角统一为 `8px`。
- 全局字体族切换为 `"HarmonyOS Sans SC", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif`；正文阅读节奏统一为 `line-height: 1.8` 与 `letter-spacing: 0.02em`，题干正文统一使用 `.question-body` 的 `15px / 1.7` 阅读基线。
- 学生端 `Layout` 现在默认以图标化折叠侧栏进入，Header 下方新增全局 Breadcrumb，仅展示当前选中的 `L4 / L5` 知识路径。
- `Student/Analysis.vue` 已改为学术精准与数据洞察风格的旭日图：内环映射 `L4`，外环映射 `L5`，颜色映射掌握度，并直接对接 `/api/knowledge-tree`。
- `Student/Home.vue` 已重构为学生学习台唯一首页入口，承接预测分 Banner、掌握度雷达、AI 助教建议、知识诊断入口与科目卡片流；完整今日任务已并入 `知识诊断 > 今日任务`。
- `Student/WrongBook.vue` 已重构为“左侧科目红点导航 + 顶部学情诊断仪表盘 + 中部诊断题卡流 + 右侧 AI 助教面板”，题卡内部不再重复展示 `L1 > L2 > L3 ...` 路径，页面级路径信息统一由全局 Breadcrumb 承担。

## 2026-03 学生学习台主体重构交付总览

- 交付总览：`frontend/src/views/Student/Home.vue` 已收敛为学生学习台唯一首页入口，首屏聚合淡蓝预测分 Banner、左侧掌握度雷达、右侧 AI 助教建议与知识诊断入口，以及底部三列科目卡片流；今日任务统一收进 `知识诊断` 二级页。
- 前端说明：全站主内容区背景统一为 `#F0F2F5`，卡片移除显式边框并统一为 `0 1px 4px rgba(0,21,41,.08)` 阴影；正文阅读节奏统一为 `line-height: 1.8` 与 `letter-spacing: 0.02em`。
- 前端说明：`frontend/src/components/student/MasteryRadar.vue` 现支持双序列模式，新用户默认展示所属专业组参考曲线；`frontend/src/layouts/DefaultLayout.vue` 同步收敛主壳层背景和面包屑卡片样式。
- 后端说明：`/api/knowledge-tree` 响应契约已补齐 `wrongCount` 字段，避免知识树节点数据在 FastAPI 响应校验阶段触发 `500`。
- 测试说明：已补充知识树响应字段回归测试，并验证学生端自动登录后首页可稳定停留在 `/student/home`，不再因知识树接口异常跳转系统错误页。
- 测试说明：首页视图模型相关规则已补到 `frontend/src/utils/studentHomeViewModel.test.js`，覆盖正常路径、异常路径、边界路径和前端联动场景关键词。
- 测试说明：本次页面改造至少应手动验证学生端 `Home -> Analysis -> Practice` 的前端联动，以及无个人学情数据时 Hero 仪表盘默认显示 `215 / 300`、雷达图回退到参考曲线的行为。

## 2026-03 全局视觉脱脂与 Typography 规范化

- 交付总览：全局卡片样式已统一到更轻的视觉基线，`el-card` 默认内边距提升到 `24px`，纵向卡片间距收敛到 `20px`，阴影统一为 `0 1px 4px rgba(0,21,41,.08)`。
- 前端说明：`frontend/src/layouts/DefaultLayout.vue` 已移除 Header 内部的 5 级路径卡片，改为 Header 下方全局 Breadcrumb，仅显示当前选中的 `L4 / L5` 路径，文字颜色固定为 `#8c8c8c`。
- 前端说明：`frontend/src/views/Student/WrongBook.vue` 已移除题卡内部重复的 `L1 > L2 > L3 ...` 面包屑，页面路径信息统一交由全局 Breadcrumb 承担。
- 前端说明：标题层级统一为 `18px / 600 / #262626`，题干类正文统一为 `15px / 1.7`，辅助信息统一为 `12px / #595959`。
- 测试说明：`frontend/src/utils/layoutBreadcrumb.test.js` 已覆盖正常路径、异常路径、边界路径和前端联动下的全局 Breadcrumb 提取规则。

## 测试说明补充

- 前端单测：`cd frontend && npm test`
- 前端构建验证：`cd frontend && npm run build`
- 仓库级 Python 单元 / 集成 / 回归 / E2E：`./tools/bin/run-tests.sh`
- 如果本机没有全局 `pytest`，请优先使用仓库脚本，它会自动走 `.venv/bin/python` 执行测试。

## 生产部署准备

已提供生产部署基础配置：

- Nginx 配置：[deploy/nginx.conf](/Users/shaotongli/Documents/newaitiku/deploy/nginx.conf)
  - 前端静态资源托管（`/` + `/assets`）
  - `/api` 反向代理到 `backend:8000`
- 前端镜像构建：[deploy/Dockerfile.frontend](/Users/shaotongli/Documents/newaitiku/deploy/Dockerfile.frontend)
- 组合部署样例：[deploy/docker-compose.prod.yml](/Users/shaotongli/Documents/newaitiku/deploy/docker-compose.prod.yml)

## 关键接口

- `GET /api/question-bank/subjects`
- `POST /api/question-bank/auth/sms-code`
- `POST /api/question-bank/auth/register`
- `POST /api/question-bank/auth/login/password`
- `POST /api/question-bank/auth/login/sms`
- `POST /api/question-bank/auth/password/reset`
- `POST /api/question-bank/auth/logout`
- `GET /api/question-bank/auth/me`
- `GET /api/question-bank/content/baseline`
- `GET /api/question-bank/knowledge/tree`
- `GET /api/question-bank/knowledge/children`
- `GET /api/question-bank/knowledge/{knowledge_id}`
- `POST /api/question-bank/knowledge`
- `PUT /api/question-bank/knowledge/{knowledge_id}`
- `POST /api/question-bank/knowledge/{knowledge_id}/prerequisites`
- `POST /api/question-bank/knowledge/layout`
- `DELETE /api/question-bank/knowledge/{knowledge_id}`
- `POST /api/question-bank/knowledge/deleted/{snapshot_id}/restore`
- `POST /api/question-bank/knowledge/{knowledge_id}/sort/{direction}`
- `GET /api/question-bank/admin/console`
- `GET /api/question-bank/admin/settings`
- `POST /api/question-bank/admin/settings`
- `GET /api/question-bank/admin/users`（支持 `page`、`size`、`role`、`keyword`）
- `POST /api/question-bank/admin/users`
- `POST /api/question-bank/admin/students/import`
- `GET /api/question-bank/admin/students/export`
- `GET /api/question-bank/admin/learning-methods`
- `POST /api/question-bank/admin/learning-methods`
- `PUT /api/question-bank/admin/learning-methods/{method_code}`
- `POST /api/question-bank/admin/learning-methods/sort`
- `GET /api/question-bank/messages`
- `POST /api/question-bank/messages/{message_id}/read`
- `POST /api/question-bank/messages/read/batch`
- `GET /api/question-bank/messages/unread-count`
- `GET /api/question-bank/messages/settings`
- `POST /api/question-bank/messages/settings`
- `POST /api/question-bank/messages/send`
- `GET /api/question-bank/messages/send-history`
- `POST /api/question-bank/messages/send-history/{trace_id}/recall`
- `GET /api/question-bank/tasks`
- `GET /api/question-bank/tasks/{task_id}`
- `POST /api/question-bank/tasks/{task_id}/cancel`
- `GET /api/question-bank/questions`
- `GET /api/question-bank/questions/{question_id}`
- `GET /api/question-bank/questions/{question_id}/reviews`
- `POST /api/question-bank/questions`
- `PUT /api/question-bank/questions/{question_id}`
- `DELETE /api/question-bank/questions/{question_id}`
- `POST /api/question-bank/questions/deleted/{snapshot_id}/restore`
- `POST /api/question-bank/questions/delete/batch`
- `POST /api/question-bank/questions/deleted/batch/{snapshot_id}/restore`
- `POST /api/question-bank/questions/{question_id}/status/{target_status}`
- `POST /api/question-bank/questions/status/batch`
- `POST /api/question-bank/imports/template/preview`
- `POST /api/question-bank/imports/template`
- `GET /api/question-bank/imports/template/example`
- `GET /api/question-bank/papers/questions`
- `GET /api/question-bank/papers/overview`
- `GET /api/question-bank/papers/templates`
- `POST /api/question-bank/papers/templates`
- `DELETE /api/question-bank/papers/templates/{template_id}`
- `POST /api/question-bank/papers/templates/deleted/{snapshot_id}/restore`
- `POST /api/question-bank/papers/manual`
- `POST /api/question-bank/papers/auto`
- `POST /api/question-bank/papers/{paper_id}/status/{paper_status}`
- `DELETE /api/question-bank/papers/{paper_id}`
- `POST /api/question-bank/papers/deleted/{snapshot_id}/restore`
- `GET /api/question-bank/papers/{paper_id}/export`
- `GET /api/question-bank/student/practice/questions`
- `GET /api/question-bank/student/practice/chapters`
- `GET /api/question-bank/learning-methods`
- `GET /api/question-bank/learning-methods/{method_code}`
- `POST /api/question-bank/learning-methods/{method_code}/start`
- `POST /api/question-bank/learning-methods/{method_code}/complete`
- `GET /api/question-bank/student/personal-bank/questions`
- `GET /api/question-bank/student/personal-bank/summary`
- `GET /api/question-bank/student/personal-bank/export`
- `GET /api/question-bank/student/dashboard`
- `POST /api/question-bank/student/profile`
- `POST /api/question-bank/student/check-in`
- `POST /api/question-bank/student/practice/questions/{question_id}/submit`
- `POST /api/question-bank/student/practice/questions/{question_id}/wrong-book`
- `POST /api/question-bank/student/practice/questions/{question_id}/personal-bank`
- `POST /api/question-bank/student/practice/questions/{question_id}/ai-marking`
- `POST /api/question-bank/student/practice/questions/{question_id}/ai-tutor`
- `GET /api/question-bank/student/wrong-book/questions`
- `GET /api/question-bank/student/wrong-book/summary`
- `POST /api/question-bank/student/wrong-book/questions/{question_id}/review`
- `POST /api/question-bank/student/wrong-book/papers`
- `GET /api/question-bank/student/papers/questions`
- `GET /api/question-bank/student/papers/reports`
- `GET /api/question-bank/student/papers/reports/{report_id}`
- `GET /api/question-bank/student/papers/{paper_id}/questions`
- `POST /api/question-bank/student/papers/{paper_id}/submit`
- `GET /api/question-bank/analytics/records`
- `GET /api/question-bank/analytics/summary`
- `GET /api/question-bank/analytics/export`

说明：

- 角色门户中的“进入超管控制台”入口会先跳转到 `/login`，登录成功后再访问超管页与超管接口。

## 自测

固定验收命令：

```bash
./tools/bin/run-acceptance.sh
```

这条命令是后续每一轮修改后的统一回归入口，会串行执行仓库级统一对齐检查、`py_compile` 和 `unit / integration / regression / e2e` 全套自动化测试。

测试环境一致性建议：

- 首次或切换分支后，先执行 `./tools/bin/bootstrap-python.sh`（默认安装 `requirements-dev.txt`）。
- 直接运行 pytest 时，优先用 `./.venv/bin/python -m pytest`，不要直接用 `./.venv/bin/pytest`，可避免虚拟环境 shebang 指向旧路径导致的模块找不到问题。
- 若出现“已安装但导入失败”，可删除 `.venv` 后重新执行 `./tools/bin/bootstrap-python.sh`。

```bash
./tools/bin/run-acceptance.sh
./tools/bin/check-alignment.sh
./tools/bin/install-launchd-alignment.sh
./tools/bin/watch-alignment.sh
./tools/bin/run-tests.sh
./tools/bin/run-click-replay.sh --role all --base-url http://127.0.0.1:8017
./tools/bin/run-unit-tests.sh
./tools/bin/run-integration-tests.sh
./tools/bin/run-regression-tests.sh
./tools/bin/run-e2e-tests.sh
```

当前状态：统一对齐守卫与四类测试套件均已收口通过，具体通过条目以最近一次命令输出为准（避免文档固化数字产生漂移）。

`./tools/bin/run-acceptance.sh` 是推荐的固定验收命令，默认直接委托给 `./tools/bin/check-alignment.sh`，适合每次功能修改后做完整回归。
`./tools/bin/check-alignment.sh` 会执行仓库级统一对齐校验，包括固定合同、关键文档、前端绑定、`py_compile` 和 `unit / integration / regression / e2e` 四类测试。
`./tools/bin/run-tests.sh` 现在是统一测试入口，支持：

- `./tools/bin/run-tests.sh --suite unit`
- `./tools/bin/run-tests.sh --suite integration`
- `./tools/bin/run-tests.sh --suite regression`
- `./tools/bin/run-tests.sh --suite e2e`
- `./tools/bin/run-tests.sh --suite all`
- `./tools/bin/run-tests.sh --suite auto --paths app/service.py tests/e2e/test_question_bank_journey.py`

三端统一真点击回放入口：

- `./tools/bin/run-click-replay.sh --role super_admin`
- `./tools/bin/run-click-replay.sh --role teacher`
- `./tools/bin/run-click-replay.sh --role student`
- `./tools/bin/run-click-replay.sh --role all --base-url http://127.0.0.1:8017`
- `./tools/bin/run-knowledge-galaxy-click-replay.sh --base-url http://127.0.0.1:5173 --api-base-url http://127.0.0.1:8000`

首次执行前请安装 Playwright 浏览器：

```bash
./tools/bin/bootstrap-python.sh
./.venv/bin/python -m playwright install chromium
```

真点击输出约定：

- 结果 JSON：`docs/<role>-click-replay-result-YYYY-MM-DD.json`
- 报告 Markdown：`docs/<role>-click-replay-report-YYYY-MM-DD.md`
- 汇总报告：`docs/three-end-click-replay-summary-YYYY-MM-DD.md`
- 统一清单：`docs/three-end-true-click-checklist.md`
- 学生端文案基线清单：`docs/release/student-copy-baseline-acceptance-2026-03-23.md`
- 统一结果 Schema：`docs/click-replay-result-schema.json`

`./tools/bin/watch-alignment.sh` 会持续监听核心目录，检测到新增、修改或删除并静置几秒后自动触发一轮 `batch` 校验，再根据变更路径自动选择匹配测试套件。
`./tools/bin/install-launchd-alignment.sh` 会把 watcher 安装成当前用户的 `LaunchAgent`，让它在后台常驻运行。

## 环境目录

根目录新增 [tools/README.md](/Users/shaotongli/Documents/newaitiku/tools/README.md) 作为统一环境目录：

- `tools/bin`：统一放启动、安装、测试脚本
- `tools/python`：统一放 Python 依赖入口
- `tools/packages`：统一缓存依赖包，便于重复安装和环境迁移

## CI

仓库已补充 GitHub Actions 工作流 [unified-alignment-ci.yml](/Users/shaotongli/Documents/newaitiku/.github/workflows/unified-alignment-ci.yml)，在 `push`、`pull_request` 和手动触发时自动执行：

- `./tools/bin/bootstrap-python.sh`
- `./tools/bin/run-ci.sh`

## 自动触发

如果你希望“改完一个功能就自动触发校验”，本地直接开一个监听进程：

```bash
./tools/bin/watch-alignment.sh
```

默认行为：

- 监听 `app/`、`frontend/`、`docs/`、`tests/`、`tools/`、`scripts/`、`.github/`、`README.md`、`requirements.txt`、`pytest.ini`、`data/schema.sql`
- 文件改动后等待约 2 秒，避免连续保存时重复触发
- 自动执行 `batch + py_compile + 变更路径匹配测试`

如果你想每次改动后都顺带跑全量测试，可以用：

```bash
./tools/bin/watch-alignment.sh --full
```

如果你希望登录后自动后台常驻，安装 `launchd` 版本：

```bash
./tools/bin/install-launchd-alignment.sh
```

注意：

- 当前仓库如果位于 `~/Documents`、`~/Desktop`、`~/Downloads` 这类 macOS 受保护目录，`launchd` 后台进程通常会被系统隐私策略拦截。
- 更稳妥的做法是把仓库移动到 `~/Code/newaitiku` 这类非受保护路径后再安装。

常用命令：

- 安装并启动：`./tools/bin/install-launchd-alignment.sh`
- 安装并启用全量模式：`./tools/bin/install-launchd-alignment.sh --full`
- 查看状态：`./tools/bin/status-launchd-alignment.sh`
- 查看日志：`./tools/bin/logs-launchd-alignment.sh`
- 卸载：`./tools/bin/uninstall-launchd-alignment.sh`

## 本轮增强

- 认证闭环：新增短信验证码、注册、密码登录、短信登录、重置密码、登录态查询与退出登录接口，前端改为 HttpOnly Cookie 会话并兼容 Bearer Token。
- 安全增强：超管写接口增加 CSRF 双提交校验（`qbCsrfToken` + `X-CSRF-Token`），Cookie 安全属性按环境收口（生产默认 `Secure=true`、`SameSite=Strict`）。
- 登录风控：密码登录按手机号/IP 做失败限流，达到阈值后锁定 10 分钟。
- 章节闯关硬约束：学生练习题列表仅返回已解锁章节，非首章节需上一章节正确率达到 80% 才可解锁。
- 练习计时判定：单题提交超过 `practiceConfig.timeLimitSec` 统一按超时判错并回写 `isTimeout`。
- 模拟卷倒计时：学生端新增“倒计时：--:--”与自动交卷逻辑，到时自动提交并生成报告。
- 章节树状态增强：新增学生章节状态接口，左侧树展示“未解锁 / 已解锁 / 正在闯关”与章节正确率，未解锁章节前端禁入。
- 模拟暂停机制：单场模拟支持暂停/恢复，最多 3 次，每次最多 10 分钟，超时自动恢复。
- 交卷判分收紧：未作答题目统一按错处理；主观题在交卷后入 `AI_MARKING` 任务队列异步批改，并在交卷响应返回待处理任务 ID。
- 模拟提交幂等：同一试卷当日重复提交按幂等返回历史结果，避免网络重试造成重复记分。
- 每日科目限制：同一学生同一科目每日最多完成 1 次全真模拟考试。
- 报告回看补齐：新增学生端 `papers/reports` 报告列表接口，页面展示最近模拟报告。
- 报告可追踪批改：`papers/reports` 增加 `subjectiveMarking` 汇总，直接查看主观题任务待处理数、完成数与平均分。
- 报告详情可回看：新增 `papers/reports/{report_id}` 详情接口，返回 `typeAccuracy`、`questionResults`、`summary`，历史列表支持一键查看详情。
- 报告历史可累计：报告记录引入 `reportId`，同一试卷不同日期的模拟成绩不再被覆盖，支持后续趋势回看。
- 权限守卫补强：页面与接口统一校验账号启停状态，并按 `question:manage`、`paper:manage`、`analytics:view`、`student:manage`、`settings:manage`、`message:send` 权限点拦截。
- 校验补强：补充导入文件类型、学情日期区间、导出格式、批量导入重复账号等边界校验。
- 学情页增强：新增 `timeRangeLabel`、`coverageRate`、`averageAnswerDurationSec`、`masteredStudentCount`、`atRiskStudentCount`、`studentRankings`。
- 导入导出完善：新增题目录入模板示例、考生目录导出、沉淀题库导出，并统一支持格式校验与页面入口。
- 题库页交互收紧：模板示例改为走后端权威接口，导入结果支持块级错误回显，题目弹窗补齐 `optionsJson` / `extJson` 前端预校验与格式化按钮。
- 录题体验增强：新增“导入预览校对 -> 确认导入当前预览”流程，预览题目可直接载入单题录入弹窗复核，详情弹窗升级为结构化展示固定字段、选项、扩展摘要与审核轨迹。
- 导入失败可追溯：题库模板预览/导入新增 `errorLog` 与 `errorLogFileName`，页面支持一键下载失败日志后修正重导。
- 模拟进度可恢复：全真模拟答题过程实时本地存档，浏览器异常关闭或网络波动后可自动恢复未交卷进度。
- 教师审核池补齐：题库列表对教师开放 `QA_IN_PROGRESS` + `REVIEW_PENDING` 审核池视角，终审协作不再漏单。
- 学情分页修复：`analytics/records` 改为单次分页，`total` 与分页大小解耦；学情明细页补齐分页导航。
- 教师检索增强：题库筛选新增 `keyword`，统一按题干与扩展字段检索，列表按 `updateTime` 倒序。
- 组卷题池增强：试卷管理新增题池筛选、分页、勾选入卷、已勾选同步写入手动组卷表单。
- 试卷状态机收紧：试卷流转固定为 `草稿 -> 待审核 -> 已发布 -> 已下架 -> 待审核` 口径，不再允许跨级发布。
- 审核轨迹增强：审核记录新增 `createTime`，并在 `question.extJson.reviewSummary` 维护审核汇总。
- 删除安全增强：题目与试卷删除新增二次确认，并返回 `undoSnapshotId` 支持撤销恢复。
- 消息中心增强：Vue 版消息中心已补齐消息设置、分类筛选、批量已读、快捷模板、分群/定时发送、发送历史与撤回。

## 2026 内容体系落地

项目已按 [河北专升本题库内容体系基准文档_2026版](/Users/shaotongli/Documents/newaitiku/河北专升本题库内容体系基准文档_2026版.md) 接入统一内容层级：

- 先落 `学科门类 + 联考专业组 + 科目` 三层字典
- 不改题目固定字段，内容体系元数据继续进入 `extJson`
- 学生画像统一使用 `examCategoryCode`、`jointExamGroupCode`
- 刷题、组卷、学情统一支持 `examCategoryCode`、`jointExamGroupCode`、`subjectCode` 筛选
- 系统设置、账号目录、消息中心、组卷模板等低频扩展数据统一进入系统用户 `user(id="__system__").extJson`
- 学生题目态、试卷报告、消息发送历史已完成拆表，分别落在 `student_question_record`、`paper_report`、`message_send_history`
- AI 异步流程固定使用 `task` 表，任务结果回写对应 `task.extJson`

## 对齐说明

字段与合同说明见 [docs/question-bank-contract.md](/Users/shaotongli/Documents/newaitiku/docs/question-bank-contract.md)。

knowledge 模块说明见 [docs/knowledge-module.md](/Users/shaotongli/Documents/newaitiku/docs/knowledge-module.md)。
