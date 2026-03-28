# 三阶段总技能路由规则

## 一、路由目标

- `software-development-readiness-governance`
- `fullstack-unified-development-standards`
- `software-delivery-unified-governance`

## 二、关键词优先级

### 开发前

- 需求
- 验收
- PRD
- 原型
- 方案
- ADR
- 冻结
- 开发前

### 开发中

- 实现
- 联调
- 开发中
- 对齐
- 新增字段
- 新增接口
- 新增页面
- 状态
- 权限
- CSS 变量
- design token
- 样式变量
- 主题变量

### 开发后

- 提测
- 上线
- 门禁
- 终检
- 回滚
- 发布
- 开发后
- UAT

## 三、冲突处理

- 若某一阶段分值显著更高，直接路由。
- 若两个或三个阶段分值接近，输出“无法安全自动路由”。
- 若完全没有命中关键词，默认从开发前开始。

## 四、状态优先

- 如果用户明确给出当前阶段，则状态优先于弱关键词。
- 若状态与强关键词冲突，输出冲突说明并建议确认。
