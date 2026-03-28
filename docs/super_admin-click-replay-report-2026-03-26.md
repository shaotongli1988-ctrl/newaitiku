# 超管端真点击回放验收报告（2026-03-26）

## 执行概览
- 角色：`super_admin`
- 回放模式：`python-playwright-true-click-replay`
- 执行时间：`2026-03-26T13:22:09.728` 至 `2026-03-26T13:24:37.292`
- 回放地址：`http://127.0.0.1:8017`
- 超时：`20 秒/步骤`
- 数据库：`/tmp/question-bank-click-replay.db`

## 结果总览
- 步骤总数：8
- 通过：1
- 失败：7
- 问题数：7

## 分步结果
- 1-超管入口未登录强制跳转登录页：FAIL
  错误：未登录访问超管控制台时不应停留在 /admin/control-center。
  产物：/Users/shaotongli/Code/newaitiku/docs/super_admin-step-fail-1-1774531330.png
- 2-超管登录并进入控制台：FAIL
  错误：Locator.fill: Timeout 20000ms exceeded.
Call log:
  - waiting for get_by_placeholder("请输入密码")
    - locator resolved to <input value="" type="password" data-v-4078f3ec="" placeholder="请输入密码" class="el-input__inner"/>
    - fill("seed-password-admin-001")
  - attempting fill action
    - waiting for element to be visible, enabled and editable

- 3-超管保存系统设置：FAIL
  错误：Locator.fill: Timeout 20000ms exceeded.
Call log:
  - waiting for locator(".content-grid > .el-card").first.locator(".el-form-item:has-text('平台名称') input")

  产物：/Users/shaotongli/Code/newaitiku/docs/super_admin-step-fail-3-1774531390.png
- 4-超管创建更新教师并验证教师端可用：FAIL
  错误：Locator.fill: Timeout 20000ms exceeded.
Call log:
  - waiting for locator(".content-grid > .el-card").nth(1).locator(".el-form-item:has-text('用户ID') input")

  产物：/Users/shaotongli/Code/newaitiku/docs/super_admin-step-fail-4-1774531417.png
- 5-超管执行考生导入与导出：FAIL
  错误：Locator.fill: Timeout 20000ms exceeded.
Call log:
  - waiting for locator(".secondary-grid > .el-card").first.locator("textarea").first

  产物：/Users/shaotongli/Code/newaitiku/docs/super_admin-step-fail-5-1774531437.png
- 6-超管校验无权限与停用边界：FAIL
  错误：Locator.fill: Timeout 20000ms exceeded.
Call log:
  - waiting for locator(".content-grid > .el-card").nth(1).locator(".el-form-item:has-text('用户ID') input")

  产物：/Users/shaotongli/Code/newaitiku/docs/super_admin-step-fail-6-1774531457.png
- 7-超管校验 CSRF 失败拦截：PASS
- 8-超管退出后不可继续写操作：FAIL
  错误：Locator.click: Timeout 20000ms exceeded.
Call log:
  - waiting for get_by_role("button", name="退出登录").first

  产物：/Users/shaotongli/Code/newaitiku/docs/super_admin-step-fail-8-1774531477.png

## 三端联调矩阵
- 超管→教师：NOT_RUN
- 教师→学生：NOT_RUN
- 学生→教师：NOT_RUN

## 结果文件
- `/Users/shaotongli/Code/newaitiku/docs/super_admin-click-replay-result-2026-03-26.json`
