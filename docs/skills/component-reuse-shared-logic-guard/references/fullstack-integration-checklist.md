# 接入主技能改动点清单

## 一、主技能元数据与说明

需要修改 [fullstack-unified-development-standards/SKILL.md](/Users/shaotongli/.codex/skills/fullstack-unified-development-standards/SKILL.md)：

1. 在能力特性描述中补一条“实现层收敛特性”。
2. 在“主守卫会自动联动同级子技能”列表中新增：
   - `component-reuse-shared-logic-guard`
3. 在显式传参说明中预留该子守卫参数，例如：
   - `--cr-force`
   - `--cr-report-md <path>`
   - `--cr-report-json <path>`
4. 在可跳过子守卫列表中新增：
   - `--skip-component-reuse-guard`

## 二、能力细则文档

需要修改 [capability-profiles.md](/Users/shaotongli/.codex/skills/fullstack-unified-development-standards/references/capability-profiles.md)：

1. 新增一节“实现层收敛子守卫”。
2. 重点写清：
   - 重复实现抽公共层
   - 页面请求统一走 `request`
   - 分页结构、返回体、时间字段、`extJson` 统一
   - 新增实体优先继承公共基类
3. 明确它不替代 API/权限/状态/错误码/测试/文档守卫。
4. 明确 `final` 阶段出现高风险实现漂移时应先修复再交付。

## 三、治理总则

需要修改 [skill-governance.md](/Users/shaotongli/.codex/skills/fullstack-unified-development-standards/references/skill-governance.md)：

1. 在决策表备注中加入该子守卫自动联动说明。
2. 在冲突收敛顺序中保持它低于主技能统一规则，高于项目局部习惯。
3. 强调其职责边界属于“实现层治理”。

## 四、主守卫脚本编排

需要修改主守卫脚本 `scripts/unified_delivery_guard.py`：

1. 注册新子守卫入口，例如：
   - `scripts/component_reuse_guard.py`
2. 在 `start/batch/final` 三阶段统一调度该子守卫。
3. 新增命令行参数透传：
   - `--cr-force`
   - `--cr-report-md`
   - `--cr-report-json`
   - `--skip-component-reuse-guard`
4. 把 `high` 风险接入现有阻断阈值。
5. 在最终汇总报告中加入“实现层收敛”章节。

## 五、子守卫脚本建议能力

未来新增 `scripts/component_reuse_guard.py` 时，建议覆盖以下扫描面：

1. 前端页内是否直接使用 `axios/fetch`
2. 是否存在明显重复的列表/表单/弹窗/分页实现
3. 是否绕开统一 `request`
4. 是否混用非标准分页结构或返回结构
5. 是否出现 `createdAt/updatedAt`
6. `extJson` 是否以字符串形态在新增代码中传播
7. 后端新增实体是否偏离公共基类字段语义

## 六、接入顺序建议

1. 先合并本子技能文档与治理说明
2. 再给主守卫补调度与跳过参数
3. 最后落地自动扫描脚本

如果短期不写脚本，可先由主技能在命中以下关键词时手动加载本技能文档：

- 组件复用
- 公共组件
- 抽公共
- useTable
- useRequest
- BaseEntity
- request 封装
- 分页统一

## 七、避免冲突的实现约束

- 不重复判定接口契约正确性，只检查是否走统一调用方式
- 不重复判定题库模块边界，只检查实现是否遵循已冻结契约
- 不重复判定权限语义，只检查权限控制是否沉淀到公共层
- 不重复判定状态流合法性，只检查状态展示和按钮策略是否复用公共实现
