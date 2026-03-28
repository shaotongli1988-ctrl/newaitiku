# 学生端真点击回放验收报告（2026-03-21）

## 执行概览
- 角色：`student`
- 回放模式：`python-playwright-true-click-replay`
- 执行时间：`2026-03-21T02:52:54.405` 至 `2026-03-21T02:54:30.443`
- 回放地址：`http://127.0.0.1:8017`
- 超时：`25 秒/步骤`
- 数据库：`/tmp/question-bank-click-replay-2026-03-21-student.db`

## 结果总览
- 步骤总数：8
- 通过：1
- 失败：7
- 问题数：7

## 分步结果
- 1-学生登录并进入刷题页：FAIL
  错误：Locator.fill: Timeout 25000ms exceeded.
Call log:
  - waiting for locator("#password-login-form input[name='phone']")

  产物：/Users/shaotongli/Code/newaitiku/docs/student-step-fail-1-1774061599.png
- 2-学生端可见教师发布题目：FAIL
  错误：Locator expected to be visible
Actual value: None
Error: element(s) not found 
Call log:
  - Expect "to_be_visible" with timeout 25000ms
  - waiting for locator("#practice-question-list")

  产物：/Users/shaotongli/Code/newaitiku/docs/student-step-fail-2-1774061624.png
- 3-学生真点击提交题目：FAIL
  错误：Locator expected to be visible
Actual value: None
Error: element(s) not found 
Call log:
  - Expect "to_be_visible" with timeout 25000ms
  - waiting for locator("[data-practice-question-id='question-seed-007']")

  产物：/Users/shaotongli/Code/newaitiku/docs/student-step-fail-3-1774061649.png
- 4-学生交卷前检查弹窗触发与返回作答：FAIL
  错误：创建学生体验回放题目: 期望 HTTP 200，实际 422。响应: {"detail":[{"type":"string_too_short","loc":["body","exam_category_code"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}},{"type":"string_too_short","loc":["body","joint_exam_group_code"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}}]}
  产物：/Users/shaotongli/Code/newaitiku/docs/student-step-fail-4-1774061650.png
- 5-学生模拟考试暂停与恢复：FAIL
  错误：创建学生体验回放题目: 期望 HTTP 200，实际 422。响应: {"detail":[{"type":"string_too_short","loc":["body","exam_category_code"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}},{"type":"string_too_short","loc":["body","joint_exam_group_code"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}}]}
  产物：/Users/shaotongli/Code/newaitiku/docs/student-step-fail-5-1774061650.png
- 6-学生模拟答题草稿刷新后恢复：FAIL
  错误：Page.wait_for_function: Timeout 10000ms exceeded.
  产物：/Users/shaotongli/Code/newaitiku/docs/student-step-fail-6-1774061660.png
- 7-学生倒计时归零自动交卷：FAIL
  错误：Page.wait_for_function: Timeout 10000ms exceeded.
  产物：/Users/shaotongli/Code/newaitiku/docs/student-step-fail-7-1774061670.png
- 8-教师侧可查询学生提交痕迹：PASS

## 三端联调矩阵
- 超管→教师：NOT_RUN
- 教师→学生：NOT_RUN
- 学生→教师：PASS

## 结果文件
- `/Users/shaotongli/Code/newaitiku/docs/student-click-replay-result-2026-03-21.json`
