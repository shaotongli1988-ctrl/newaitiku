# 学生端考试大纲页实施说明（2026-03-23）

## 本次落地范围

- 页面重构为“当前报考范围摘要 + 必看 4 门完整展示 + 其他科目折叠区”结构。
- 学生端考试大纲内容改为复用教师端思维导图风格的只读导图卡。
- 保持 `GET /api/question-bank/student/syllabus/catalog` 只读接口不变。
- 额外读取学生看板 `coreSubjects`，作为“当前学生需要完整查看的 4 门科目”来源，不新增后端写接口。

## 关键交互

- 页面顶部直接展示当前报考门类 / 专业组，并给出 4 门必看科目的跳转锚点。
- `coreSubjects` 对应的 4 门科目默认完整展开，连续展示完整思维导图。
- 非当前报考范围的科目仍保留在页面中，但进入折叠面板，默认收起。
- 折叠区支持关键字筛选，并支持一键“展开全部 / 全部收起”。
- 页面继续保留加载态与空态语义，不引入新的写操作。

## 主要实现文件

- `frontend/src/views/Student/QuestionBankSyllabus.vue`
- `frontend/src/components/student/StudentSyllabusMindmap.vue`
- `frontend/src/utils/studentSyllabusAtlas.js`
- `frontend/src/utils/studentSyllabusAtlas.test.js`

## 数据说明

- 本次仅消费既有考试大纲只读接口返回的数据，不修改接口结构。
- 当前学生“必看 4 门”的默认展开顺序取自 `GET /api/question-bank/student/dashboard` 返回的 `coreSubjects`。
- 不涉及数据库表结构调整、历史数据处理脚本、双写链路或运行时主读写路径切换。
- 思维导图节点直接由大纲接口已有 `nodes` 前端适配生成，不额外请求教师端知识图谱接口。

## 视觉与复用说明

- 学生端导图卡复用了教师端图谱的核心表达能力：
  - `KnowledgeGraphFlowSurface`
  - `buildTeacherKnowledgeIndex`
  - `buildTeacherAutoLayout`
  - `buildTeacherContentOutlineTree`
  - `buildTeacherExamSectionSummary`
- 节点保持教师端的导图层级视觉，但在学生端收敛为只读浏览，不带关系编辑与强化练入口。

## API 契约对齐

- 对齐了 `frontend/src/api/contracts.ts` 中与后端 `app/contracts.py` 的存量漂移。
- `KnowledgeNode` 补齐了 `full_label`、`short_label`、`wrong_count` 及对应 camel alias。
- `StudentAiMarkingSubmitRequest`、`StudentPracticeSubmitRequest`、`PracticeSubmitModel` 补齐了提交链路中的可选字段别名。
- 新增 `ExamTaskCreateRequest`、`StudentMockExamStartRequest` 前端契约声明，补齐之前缺失的 schema 映射。
- `BaseResponse` 明确保留题库统一响应包 `{ code, message, data }`。
- 前端服务层把删除类接口与 `GET /api/knowledge-tree`、`GET /api/question-bank/admin/console` 收敛成守卫可识别的标准 endpoint 写法。
- 后端 OpenAPI 取消暴露页面引导路由（含教师端、学生端、管理端与消息中心入口），只保留真实 API 契约。
- 静态契约文件 `docs/contracts/current/openapi.json` 已通过 `scripts/export_openapi.py` 与当前运行时 OpenAPI 重新同步，并移除了不影响契约校验的展示元数据，避免文档与实现继续漂移且确保守卫可完整解析。

## 已验证

- `npm test -- src/utils/studentSyllabusAtlas.test.js`
- `npm run build`

## UI 兼容层增量收敛

- 本轮继续把 Element Plus 的基础表单组件逐步替换为本地 Vue 兼容实现，保持现有页面模板中的 `<el-*>` 写法不变。
- 已新增本地兼容层：
  - `ElRadio / ElRadioGroup / ElRadioButton`
  - `ElSwitch`
  - `ElInputNumber`
  - `ElForm / ElFormItem`
- `ElInputNumber` 已覆盖当前项目真实使用到的能力：
  - `v-model`
  - `:min / :max / :step`
  - `:precision`
  - `:disabled`
  - `controls-position="right"`
  - `@change`
- `ElForm / ElFormItem` 已覆盖当前项目真实使用到的核心能力：
  - `:model / :rules`
  - `label-position / label-width`
  - `prop / required`
  - 表单实例 `validate()`
  - 表单实例 `clearValidate()`
  - `required` 与自定义 `validator` 规则
- 本轮继续沿用 `frontend/vite.config.js` 中的本地 resolver，把页面模板无感切到本地组件，目标是持续压缩 `vendor-ep-form` 与基础样式体积。

## 本轮补充验证

- `npm --prefix frontend test -- src/ui/components/radioShared.test.js src/ui/components/switchShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/formShared.test.js`
- `npm --prefix frontend run build`

## 2026-03-24 续补说明

- 本轮继续收敛 Element Plus 表单依赖，新增 `ElForm / ElFormItem` 的 Vue 本地兼容实现，并通过 `frontend/vite.config.js` resolver 无感替换现有页面中的 `<el-form>` 与 `<el-form-item>`。
- 本地表单兼容层当前覆盖项目实际使用到的 `model / rules / prop / required / label-position / label-width` 能力，同时支持表单实例 `validate()` 与 `clearValidate()`。
- `FormItem` 已补齐错误态后的值变更重校验逻辑，确保学生端与教师端既有表单页面在不改模板的前提下保持可用。
- 本轮针对表单批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

## 2026-03-24 选择器批次续补

- 本轮继续把高频表单组件从 Element Plus 收敛到 Vue 本地兼容层，新增 `ElSelect / ElOption` 的本地实现，并接入 `frontend/vite.config.js` resolver。
- 选择器兼容层保持现有 `<el-select><el-option /></el-select>` 模板结构不变，通过隐藏 slot 注册 option，再由本地下拉层统一承接展示与交互。
- 当前批次已覆盖项目真实使用到的核心能力：
  - `v-model / model-value`
  - `clearable`
  - `filterable`
  - `multiple`
  - `collapse-tags`
  - `disabled`
  - `@change`
- 本轮针对选择器批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

## 2026-03-24 级联选择批次续补

- 本轮继续收敛剩余高频表单族组件，新增 `ElCascader` 的 Vue 本地兼容实现，并接入 `frontend/vite.config.js` resolver。
- 级联兼容层当前覆盖项目真实使用到的核心能力：
  - `:options`
  - `:props="{ value, label, children, emitPath, checkStrictly }"`
  - `clearable`
  - `filterable`
  - `show-all-levels`
  - `@change`
  - `@visible-change`
- 当前实现重点承接专业范围选择、知识树路径筛选、批量标签纠偏等场景，兼容 `emitPath: true` 下的路径数组回传语义，并保留严格/非严格选择的差异。
- 本轮针对级联批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

## 2026-03-24 日期选择批次续补

- 本轮继续收敛消息发送等表单场景里的时间控件依赖，新增 `ElDatePicker` 的 Vue 本地兼容实现，并接入 `frontend/vite.config.js` resolver。
- 当前日期控件兼容层已覆盖项目真实使用到的核心能力：
  - `type="datetime"`
  - `value-format="YYYY-MM-DDTHH:mm:ss"`
  - `clearable`
  - `disabled`
  - `v-model`
  - `@change`
- 本轮实现以消息中心发送表单为主路径，同时保留基础 `date` 输入能力，确保后续若有简单日期场景可以直接复用。
- 本轮针对日期批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/components/datePickerShared.test.js src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

## 2026-03-24 按钮与输入批次续补

- 本轮继续把高频基础控件从 Element Plus 收敛到 Vue 本地兼容层，新增 `ElButton / ElInput / ElIcon` 的本地实现，并接入 `frontend/vite.config.js` resolver。
- 当前按钮兼容层已覆盖项目真实使用到的核心能力：
  - `type="primary|success|warning|danger|info"`
  - `plain / link / text`
  - `size="small|large"`
  - `:loading`
  - `:disabled`
  - `:icon`
- 当前输入兼容层已覆盖项目真实使用到的核心能力：
  - `v-model / model-value`
  - `clearable`
  - `type="textarea"`
  - `type="password" + show-password`
  - `maxlength + show-word-limit`
  - `readonly / disabled`
  - `rows`
  - `@input / @change / @focus / @blur`
- 当前图标兼容层重点承接导航、消息中心和上传入口里的 `<el-icon>` 包裹场景，保持既有 slot 图标写法不变。
- 本轮针对按钮与输入批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/components/buttonShared.test.js src/ui/components/inputShared.test.js src/ui/components/datePickerShared.test.js src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

## 2026-03-24 弹窗与抽屉批次续补

- 本轮继续收敛页面容器型组件依赖，新增 `ElDialog / ElDrawer` 的 Vue 本地兼容实现，并接入 `frontend/vite.config.js` resolver。
- 当前弹窗兼容层已覆盖项目真实使用到的核心能力：
  - `v-model`
  - `title`
  - `width`
  - `show-close`
  - `close-on-click-modal`
  - `destroy-on-close`
  - `#footer`
  - `@closed`
- 当前抽屉兼容层已覆盖项目真实使用到的核心能力：
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
- 这一批重点承接教师端组卷、题目详情、考试任务创建、学生端交卷确认、移动端菜单和消息类辅助面板等既有弹层场景，并保留 `el-dialog__header/body/footer`、`el-drawer__header/body/footer` 类名，确保现有页面样式继续生效。
- 本轮针对弹窗与抽屉批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/components/dialogShared.test.js src/ui/components/buttonShared.test.js src/ui/components/inputShared.test.js src/ui/components/datePickerShared.test.js src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

## 2026-03-24 表格批次续补

- 本轮继续收敛高频数据展示组件依赖，新增 `ElTable / ElTableColumn` 的 Vue 本地兼容实现，并接入 `frontend/vite.config.js` resolver。
- 当前表格兼容层已覆盖项目真实使用到的核心能力：
  - `:data`
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
- 这一批重点承接教师端题库筛选、组卷选题、试卷模板、消息发送历史、管理端学生列表以及批量导入结果等表格场景，优先保证“选择列、展开列、空态和固定操作列”这些高风险路径可用。
- 本轮针对表格批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/components/tableShared.test.js src/ui/components/dialogShared.test.js src/ui/components/buttonShared.test.js src/ui/components/inputShared.test.js src/ui/components/datePickerShared.test.js src/ui/components/cascaderShared.test.js src/ui/components/selectShared.test.js src/ui/components/formShared.test.js src/ui/components/inputNumberShared.test.js src/ui/components/switchShared.test.js src/ui/components/radioShared.test.js`
  - `npm --prefix frontend run build`

## 2026-03-24 上传与轻交互批次续补

- 本轮继续收敛仍然依赖 Element Plus 的轻交互组件，新增 `ElUpload / ElAutocomplete / ElDropdown / ElDropdownMenu / ElDropdownItem / ElSlider / ElCollapseTransition` 的 Vue 本地兼容实现，并接入 `frontend/vite.config.js` resolver。
- 当前上传兼容层已覆盖项目真实使用到的核心能力：
  - `drag`
  - `accept`
  - `:limit`
  - `:file-list`
  - `:show-file-list="false"`
  - `:auto-upload="false"`
  - `:on-change / :on-remove / :on-exceed`
- 当前自动补全兼容层已覆盖项目真实使用到的核心能力：
  - `v-model`
  - `:fetch-suggestions`
  - `value-key`
  - `clearable`
  - `@select`
  - `#default="{ item }"`
- 当前下拉菜单兼容层已覆盖项目真实使用到的核心能力：
  - `trigger="click"`
  - `@command`
  - `#dropdown`
  - `:command`
- 当前滑块与折叠过渡兼容层已覆盖项目真实使用到的核心能力：
  - `ElSlider` 的 `v-model / min / max / step / disabled / show-input`
  - `ElCollapseTransition` 对 `v-show` 折叠容器的高度与透明度过渡
- 这一批重点承接管理端大纲 AI 文件上传、题目录入知识点自动补全、教师端试卷状态流转菜单、AI 组卷难度滑块以及筛选面板折叠动画等真实页面路径，继续保持既有 `<el-*>` 模板不改写。
- 数据与契约说明：
  - 本轮仅替换前端组件承载层，不修改接口结构、数据库表结构、历史数据处理逻辑与读写链路。
  - 上传组件仍沿用页面既有 `on-change / on-remove / on-exceed` 回调控制文件状态，不新增上传直传协议。
- 本轮针对上传与轻交互批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/components/uploadShared.test.js src/ui/components/autocompleteShared.test.js src/ui/components/dropdownShared.test.js src/ui/components/sliderShared.test.js src/ui/components/collapseTransitionShared.test.js`
  - `npm --prefix frontend run build`

## 2026-03-24 树形组件批次续补

- 本轮继续收敛剩余的 Element Plus 树形组件依赖，新增 `ElTreeSelect / ElTreeV2` 的 Vue 本地兼容实现，并接入 `frontend/vite.config.js` resolver。
- 当前 `ElTreeV2` 兼容层已覆盖项目真实使用到的核心能力：
  - `:data`
  - `:props="{ value, label, children }"`
  - `:height`
  - `node-key`
  - `highlight-current`
  - `:draggable`
  - `:allow-drop`
  - `:filter-method`
  - `@node-click`
  - `@node-drop`
  - 组件实例 `setCurrentKey() / filter()`
- 当前 `ElTreeSelect` 兼容层已覆盖项目真实使用到的核心能力：
  - `v-model`
  - `:data`
  - `multiple`
  - `show-checkbox`
  - `check-strictly`
  - `clearable`
  - `collapse-tags`
  - `collapse-tags-tooltip`
  - `:disabled`
- 这一批重点承接教师端知识点树拖拽排序、当前节点高亮、关键字过滤，以及 AI 组卷弹窗里的知识点多选筛选场景，继续保持既有 `<el-tree-v2>` / `<el-tree-select>` 模板不改写。
- 数据与状态说明：
  - 本轮仅替换前端树形组件承载层，不修改知识点树接口结构、排序接口、数据库表结构与状态流定义。
  - 拖拽排序仍沿用现有页面里的同级拖拽校验与后端 `moveKnowledgeNode` 顺序调整逻辑，不新增额外排序协议。
- 本轮针对树形组件批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/components/treeShared.test.js src/ui/components/uploadShared.test.js src/ui/components/autocompleteShared.test.js src/ui/components/dropdownShared.test.js src/ui/components/sliderShared.test.js src/ui/components/collapseTransitionShared.test.js`
  - `npm --prefix frontend run build`

## 2026-03-24 Element 依赖清理续补

- 本轮继续收敛剩余的 `element-plus` 直接依赖，不再通过 `ElementPlusResolver` 回退加载第三方组件。
- 新增本地图标桥接：
  - `frontend/src/ui/icons/library.js`
  - `frontend/src/ui/iconFactory.js`
- 新增统一项目内入口：
  - `frontend/src/ui/icons/index.js`
  - `frontend/src/ui/feedback/index.js`
- 业务文件中的图标与反馈服务导入已统一收口到 `@/ui/icons` 与 `@/ui/feedback`，不再保留 `element-plus` 与 `@element-plus/icons-vue` 源码导入。
- `element-plus` 现已从前端依赖清单与锁文件中移除，消息、确认框、通知继续由 `frontend/src/ui/feedback/service.js` 提供本地承接。
- 同时清理了 `frontend/vite.config.js` 中已失效的 Element Plus chunk 分包规则，避免后续构建继续保留无效配置。
- 同时移除了不再需要的 `element-plus` / `@element-plus/icons-vue` Vite alias 与历史桥接入口。
- 这一批的交付意义：
  - 前端构建产物中不再生成 `vendor-ep-*` 相关 chunk。
  - 组件模板、消息调用与图标 import 方式保持不变，业务页面无需改写。
- 数据与状态说明：
  - 本轮只处理前端依赖与构建入口，不修改接口、数据库、状态流与业务读写逻辑。
- 本轮针对依赖清理批次额外完成以下验证：
  - `npm --prefix frontend test -- src/ui/icons/library.test.js src/ui/components/treeShared.test.js src/ui/components/uploadShared.test.js src/ui/components/autocompleteShared.test.js src/ui/components/dropdownShared.test.js src/ui/components/sliderShared.test.js src/ui/components/collapseTransitionShared.test.js`
  - `npm --prefix frontend run build`
