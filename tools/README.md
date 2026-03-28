# Tools Directory

`tools/` 用来统一存放项目环境依赖、可执行脚本和后续需要补充的本地工具。

当前目录结构：

- `bin/bootstrap-python.sh`：创建虚拟环境、安装依赖，并把 Python 依赖下载到本地缓存目录。
- `bin/run-acceptance.sh`：固定验收命令，统一调用仓库级对齐检查、编译检查和全套自动化测试。
- `bin/check-alignment.sh`：执行仓库级统一对齐校验，默认包含静态合同检查、`py_compile` 和四类测试套件。
- `bin/install-launchd-alignment.sh`：安装当前用户级 LaunchAgent，让对齐 watcher 在 macOS 后台常驻运行。
- `bin/logs-launchd-alignment.sh`：跟随查看 LaunchAgent 的 stdout/stderr 日志。
- `bin/run-dev.sh`：启动本地开发服务。
- `bin/run-ci.sh`：供 CI 直接调用的统一入口，当前会执行 `check-alignment.sh`。
- `bin/run-tests.sh`：执行统一测试入口，支持 `--suite all|auto|unit|integration|regression|e2e`。
- `bin/run-click-replay.sh`：执行三端统一 Python Playwright 真点击回放，支持 `--role student|teacher|super_admin|all`。
- `bin/run-unit-tests.sh`：执行单元测试。
- `bin/run-integration-tests.sh`：执行集成测试。
- `bin/run-regression-tests.sh`：执行回归测试。
- `bin/run-e2e-tests.sh`：执行端到端测试。
- `bin/status-launchd-alignment.sh`：查看 LaunchAgent 当前状态。
- `bin/uninstall-launchd-alignment.sh`：卸载 LaunchAgent。
- `bin/watch-alignment.sh`：持续监听仓库关键目录，检测到新增、修改、删除后自动触发对齐校验和匹配测试套件。
- `python/test_suite_runner.py`：统一编排 `unit / integration / regression / e2e` 四类测试，并支持按变更路径自动选套件。
- `python/click_replay_runner.py`：三端统一真点击回放 runner（步骤级 PASS/FAIL、截图、issues 聚合、统一报告产物）。
- `python/click_replay_server.py`：真点击回放隔离服务启动器（支持 `--db-path` 隔离库）。
- `python/unified_alignment_guard.py`：仓库级统一对齐守卫脚本。
- `python/watch_alignment.py`：仓库级自动监听脚本，默认在改动静置后执行 `batch` 校验和新增文件自动测试分流。
- `python/requirements.txt`：统一指向根目录依赖清单，避免维护两份版本。
- `packages/`：本地依赖缓存目录，便于重复安装或离线分发。

常用命令：

```bash
./tools/bin/bootstrap-python.sh
./tools/bin/run-acceptance.sh
./tools/bin/check-alignment.sh
./tools/bin/install-launchd-alignment.sh
./tools/bin/logs-launchd-alignment.sh
./tools/bin/run-dev.sh
./tools/bin/run-ci.sh
./tools/bin/run-tests.sh
./tools/bin/run-click-replay.sh --role all --base-url http://127.0.0.1:8017
./tools/bin/run-unit-tests.sh
./tools/bin/run-integration-tests.sh
./tools/bin/run-regression-tests.sh
./tools/bin/run-e2e-tests.sh
./tools/bin/status-launchd-alignment.sh
./tools/bin/uninstall-launchd-alignment.sh
./tools/bin/watch-alignment.sh
```

首次启用真点击回放前，请补装 Playwright 浏览器：

```bash
./tools/bin/bootstrap-python.sh
./.venv/bin/python -m playwright install chromium
```
