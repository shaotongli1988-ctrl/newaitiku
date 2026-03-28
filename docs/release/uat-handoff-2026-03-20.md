# UAT 交接说明（2026-03-20）

## 文档信息

- 文档类型：UAT 交接材料
- 适用版本：2026-03-20 发布批次
- 适用角色：产品、测试、研发
- 交接目标：确认 UAT 可执行、可反馈、可签收

## 一、目标

- 为本次版本提供可直接执行的 UAT 交接材料。

## 二、环境入口

- 登录页：`/login`
- 超管首页：`/admin/home`
- 教师首页：`/teacher/home`
- 学生首页：`/student/home`

## 三、测试角色

### 超管

- 目标：验证后台首页、控制中心、权限与发布入口

### 教师

- 目标：验证题库管理、题目详情、编辑、状态流转、组卷

### 学生

- 目标：验证首页、练习、我的题库、消息、试卷练习

## 四、前置条件

- [ ] 测试环境已部署到待验收版本
- [ ] 提供有效测试账号
- [ ] 提供环境入口和访问说明
- [ ] 已同步本次发布范围与已知限制

## 五、UAT 验收步骤

### 1. 登录与跳转

1. 访问 `/login`
2. 输入合法账号密码
3. 验证登录后跳转到对应角色首页

### 2. 教师端题库

1. 进入教师首页
2. 打开题库管理页
3. 执行搜索、分页、详情、编辑
4. 验证状态流转按钮可用

### 3. 教师端组卷

1. 进入教师试卷页
2. 打开手动选题抽屉
3. 打开 AI 组卷弹层
4. 验证试卷列表正常展示

### 4. 学生端学习路径

1. 进入学生首页
2. 验证首页卡片、章节树、AI 队列
3. 进入练习页完成作答
4. 进入我的题库，检查错题中心、沉淀题库与考试大纲数据

## 六、预期结果

- 登录流程正常
- 页面无空白、无报错
- 题库与组卷关键路径可访问
- 学生练习与错题路径可访问
- 权限越权访问会被拦截

## 七、反馈方式

- 问题统一记录到 Bug 清单
- 阻断级问题立即同步研发与运维
- UAT 通过后再进入正式上线流程

## 八、责任归属

- 产品：确认验收口径
- 测试：组织 UAT 执行
- 研发：处理阻断级缺陷

## 九、签收

- 产品验收结论：__________
- 测试验收结论：__________
- 阻断问题是否清零：__________
- 允许进入正式上线：__________

## 十、自动化复核记录（2026-03-20）

- 已执行关键路径自动化回归，结果：`7 / 7` 通过。
- 覆盖范围：
  1. 超管通过 `/login` 登录后台、进入控制台、登出清理会话。
  2. 超管写操作仍受 CSRF 保护。
  3. 学生首页 / 练习页 / 我的题库子页页面可访问。
  4. 教师消息中心与学生消息中心角色隔离正常。
  5. 学生练习、错题中心、AI 助教、消息已读、试卷提交主路径可走通。
  6. 教师出题后，学生提交练习，教师学情记录可关联查看。
  7. 学生首页看板与考试画像接口可正常返回。
- 复核命令：

```bash
python3 -m pytest -q \
  tests/test_question_bank.py::test_super_admin_cookie_login_allows_admin_console_and_logout_clears_cookie \
  tests/test_question_bank.py::test_super_admin_cookie_session_requires_csrf_for_admin_write \
  tests/e2e/test_student_interaction_acceptance.py::test_student_pages_keep_navigation_isolated \
  tests/e2e/test_student_interaction_acceptance.py::test_message_center_layout_isolated_for_student_and_teacher \
  tests/e2e/test_student_interaction_acceptance.py::test_student_interaction_round_acceptance \
  tests/e2e/test_question_bank_journey.py::test_teacher_student_submit_and_teacher_analytics_record_linked \
  tests/test_question_bank.py::test_student_dashboard_profile_and_check_in
```

- 自动化复核结论：当前超管 / 教师 / 学生关键路径未发现阻断级问题，可作为 UAT 通过前的技术佐证。
