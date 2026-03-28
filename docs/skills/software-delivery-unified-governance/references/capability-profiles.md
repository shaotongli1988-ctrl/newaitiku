# 能力特性细则（软件交付全流程）

本文件定义软件交付总技能的核心能力面，统一由总守卫调度。

## A. 需求冻结特性

- 需求必须明确、可验收、可量化。
- 不明确需求不进入设计，不明确设计不进入开发。
- 需求变更必须评估影响范围。

## B. 发布前检查特性

- 构建产物、配置、数据库脚本、监控、日志、告警、回滚条件必须在发布前核对。
- 发布前不允许只看代码结果，不看环境与部署条件。

## C. 回滚就绪特性

- 应用、配置、数据库三层必须具备回滚方案。
- 数据库不可逆变更必须单独标注并评估。
- 功能开关与止血手段应优先存在。

## D. 迁移安全特性

- 大表 DDL、索引构建、数据回填、兼容迁移必须提前识别风险。
- 应明确先发库还是先发代码，是否存在灰度兼容窗口。

## E. 配置对齐特性

- dev/test/prod 配置差异必须可见、可审计。
- 域名、证书、回调地址、第三方依赖地址必须纳入检查。

## F. 安全基线特性

- 鉴权、输入校验、注入防护、敏感日志与最小权限必须达标。
- 不因“功能可用”降低安全要求。

## G. P0 子守卫

- `requirements-freeze-guard`
- `release-preflight-guard`
- `rollback-readiness-guard`
- `database-migration-safety-guard`
- `deployment-config-alignment`
- `app-security-baseline-guard`

`final` 阶段如任一 P0 子守卫出现高风险，应阻断上线。

## H. P1 子守卫

- `acceptance-criteria-builder`
- `prd-ui-traceability-guard`
- `ux-state-completeness-checker`
- `release-quality-gate`
- `uat-handoff-guard`
- `observability-readiness-guard`
- `git-flow-enforcer`
- `release-branch-readiness-checker`

`final` 阶段如 P1 子守卫出现高风险，原则上不建议上线，除非明确说明豁免原因。
