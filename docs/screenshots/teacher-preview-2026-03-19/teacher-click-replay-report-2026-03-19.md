# 教师端真点击回放验收报告（2026-03-19）

## 执行概览
- 角色：`teacher`
- 回放模式：`python-playwright-true-click-replay`
- 执行时间：`2026-03-19T14:54:25.864` 至 `2026-03-19T14:55:06.109`
- 回放地址：`http://127.0.0.1:8000`
- 超时：`20 秒/步骤`
- 数据库：``

## 结果总览
- 步骤总数：4
- 通过：0
- 失败：4
- 问题数：4

## 分步结果
- 1-教师登录并进入题库页：FAIL
  错误：Locator.fill: Timeout 20000ms exceeded.
Call log:
  - waiting for locator("#password-login-form input[name='phone']")

  产物：/Users/shaotongli/Code/newaitiku/docs/screenshots/teacher-preview-2026-03-19/teacher-step-fail-1-1773932086.png
- 2-教师真点击创建题目：FAIL
  错误：Locator.click: Timeout 20000ms exceeded.
Call log:
  - waiting for locator("#open-create-modal")

  产物：/Users/shaotongli/Code/newaitiku/docs/screenshots/teacher-preview-2026-03-19/teacher-step-fail-2-1773932106.png
- 3-教师真点击发布题目：FAIL
  错误：缺少新建题目ID，无法发布。
  产物：/Users/shaotongli/Code/newaitiku/docs/screenshots/teacher-preview-2026-03-19/teacher-step-fail-3-1773932106.png
- 4-教师发布题目在学生端可见：FAIL
  错误：缺少教师发布题目 ID。
  产物：/Users/shaotongli/Code/newaitiku/docs/screenshots/teacher-preview-2026-03-19/teacher-step-fail-4-1773932106.png

## 三端联调矩阵
- 超管→教师：NOT_RUN
- 教师→学生：NOT_RUN
- 学生→教师：NOT_RUN

## 结果文件
- `/Users/shaotongli/Code/newaitiku/docs/screenshots/teacher-preview-2026-03-19/teacher-click-replay-result-2026-03-19.json`
