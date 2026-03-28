# 三端统一真点击回放汇总（2026-03-18）

## 三端状态
- 超管端（`super_admin`）：PASS（失败 0）
- 教师端（`teacher`）：PASS（失败 0）
- 学生端（`student`）：PASS（失败 0）

## 三端联调矩阵
- 超管→教师：PASS
- 教师→学生：PASS
- 学生→教师：PASS

## 失败定位建议
- 页面失败：优先检查页面元素选择器、跳转路径与角色入口守卫。
- 接口失败：优先检查 `{code,message,data}` 包络、状态码与分页参数。
- 权限失败：优先检查 `X-Role/X-User-Id` 与账号权限点/启停状态。

## 产物目录
- `/Users/shaotongli/Code/newaitiku/docs`
