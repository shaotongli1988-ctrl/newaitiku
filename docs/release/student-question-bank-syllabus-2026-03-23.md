# 学生端我的题库三子页与考试大纲页交付说明（2026-03-23）

## 1. 交付概览

- `我的题库` 现已统一为 3 个子页面：
  - `错题中心`
  - `沉淀题库`
  - `考试大纲`
- `考试大纲` 页面展示的是全部考试科目的总大纲，但会优先按当前学生报考范围自动展开 4 门必看科目。
- 页面结构继续复用教师端知识图谱中的“大纲脑图”表达方式，但在学生端收敛为只读总览，便于快速查阅。

## 2. 前端改动

### 2.1 路由与导航

- 新增学生端子路由：
  - `/student/question-bank/syllabus`
- `我的题库` 壳子页的二级导航已更新为：
  - `错题中心`
  - `沉淀题库`
  - `考试大纲`
- 原 `待修复 / 题库沉淀` 页内主标题已同步改名为 `错题中心 / 沉淀题库`，保证题库壳子与页内文案一致。

### 2.2 考试大纲页

- 新增页面：
  - `frontend/src/views/Student/QuestionBankSyllabus.vue`
- 页面能力：
  - 汇总全部考试科目
  - 自动识别当前学生 `coreSubjects` 对应的 4 门必看科目并完整展示
  - 非当前报考范围的科目保留在页面中，但默认折叠
  - 每门科目以只读思维导图式结构展示正式大纲节点
- 学生端大纲页不依赖 `subjectCode` 路由切换展示主体，而是以“当前报考范围 + 全科补充查阅”作为阅读入口。

### 2.3 公共工具与组件

- 新增学生端大纲工具：
  - `frontend/src/utils/studentSyllabusAtlas.js`
- 新增学生端只读导图组件：
  - `frontend/src/components/student/StudentSyllabusMindmap.vue`
- 大纲页复用了教师端已有的知识大纲解析工具：
  - `buildTeacherKnowledgeIndex`
  - `buildTeacherExamSectionSummary`
  - `buildTeacherContentOutlineTree`
  - `buildTeacherAutoLayout`
  - `resolveTeacherSpecialSections`

## 3. 接口说明

### 3.1 新增只读接口

- `GET /api/question-bank/student/syllabus/catalog`

用途：

- 向学生端 `考试大纲` 子页返回全部考试科目的总大纲目录。

返回内容：

- `generatedAt`
- `policyVersionCode`
- `subjectCount`
- `nodeCount`
- `examCategoryCount`
- `jointExamGroupCount`
- `publicSubjectCount`
- `professionalSubjectCount`
- `subjects[]`

`subjects[]` 中包含：

- `subjectCode`
- `subjectName`
- `subjectType`
- `examCategoryCode`
- `examCategoryName`
- `jointExamGroupCode`
- `jointExamGroupName`
- `nodeCount`
- `sourceFile`
- `tree`
- `nodes`

### 3.2 数据来源

- 本接口为只读聚合接口。
- 数据来源于本地大纲种子文件：
  - `data/knowledge_tree.json`
- 学生端默认展开的 4 门科目来自学生看板接口返回的 `coreSubjects`。
- 本次未新增数据库表、未新增写接口、未修改题库写入合同。

## 4. 状态与边界

- 本次不修改 `错题中心` 与 `沉淀题库` 的业务状态流。
- `错题归档 -> 沉淀题库 -> 恢复到错题中心` 的原有状态流保持不变。
- `考试大纲` 是纯查看页，不参与错题、沉淀、复习计划、归档恢复等写操作。
- 当前学生切换科目只影响其他学生学习页，不影响 `考试大纲` 子页的全科总览语义。

## 5. 测试与验证

### 5.1 单测

- 命令：
  - `npm --prefix frontend test -- src/utils/studentSyllabusAtlas.test.js`
- 结果：
  - 通过

### 5.2 构建验证

- 命令：
  - `npm --prefix frontend run build`
- 结果：
  - 通过

### 5.3 本地 UI 兼容层回归

- 本轮新增表单类本地兼容组件：
  - `ElRadio / ElRadioGroup / ElRadioButton`
  - `ElSwitch`
  - `ElInputNumber`
  - `ElForm / ElFormItem`
- 目的：
  - 继续保持学生端与教师端现有页面模板不改写
  - 通过 resolver 把常用 Element 组件逐步收敛到 Vue 本地实现
  - 继续压缩 `vendor-ep-form` 与 Element 相关基础包体积
- 额外验证命令：
  - `npm --prefix frontend test -- src/ui/components/radioShared.test.js src/ui/components/switchShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/formShared.test.js`

### 5.4 2026-03-24 续补说明

- 本轮继续把表单族组件从 Element Plus 逐步收敛到 Vue 本地兼容层，新增 `ElForm / ElFormItem` 的 resolver 映射，保持现有页面模板无需改写。
- 前端侧本次补齐的表单能力包括：
  - `model / rules`
  - `prop / required`
  - `label-position / label-width`
  - 表单实例 `validate()` 与 `clearValidate()`
- 该批次重点保证学生端、教师端现有表单场景仍沿用 `<el-form>` 语义，同时继续降低 `vendor-ep-form` 与基础样式包负担。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

### 5.5 2026-03-24 选择器批次续补说明

- 本轮继续收敛高频选择器场景，新增 `ElSelect / ElOption` 的本地 Vue 兼容实现，并通过 resolver 保持现有页面模板不改写。
- 当前已覆盖的选择器能力包括：
  - `clearable`
  - `filterable`
  - `multiple`
  - `collapse-tags`
  - `disabled`
  - `@change`
- 该批次重点承接学生端筛选器、教师端任务配置、题库筛选面板等高频下拉场景，减少后续继续依赖 Element Plus 选择器运行时。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

### 5.6 2026-03-24 级联选择批次续补说明

- 本轮继续收敛知识树与专业范围选择场景，新增 `ElCascader` 的本地 Vue 兼容实现，并通过 resolver 保持现有页面模板不改写。
- 当前已覆盖的级联选择能力包括：
  - `options`
  - `props.value / props.label / props.children`
  - `props.emitPath / props.checkStrictly`
  - `clearable`
  - `filterable`
  - `show-all-levels`
  - `@change / @visible-change`
- 该批次重点承接学生端知识路径筛选、教师端知识树定位、题目录入与试卷配置中的专业范围级联选择，减少后续继续依赖 Element Plus 级联运行时。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

### 5.7 2026-03-24 日期选择批次续补说明

- 本轮继续收敛消息中心等表单页中的时间选择场景，新增 `ElDatePicker` 的本地 Vue 兼容实现，并通过 resolver 保持现有页面模板不改写。
- 当前已覆盖的日期选择能力包括：
  - `type="datetime"`
  - `value-format="YYYY-MM-DDTHH:mm:ss"`
  - `clearable`
  - `disabled`
  - `v-model`
  - `@change`
- 该批次重点承接消息中心的定时发送时间录入场景，并保留基础 `date` 输入能力，减少后续继续依赖 Element Plus 日期控件运行时。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/components/datePickerShared.test.js src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

### 5.8 2026-03-24 按钮与输入批次续补说明

- 本轮继续收敛最常见的基础交互控件，新增 `ElButton / ElInput / ElIcon` 的本地 Vue 兼容实现，并通过 resolver 保持现有页面模板不改写。
- 当前已覆盖的按钮能力包括：
  - `type="primary|success|warning|danger|info"`
  - `plain / link / text`
  - `size="small|large"`
  - `loading`
  - `disabled`
  - `icon`
- 当前已覆盖的输入能力包括：
  - `v-model / model-value`
  - `clearable`
  - `type="textarea"`
  - `type="password" + show-password`
  - `maxlength + show-word-limit`
  - `readonly / disabled`
  - `rows`
  - `@input / @change / @focus / @blur`
- 当前图标兼容层重点承接导航、上传入口与消息中心 tab 图标等 `<el-icon>` 包裹场景，减少继续依赖 Element Plus 包裹组件。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/components/buttonShared.test.js src/ui/components/inputShared.test.js src/ui/components/datePickerShared.test.js src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

### 5.9 2026-03-24 弹窗与抽屉批次续补说明

- 本轮继续收敛页面容器型组件，新增 `ElDialog / ElDrawer` 的本地 Vue 兼容实现，并通过 resolver 保持现有页面模板不改写。
- 当前已覆盖的弹窗能力包括：
  - `v-model`
  - `title`
  - `width`
  - `show-close`
  - `close-on-click-modal`
  - `destroy-on-close`
  - `#footer`
  - `@closed`
- 当前已覆盖的抽屉能力包括：
  - `v-model`
  - `title`
  - `size`
  - `direction="rtl|ltr|ttb"`
  - `with-header`
  - `show-close`
  - `close-on-click-modal`
  - `destroy-on-close`
  - `#footer`
  - `@closed`
- 该批次重点承接教师端任务创建、题目详情、组卷编辑、AI 辅助面板、学生端交卷确认以及移动端侧边菜单等弹层场景，并保留 `el-dialog__*`、`el-drawer__*` 结构类名以兼容现有样式覆写。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/components/dialogShared.test.js src/ui/components/buttonShared.test.js src/ui/components/inputShared.test.js src/ui/components/datePickerShared.test.js src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

### 5.10 2026-03-24 表格批次续补说明

- 本轮继续收敛高频数据展示组件，新增 `ElTable / ElTableColumn` 的本地 Vue 兼容实现，并通过 resolver 保持现有页面模板不改写。
- 当前已覆盖的表格能力包括：
  - `data`
  - `border / stripe / size="small"`
  - `empty-text`
  - `row-key`
  - `max-height`
  - `type="selection|index|expand"`
  - `reserve-selection`
  - `show-overflow-tooltip`
  - `fixed="left|right"`
  - `expand-row-keys`
  - `@selection-change`
  - 表格实例 `clearSelection() / toggleRowSelection() / toggleRowExpansion()`
- 该批次重点承接教师端题库管理、组卷中心、试卷模板、消息历史、管理端学生列表以及批量导入结果等表格主路径，优先保证选择列、展开列、空态和固定操作列这些高频交互不回退。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/components/tableShared.test.js src/ui/components/dialogShared.test.js src/ui/components/buttonShared.test.js src/ui/components/inputShared.test.js src/ui/components/datePickerShared.test.js src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

### 5.11 2026-03-24 上传与轻交互批次续补说明

- 本轮继续收敛剩余的 Element Plus 轻交互组件，新增 `ElUpload / ElAutocomplete / ElDropdown / ElDropdownMenu / ElDropdownItem / ElSlider / ElCollapseTransition` 的本地 Vue 兼容实现，并通过 resolver 保持现有页面模板不改写。
- 当前已覆盖的上传能力包括：
  - `drag`
  - `accept`
  - `limit`
  - `file-list`
  - `show-file-list`
  - `auto-upload`
  - `on-change / on-remove / on-exceed`
- 当前已覆盖的自动补全能力包括：
  - `v-model`
  - `fetch-suggestions`
  - `value-key`
  - `clearable`
  - `select`
  - 自定义建议项 slot
- 当前已覆盖的下拉菜单能力包括：
  - `trigger="click"`
  - `command`
  - `dropdown` 命名 slot
  - `dropdown-item.command`
- 当前已覆盖的滑块与折叠动画能力包括：
  - `ElSlider` 的 `min / max / step / disabled / show-input / v-model`
  - `ElCollapseTransition` 对筛选面板折叠区的高度动画
- 该批次重点承接管理端大纲 AI 解析上传、教师端试卷状态流转菜单、题目录入知识点搜索补全、AI 组卷难度设置以及筛选器收起展开等现有主路径，继续减少后续对 Element Plus 运行时的依赖。
- 数据说明：
  - 本轮仅替换前端交互组件，不修改现有接口合同、数据库结构、读写链路或历史数据。
  - 上传动作仍然由业务页面的既有回调驱动，不新增新的文件传输契约。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/components/uploadShared.test.js src/ui/components/autocompleteShared.test.js src/ui/components/dropdownShared.test.js src/ui/components/sliderShared.test.js src/ui/components/collapseTransitionShared.test.js`
  - `npm --prefix frontend run build`

### 5.12 2026-03-24 树形组件批次续补说明

- 本轮继续收敛剩余的 Element Plus 树形组件，新增 `ElTreeSelect / ElTreeV2` 的本地 Vue 兼容实现，并通过 resolver 保持现有页面模板不改写。
- 当前已覆盖的树列表能力包括：
  - `data`
  - `props.value / props.label / props.children`
  - `height`
  - `node-key`
  - `highlight-current`
  - `draggable`
  - `allow-drop`
  - `filter-method`
  - `node-click / node-drop`
  - 组件实例 `setCurrentKey() / filter()`
- 当前已覆盖的树选择能力包括：
  - `v-model`
  - `data`
  - `multiple`
  - `show-checkbox`
  - `check-strictly`
  - `clearable`
  - `collapse-tags`
  - `collapse-tags-tooltip`
  - `disabled`
- 该批次重点承接教师端动态知识点树的拖拽排序与高亮定位，以及 AI 组卷参数弹窗中的知识点多选筛选场景，继续减少对 Element Plus 树形运行时的依赖。
- 数据说明：
  - 本轮仅替换前端树形组件，不修改知识点树接口结构、拖拽排序写接口、数据库结构与既有状态流。
  - 拖拽排序仍由页面原有的同级拖拽约束与后端排序逻辑共同控制，不新增新的排序契约。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/components/treeShared.test.js src/ui/components/uploadShared.test.js src/ui/components/autocompleteShared.test.js src/ui/components/dropdownShared.test.js src/ui/components/sliderShared.test.js src/ui/components/collapseTransitionShared.test.js`
  - `npm --prefix frontend run build`

### 5.13 2026-03-24 Element 依赖清理续补说明

- 本轮继续收敛剩余的 Element 运行时依赖，移除了 `ElementPlusResolver` 回退，并新增本地 Vue 图标库入口。
- 本轮新增的本地图标桥接文件包括：
  - `frontend/src/ui/iconFactory.js`
  - `frontend/src/ui/icons/library.js`
- 本轮新增统一项目内入口：
  - `frontend/src/ui/icons/index.js`
  - `frontend/src/ui/feedback/index.js`
- 当前页面中的图标与反馈服务导入已统一改为 `@/ui/icons` 与 `@/ui/feedback`，不再保留第三方 UI 包源码引用。
- 本轮已完成：
  - 从 `frontend/package.json` 与 `frontend/package-lock.json` 移除 `element-plus`
  - 清理 `frontend/vite.config.js` 中失效的 `vendor-ep-*` chunk 分包规则
  - 清理 `frontend/vite.config.js` 中不再需要的 `element-plus` / `@element-plus/icons-vue` alias
- 结果：
  - 前端构建产物不再生成 `vendor-ep-base / vendor-ep-form / vendor-ep-data / vendor-ep-feedback / vendor-ep-icons` 相关 chunk
  - 业务页面模板、消息调用方式和图标 import 方式均保持不变
- 数据说明：
  - 本轮仅处理前端依赖、图标桥接与构建配置，不修改接口合同、数据库结构、状态流与业务读写逻辑。
- 本轮补充验证命令：
  - `npm --prefix frontend test -- src/ui/icons/library.test.js src/ui/components/treeShared.test.js src/ui/components/uploadShared.test.js src/ui/components/autocompleteShared.test.js src/ui/components/dropdownShared.test.js src/ui/components/sliderShared.test.js src/ui/components/collapseTransitionShared.test.js`
  - `npm --prefix frontend run build`

## 6. 风险说明

- 当前 `考试大纲` 页面依赖 `data/knowledge_tree.json` 的结构稳定性。
- 若后续大纲种子文件字段调整，需要同步维护学生端聚合接口与学生端大纲工具函数。
- 本次采用只读聚合接口，避免了学生端一次性并发请求全部科目知识树带来的性能和一致性风险。
