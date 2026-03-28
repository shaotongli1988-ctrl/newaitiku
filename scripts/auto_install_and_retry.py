#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


PYTHON_PACKAGE_MAP = {
    "PIL": "Pillow",
    "bs4": "beautifulsoup4",
    "cv2": "opencv-python",
    "dotenv": "python-dotenv",
    "Crypto": "pycryptodome",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
}


def _run(command: List[str], cwd: Path, env: Dict[str, str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        env=env,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc


def _is_command_available(name: str) -> bool:
    return shutil.which(name) is not None


def _normalize_js_package(raw: str) -> Optional[str]:
    if not raw:
        return None
    if raw.startswith(("node:", ".", "/", "file:")):
        return None
    if raw.startswith("@"):
        parts = raw.split("/")
        if len(parts) >= 2:
            return "/".join(parts[:2])
        return None
    return raw.split("/")[0]


def _normalize_python_package(raw_module: str) -> Optional[str]:
    module = raw_module.split(".")[0].strip()
    if not module:
        return None
    return PYTHON_PACKAGE_MAP.get(module, module)


def _detect_package_manager(cwd: Path) -> Optional[str]:
    if (cwd / "pnpm-lock.yaml").exists() and _is_command_available("pnpm"):
        return "pnpm"
    if (cwd / "yarn.lock").exists() and _is_command_available("yarn"):
        return "yarn"
    if (cwd / "package-lock.json").exists() and _is_command_available("npm"):
        return "npm"
    if (cwd / "package.json").exists() and _is_command_available("npm"):
        return "npm"
    return None


def _shared_paths(cwd: Path, shared_dir: str) -> Dict[str, Path]:
    root = Path(shared_dir)
    if not root.is_absolute():
        root = cwd / root
    root = root.resolve()
    return {
        "root": root,
        "js_workspace": root / "js",
        "js_node_modules": root / "js" / "node_modules",
        "js_bin": root / "js" / "node_modules" / ".bin",
        "python_site": root / "python" / "site-packages",
        "go_modcache": root / "go" / "pkg" / "mod",
        "go_build_cache": root / "go" / "build-cache",
    }


def _prepend_env(env: Dict[str, str], key: str, value: Path) -> None:
    rendered = str(value)
    current = env.get(key, "")
    env[key] = f"{rendered}{os.pathsep}{current}" if current else rendered


def _build_runtime_env(paths: Dict[str, Path]) -> Dict[str, str]:
    env = os.environ.copy()
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["js_workspace"].mkdir(parents=True, exist_ok=True)
    paths["python_site"].mkdir(parents=True, exist_ok=True)
    paths["go_modcache"].mkdir(parents=True, exist_ok=True)
    paths["go_build_cache"].mkdir(parents=True, exist_ok=True)

    _prepend_env(env, "PATH", paths["js_bin"])
    _prepend_env(env, "NODE_PATH", paths["js_node_modules"])
    _prepend_env(env, "PYTHONPATH", paths["python_site"])
    env["GOMODCACHE"] = str(paths["go_modcache"])
    env["GOCACHE"] = str(paths["go_build_cache"])
    return env


def _ensure_js_workspace(js_workspace: Path) -> None:
    js_workspace.mkdir(parents=True, exist_ok=True)
    package_json = js_workspace / "package.json"
    if not package_json.exists():
        package_json.write_text(
            json.dumps({"name": "shared-project-deps", "private": True}, indent=2) + "\n",
            encoding="utf-8",
        )


def _extract_dependency(log_text: str, cwd: Path) -> Tuple[Optional[str], Optional[str]]:
    js_patterns = [
        r"Cannot find module ['\"]([^'\"]+)['\"]",
        r"Cannot find package ['\"]([^'\"]+)['\"]",
        r"Error \[ERR_MODULE_NOT_FOUND\]: Cannot find package ['\"]([^'\"]+)['\"]",
        r"Module not found: Error: Can't resolve ['\"]([^'\"]+)['\"]",
        r"Module not found: Can't resolve ['\"]([^'\"]+)['\"]",
    ]
    for pattern in js_patterns:
        match = re.search(pattern, log_text)
        if match:
            dep = _normalize_js_package(match.group(1).strip())
            if dep:
                return "js", dep

    py_patterns = [
        r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]",
        r"No module named ['\"]([^'\"]+)['\"]",
    ]
    for pattern in py_patterns:
        match = re.search(pattern, log_text)
        if match:
            dep = _normalize_python_package(match.group(1))
            if dep:
                return "python", dep

    go_match = re.search(r"no required module provides package ([^\s:]+)", log_text)
    if go_match:
        dep = go_match.group(1).strip()
        if dep:
            return "go", dep

    cmd_missing = re.search(r"(?:zsh|bash|sh)(?::\d+)?: command not found: ([^\s:]+)", log_text)
    if cmd_missing and (cwd / "package.json").exists():
        dep = _normalize_js_package(cmd_missing.group(1).strip())
        if dep:
            return "js", dep

    return None, None


def _build_install_command(
    ecosystem: str, dep: str, cwd: Path, paths: Dict[str, Path]
) -> Optional[List[str]]:
    if ecosystem == "js":
        _ensure_js_workspace(paths["js_workspace"])
        pm = _detect_package_manager(cwd)
        if pm == "pnpm":
            return ["pnpm", "--dir", str(paths["js_workspace"]), "add", dep]
        if pm == "yarn":
            return ["yarn", "--cwd", str(paths["js_workspace"]), "add", dep]
        if pm == "npm":
            return ["npm", "install", "--prefix", str(paths["js_workspace"]), dep]
        return None

    if ecosystem == "python":
        return [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            str(paths["python_site"]),
            dep,
        ]

    if ecosystem == "go":
        if _is_command_available("go"):
            return ["go", "get", dep]
        return None

    return None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        add_help=False,
        description=(
            "使用项目级共享依赖目录运行命令；若识别到缺失依赖则自动安装 1 个并重试 1 次。"
        )
    )
    parser.add_argument("-h", "--help", action="help", help="显示帮助并退出。")
    parser.add_argument("--cwd", default=os.getcwd(), help="工作目录（默认当前目录）。")
    parser.add_argument(
        "--shared-dir",
        default=".shared-deps",
        help="共享依赖目录（默认是 cwd 下的 .shared-deps）。",
    )
    parser.add_argument("--dry-run", action="store_true", help="仅打印识别结果和安装命令，不真正安装。")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="要执行的命令，放在 '--' 之后。")
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("缺少命令。示例：auto_install_and_retry.py -- npm run dev")
    return args


def main() -> int:
    args = _parse_args()
    cwd = Path(args.cwd).resolve()
    paths = _shared_paths(cwd, args.shared_dir)
    runtime_env = _build_runtime_env(paths)

    print(f"[auto-install] 共享依赖目录: {paths['root']}")
    print(f"[auto-install] 执行命令: {' '.join(args.command)}")
    first = _run(args.command, cwd, runtime_env)
    if first.returncode == 0:
        print("[auto-install] 命令执行成功，无需安装依赖。")
        return 0

    merged_output = f"{first.stdout}\n{first.stderr}"
    ecosystem, dep = _extract_dependency(merged_output, cwd)
    if not ecosystem or not dep:
        print("[auto-install] 未能从输出中推断出缺失依赖。", file=sys.stderr)
        return first.returncode

    install_cmd = _build_install_command(ecosystem, dep, cwd, paths)
    if not install_cmd:
        print(
            f"[auto-install] 已推断缺失依赖 '{dep}'（{ecosystem}），但当前环境没有可用安装命令。",
            file=sys.stderr,
        )
        return first.returncode

    print(f"[auto-install] 检测到缺失依赖: {dep} ({ecosystem})")
    print(f"[auto-install] 安装命令: {' '.join(install_cmd)}")
    if args.dry_run:
        print("[auto-install] 已开启 dry-run，安装前停止。")
        return 0

    install_proc = _run(install_cmd, cwd, runtime_env)
    if install_proc.returncode != 0:
        print("[auto-install] 依赖安装失败。", file=sys.stderr)
        return install_proc.returncode

    print("[auto-install] 依赖安装成功，开始重试原命令 1 次。")
    second = _run(args.command, cwd, runtime_env)
    if second.returncode == 0:
        print("[auto-install] 重试成功。")
    else:
        print("[auto-install] 重试失败，请继续手动排查。", file=sys.stderr)
    return second.returncode


if __name__ == "__main__":
    sys.exit(main())
