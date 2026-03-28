# API Schema Drift Checklist

## 目录

1. 输入基线
2. 字段漂移
3. 枚举漂移
4. 端点漂移
5. 输出与闸门

## 1. 输入基线

- 确认 Producer 契约来源：
  - OpenAPI/Swagger
  - 后端 DTO/VO/Entity
- 确认 Consumer 契约来源：
  - 前端 `interface/type/enum`
  - 前端请求调用（`axios/fetch/request`）
- 优先收敛“单一真实来源”，避免双向猜字段。

## 2. 字段漂移

- `HIGH`：Producer 必填字段缺失于 Consumer。
- `MEDIUM`：Producer 可选字段缺失于 Consumer。
- `MEDIUM`：Consumer 多出 Producer 不存在的字段（通常是过时字段）。
- 修复动作：
  - 优先更新 Consumer 类型；
  - 若 Producer 契约错误，先修 OpenAPI/DTO，再更新消费端；
  - 避免长期双字段兼容。

## 3. 枚举漂移

- `HIGH`：Consumer 缺少 Producer 枚举值（状态流风险最高）。
- `MEDIUM`：Consumer 有 Producer 不存在的枚举值（脏状态风险）。
- 修复动作：
  - 后端与前端同提交同步枚举；
  - 补充状态流测试与回归断言。

## 4. 端点漂移

- `HIGH`：Consumer 调用方法/路径无法在 OpenAPI 匹配。
- `LOW`：OpenAPI 声明但 Consumer 未使用（信息性，需结合业务判断）。
- 修复动作：
  - 优先修 URL 与 method；
  - 若新接口尚未入文档，先补 OpenAPI 再联调。

## 5. 输出与闸门

- 执行节奏：
  - `start`：首次编辑前扫描，确认基线可读。
  - `batch`：每批改动后扫描，尽早消化高风险。
  - `final`：交付前扫描，高风险不得放行。
- 报告落盘：
  - `--report-md`
  - `--report-json`

