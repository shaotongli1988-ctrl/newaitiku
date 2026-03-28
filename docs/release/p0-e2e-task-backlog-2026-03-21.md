# P0 E2E 补测任务清单（2026-03-21）

## 一、目标

- 把 [功能链路测试矩阵](/Users/shaotongli/Documents/newaitiku/docs/release/feature-chain-test-matrix-2026-03-21.md) 中的 `P0` 缺口拆成可以直接实施的 e2e 任务。
- 每个任务都给出建议测试文件、复用入口、关键步骤和通过判定。
- 默认优先使用现有 `tests/e2e` 的启动、登录和请求上下文模式，避免重复搭脚手架。

## 二、执行顺序

1. `E2E-P0-01` 超管系统设置保存与退出后写拦截
2. `E2E-P0-02` 超管考生导入导出
3. `E2E-P0-03` 教师消息历史与撤回
4. `E2E-P0-04` 学生模拟卷倒计时自动交卷
5. `E2E-P0-05` 学生模拟卷暂停超时恢复
6. `E2E-P0-06` 学生草稿恢复与交卷前风险检查

说明：
- 前 3 项优先补管理与消息链路缺口。
- 后 3 项优先补学生端真点击体验缺口。

## 三、任务拆解

### E2E-P0-01 超管系统设置保存与退出后写拦截

- 优先级：`P0`
- 建议测试文件：`tests/e2e/test_admin_settings_logout_guard.py`
- 建议类型：Playwright UI + API 联动
- 可复用实现：
  - [tests/e2e/test_cross_entry_login_redirect.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_cross_entry_login_redirect.py)
  - [frontend/src/views/Admin/ControlCenter.vue](/Users/shaotongli/Documents/newaitiku/frontend/src/views/Admin/ControlCenter.vue)
  - [tests/test_question_bank.py](/Users/shaotongli/Documents/newaitiku/tests/test_question_bank.py#L247)

- 目标：
  - 验证超管登录后可在控制台修改并保存系统参数。
  - 验证刷新或二次读取后参数仍一致。
  - 验证退出会话后，超管写接口不再允许执行。

- 关键步骤：
  1. 启动后端和前端测试服务。
  2. 从 `/login?redirect=%2Fadmin%2Fcontrol-center` 登录超管。
  3. 进入“系统参数”区域，修改 `platformName` 和一个数值型字段。
  4. 点击“保存参数”并断言成功提示 `系统参数已保存。`
  5. 刷新页面，重新读取表单值，断言保存后的值仍存在。
  6. 调用 `/api/question-bank/auth/logout` 退出登录。
  7. 再直接请求 `POST /api/question-bank/admin/settings`，断言返回 `403`。

- 通过判定：
  - 页面保存成功。
  - 保存后的值刷新后不丢失。
  - 退出后写接口被拦截。

- 实施备注：
  - 页面当前没有稳定测试 ID，优先用表单 label 和按钮文本定位。
  - 若需要更稳的控件定位，可后补少量 `data-testid`。

### E2E-P0-02 超管考生导入导出

- 优先级：`P0`
- 建议测试文件：`tests/e2e/test_admin_student_import_export.py`
- 建议类型：API e2e
- 可复用实现：
  - [tests/test_question_bank.py](/Users/shaotongli/Documents/newaitiku/tests/test_question_bank.py#L3427)
  - [app/main.py](/Users/shaotongli/Documents/newaitiku/app/main.py#L723)
  - [app/service_modules/system.py](/Users/shaotongli/Documents/newaitiku/app/service_modules/system.py)

- 目标：
  - 验证考生目录导入成功。
  - 验证导入后列表可见。
  - 验证导出结果包含新导入考生。

- 关键步骤：
  1. 使用超管身份建立带 Cookie + CSRF 的请求上下文。
  2. 生成一份最小合法导入文本，包含 2 条考生数据。
  3. 请求 `POST /api/question-bank/admin/students/import`。
  4. 请求 `GET /api/question-bank/admin/users?page=1&size=200&role=student`，断言导入用户存在。
  5. 请求 `GET /api/question-bank/admin/students/export?format=csv`。
  6. 断言导出内容包含导入的 `userId`、`mobile` 和表头字段。

- 通过判定：
  - 导入返回成功，包含成功条数。
  - 列表查询能查到新导入考生。
  - 导出内容结构正确，且包含新导入考生。

- 实施备注：
  - 该任务用 API e2e 性价比最高，不必强行走前端。
  - 可顺带补一个异常断言：重复 `userId` 时返回明确错误。

### E2E-P0-03 教师消息历史与撤回

- 优先级：`P0`
- 建议测试文件：`tests/e2e/test_teacher_message_history_recall.py`
- 建议类型：API e2e
- 可复用实现：
  - [tests/test_question_bank.py](/Users/shaotongli/Documents/newaitiku/tests/test_question_bank.py#L4049)
  - [app/main.py](/Users/shaotongli/Documents/newaitiku/app/main.py#L815)
  - [app/service_modules/messages.py](/Users/shaotongli/Documents/newaitiku/app/service_modules/messages.py)

- 目标：
  - 验证教师发送即时消息与定时消息后，发送历史可查。
  - 验证撤回成功后，历史状态更新为 `RECALLED`。
  - 验证撤回后学生侧不再把该消息当作可处理的新消息。

- 关键步骤：
  1. 教师发送一条即时消息，记录 `traceId`。
  2. 教师再发送一条未来时间的定时消息，记录第二个 `traceId`。
  3. 请求 `GET /api/question-bank/messages/send-history`，断言两条记录都存在。
  4. 对即时消息执行 `POST /api/question-bank/messages/send-history/{traceId}/recall`。
  5. 再查历史列表，断言该记录状态为 `RECALLED`。
  6. 用学生身份读取消息列表，确认撤回后的消息不再作为未读消息出现，或状态已被过滤。

- 通过判定：
  - 发送历史可查。
  - 撤回动作成功。
  - 学生侧观察结果与撤回语义一致。

- 实施备注：
  - 该链路已有单测基础，补成 e2e 主要是为了覆盖角色联动。
  - 若学生侧目前仍能看到已发送后再撤回的消息，需要按现有业务语义确认预期。

### E2E-P0-04 学生模拟卷倒计时自动交卷

- 优先级：`P0`
- 建议测试文件：`tests/e2e/test_student_paper_auto_submit_ui.py`
- 建议类型：Playwright UI
- 可复用实现：
  - [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py)
  - [tests/e2e/test_cross_entry_login_redirect.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_cross_entry_login_redirect.py)

- 目标：
  - 验证学生进入模拟卷后，倒计时归零时系统自动交卷。
  - 验证自动交卷后跳转或展示报告成功。

- 关键步骤：
  1. 启动前后端测试服务并登录学生。
  2. 预先构造一个超短时长的试卷或通过测试桩缩短倒计时。
  3. 进入模拟卷答题页，至少填写 1 题答案。
  4. 等待倒计时归零。
  5. 断言自动触发交卷，不需要再次人工点击。
  6. 断言页面进入报告态，或后端生成 `reportId`。

- 通过判定：
  - 倒计时归零后自动提交。
  - 不会停留在未提交的答题页。
  - 后端有报告产出。

- 实施备注：
  - 这是典型真点击场景，必要时允许增加仅测试环境启用的“短倒计时”参数。

### E2E-P0-05 学生模拟卷暂停超时恢复

- 优先级：`P0`
- 建议测试文件：`tests/e2e/test_student_paper_pause_resume_ui.py`
- 建议类型：Playwright UI
- 可复用实现：
  - [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L147)
  - [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L247)

- 目标：
  - 验证学生在模拟卷中点击暂停后，超过允许暂停时长会自动恢复或禁止继续暂停。
  - 验证剩余暂停次数与状态文案一致。

- 关键步骤：
  1. 登录学生并进入模拟卷。
  2. 点击“暂停”按钮，进入暂停态。
  3. 使用短时长测试配置或时间推进方式触发超时。
  4. 断言页面自动恢复到作答态，或提示“暂停已到期，已恢复考试”。
  5. 再次打开暂停能力，确认次数或可用状态已正确扣减。

- 通过判定：
  - 暂停不会无限停留。
  - 超时恢复动作有明确 UI 结果。
  - 恢复后仍可继续答题并提交。

- 实施备注：
  - 若当前没有稳定的暂停控件实现，可先补页面测试标识，再落 Playwright。

### E2E-P0-06 学生草稿恢复与交卷前风险检查

- 优先级：`P0`
- 建议测试文件：`tests/e2e/test_student_paper_draft_restore_risk_guard_ui.py`
- 建议类型：Playwright UI
- 可复用实现：
  - [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L151)
  - [docs/three-role-feature-inventory.md](/Users/shaotongli/Documents/newaitiku/docs/three-role-feature-inventory.md#L152)

- 目标：
  - 验证答题中离开后能恢复本地草稿。
  - 验证交卷前对未答题、主观题过短、多选疑似漏选等风险给出提醒。

- 关键步骤：
  1. 登录学生并进入模拟卷。
  2. 填写部分答案但不交卷，主动刷新页面或重新进入试卷。
  3. 断言页面提示恢复草稿，并在确认后恢复已填写内容。
  4. 保留部分题未答，或给主观题输入极短答案。
  5. 点击交卷。
  6. 断言先出现风险检查提示，而不是直接提交。
  7. 在二次确认后完成交卷，并生成报告。

- 通过判定：
  - 草稿可恢复。
  - 风险检查弹窗或提示包含至少一类风险项。
  - 用户确认后仍能完成交卷。

- 实施备注：
  - 该任务和 `E2E-P0-04`、`E2E-P0-05` 可以共用同一套学生登录和试卷构造逻辑。

## 四、复用建议

- 前后端启动与端口探测：优先复用 [tests/e2e/test_cross_entry_login_redirect.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_cross_entry_login_redirect.py) 的模式。
- 管理端请求上下文：优先复用 [tests/e2e/test_teacher_assigned_scope_ui.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_teacher_assigned_scope_ui.py) 的 Bearer Token 初始化方式。
- 学生主链路数据准备：优先复用 [tests/e2e/test_student_interaction_acceptance.py](/Users/shaotongli/Documents/newaitiku/tests/e2e/test_student_interaction_acceptance.py) 的现有题目、消息和试卷种子数据。

## 五、完成定义

- 以上 6 个任务全部有对应测试文件。
- 至少 `E2E-P0-01`、`E2E-P0-02`、`E2E-P0-03` 可以进入默认 `tests/e2e` 回归。
- 学生端 3 个真点击任务至少完成 1 个，其余 2 个进入明确排期，避免继续停留在“建议补测”。
