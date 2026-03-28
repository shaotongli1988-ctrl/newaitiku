# 三端统一真点击清单

## 执行命令
- `./tools/bin/run-click-replay.sh --role super_admin --base-url http://127.0.0.1:8017`
- `./tools/bin/run-click-replay.sh --role teacher --base-url http://127.0.0.1:8017`
- `./tools/bin/run-click-replay.sh --role student --base-url http://127.0.0.1:8017`
- `./tools/bin/run-click-replay.sh --role all --base-url http://127.0.0.1:8017`

## 统一参数
- `--base-url`：回放访问地址（默认 `http://127.0.0.1:8017`）
- `--headless/--headed`：无头/有头模式（默认无头）
- `--output-dir`：结果输出目录（默认 `docs`）
- `--timeout-sec`：单步骤超时秒数
- `--db-path`：隔离数据库文件（默认 `/tmp/question-bank-click-replay.db`）

## 超管端（super_admin）
### 前置条件
- 服务可访问。
- 使用已配置的超管账号通过 `/login` 正常登录，禁止在公开文档中记录默认密码。

### 真点击步骤
1. 未登录访问 `/admin/control-center` 被强制跳转 `/login`。
2. 超管登录并进入控制台。
3. 保存系统设置成功。
4. 创建并更新教师账号，验证教师页/教师接口可访问。
5. 批量导入考生并导出目录成功。
6. 权限边界验证：无 `question:manage`、已停用账号均返回 403。
7. CSRF 缺失写接口返回 403。
8. 退出会话后不可继续写操作。

### 通过判定
- 所有步骤 `PASS`。
- 联调链路 `superAdminToTeacher=PASS`。

## 教师端（teacher）
### 前置条件
- 服务可访问。
- 使用教师种子账号登录（`13800000002 / seed-password-teacher-001`）。

### 真点击步骤
1. 教师登录并进入题库页。
2. 真点击创建题目。
3. 真点击流转到 `PUBLISHED`。
4. 验证学生端练习列表可见该题。

### 通过判定
- 所有步骤 `PASS`。
- 联调链路 `teacherToStudent=PASS`。

## 学生端（student）
### 前置条件
- 服务可访问。
- 使用学生种子账号登录（`13800000005 / seed-password-student-001`）。
- 学生端页面文案锚点以 [学生端页面文案基线验收清单（2026-03-23）](/Users/shaotongli/Documents/newaitiku/docs/release/student-copy-baseline-acceptance-2026-03-23.md) 为准。

### 真点击步骤
1. 学生登录并进入刷题页。
2. 真点击进入 `知识诊断 > 今日任务`，确认二级导航与任务页锚点文案可见。
3. 学生端可见教师已发布题目。
4. 真点击提交题目。
5. 真点击触发交卷前检查弹窗，并可返回继续作答。
6. 真点击验证模拟考试暂停与恢复。
7. 真点击验证刷新后草稿恢复。
8. 真点击验证倒计时归零自动交卷。
9. 教师侧学情记录可查询该提交痕迹。

### 通过判定
- 所有步骤 `PASS`。
- 联调链路 `studentToTeacher=PASS`。
