# 发布包保留 / 排除名单（2026-03-20）

## 一、目的

- 给本次发布提供“一眼能照着打包”的目录名单。
- 区分哪些目录应该进入发布，哪些目录只属于本地开发、测试、评审或临时产物。

## 二、顶层目录建议

### 建议保留进发布

- `app/`
  - 后端应用代码
- `frontend/`
  - 前端源码与构建配置
- `static/`
  - 静态页脚本与资源
- `templates/`
  - 模板文件
- `deploy/`
  - Docker、compose、Nginx 配置
- `data/schema.sql`
  - 数据库初始化 / 索引脚本
- `scripts/`
  - 仅保留实际发布或运维需要的脚本
- `requirements.txt`
  - 后端生产依赖
- `README.md`
  - 可按需保留，供运维或交付说明使用

### 不建议进入发布

- `.codex-runtime/`
- `.shared-deps/`
- `.venv/`
- `.venv-e2e/`
- `.venv313/`
- `.pytest_cache/`
- `tmp/`
- `tools/logs/`
- `tests/`
- `skills/`
- `*.db`
- 本地备份数据库
- 评审截图、临时产物、实验文件

## 三、前端目录建议

### 建议保留

- `frontend/src/`
- `frontend/public/`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.*`
- `frontend/index.html`

### 不建议保留

- `frontend/node_modules/`
- `frontend/dist/`
  - 若发布流程是“现场重新构建”，不需要提交已构建产物
  - 若发布流程是“直接发静态产物”，则应由专门产物目录接管，而不是混在源码包里
- `frontend/.screenshots/`
- `frontend/.vscode/`

## 四、脚本目录建议

### 可随发布保留

- `scripts/unified_delivery_guard.py`
  - 若发布前还需要跑总守卫，可保留
- `scripts/data_contract_cleanup.py`
  - 仅在运维明确需要时保留

### 不建议进入发布

- `scripts/__pycache__/`
- 临时调试脚本、一次性数据修复脚本

## 五、当前基于本仓库的打包建议

### 源码发布包建议包含

- `app/`
- `frontend/`（不含 `node_modules/`、`dist/`、截图与编辑器配置）
- `static/`
- `templates/`
- `deploy/`
- `scripts/` 中必要脚本
- `data/schema.sql`
- `requirements.txt`
- `.dockerignore`
- `.gitignore`

### 当前明确不要带入发布

- `tmp/`
- `.shared-deps/`
- `.codex-runtime/`
- `tools/logs/`
- `tmp_test.db`
- `tmp_test2.db`
- `tmp_test3.db`
- `tmp_test4.db`
- `tmp_verify_super.db`
- `data/question_bank.db`
- `data/question_bank.backup-*.db`

## 六、打包前人工核对

- [ ] 本次发布是否走源码包
- [ ] 若走 Docker 构建，已确认 `.dockerignore` 生效
- [ ] 若走 compose 挂载仓库目录，已确认工作区无临时工件
- [ ] `frontend/node_modules/`、`frontend/dist/` 未混入源码发布包
- [ ] 本地数据库与日志未进入交付目录
- [ ] 仅保留正式交付所需脚本与配置

## 七、一句话执行建议

- 当前最稳妥的做法是：按“源码 + 配置 + schema.sql”交付，不带任何本地数据库、缓存、日志、截图和临时评审产物。

