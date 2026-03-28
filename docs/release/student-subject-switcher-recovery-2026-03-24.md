# 学生端科目切换恢复说明

## 交付总览

- 恢复学生端右上角科目切换区的数据链路，优先使用学生 dashboard 的 `coreSubjects`，异常时回退到 content baseline。
- 修正学生端初始化语义，避免 dashboard 与 baseline 都失败时仍把 store 标记为已完成初始化。
- 收紧顶栏科目同步逻辑，路由中的 `subjectCode` 必须是当前可选科目之一，否则自动回退到有效科目并同步地址栏。

## 前端说明

- `frontend/src/stores/userStore.js` 为学生端补上 baseline 初始化兜底，并保留专业组下的 `subjects` 结构，供页面与标签映射复用。
- `frontend/src/stores/subjectContextStore.js` 与 `frontend/src/layouts/DefaultLayout.vue` 共用同一套有效科目解析规则，避免右上角选择器被无效 query 污染。
- 右上角切换区继续沿用现有中文科目下拉，不新增额外交互。

## 测试说明

- 新增 `frontend/src/stores/userStore.test.js`，覆盖 dashboard 不可用时的 baseline 恢复，以及彻底失败时不再误判初始化成功。
- 新增 `frontend/src/utils/studentSubjectContext.test.js`，覆盖无效 `subjectCode` 的回退解析规则。
