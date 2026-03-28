# 发布包执行说明（2026-03-20）

## 一、目标

- 面向当前 `deploy/` 下的 Docker / compose 发布方式，明确真正需要进入构建上下文和运行环境的内容。

## 二、当前发布结构

### 前端

- Dockerfile：`deploy/Dockerfile.frontend`
- 构建方式：
  1. 复制 `frontend/package*.json`
  2. 安装前端依赖
  3. 复制 `frontend/`
  4. 构建 `dist`
  5. 用 `nginx` 承载静态产物

### 后端

- compose 文件：`deploy/docker-compose.prod.yml`
- 当前方式：`backend` 服务通过 `../:/srv/app` 挂载整个仓库目录运行

## 三、当前发布方式的注意点

1. 前端镜像构建使用仓库根目录作为上下文。
2. 如果没有 `.dockerignore`，本地 `tmp/`、`.shared-deps/`、日志、测试数据库也会进入构建上下文。
3. 当前后端生产 compose 仍挂载整个仓库目录，因此工作区里的非发布工件如果不清理，运行环境也可能看得到这些文件。

## 四、本次已补充的防护

- 已新增 [`.dockerignore`](/Users/shaotongli/Documents/newaitiku/.dockerignore)
- 已默认排除以下内容进入 Docker 构建上下文：
  - `.codex-runtime/`
  - `.shared-deps/`
  - `tmp/`
  - `tools/logs/`
  - `*.db`
  - `__pycache__/`
  - `.pytest_cache/`
  - `node_modules/`

## 五、建议保留的交付目录

- `app/`
- `frontend/`
- `static/`
- `templates/`
- `deploy/`
- `scripts/` 中确需上线执行的脚本
- `data/schema.sql`
- `requirements.txt`
- `requirements-dev.txt` 仅在测试或运维明确需要时保留

## 六、建议排除的非发布内容

- `tmp/`
- `.shared-deps/`
- `.codex-runtime/`
- `tools/logs/`
- 本地测试数据库与备份数据库
- 调试截图、评审产物、临时蓝图文件

## 七、发布前执行建议

1. 先按 [发布包清理检查](/Users/shaotongli/Documents/newaitiku/docs/release/release-package-cleanup-2026-03-20.md) 逐项确认。
2. 若继续使用当前 compose 方式，务必确认工作区中无敏感或临时工件。
3. 若条件允许，后续建议将后端也改为镜像构建，而不是直接挂载整个仓库目录。

## 八、当前结论

- 前端构建上下文已通过 `.dockerignore` 做了第一层隔离。
- 后端运行环境仍依赖工作区整洁度，因此本次发布前仍需要人工完成工作区清理确认。
