# 功能链路测试矩阵（2026-03-21）

## 一、文档目的

- 这份文档用于收口当前软件可做链路测试的功能范围。
- 输出口径分为三类：`已自动化`、`待补自动化`、`仅文档回归`。
- 本文面向提测前、上线前和补测排期使用。

## 二、阶段路由结果

- 三阶段路由结果：`开发后`
- 对应总技能：`software-delivery-unified-governance`
- 路由依据：当前任务是整理测试矩阵、收口验收口径，更符合开发后终检与交付治理阶段。

## 三、统计口径

- 模块口径：`17 个主功能模块`
- 链路口径：`25 条链路项`
- 当前状态汇总：
  - `已自动化`：16 条
  - `部分自动化`：1 条
  - `仅文档回归`：6 条
  - `待补自动化`：2 条

说明：
- “主功能模块”按超管、教师、学生三端业务模块统计。
- “链路项”按可独立验收的主路径拆分，因此会比模块数更多。
- “待补自动化”优先指前端真点击缺口。

## 四、模块总览

| 角色 | 主功能模块数 | 说明 |
|---|---:|---|
| 超管 | 5 | 登录安全、系统设置、账号权限、考生导入、考生导出 |
| 教师 | 6 | 题库、知识点、内容体系、试卷、学情、消息 |
| 学生 | 6 | 学习台、刷题与 AI、我的题库、模拟卷、消息 |

## 五、链路测试矩阵

| 角色 | 功能链路 | 当前状态 | 自动化证据 | 补测建议 |
|---|---|---|---|---|
| 超管 | 登录与跨入口跳转 | 已自动化 | [tests/e2e/test_cross_entry_login_redirect.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_cross_entry_login_redirect.py#L52) | 保持回归 |
| 超管 | 系统设置保存 | 仅文档回归 | [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L217) | 补 1 条 UI 或 API e2e |
| 超管 | 账号创建 / 更新 / 启停 / 权限分配 | 仅文档回归 | [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L219) | 补 1 条主链路 e2e |
| 超管 | 考生导入 | 仅文档回归 | [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L219) | 补“导入后列表校验” |
| 超管 | 考生导出 | 仅文档回归 | [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L219) | 补导出文件断言 |
| 教师 | 题库建题 -> 状态流转 -> 发布 -> 学生可见 | 已自动化 | [tests/e2e/test_question_bank_journey.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_question_bank_journey.py#L9) | 保持回归 |
| 教师 | 知识点增删改查 / 排序 / 恢复 | 仅文档回归 | [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L229) | 补 1 组 API + UI |
| 教师 | 知识树展开 / 折叠 / 筛选组合操作 | 待补自动化 | [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L257) | 优先补真点击 |
| 教师 | 内容体系 / 专业树范围校验 | 部分自动化 | [tests/e2e/test_papers_professional_scope_publish.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_papers_professional_scope_publish.py#L50) | 补页面级链路 |
| 教师 | 试卷手动组卷 | 已自动化 | [tests/e2e/test_teacher_assigned_scope_ui.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_teacher_assigned_scope_ui.py#L132) | 保持回归 |
| 教师 | 试卷 AI 组卷 | 已自动化 | [tests/e2e/test_teacher_assigned_scope_ui.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_teacher_assigned_scope_ui.py#L152) | 保持回归 |
| 教师 | 试卷发布范围约束 | 已自动化 | [tests/e2e/test_papers_professional_scope_publish.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_papers_professional_scope_publish.py#L139) | 保持回归 |
| 教师 | 学情查询 / 学生作答回流 | 已自动化 | [tests/e2e/test_question_bank_journey.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_question_bank_journey.py#L62) | 保持回归 |
| 教师 | 消息发送 | 已自动化 | [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py#L121) | 保持回归 |
| 教师 | 消息历史 / 撤回 / 定时发送 | 仅文档回归 | [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L232) | 补 1 到 2 条 e2e |
| 学生 | 学习台 / 档案切换 / Dashboard 刷新 | 已自动化 | [tests/e2e/test_playwright_async_adaptation.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_playwright_async_adaptation.py#L97) | 保持回归 |
| 学生 | 页面隔离与越权跳转拦截 | 已自动化 | [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py#L18)；[tests/e2e/test_playwright_async_adaptation.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_playwright_async_adaptation.py#L176) | 保持回归 |
| 学生 | 章节刷题查询与提交 | 已自动化 | [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py#L74) | 保持回归 |
| 学生 | 进入错题中心并查询错题 | 已自动化 | [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py#L90) | 保持回归 |
| 学生 | 按错因生成专项卷 | 已自动化 | [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py#L101) | 保持回归 |
| 学生 | AI 答疑 / 任务轮询 | 已自动化 | [tests/e2e/test_playwright_async_adaptation.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_playwright_async_adaptation.py#L146) | 保持回归 |
| 学生 | 沉淀题库列表 / 汇总 / 复习计划 / 导出 / 恢复 | 已自动化 | [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py) | 保持回归 |
| 学生 | 模拟卷拉题 / 作答 / 交卷 / 报告生成 | 已自动化 | [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py#L147) | 保持回归 |
| 学生 | 倒计时 / 暂停恢复 / 草稿恢复 / 交卷前检查 | 待补自动化 | [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L247) | 优先补真点击 |
| 学生 | 消息中心未读 / 批量已读 | 已自动化 | [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py#L133) | 保持回归 |

## 六、优先补测清单

### P0

1. 超管系统设置保存，补“保存成功 -> 二次读取一致 -> 退出后写接口拦截”完整链路。
2. 超管考生导入导出，补“导入 -> 列表可见 -> 导出文件结构正确”完整链路。
3. 教师消息中心，补“发送历史 -> 撤回 -> 学生侧状态变化”链路。
4. 学生模拟卷体验，补“倒计时归零自动交卷 / 暂停超时恢复 / 草稿恢复 / 交卷前风险检查弹窗”真点击链路。

对应可执行拆分见：[P0 E2E 补测任务清单](/Users/shaotongli/Documents/newaitiku/docs/release/p0-e2e-task-backlog-2026-03-21.md)

### P1

1. 教师知识树展开 / 折叠 / 筛选组合操作。
2. 教师内容体系字典页的页面级查看与筛选行为。

## 七、当前判断

- 三端核心业务闭环 `超管 -> 教师 -> 学生 -> 教师` 已具备自动化证据。
- 当前主要缺口不在主业务能力，而在少量超管后台链路和前端真点击细节。
- 若本轮目标是提测前收口，优先消化 `P0` 补测项即可明显降低回归盲区。

## 八、备注

- 路由脚本已执行：`python3 scripts/three_stage_orchestrator.py --task "整理并落库该软件的功能链路测试矩阵，区分已自动化、待补自动化、仅文档回归" --current-stage delivery`
- `scripts/fullstack_test_matrix_guard.py` 当前在仓库中不存在，因此未能直接用守卫脚本生成矩阵，本文件为基于现有 `tests/e2e`、`docs/three-role-feature-inventory.md` 与页面/路由实现的人工收口结果。
