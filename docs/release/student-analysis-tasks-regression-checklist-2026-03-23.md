# 知识诊断今日任务回归清单（2026-03-23）

## 1. 目的

- 把 `知识诊断 > 今日任务` 相关回归入口、覆盖范围和推荐执行方式沉淀为统一清单。
- 避免后续页面改版时出现“代码改了，但没人知道该跑哪些回归”的情况。
- 为开发自测、提测前回归和问题复现提供单一入口。

## 2. 覆盖范围

当前清单覆盖以下能力：

- 页面口径：
  - 全局任务
  - 科目弱项
  - 练习积分作为知识诊断二级详情页
- 展示规则：
  - 统计卡口径
  - 错误态文案
  - 任务状态语义
  - 行级任务归一化
- API / 页面协同契约：
  - 页面 bootstrap
  - 学生 dashboard
  - 任务列表
  - 科目知识树
- 真实业务闭环：
  - 今日任务 -> 章节闯关
  - 今日任务 -> 错题修复
  - 今日任务 -> 模拟考试

## 3. 回归分层

### 3.1 轻量规则单测

文件：

- [`frontend/src/utils/studentTasksCopy.test.js`](/Users/shaotongli/Documents/newaitiku/frontend/src/utils/studentTasksCopy.test.js)

覆盖内容：

- `全局任务 / 科目弱项` 文案口径
- 统计摘要口径
- 错误态标题与 fallback 文案
- 任务状态语义
- 行级任务归一化

推荐命令：

```bash
npm --prefix /Users/shaotongli/Documents/newaitiku/frontend run test -- studentTasksCopy.test.js
```

### 3.2 练习路由 helper 单测

文件：

- [`frontend/src/utils/studentPracticeNavigation.test.js`](/Users/shaotongli/Documents/newaitiku/frontend/src/utils/studentPracticeNavigation.test.js)

覆盖内容：

- `buildStudentPracticeRouteLocation(...)` 的模块路由选择
- `module=mock` 不被默认章节模块覆盖
- `practiceSource / practiceSourceLabel` 透传
- 今日任务进入练习页的来源语义

推荐命令：

```bash
npm --prefix /Users/shaotongli/Documents/newaitiku/frontend run test -- studentPracticeNavigation.test.js
```

### 3.3 API / 页面协同契约回归

文件：

- [`tests/test_question_bank.py`](/Users/shaotongli/Documents/newaitiku/tests/test_question_bank.py)

重点用例：

- `test_student_analysis_tasks_page_contract_aligns_global_tasks_with_subject_weakness_tree`

覆盖内容：

- `/student/analysis/tasks` 页面 bootstrap 稳定
- `/student/analysis/points` 页面 bootstrap 稳定
- `/student/points` 旧入口正确跳转到 `/student/analysis/points`
- `/api/question-bank/student/dashboard` 提供全局 `dailyTasks`
- `/api/question-bank/tasks` 提供任务列表与 `aiQuota`
- `/api/question-bank/knowledge/tree` 按 `subjectCode` 真正区分科目弱项

推荐命令：

```bash
./.venv/bin/python -m pytest /Users/shaotongli/Documents/newaitiku/tests/test_question_bank.py -q -k student_analysis_tasks_page_contract_aligns_global_tasks_with_subject_weakness_tree
```

### 3.4 真点击业务闭环回归

文件：

- [`tests/e2e/test_student_true_click_ui.py`](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_true_click_ui.py)

当前已覆盖用例：

1. 学生主导航进入 `知识诊断 > 今日任务`
2. 切科目后：
   - 全局任务提示保持不变
   - 弱项提醒中的科目名称同步变化
3. `去做章节闯关`：
   - 落到 `/student/practice/chapter`
   - 保留 `practiceSource=TASK`
4. `去复习错题`：
   - 落到 `/student/question-bank/repair`
   - 保留当前 `subjectCode`
5. `去做模拟考试`：
   - 落到 `/student/practice/mock`
   - 保留 `module=mock`
   - 保留 `practiceSource=TASK`
   - 保留 `practiceSourceLabel=完成1次模拟考试`

推荐命令：

```bash
./.venv/bin/python -m pytest /Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_true_click_ui.py -q
```

## 4. 推荐跑法

### 4.1 日常快速自测

适用场景：

- 改了 `Tasks.vue`
- 改了 `studentTasksCopy`
- 改了 `studentPracticeNavigation`

推荐命令：

```bash
npm --prefix /Users/shaotongli/Documents/newaitiku/frontend run test -- studentTasksCopy.test.js
npm --prefix /Users/shaotongli/Documents/newaitiku/frontend run test -- studentPracticeNavigation.test.js
./.venv/bin/python -m pytest /Users/shaotongli/Documents/newaitiku/tests/test_question_bank.py -q -k student_analysis_tasks_page_contract_aligns_global_tasks_with_subject_weakness_tree
```

### 4.2 提测前完整回归

适用场景：

- 提测前
- 合并前
- `知识诊断 / 今日任务 / 练习积分 / 刷题升本 / 错题中心` 任一链路改动后

推荐命令：

```bash
npm --prefix /Users/shaotongli/Documents/newaitiku/frontend run build
./.venv/bin/python -m pytest /Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_true_click_ui.py -q
```

## 5. 当前结论

截至 `2026-03-23`，`知识诊断 > 今日任务` 相关回归已形成四层保护：

1. 轻量 helper 单测
2. 路由 helper 单测
3. API / 页面协同契约回归
4. 真点击业务闭环回归

当前三条核心任务动作闭环均已纳入真点击回归：

- `去做章节闯关`
- `去复习错题`
- `去做模拟考试`

## 6. 维护规则

- 若只改 `Tasks.vue` 文案或展示规则，至少更新轻量单测。
- 若改任务跳转逻辑，必须同步更新 `studentPracticeNavigation` 单测和真点击回归。
- 若改 dashboard / task list / knowledge tree 任一接口口径，必须同步更新 API / 页面协同回归。
- 若新增新的今日任务动作入口，应优先补一条对应的真点击闭环用例。
