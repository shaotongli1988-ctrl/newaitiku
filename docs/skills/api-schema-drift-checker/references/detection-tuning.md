# Detection Tuning

## 1. 指定扫描范围

默认会自动发现文件。大仓库建议显式传路径，减少误报：

```bash
python3 scripts/schema_drift_guard.py \
  --phase final \
  --openapi backend/docs/openapi.yaml \
  --producer backend/src \
  --consumer frontend/src
```

## 2. 处理命名不一致

当后端 `UserDTO` 对应前端 `UserItem` 时，使用 `--alias-map`：

```bash
python3 scripts/schema_drift_guard.py \
  --phase final \
  --alias-map references/alias-map.example.json
```

推荐 alias 结构：

- 顶层键值：`"UserDTO": "UserItem"`
- 或显式分区：
  - `producer_to_consumer`
  - `consumer_to_producer`

## 3. 处理路径前缀差异

当前端调用带 `/api` 前缀而 OpenAPI 不带前缀，使用：

```bash
python3 scripts/schema_drift_guard.py \
  --phase final \
  --strip-prefix /api \
  --strip-prefix /v1
```

## 4. 严格度控制

- 默认 `--fail-on auto`
  - `start` 不阻断
  - `batch/final` 对 `high` 阻断
- 需要更严格可改为：
  - `--fail-on medium`

## 5. 常见误报与收敛

- 场景：Consumer 中存在纯 UI 视图模型，非后端直出字段。
  - 处理：拆分“后端契约类型”与“视图类型”，仅扫描契约层目录。
- 场景：动态 URL 模板导致路径不匹配。
  - 处理：统一路径模板，必要时增加 `--strip-prefix`。
- 场景：OpenAPI 为 YAML 且环境无 PyYAML。
  - 处理：安装 `pyyaml` 或临时导出 JSON 契约。

