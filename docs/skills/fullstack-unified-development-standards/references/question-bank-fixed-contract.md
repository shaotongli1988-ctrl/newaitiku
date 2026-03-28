# 题库固定契约

当任务涉及题库模块的表结构、DTO、接口、前端模型、页面绑定、测试或文档时，必须先读取本文件。

## 全局规则

- 只使用当前需求与当前题库新架构，不引用历史项目、历史目录、历史字段设计。
- 只改用户指定模块，不得自行扩展到其他模块。
- 数据库、后端、接口、前端、测试、文档字段必须同名。
- 仅使用下方定义的固定字段集合。
- 不得把“通用基类字段”强行注入未声明的表。
- 不得新增顶层业务列；契约外业务数据统一进入 `extJson`。
- 表关系仅允许 ID 关联，不允许嵌套记录，不允许跨表复制字段。

## 响应包

所有接口统一返回：

```json
{
  "code": "OK",
  "message": "success",
  "data": {}
}
```

- 顶层键固定：`code`、`message`、`data`。
- 分页结构必须放在 `data` 内，不允许额外顶层包装。

## 固定表

### `user`

字段：`id`, `phone`, `password`, `status`, `extJson`, `createTime`, `updateTime`

### `userAuth`

字段：`id`, `userId`, `type`, `openid`, `unionid`, `extJson`, `createTime`, `updateTime`

### `knowledge`

字段：`id`, `parentId`, `name`, `sort`, `status`, `extJson`, `createTime`, `updateTime`

### `question`

字段：`id`, `knowledgeId`, `userId`, `type`, `stem`, `optionsJson`, `answer`, `status`, `extJson`, `createTime`, `updateTime`

### `task`

字段：`id`, `userId`, `type`, `status`, `progress`, `extJson`, `createTime`, `updateTime`

## 固定执行顺序

1. 冻结用户指定模块的精确契约。
2. 更新该模块数据库层。
3. 更新该模块后端与接口层。
4. 更新该模块前端层。
5. 更新该模块测试与文档。
6. 执行题库对齐清单。
