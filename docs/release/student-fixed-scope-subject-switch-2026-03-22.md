# 学生端固定范围与科目切换收敛说明

## 交付总览

- 学生端顶部范围展示改为单行信息：`学科门类：xxx  联考专业组：xxx`
- 原有全局“切换科目”能力继续保留，并与专业信息保持同一行展示，视觉尺寸和当前科目选择接近
- 其他专业会按当前账号实际范围自动显示对应的学科门类和联考专业组，不再写死单一专业

## 前端说明

- 新增 `frontend/src/utils/studentSubjectScope.js`，统一维护学生端顶部范围展示的默认兜底口径
- `frontend/src/layouts/DefaultLayout.vue` 改为在同一行中展示“学科门类 / 联考专业组”与科目下拉，不再显示“固定范围”
- `frontend/src/views/Student/Home.vue` 恢复按当前联考专业组动态计算首页参考组别，保证其他专业展示正确

## 数据说明

- 本次仅涉及学生端前端展示与文案口径收敛
- 不涉及接口字段、数据库结构、数据迁移、回填或切流
- 现有科目列表仍复用学生看板返回的 `coreSubjects`

## 测试说明

- 新增 `frontend/src/utils/studentSubjectScope.test.js`，覆盖固定范围常量、前缀拼接和空科目兜底
- 执行 `npm test -- src/utils/studentSubjectScope.test.js src/utils/studentHomeViewModel.test.js src/utils/practiceScope.test.js`
- 执行 `npm run build`
