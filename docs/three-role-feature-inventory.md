# 三端功能梳理（超管端 / 教师端 / 学生端）

更新时间：2026-03-18

## 1. 梳理范围

本清单基于当前仓库已实现能力梳理，覆盖：

- 页面入口（`frontend/index.html`、`frontend/src/entries/*.js`、`frontend/src/router/*.js`）
- 前端可操作动作（`frontend/src/views/*.vue` + `frontend/src/api/services/*.js`）
- 后端接口与角色守卫（`app/main.py` + `app/auth.py`）

不包含尚未落地的规划项，仅描述当前可用能力。

## 2. 三端角色边界

- 超管端（`super_admin`）：账号、权限、系统配置、考生目录治理。
- 教师端（`teacher`）：题库、知识点、内容体系、试卷、学情、教学消息触达。
- 学生端（`student`）：学习台、章节刷题、模拟考试、我的题库、学习成长。

核心隔离规则：

- 超管页面与超管接口仅允许登录态访问，且必须是 `super_admin`。
- 教师管理页面与接口要求教师角色，且受权限点校验。
- 学生页面与接口仅允许学生角色。

## 3. 超管端功能清单

### 3.1 页面入口

- `/admin/home`（管理驾驶舱）
- `/admin/control-center`（超管控制台）
- `/admin/syllabus`（大纲仓库）
- `/messages`（消息中心：可查看/设置，不可发送教学消息）
- `/login`（账号中心）

### 3.2 核心功能

- 登录态与安全治理
- 未登录访问超管页自动跳转 `/login`
- 写接口启用 CSRF 双提交校验（`qbCsrfToken` + `X-CSRF-Token`）
- 系统设置维护
- 平台名称、默认考试时长、积分规则、AI每日配额等参数维护
- 账号与权限治理
- 账号新建/更新、启停控制、角色分配
- 教师权限点维护（如 `question:manage`、`paper:manage`、`analytics:view`、`message:send`）
- 学生账号要求绑定报考大类与联考专业组
- 考生批量导入导出
- 文本模板批量导入考生
- 按 `csv/pdf` 导出考生目录
- 账号目录检索分页
- 按角色与关键词过滤
- 分页浏览账号目录

### 3.3 关键接口

- `GET /api/question-bank/admin/console`
- `GET /api/question-bank/admin/settings`
- `POST /api/question-bank/admin/settings`
- `GET /api/question-bank/admin/users`
- `POST /api/question-bank/admin/users`
- `POST /api/question-bank/admin/students/import`
- `GET /api/question-bank/admin/students/export`

### 3.4 权限点

- `settings:manage`：系统设置与控制台摘要
- `student:manage`：账号目录、考生导入导出

## 4. 教师端功能清单

### 4.1 页面入口

- `/teacher/questions`（题库管理）
- `/teacher/knowledge`（知识点三级树）
- `/teacher/content-system`（内容体系字典）
- `/teacher/papers`（试卷管理）
- `/teacher/analytics`（学情管理）
- `/messages`（消息中心）

### 4.2 核心功能

- 题库管理
- 单题新增/编辑/删除
- 题目筛选（知识点、题型、状态、大类、专业组、科目等）
- 题目状态流转（单题/批量）与审核轨迹查看
- 批量删除与撤销恢复
- 模板导入（预览校对、勾选导入、失败日志下载）
- 知识点三级树
- 树形浏览、关键词过滤、展开/折叠
- 节点增删改、上下移动排序
- 删除撤销恢复
- 内容体系字典
- 查看政策版本、大类、联考专业组、科目三层基线数据
- 试卷管理
- 手动组卷、自动组卷
- 组卷模板保存/删除/恢复
- 试卷状态流转（草稿、待审核、发布、下架）
- 试卷导出与删除恢复
- 学情管理
- 学情汇总看板（覆盖率、正确率、掌握度、风险学生等）
- 刷题明细分页查询
- 学情报表导出（`csv/pdf`）
- 教学消息触达
- 教师可发送学习提醒/周报/系统公告
- 支持按用户ID或按分群发送
- 支持定时发送、发送历史、撤回

### 4.3 关键接口

- 题库：`/api/question-bank/questions*`、`/api/question-bank/imports/template*`
- 知识点：`/api/question-bank/knowledge*`
- 内容体系：`GET /api/question-bank/content/baseline`
- 试卷：`/api/question-bank/papers*`
- 学情：`/api/question-bank/analytics*`
- 消息：`/api/question-bank/messages*`

### 4.4 权限点

- `question:manage`：题库与知识点
- `paper:manage`：内容体系与试卷
- `analytics:view`：学情查询与导出
- `message:send`：消息发送、历史、撤回

## 5. 学生端功能清单

### 5.1 页面入口

- `/student/home`（专属学习台）
- `/student/practice`（章节刷题 + 全真模拟）
- `/student/question-bank/repair`（我的题库 > 错题中心）
- `/student/question-bank/archive`（我的题库 > 沉淀题库）
- `/student/question-bank/syllabus`（我的题库 > 考试大纲）
- `/messages`（消息中心）
- `/login`（账号中心）

### 5.2 核心功能

- 专属学习台
- 报考大类/联考专业组设置
- 每日任务、成长头衔、核心科目进度、积分流水
- 每日打卡与积分发放
- 章节闯关刷题
- 科目树 + 章节解锁（上一章节正确率达标后解锁）
- 题目作答提交（含答题耗时）
- 标记重点复习、加入错题记录、加入/移出沉淀题库
- 主观题 AI 批改、全题型 AI 答疑
- AI任务队列可视化与取消
- 草稿自动保存与离开提醒
- 全真模拟考试
- 试卷列表与试题作答
- 倒计时、自动交卷
- 暂停/恢复（最多 3 次，每次最多 10 分钟）
- 本地草稿恢复
- 交卷前风险检查（未答题、主观题过短、多选疑似漏选、标记待查）
- 报告生成与历史报告回看
- 我的题库
- 错题中心、沉淀题库与考试大纲三子页
- 错题列表、错因统计
- 按错因生成专项巩固卷
- 生成 AI 专属同类卷
- 错题复习打点
- 沉淀题库
- 收藏题统计、复习计划与归档恢复
- 题目筛选、分批加载
- 在沉淀题库内直接作答、AI批改、AI答疑
- 导出沉淀题库（`csv/pdf`）
- 考试大纲
- 汇总展示全部考试科目的大纲，并以思维导图式查看结构
- 消息中心
- 消息筛选、单条已读、批量已读
- 个人消息偏好设置

### 5.3 关键接口

- 学习台：`/api/question-bank/student/dashboard`、`/student/profile`、`/student/check-in`
- 练习：`/api/question-bank/student/practice/*`
- 我的题库（页面统一）
- 错题中心接口仍为：`/api/question-bank/student/wrong-book/*`
- 沉淀题库接口仍为：`/api/question-bank/student/personal-bank/*`
- 考试大纲接口：`/api/question-bank/student/syllabus/catalog`
- 模拟卷：`/api/question-bank/student/papers/*`
- 任务：`/api/question-bank/tasks*`
- 消息：`/api/question-bank/messages*`

### 5.4 权限点

- 学生端为角色隔离访问，不依赖教师/超管权限点。

## 6. 三端业务闭环

- 超管 -> 教师
- 超管创建并启用教师账号，分配权限点，教师端功能才可访问。
- 教师 -> 学生
- 教师发布题目与试卷后，学生端可见并可作答。
- 学生 -> 教师
- 学生作答、交卷、AI任务结果会进入学情统计，教师端可查询与导出。
- 教师 -> 学生
- 教师通过消息中心向学生定向/分群触达学习提醒与公告。

## 7. 建议的验收入口

- 三端联调验收：`./tools/bin/run-click-replay.sh --role all --base-url http://127.0.0.1:8017`
- 三端手工清单：`docs/three-end-true-click-checklist.md`

## 8. 实测达成度（2026-03-18）

### 8.1 本轮执行记录

- 真点击回放：`./tools/bin/run-click-replay.sh --role all`
  - 结果：`super_admin 8/8 PASS`、`teacher 4/4 PASS`、`student 4/4 PASS`
  - 汇总：`docs/three-end-click-replay-summary-2026-03-18.md`
- 自动化测试：`./tools/bin/run-tests.sh --suite all`
  - 结果：`unit 4/4`、`integration 2/2`、`regression 84/84`、`e2e 5/5`
  - 合计：`95/95 PASS`

### 8.2 结论口径

- `已达成`：已有真点击或自动化用例直接验证通过。
- `部分达成`：后端能力已验证，但前端交互仅做页面存在性或未做真点击链路验证。
- `待补验证`：当前自动化未覆盖，需要手工走查或新增回放脚本。

### 8.3 超管端达成情况

- 已达成
- 登录态进入控制台、未登录强制跳转登录页。
- 系统设置保存、账号创建更新、考生导入导出、权限边界（无权限/停用）校验。
- CSRF 防护与退出后写接口拦截。
- 账号目录与权限治理接口（含分页、过滤、导入导出）回归通过。
- 结论：超管端清单能力当前为 `已达成`。

### 8.4 教师端达成情况

- 已达成
- 题库主流程：建题 -> 状态流转 -> 发布 -> 学生可见。
- 题目批量删除/恢复、驳回原因、导入预览/选中导入/示例模板、关键筛选与排序规则。
- 知识点：增删改查、层级校验、排序、删除恢复。
- 试卷：手动/自动组卷、模板、状态机、删除恢复、导出、题池筛选。
- 学情：记录查询、汇总、导出、分页稳定性、权限隔离。
- 消息中心：发送、已读、批量已读、分群发送、定时发送、历史与撤回。
- 部分达成
- 教师页面的一些细粒度前端交互（例如知识树“展开/折叠”按钮行为）主要是接口与页面结构级验证，真点击场景仍以核心链路为主。
- 结论：教师端总体 `已达成（核心链路）`，少量 UI 细节为 `部分达成`。

### 8.5 学生端达成情况

- 已达成
- 学习台：档案设置、打卡、积分/任务核心数据查询。
- 刷题：章节题查询、作答提交、章节解锁约束、超时判错、错题中心/沉淀题库联动。
- AI：AI 批改、AI 答疑任务生成与任务查询/取消。
- 错题中心：错题查询、错因记录、专项卷与同类卷生成、复习打点。
- 沉淀题库：列表、汇总、复习计划、导出、在库作答与 AI 能力联动。
- 考试大纲：全部考试科目大纲查看、结构浏览与思维导图式展开。
- 模拟卷：可用试卷查询、交卷、未作答按错、主观题异步任务、同日幂等、日报限次、报告列表与详情。
- 消息中心：筛选、已读/批量已读、个人消息设置。
- 部分达成
- 页面级前端体验逻辑（倒计时展示文案、暂停/恢复按钮交互、本地草稿恢复弹性、交卷前检查弹窗）已具备实现代码，但当前自动化主要验证接口结果与关键路径，UI 动效与边界手势未做全量真点击覆盖。
- 结论：学生端后端能力和核心业务链路 `已达成`，前端体验细节为 `部分达成`。

## 9. 当前总体判断

- 三端核心业务闭环（超管 -> 教师 -> 学生 -> 教师）已实测打通并通过。
- 文档所列核心能力大部分已达到可用状态。
- 尚需补强的是“前端体验细节”的真点击覆盖深度，而非主业务能力缺失。

## 10. 下一步补强建议

- 补一组学生端 UI 真点击脚本：倒计时归零自动交卷、暂停超时自动恢复、草稿恢复、交卷前检查弹窗。
- 补一组教师端页面交互脚本：知识树展开/折叠与筛选组合操作。
- 保持每次改动后固定执行：`run-click-replay --role all` + `run-tests --suite all`。
