# knowledge 模块合同

本模块按 `$question-bank-fullstack-alignment-engineer` 的固定合同单独落地，只覆盖 `knowledge` 模块。

## 表字段

`knowledge` 表固定字段如下：

`id`, `parentId`, `name`, `sort`, `status`, `extJson`, `createTime`, `updateTime`

说明：

- `id`
  - 节点主键
- `parentId`
  - 父节点 ID，根节点为空
- `name`
  - 节点名称
- `sort`
  - 同级排序值
- `status`
  - `ENABLED` / `DISABLED`
- `extJson`
  - 模块扩展信息，仅存放非固定字段，例如 `level`、`subjectId`、`weight`
- `createTime`
  - 创建时间
- `updateTime`
  - 更新时间

## 功能范围

- 三级树查询
- 父子节点查询
- 节点 CRUD
- 同级排序字段维护
- 节点上移/下移排序

## API

- `GET /api/question-bank/knowledge/tree`
- `GET /api/knowledge-tree`
- `GET /api/question-bank/knowledge/children`
- `GET /api/question-bank/knowledge/{knowledge_id}`
- `POST /api/question-bank/knowledge`
- `PUT /api/question-bank/knowledge/{knowledge_id}`
- `DELETE /api/question-bank/knowledge/{knowledge_id}`
- `POST /api/question-bank/knowledge/{knowledge_id}/sort/{direction}`

所有接口统一返回：

```json
{
  "code": "OK",
  "message": "success",
  "data": {}
}
```

## 校验规则

- 支持 L1-L5 五级知识树
- 节点 `extJson` 需同步维护 `level` 与 `levelCode`（`L1`-`L5`）
- 同级节点 `name` 不可重复
- `parentId` 必须存在，且不能指向自身或自己的子孙节点
- 有子节点的节点不可直接删除
- `status` 仅支持 `ENABLED`、`DISABLED`

## 前端页面

- 页面地址：`/teacher/knowledge`
- 页面地址：`/student/analysis`
- 页面结构保持左侧菜单、顶部导航、中心内容卡片
- 表单字段与 API 字段完全同名，不引入别名
- 学生端“知识星系”页面首屏默认调用 `GET /api/knowledge-tree?subject_code=POLITICS`
- 星系主图使用 ECharts Sunburst，中心显示科目，内环映射 L4 章节，外环映射 L5 原子知识点
- L5 着色规则统一为：未练习灰色、`< 60` 薄暮红、`60-85` 金黄色、`> 85` 成就绿
- 默认只显示中心科目和 L4 章节文字；L5 扇区默认不显示文字，只保留颜色编码
- hover 任一扇区时，右侧详情面板展示完整路径、掌握度、错误频次、关联题量
- click 任一扇区后锁定右侧详情；click L4 章节同时触发图内钻取，放大当前章节
- 专项练习入口统一放在右侧详情面板，不再直接由图表扇区跳转
- `GET /api/knowledge-tree` 的节点数据补充 `wrongCount`，学生端用于右侧详情面板展示错误频次

## 测试与验证

- 前端知识星系数据整理逻辑由 `frontend/src/utils/studentAnalysisGalaxy.test.js` 覆盖
- 至少验证 5 类场景：掌握度阈值分段、L4/L5 层级映射、`wrongCount` 聚合、旭日图数据结构、章节下钻后的详情联动
- 本次实现已通过 `npx vitest run src/utils/studentAnalysisGalaxy.test.js`
- 本次实现已通过 `npm exec vite -- build`
- 若整站构建失败，需先排除与本页无关的全局缺失依赖或缺失组件问题，再复核学生端 `Analysis.vue`
