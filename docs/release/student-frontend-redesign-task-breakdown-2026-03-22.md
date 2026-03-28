# 学生端前端改版任务拆解表（2026-03-22）

## 阶段结论

- 当前阶段：开发前
- 对应总技能：`software-development-readiness-governance`
- 说明：本次先冻结学生端信息架构、页面职责、导航层级、移动端方案与验收口径，再进入代码实施。

## 已冻结决策

1. 首页完全移除雷达图。
2. 任务中心彻底去表格化，改成任务卡片流与时间线。
3. 知识诊断不保留“知识星系”品牌副标题，统一使用“知识诊断”。
4. 学生题库入口统一为“我的题库”，下挂错题中心、沉淀题库、考试大纲。
5. 移动端底部导航固定为 5 项：`首页 / 任务 / 练习 / 题库 / 诊断`。

## 目标结构

### 一级导航

- 学习首页
- 任务中心
- 自由练习
- 我的题库
- 知识诊断
- 消息中心

### 我的题库二级结构

- `错题中心`
- `已归档`
- `沉淀题库`
- `复习计划`

## 总体实施顺序

1. 先改全局壳层与路由结构，统一导航与移动端入口。
2. 再做首页、任务中心和练习页，先解决主流程可达性。
3. 最后统一学生题库入口，收尾知识诊断与消息中心。

## P0 任务

### P0-1 统一学生端壳层与导航

- 目标：
  - 移除 `galaxy/sanctuary` 双壳层。
  - 顶部与侧边导航收敛为一套唯一主导航。
  - 小屏下补足底部导航与更多抽屉，禁止主导航消失。
- 影响页面：
  - 全学生端
- 主要文件：
  - `frontend/src/layouts/DefaultLayout.vue`
  - `frontend/src/router/studentRoutes.js`
  - `frontend/src/router/student.js`
  - `frontend/src/assets/styles/variables.css`
  - `frontend/src/style.css`
- 改造动作：
  - 删除双模式壳层判断与两套顶部 tabs。
  - 把侧边栏改成唯一一级导航。
  - 增加移动端底部导航和“更多”入口。
  - 将消息入口保留在顶部，不占底部 tab。
- 验收点：
  1. 所有学生页共用同一套 shell。
  2. `1080px` 以下不再出现顶部导航消失后无替代入口。
  3. `900px` 以下可稳定访问全部一级页面。
  4. 当前激活导航在桌面端和移动端都可见。

### P0-2 首页收敛为决策页

- 目标：
  - 首页只保留“今天先做什么”和少量进度信息。
- 影响页面：
  - `/student/home`
- 主要文件：
  - `frontend/src/views/Student/Home.vue`
  - `frontend/src/components/student/StudentHeroBanner.vue`
  - `frontend/src/components/student/StudentSubjectDrawer.vue`
- 改造动作：
  - 删除雷达图及其挂载区。
  - 删除重复任务摘要、科目卡大阵列和重型建议卡组。
  - 保留今日主任务卡、进度摘要、快捷入口、单条弱项提醒。
  - 将深度分析后移到知识诊断，详细任务后移到任务中心。
- 验收点：
  1. 首页首屏控制在 4 个核心模块以内。
  2. 首屏必须包含“立即开始”的主动作。
  3. 首页不再出现雷达图。
  4. 首屏一屏内能看完核心信息。

### P0-3 任务中心去表格化

- 目标：
  - 把任务中心改造成 `知识诊断 > 今日任务` 二级页。
- 影响页面：
  - `/student/analysis/tasks`
- 主要文件：
  - `frontend/src/views/Student/Tasks.vue`
- 改造动作：
  - 移除 `el-table` 任务流水。
  - 改为任务卡片流、最近执行时间线、失败任务重试卡。
  - 保留打卡、今日任务、弱项执行、最近结果。
  - 作为知识诊断二级页承接“先诊断，后执行”的动作闭环。
- 验收点：
  1. 首屏直接展示可执行任务，不再要求先读表格。
  2. 失败任务有明确重试入口。
  3. 任务列表字段变为学生可理解语义，而不是后台字段。
  4. 页面内不再出现任务宽表格。

### P0-4 自由练习首屏见题

- 目标：
  - 进入练习页后优先看到题目，而不是大量说明和筛选容器。
- 影响页面：
  - `/student/practice`
- 主要文件：
  - `frontend/src/views/Student/Practice.vue`
- 改造动作：
  - 压缩首屏 Hero、context-atlas 和多条 alert。
  - 把来源、进度、筛选摘要合并到顶部轻量状态条。
  - 高级筛选改成抽屉或折叠区。
  - 题目工作台提前到首屏核心位置。
- 验收点：
  1. 首次进入页面即能看到题目主体。
  2. 高级筛选默认不铺满首屏。
  3. 页面顶部只保留一层状态摘要。
  4. 空题单时有“调整筛选/返回任务中心”的动作。

## P1 任务

### P1-1 统一学生题库入口为“我的题库”

- 目标：
  - 把相近能力收敛到同一一级导航下，减少学生理解成本。
- 影响页面：
  - `/student/question-bank/repair`
  - `/student/question-bank/archive`
  - `/student/question-bank/syllabus`
- 主要文件：
  - `frontend/src/views/Student/WrongBook.vue`
  - `frontend/src/views/Student/PersonalBank.vue`
  - `frontend/src/router/studentRoutes.js`
- 改造动作：
  - 新建统一一级入口“我的题库”。
  - 内部用子页面或分段控制承载“错题中心 / 沉淀题库 / 考试大纲”。
  - 抽取统一筛选区、统一题目列表容器、统一批量操作区。
  - 将现有错题修复和归档恢复逻辑迁入统一容器。
- 验收点：
  1. 一级导航中不再同时出现独立的“错题本”和“个人题库”入口。
  2. 学生可在一个入口内完成修错、恢复、沉淀、复习计划切换和考试大纲查看。
  3. 现有主要业务动作仍可达：去练习、生成修复卷、恢复归档、执行计划。

### P1-2 错题修复页改成操作型布局

- 目标：
  - 列表前置，诊断信息做摘要，不再让趋势卡片占用主流程。
- 影响页面：
  - “我的题库 > 错题中心”
- 主要文件：
  - `frontend/src/views/Student/WrongBook.vue`
- 改造动作：
  - 将当前诊断看板压缩为修复总卡。
  - 将错题列表和批量操作前置。
  - 将 AI 修复建议改成折叠区或抽屉。
- 验收点：
  1. 首屏先看到修复动作和错题列表。
  2. 批量操作固定且易达。
  3. 趋势与热点信息不再压过题目列表。

### P1-3 沉淀题库改成搜索驱动页

- 目标：
  - 先找题，再看洞察。
- 影响页面：
  - “我的题库 > 沉淀题库 / 复习计划”
- 主要文件：
  - `frontend/src/views/Student/PersonalBank.vue`
- 改造动作：
  - 把搜索与筛选区固定在顶部。
  - 把概览指标压缩成轻量头部。
  - 把 L3 洞察改为折叠区或二级内容区。
- 验收点：
  1. 首屏可直接搜索与筛选。
  2. 题目列表位置高于洞察区。
  3. 复习计划和恢复操作有明确入口。

### P1-3A 新增考试大纲总览页

- 目标：
  - 把全部考试科目的大纲统一放进 `我的题库` 内，作为只读总览页收口。
- 影响页面：
  - “我的题库 > 考试大纲”
- 主要文件：
  - `frontend/src/views/Student/QuestionBankSyllabus.vue`
  - `frontend/src/components/student/QuestionBankSyllabusBranch.vue`
  - `app/main.py`
- 改造动作：
  - 新增学生端考试大纲子页。
  - 页面展示全部考试科目，不跟随当前科目切换。
  - 以教师端思维导图结构为参考，展开“具体内容与要求”。
- 验收点：
  1. 可浏览全部考试科目。
  2. 可切换某一科目查看完整大纲。
  3. 可看到考试形式与参考题型、正文结构和思维导图式分支。

### P1-4 知识诊断命名与职责收口

- 目标：
  - 保留诊断价值，去掉品牌副标题和执行型内容。
- 影响页面：
  - `/student/analysis`
- 主要文件：
  - `frontend/src/views/Student/Analysis.vue`
  - `frontend/src/layouts/DefaultLayout.vue`
- 改造动作：
  - 全站将“知识星系”收敛为“知识诊断”。
  - 保留图谱主画布、节点详情、推荐动作。
  - 新增二级页：`诊断总览 / 今日任务`。
- 验收点：
  1. 页面标题和导航文案统一使用“知识诊断”。
  2. `诊断总览` 负责结构诊断与薄弱点定位。
  3. `今日任务` 负责承接诊断后的执行动作。

## P2 任务

### P2-1 消息中心与异步反馈收口

- 目标：
  - 把 AI 结果、任务反馈、系统通知统一到消息中心。
- 影响页面：
  - `/messages`
  - 全学生端异步动作
- 主要文件：
  - `frontend/src/views/System/Messages.vue`
  - 学生端各页面触发异步结果的模块
- 改造动作：
  - 将系统通知、任务反馈、AI 结果做分类。
  - 从消息中心提供直接跳转回业务页的能力。
- 验收点：
  1. 重要异步结果可在消息中心找到。
  2. 消息可直接跳回相关任务或题目。

### P2-2 全页状态规范化

- 目标：
  - 为学生端统一加载、空、错、禁用、成功反馈。
- 影响页面：
  - `Home.vue`
  - `Tasks.vue`
  - `Practice.vue`
  - `WrongBook.vue`
  - `PersonalBank.vue`
  - `Analysis.vue`
  - 共享弹层与基础组件
- 主要文件：
  - `frontend/src/views/Student/*.vue`
  - `frontend/src/components/common/*.vue`
  - `frontend/src/assets/styles/variables.css`
- 改造动作：
  - 将当前大量 toast-only 错误改为页内错误卡片 + 重试动作。
  - 空状态统一带下一步动作。
  - 禁用按钮统一给出原因说明。
  - 成功反馈统一为页内提示或消息中心回执。
- 验收点：
  1. 核心页面都有加载/空/错/禁用/成功 5 类状态。
  2. 错误态不再只依赖 `ElMessage`。
  3. 空状态都有下一步动作。

### P2-3 文案去概念化

- 目标：
  - 把页面标题和按钮文案改成结果导向表达。
- 影响页面：
  - 全学生端
- 主要文件：
  - `frontend/src/layouts/DefaultLayout.vue`
  - `frontend/src/views/Student/*.vue`
  - `frontend/src/router/studentRoutes.js`
- 改造动作：
  - 移除“学府圣地”等概念包装。
  - 一级标题改为学习首页、任务中心、自由练习、我的题库、知识诊断。
  - CTA 改成“立即开始 / 去练习 / 去修复 / 去完成”这类动作导向文案。
- 验收点：
  1. 一级标题全部说人话。
  2. 按钮全部是动作型表达。
  3. 空态和错误态文案可直接指导下一步。

## 路由与文件范围建议

### 路由重命名建议

- `studentHome` 保留
- `studentTasks` 保留
- `studentPractice` 保留
- `studentWrongBook` 与 `studentPersonalBank` 合并为 `studentQuestionBank`
- `studentAnalysis` 建议文案层改名为“知识诊断”，路径可保留 `/student/analysis` 以降低改动面

### 建议新增或重构的组件层

- `frontend/src/components/student/StudentBottomNav.vue`
- `frontend/src/components/student/StudentTaskCard.vue`
- `frontend/src/components/student/StudentTaskTimeline.vue`
- `frontend/src/components/student/StudentQuestionBankTabs.vue`
- `frontend/src/components/common/PageErrorState.vue`
- `frontend/src/components/common/PageEmptyState.vue`

## UAT 验收清单

1. 学生端桌面端与移动端均可访问全部一级入口。
2. 首页首屏不再出现雷达图，且一屏内能完成开始动作。
3. 任务中心不再出现宽表格，改为卡片流或时间线。
4. 自由练习进入后首屏可见题目主体。
5. “我的题库”可完成修错、恢复、沉淀、复习计划切换。
6. 知识诊断页面标题和导航文案不再出现“知识星系”。
7. 核心页面均具备页内错误态和重试动作。
8. 移动端底部导航固定 5 项，消息不占底部 tab。
9. 学生端核心导航页文案锚点与命名统一按 [学生端页面文案基线验收清单（2026-03-23）](/Users/shaotongli/Documents/newaitiku/docs/release/student-copy-baseline-acceptance-2026-03-23.md) 验收。

## 风险与依赖

- 统一学生题库入口时，需要优先确认接口与筛选字段能否共用。
- 若保持旧路径兼容，需要处理历史跳转与收藏链接。
- 任务中心去表格化时，需要确认任务记录字段如何映射为学生可读文案。
- 页内错误态统一前，需先梳理现有 `ElMessage` 触发点。

## 建议进入开发前补充的实施基线

1. 先确认“我的题库”是否走单页 tab，还是单页 + 子路由。
2. 先确认移动端底部导航第 5 项固定为“诊断”，消息保持顶部入口。
3. 先确认首页首屏模块上限为 4 个。
4. 先确认任务中心记录区采用“时间线”还是“卡片列表”主形态。
5. 先确认统一页内错误态组件的视觉与交互规范。
