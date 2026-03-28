# 学习方法模块提测群公告模板（2026-03-25）

## 一、提测申请模板

```text
【提测申请】
模块：学习方法（learning_method）
批次：2026-03-25
当前结论：可提测

本次主要变更：
1. 修复 API schema drift，前后端契约对齐
2. 学习进度状态流守卫补强（start/complete）
3. 发布证据、配置核对、回滚方案已补齐

验证结果：
- schema drift：none
- openapi 范围：2 passed
- integration：46 passed
- acceptance：120/120 passed
- delivery guard：可上线（无阻断）

请产品/测试确认进入提测执行窗口。
```

## 二、提测开始模板

```text
【提测开始】
模块：学习方法（learning_method）
批次：2026-03-25
开始时间：____

提测范围：
1. 学习方法列表/详情
2. 学习方法开始练习、完成练习
3. 管理端学习方法维护与排序

请按交接文档执行：
- docs/release/learning-method-test-handoff-2026-03-25.md
```

## 三、提测通过模板

```text
【提测通过】
模块：学习方法（learning_method）
批次：2026-03-25
结论：通过

回归结论：
1. 关键接口与页面验证通过
2. 契约一致性无漂移
3. 无阻断问题

建议进入发布排期。
```

## 四、提测不通过模板

```text
【提测不通过】
模块：学习方法（learning_method）
批次：2026-03-25
结论：不通过

阻断问题：
1. ____
2. ____

处理动作：
1. 研发修复后回归
2. 更新提测时间并重新提测
```

## 五、关联文档

- `docs/release/learning-method-test-handoff-2026-03-25.md`
- `docs/release/learning-method-ops-release-brief-2026-03-25.md`
- `docs/release/learning-method-rollback-switch-2026-03-25.md`
- `docs/release/delivery-guard-2026-03-25-final.md`
