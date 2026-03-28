#!/usr/bin/env python3
"""
Lightweight guard for fullstack-unified-development-standards.

This script provides an automatic checklist entry point for three phases:
- start: before the first edit
- batch: after each meaningful code batch
- final: before delivery

It uses git-aware file heuristics plus optional task text to surface likely
full-stack drift. It is intentionally conservative: warnings indicate areas to
review, not proof of a bug.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SHARED_RUNTIME_SCRIPTS = SCRIPT_PATH.parents[2] / "shared-guard-runtime" / "scripts"
if str(SHARED_RUNTIME_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SHARED_RUNTIME_SCRIPTS))

from change_set import collect_changed_files as shared_collect_changed_files, prepare_changed_files_for_subguards as shared_prepare_changed_files_for_subguards  # type: ignore


TRIGGER_PHRASES = (
    "一键开发",
    "全端统一规范",
    "统一入口",
    "开发中总技能",
    "开发中别跑偏",
    "实现阶段总入口",
    "边开发边校验",
    "总调度",
    "统一字段",
    "统一接口",
    "统一页面",
    "统一状态",
    "统一权限",
    "统一校验",
    "统一错误",
    "自动生成文档与测试",
    "九端对齐检查",
    "十端对齐检查",
    "自动对齐检查",
    "自动触发检查",
    "全端检查",
)

QUESTION_BANK_MODULES = ("user", "userAuth", "knowledge", "question", "task")

DOMAIN_LABELS = (
    ("field", "Field standards"),
    ("api", "API standards"),
    ("page", "Page standards"),
    ("status", "Status standards"),
    ("permission", "Permission standards"),
    ("validation", "Validation standards"),
    ("error", "Error standards"),
    ("extension", "Extension standards"),
    ("documentation", "Documentation standards"),
    ("tests", "Test standards"),
)

PATH_RULES = {
    "field": (
        r"entity|model|schema|migration|prisma|dto|vo|types?|interface|form|table",
    ),
    "api": (
        r"controller|route|router|api|handler|endpoint|swagger|openapi|dto|request|response|client",
    ),
    "page": (
        r"page|pages|view|views|screen|component|components|form|table|modal|dialog|drawer",
    ),
    "status": (
        r"status|state|transition|workflow|enum",
    ),
    "permission": (
        r"permission|permissions|auth|role|guard|acl|rbac|access",
    ),
    "validation": (
        r"valid|validator|validation|schema|rule|rules|zod|yup|joi|class-validator",
    ),
    "error": (
        r"error|errors|exception|exceptions|interceptor|result|response",
    ),
    "extension": (
        r"extjson|extension|extensions|meta|extra|custom",
    ),
    "documentation": (
        r"(^|/)(docs?|doc)(/|$)|\.md$|openapi|swagger",
    ),
    "tests": (
        r"(^|/)(__tests__|tests?)(/|$)|\.(spec|test)\.",
    ),
}

SURFACE_RULES = {
    "persistence": (r"migration|migrations|prisma|schema|entity|model|repository|mapper|dao|sql",),
    "backend": (r"service|controller|route|router|handler|api|dto|vo|biz|domain|server",),
    "frontend": (
        r"frontend/src/(api|services|request|types?|models?|composables|utils)(/|$)",
        r"src/.*/(pages|views|components|api|services|request|types?|models?)(/|$)",
        r"page|pages|view|views|component|components|form|table|modal|dialog",
    ),
    "docs": (r"(^|/)(docs?|doc)(/|$)|\.md$",),
    "tests": (r"(^|/)(__tests__|tests?)(/|$)|\.(spec|test)\.",),
}

CONTENT_RULES = {
    "status": (r"\bstatus\b|\bstate\b|\bworkflow\b|\btransition\b",),
    "permission": (r"\bpermission\b|\bauth\b|\brole\b|\bguard\b|\bacl\b|\brbac\b",),
    "validation": (r"\bvalidate\b|\bvalidator\b|\bvalidation\b|\brules?\b|required|length|min|max",),
    "error": (r"\berror\b|\bexception\b|\bthrow\b|\bcatch\b",),
    "extension": (r"\bextJson\b|\bextjson\b|\bextension\b|\bextra\b|\bmeta\b",),
}

CACHE_PATH_RULES = (
    r"cache",
    r"redis",
    r"memcache",
    r"kv",
)

CACHE_CONTENT_RULES = (
    r"\bredis\b",
    r"\bcache\b",
    r"\bttl\b",
    r"\bexpire\b",
    r"\bsetex\b",
    r"\binvalidate\b",
    r"\bevict\b",
    r"\bpreheat\b",
    r"\bwarm\b",
)

CACHE_TASK_SIGNALS = (
    "cache",
    "redis",
    "ttl",
    "热点",
    "热 key",
    "feed",
    "leaderboard",
    "排行榜",
    "缓存",
    "切流",
    "回填",
    "backfill",
    "cutover",
)

AUTO_TEST_GENERATOR_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx"}
AUTO_TEST_GENERATOR_TASK_SIGNALS = ("补测试", "测试骨架", "回归测试", "generate test", "test skeleton")
TEST_HINTS = ("test", "spec", "__tests__")
AUTO_INSTALL_TASK_SIGNALS = (
    "cannot find module",
    "module not found",
    "modulenotfounderror",
    "no required module provides package",
    "command not found",
    "缺失依赖",
    "缺依赖",
)
CI_TRIAGE_TASK_SIGNALS = (
    "ci",
    "pipeline",
    "workflow",
    "流水线",
    "红灯",
    "构建失败",
    "测试失败",
    "build failed",
)
CI_TRIAGE_FILE_HINTS = (
    ".github/workflows",
    ".gitlab-ci",
    ".circleci",
    "jenkins",
    "buildkite",
    "azure-pipelines",
    "bitrise",
    "workflow",
)
CUTOVER_TASK_SIGNALS = (
    "回填",
    "切流",
    "backfill",
    "cutover",
    "迁移",
)
CUTOVER_FILE_HINTS = (
    "migration",
    "schema",
    "sql",
    "prisma",
    "backfill",
    "cutover",
)
RELEASE_EVIDENCE_TASK_SIGNALS = (
    "发布证据",
    "交付材料",
    "release evidence",
    "上线包",
    "handoff",
    "交接材料",
)
GENERIC_RELEASE_TASK_SIGNALS = (
    "发布",
    "上线",
    "交付",
    "交接",
    "release",
    "go live",
    "go-live",
    "handoff",
)
RELEASE_EVIDENCE_FILE_HINTS = (
    "release-gate",
    "release-dashboard",
    "gate-summary",
    "rollback",
    "uat",
    "replay",
    "quality-gate",
)
RELEASE_EVIDENCE_RECOMMENDATION_FILE_HINTS = RELEASE_EVIDENCE_FILE_HINTS + (
    "deploy",
    "preflight",
    "release-note",
    "release-notes",
    "delivery",
    "handoff",
)

EXECUTION_SKILL_HINTS = {
    "ci-failure-triager": "推荐显式调用 `ci-failure-triager`，用于先归因 CI / 构建 / 测试失败主因，再决定修复顺序。",
    "test-code-generator": "推荐显式调用 `test-code-generator`，为当前改动快速生成测试骨架并补齐正常/异常/边界用例位。",
    "cutover-backfill-executor": "推荐显式调用 `cutover-backfill-executor`，为切流、回填、审计和回滚生成执行资产。",
    "auto-install-missing-deps": "推荐显式调用 `auto-install-missing-deps`，先自动补齐缺失依赖并重试失败命令，再继续排查实现问题。",
    "release-evidence-packager": "推荐显式调用 `release-evidence-packager`，把 gate、rollback、UAT、replay 与关键日志收敛成统一发布证据包。",
}

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
NOISE_DIR_PARTS = {
    ".codex-runtime",
    ".pdfdeps",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".screenshots",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "tmp",
}
NOISE_FILENAMES = {".ds_store", "thumbs.db"}
NOISE_SUFFIXES = {
    ".log",
    ".pid",
    ".tmp",
    ".cache",
    ".bak",
    ".swp",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".whl",
    ".dylib",
    ".so",
    ".pyc",
    ".pdf",
    ".ttf",
    ".otf",
    ".pfb",
    ".afm",
    ".sfd",
}
NOISE_PATH_PATTERNS = ("/tools/packages/", "/tmp/", "/.codex-runtime/", "/.pdfdeps/", "/docs/screenshots/")
HIGH_SIGNAL_PATH_PATTERNS = (
    "/frontend/src/",
    "/app/",
    "/tests/",
    "/docs/release/",
    "/docs/contracts/",
    "/scripts/",
    "/readme",
    "/package.json",
    "/package-lock.json",
    "/pnpm-lock.yaml",
    "/yarn.lock",
    "/requirements",
    "/pytest.ini",
    "/vite.config",
    "/vitest.config",
)
LOW_SIGNAL_PATH_PATTERNS = (
    "/data/",
    "/docs/screenshots/",
    "/docs/student-step-",
    "/docs/teacher-step-",
    "/2026",
)
MAX_SUBGUARD_CHANGED_FILES = 200


@dataclass
class GuardResult:
    phase: str
    cwd: Path
    git_root: Path | None
    matched_triggers: list[str]
    changed_files: list[Path]
    ignored_noise_files: int
    domains: dict[str, bool]
    surfaces: dict[str, bool]
    fail_threshold: str
    warning_items: list["GuardWarning"]
    warnings: list[str]
    recommended_skills: list[str]
    api_schema_guard: "SubGuardResult"
    question_bank_guard: "SubGuardResult"
    rbac_guard: "SubGuardResult"
    state_machine_guard: "SubGuardResult"
    error_code_guard: "SubGuardResult"
    test_matrix_guard: "SubGuardResult"
    delivery_doc_sync_guard: "SubGuardResult"
    component_reuse_guard: "SubGuardResult"
    cache_consistency_guard: "SubGuardResult"
    tooling_pilots: list["ToolingPilotResult"] = field(default_factory=list)


@dataclass
class SubGuardResult:
    enabled: bool
    name: str
    script_path: Path | None
    command: list[str]
    returncode: int | None
    output: str
    warnings: list[str]


@dataclass
class GuardWarning:
    code: str
    severity: str
    message: str
    source: str = "core"


@dataclass
class ToolingPilotResult:
    enabled: bool
    name: str
    reason: str
    target: Path | None
    output_path: Path | None
    summary_path: Path | None
    command: list[str]
    returncode: int | None
    output: str
    warnings: list[str]


def run_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def find_git_root(cwd: Path) -> Path | None:
    result = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def parse_git_status(root: Path) -> list[Path]:
    result = run_cmd(["git", "status", "--porcelain", "--untracked-files=all"], root)
    if result.returncode != 0:
        return []
    changed: list[Path] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line:
            continue
        line = raw_line[3:] if len(raw_line) > 3 else raw_line
        if " -> " in line:
            line = line.split(" -> ", 1)[1]
        changed.append(root / line)
    return changed


def is_noise_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if any(part in parts for part in NOISE_DIR_PARTS):
        return True
    if path.name.lower() in NOISE_FILENAMES:
        return True
    normalized = path.as_posix().lower()
    if any(pattern in normalized for pattern in NOISE_PATH_PATTERNS):
        return True
    if normalized.endswith(tuple(NOISE_SUFFIXES)):
        return True
    if "/screenshots/" in normalized and normalized.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return True
    return False


def filter_changed_files(changed_files: list[Path]) -> tuple[list[Path], list[Path]]:
    kept: list[Path] = []
    ignored: list[Path] = []
    seen: set[Path] = set()
    for path in changed_files:
        normalized = path.resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        if is_noise_path(normalized):
            ignored.append(normalized)
            continue
        kept.append(normalized)
    return kept, ignored


def changed_files_for_subguards(changed_files: list[Path], cwd: Path) -> list[Path]:
    prepared_files, _warnings = shared_prepare_changed_files_for_subguards(
        changed_files,
        cwd,
        max_files=MAX_SUBGUARD_CHANGED_FILES,
        placeholder_name=".unified_guard_empty_change_set",
    )
    return prepared_files


def changed_file_priority(path: Path) -> tuple[int, float, int, str]:
    normalized = path.as_posix().lower()
    score = 100

    if any(pattern in normalized for pattern in HIGH_SIGNAL_PATH_PATTERNS):
        score -= 70
    if any(pattern in normalized for pattern in LOW_SIGNAL_PATH_PATTERNS):
        score += 25
    if "/src/" in normalized or normalized.endswith((".py", ".js", ".ts", ".vue")):
        score -= 20
    if "/tests/" in normalized or ".test." in normalized or ".spec." in normalized:
        score -= 15
    if normalized.endswith(".md"):
        score -= 10

    try:
        modified_at = -path.stat().st_mtime
    except OSError:
        modified_at = 0.0

    return (score, modified_at, len(normalized), normalized)


def read_text(path: Path, limit: int = 64000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def is_documentation_path(path: Path) -> bool:
    return matches_any(path.as_posix().lower(), PATH_RULES["documentation"])


def is_test_support_path(path: Path) -> bool:
    normalized = path.as_posix().lower()
    return matches_any(normalized, PATH_RULES["tests"])


def is_support_only_path(path: Path) -> bool:
    return is_skill_support_path(path) or is_documentation_path(path) or is_test_support_path(path)


def is_skill_support_path(path: Path) -> bool:
    normalized = path.as_posix().lower()
    parts = {part.lower() for part in path.parts}
    if "skills" not in parts:
        return False
    if path.name == "SKILL.md":
        return True
    if "/references/" in normalized:
        return True
    if normalized.endswith("/agents/openai.yaml"):
        return True
    if "/scripts/" in normalized:
        return True
    return False


def compute_threshold(phase: str, fail_on: str) -> str:
    if fail_on != "auto":
        return fail_on
    if phase == "start":
        return "none"
    return "high"


def warning_meets_threshold(severity: str, threshold: str) -> bool:
    if threshold == "none":
        return False
    return SEVERITY_RANK[severity] <= SEVERITY_RANK[threshold]


def dedupe_warning_items(items: list["GuardWarning"]) -> list["GuardWarning"]:
    seen: set[tuple[str, str, str]] = set()
    result: list[GuardWarning] = []
    for item in items:
        key = (item.source, item.code, item.message)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def warning_text(item: "GuardWarning") -> str:
    return f"[{item.severity.upper()}][{item.source}] {item.message}"


def detect_domains(changed_files: list[Path]) -> dict[str, bool]:
    domains = {key: False for key, _ in DOMAIN_LABELS}
    for path in changed_files:
        if is_support_only_path(path):
            if is_skill_support_path(path) or is_documentation_path(path):
                domains["documentation"] = True
            if is_test_support_path(path):
                domains["tests"] = True
            continue
        normalized = path.as_posix().lower()
        for key in domains:
            if matches_any(normalized, PATH_RULES[key]):
                domains[key] = True
        content = read_text(path).lower()
        for key in CONTENT_RULES:
            if matches_any(content, CONTENT_RULES[key]):
                domains[key] = True
    return domains


def detect_surfaces(changed_files: list[Path]) -> dict[str, bool]:
    surfaces = {key: False for key in SURFACE_RULES}
    for path in changed_files:
        if is_skill_support_path(path):
            surfaces["docs"] = True
            continue
        normalized = path.as_posix().lower()
        for key, patterns in SURFACE_RULES.items():
            if matches_any(normalized, patterns):
                surfaces[key] = True
    return surfaces


def detect_triggers(task: str) -> list[str]:
    if not task:
        return []
    lowered = task.lower()
    matches = [phrase for phrase in TRIGGER_PHRASES if phrase.lower() in lowered]
    if any(module.lower() in lowered for module in QUESTION_BANK_MODULES):
        matches.append("question-bank-module")
    return matches


def detect_cache_context(changed_files: list[Path], task: str) -> bool:
    lowered_task = task.lower()
    if any(signal.lower() in lowered_task for signal in CACHE_TASK_SIGNALS):
        return True
    for path in changed_files:
        normalized = path.as_posix().lower()
        if is_skill_support_path(path) or is_documentation_path(path):
            continue
        if matches_any(normalized, CACHE_PATH_RULES):
            return True
        content = read_text(path).lower()
        if matches_any(content, CACHE_CONTENT_RULES):
            return True
    return False


def recommend_execution_skills(changed_files: list[Path], task: str, surfaces: dict[str, bool]) -> list[str]:
    recommendations: list[str] = []
    lowered_task = task.lower()
    has_impl = surfaces["backend"] or surfaces["frontend"] or surfaces["persistence"]

    if (
        has_impl and not surfaces["tests"]
    ) or any(token in lowered_task for token in ("补测试", "测试骨架", "回归测试", "generate test", "test skeleton")):
        recommendations.append(EXECUTION_SKILL_HINTS["test-code-generator"])

    if detect_cutover_context(changed_files, task):
        recommendations.append(EXECUTION_SKILL_HINTS["cutover-backfill-executor"])

    if detect_ci_triage_recommendation_context(changed_files, task):
        recommendations.append(EXECUTION_SKILL_HINTS["ci-failure-triager"])

    if any(
        token in lowered_task
        for token in (
            "cannot find module",
            "module not found",
            "modulenotfounderror",
            "no required module provides package",
            "command not found",
            "缺失依赖",
            "缺依赖",
        )
    ):
        recommendations.append(EXECUTION_SKILL_HINTS["auto-install-missing-deps"])

    if detect_release_evidence_recommendation_context(changed_files, task):
        recommendations.append(EXECUTION_SKILL_HINTS["release-evidence-packager"])

    return dedupe(recommendations)


def should_run_test_code_generator_pilot(
    phase: str,
    changed_files: list[Path],
    task: str,
    surfaces: dict[str, bool],
) -> bool:
    if phase == "start":
        return False
    lowered_task = task.lower()
    has_impl = surfaces["backend"] or surfaces["frontend"] or surfaces["persistence"]
    has_candidate = any(
        path.suffix.lower() in AUTO_TEST_GENERATOR_SUFFIXES and not any(hint in path.name.lower() for hint in TEST_HINTS)
        for path in changed_files
    )
    task_requests_tests = any(token in lowered_task for token in AUTO_TEST_GENERATOR_TASK_SIGNALS)
    return has_candidate and has_impl and (not surfaces["tests"] or task_requests_tests)


def pick_test_generator_target(changed_files: list[Path]) -> Path | None:
    for path in changed_files:
        if path.suffix.lower() in AUTO_TEST_GENERATOR_SUFFIXES and not any(hint in path.name.lower() for hint in TEST_HINTS):
            return path
    return None


def resolve_test_code_generator_script() -> Path | None:
    candidate = SCRIPT_PATH.parents[2] / "test-code-generator" / "scripts" / "test_code_generator.py"
    return candidate if candidate.exists() else None


def infer_pilot_test_output_path(cwd: Path, target: Path) -> tuple[Path, Path]:
    try:
        relative_parent = target.resolve().relative_to(cwd.resolve()).parent
    except ValueError:
        relative_parent = Path("external")
    runtime_root = cwd / ".codex-runtime" / "generated-tests" / relative_parent
    if target.suffix.lower() == ".py":
        output = runtime_root / f"test_{target.stem}.py"
    else:
        output = runtime_root / f"{target.stem}.test{target.suffix}"
    summary = runtime_root / f"{target.stem}.pilot-summary.md"
    return output, summary


def run_test_code_generator_pilot(
    args: argparse.Namespace,
    cwd: Path,
    changed_files: list[Path],
    surfaces: dict[str, bool],
) -> ToolingPilotResult:
    if not should_run_test_code_generator_pilot(args.phase, changed_files, args.task, surfaces):
        return ToolingPilotResult(
            enabled=False,
            name="test-code-generator",
            reason="No missing-test signal detected.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    script_path = resolve_test_code_generator_script()
    if not script_path:
        return ToolingPilotResult(
            enabled=False,
            name="test-code-generator",
            reason="Pilot skipped because test-code-generator script was not found.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    target = pick_test_generator_target(changed_files)
    if not target:
        return ToolingPilotResult(
            enabled=False,
            name="test-code-generator",
            reason="Pilot skipped because no code target was eligible for skeleton generation.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    output_path, summary_path = infer_pilot_test_output_path(cwd, target)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--task",
        args.task,
        "--target",
        str(target),
        "--mode",
        "unit",
        "--output",
        str(output_path),
        "--output-md",
        str(summary_path),
    ]
    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)
    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"test-code-generator pilot returned non-zero ({result.returncode}). Review generated skeleton flow before relying on the pilot output."
        )
    return ToolingPilotResult(
        enabled=True,
        name="test-code-generator",
        reason="Implementation changes lacked test evidence, so a runtime-scoped test skeleton was generated automatically.",
        target=target,
        output_path=output_path,
        summary_path=summary_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def should_run_auto_install_missing_deps_pilot(phase: str, task: str, dep_pilot_command: str) -> bool:
    if phase == "start":
        return False
    lowered_task = task.lower()
    has_signal = any(token in lowered_task for token in AUTO_INSTALL_TASK_SIGNALS)
    return has_signal and bool(dep_pilot_command.strip())


def detect_cutover_context(changed_files: list[Path], task: str) -> bool:
    lowered_task = task.lower()
    if any(token in lowered_task for token in CUTOVER_TASK_SIGNALS):
        return True
    normalized = [path.as_posix().lower() for path in changed_files if not is_support_only_path(path)]
    return any(token in item for item in normalized for token in CUTOVER_FILE_HINTS)


def detect_ci_triage_recommendation_context(changed_files: list[Path], task: str) -> bool:
    lowered_task = task.lower()
    if any(token in lowered_task for token in CI_TRIAGE_TASK_SIGNALS):
        return True
    normalized = [path.as_posix().lower() for path in changed_files if not is_support_only_path(path)]
    return any(token in item for item in normalized for token in CI_TRIAGE_FILE_HINTS)


def detect_release_evidence_context(changed_files: list[Path], task: str) -> bool:
    lowered_task = task.lower()
    if any(token in lowered_task for token in RELEASE_EVIDENCE_TASK_SIGNALS):
        return True
    normalized = [path.as_posix().lower() for path in changed_files if not is_skill_support_path(path)]
    return any(token in item for item in normalized for token in RELEASE_EVIDENCE_FILE_HINTS)


def detect_release_evidence_recommendation_context(changed_files: list[Path], task: str) -> bool:
    if detect_release_evidence_context(changed_files, task):
        return True
    lowered_task = task.lower()
    if not any(token in lowered_task for token in GENERIC_RELEASE_TASK_SIGNALS):
        return False
    normalized = [path.as_posix().lower() for path in changed_files if not is_skill_support_path(path)]
    return any(token in item for item in normalized for token in RELEASE_EVIDENCE_RECOMMENDATION_FILE_HINTS)


def resolve_auto_install_missing_deps_script() -> Path | None:
    candidate = SCRIPT_PATH.parents[2] / "auto-install-missing-deps" / "scripts" / "auto_install_and_retry.py"
    return candidate if candidate.exists() else None


def run_auto_install_missing_deps_pilot(args: argparse.Namespace, cwd: Path) -> ToolingPilotResult:
    lowered_task = args.task.lower()
    if not any(token in lowered_task for token in AUTO_INSTALL_TASK_SIGNALS):
        return ToolingPilotResult(
            enabled=False,
            name="auto-install-missing-deps",
            reason="No dependency-failure signal detected.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    if not getattr(args, "dep_pilot_command", "").strip():
        return ToolingPilotResult(
            enabled=False,
            name="auto-install-missing-deps",
            reason="Dependency-failure signal detected, but no --dep-pilot-command was provided for safe replay.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    if args.phase == "start":
        return ToolingPilotResult(
            enabled=False,
            name="auto-install-missing-deps",
            reason="Dependency install pilot only runs in batch/final, not in start.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    script_path = resolve_auto_install_missing_deps_script()
    if not script_path:
        return ToolingPilotResult(
            enabled=False,
            name="auto-install-missing-deps",
            reason="Pilot skipped because auto-install-missing-deps script was not found.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    try:
        replay_command = shlex.split(args.dep_pilot_command)
    except ValueError as exc:
        return ToolingPilotResult(
            enabled=False,
            name="auto-install-missing-deps",
            reason=f"Invalid --dep-pilot-command: {exc}",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )
    if not replay_command:
        return ToolingPilotResult(
            enabled=False,
            name="auto-install-missing-deps",
            reason="The provided --dep-pilot-command was empty after parsing.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    shared_dir = cwd / ".codex-runtime" / "shared-deps-pilot"
    cmd = [
        sys.executable,
        str(script_path),
        "--cwd",
        str(cwd),
        "--shared-dir",
        str(shared_dir),
        "--dry-run",
        "--",
        *replay_command,
    ]
    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)
    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"auto-install-missing-deps pilot returned non-zero ({result.returncode}). Review dependency detection before enabling real install retries."
        )
    return ToolingPilotResult(
        enabled=True,
        name="auto-install-missing-deps",
        reason="Dependency-failure signal and replay command were both provided, so a dry-run dependency recovery pilot was executed.",
        target=None,
        output_path=shared_dir,
        summary_path=None,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def should_run_ci_failure_triager_pilot(phase: str, task: str, ci_pilot_log: str) -> bool:
    if phase == "start":
        return False
    lowered_task = task.lower()
    has_signal = any(token in lowered_task for token in CI_TRIAGE_TASK_SIGNALS)
    return has_signal and bool(ci_pilot_log.strip())


def resolve_ci_failure_triager_script() -> Path | None:
    candidate = SCRIPT_PATH.parents[2] / "ci-failure-triager" / "scripts" / "ci_failure_triager.py"
    return candidate if candidate.exists() else None


def should_run_cutover_backfill_executor_pilot(
    phase: str,
    changed_files: list[Path],
    task: str,
    cutover_pilot_spec: str,
) -> bool:
    if phase == "start":
        return False
    return detect_cutover_context(changed_files, task) and bool(cutover_pilot_spec.strip())


def resolve_cutover_backfill_executor_script() -> Path | None:
    candidate = SCRIPT_PATH.parents[2] / "cutover-backfill-executor" / "scripts" / "cutover_backfill_executor.py"
    return candidate if candidate.exists() else None


def should_run_release_evidence_packager_pilot(
    phase: str,
    changed_files: list[Path],
    task: str,
    release_evidence_sources: list[str],
) -> bool:
    if phase == "start":
        return False
    return detect_release_evidence_context(changed_files, task) and any(source.strip() for source in release_evidence_sources)


def resolve_release_evidence_packager_script() -> Path | None:
    candidate = SCRIPT_PATH.parents[2] / "release-evidence-packager" / "scripts" / "release_evidence_packager.py"
    return candidate if candidate.exists() else None


def run_cutover_backfill_executor_pilot(
    args: argparse.Namespace,
    cwd: Path,
    changed_files: list[Path],
) -> ToolingPilotResult:
    if not detect_cutover_context(changed_files, args.task):
        return ToolingPilotResult(
            enabled=False,
            name="cutover-backfill-executor",
            reason="No cutover/backfill signal detected.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    spec_value = getattr(args, "cutover_pilot_spec", "").strip()
    if not spec_value:
        return ToolingPilotResult(
            enabled=False,
            name="cutover-backfill-executor",
            reason="Cutover/backfill signal detected, but no --cutover-pilot-spec was provided for safe asset generation.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    if args.phase == "start":
        return ToolingPilotResult(
            enabled=False,
            name="cutover-backfill-executor",
            reason="Cutover/backfill pilot only runs in batch/final, not in start.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    script_path = resolve_cutover_backfill_executor_script()
    if not script_path:
        return ToolingPilotResult(
            enabled=False,
            name="cutover-backfill-executor",
            reason="Pilot skipped because cutover-backfill-executor script was not found.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    spec_path = Path(spec_value).expanduser()
    output_root = cwd / ".codex-runtime" / "cutover-backfill-pilot"
    assets_dir = output_root / "assets"
    output_root.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    report_md = output_root / "cutover-backfill-report.md"
    report_json = output_root / "cutover-backfill-report.json"
    cmd = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
        "--spec",
        str(spec_path),
        "--output-dir",
        str(assets_dir),
        "--report-md",
        str(report_md),
        "--report-json",
        str(report_json),
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    if getattr(args, "cutover_pilot_batch_size", 0) > 0:
        cmd.extend(["--batch-size", str(args.cutover_pilot_batch_size)])
    if getattr(args, "cutover_pilot_concurrency", 0) > 0:
        cmd.extend(["--concurrency", str(args.cutover_pilot_concurrency)])
    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)
    warnings: list[str] = []
    if result.returncode not in (0, 1):
        warnings.append(
            f"cutover-backfill-executor pilot returned unexpected code ({result.returncode}). Review cutover asset generation before widening the pilot."
        )
    return ToolingPilotResult(
        enabled=True,
        name="cutover-backfill-executor",
        reason="Cutover/backfill signal and migration spec were both provided, so runtime-scoped execution assets were generated automatically.",
        target=spec_path,
        output_path=assets_dir,
        summary_path=report_md,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_ci_failure_triager_pilot(args: argparse.Namespace, cwd: Path) -> ToolingPilotResult:
    lowered_task = args.task.lower()
    if not any(token in lowered_task for token in CI_TRIAGE_TASK_SIGNALS):
        return ToolingPilotResult(
            enabled=False,
            name="ci-failure-triager",
            reason="No CI-failure signal detected.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    log_path = Path(getattr(args, "ci_pilot_log", "")).expanduser() if getattr(args, "ci_pilot_log", "") else None
    if not log_path:
        return ToolingPilotResult(
            enabled=False,
            name="ci-failure-triager",
            reason="CI-failure signal detected, but no --ci-pilot-log was provided for safe local triage.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    if args.phase == "start":
        return ToolingPilotResult(
            enabled=False,
            name="ci-failure-triager",
            reason="CI triage pilot only runs in batch/final, not in start.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    script_path = resolve_ci_failure_triager_script()
    if not script_path:
        return ToolingPilotResult(
            enabled=False,
            name="ci-failure-triager",
            reason="Pilot skipped because ci-failure-triager script was not found.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    output_root = cwd / ".codex-runtime" / "ci-triage-pilot"
    output_root.mkdir(parents=True, exist_ok=True)
    report_md = output_root / "ci-triage-report.md"
    report_json = output_root / "ci-triage-report.json"
    cmd = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        "none",
        "--log",
        str(log_path),
        "--job-name",
        getattr(args, "ci_pilot_job_name", "") or "pilot-job",
        "--report-md",
        str(report_md),
        "--report-json",
        str(report_json),
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)
    warnings: list[str] = []
    if result.returncode not in (0, 1):
        warnings.append(
            f"ci-failure-triager pilot returned unexpected code ({result.returncode}). Review CI triage flow before widening the pilot."
        )
    return ToolingPilotResult(
        enabled=True,
        name="ci-failure-triager",
        reason="CI-failure signal and pilot log were provided, so a runtime-scoped CI triage report was generated automatically.",
        target=log_path,
        output_path=report_json,
        summary_path=report_md,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_release_evidence_packager_pilot(
    args: argparse.Namespace,
    cwd: Path,
    changed_files: list[Path],
) -> ToolingPilotResult:
    if not detect_release_evidence_context(changed_files, args.task):
        return ToolingPilotResult(
            enabled=False,
            name="release-evidence-packager",
            reason="No release-evidence packaging signal detected.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    source_values = [item.strip() for item in getattr(args, "release_evidence_source", []) if item.strip()]
    if not source_values:
        return ToolingPilotResult(
            enabled=False,
            name="release-evidence-packager",
            reason="Release-evidence signal detected, but no --release-evidence-source was provided for safe packaging.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    if args.phase == "start":
        return ToolingPilotResult(
            enabled=False,
            name="release-evidence-packager",
            reason="Release-evidence packaging pilot only runs in batch/final, not in start.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    script_path = resolve_release_evidence_packager_script()
    if not script_path:
        return ToolingPilotResult(
            enabled=False,
            name="release-evidence-packager",
            reason="Pilot skipped because release-evidence-packager script was not found.",
            target=None,
            output_path=None,
            summary_path=None,
            command=[],
            returncode=None,
            output="Skipped",
            warnings=[],
        )

    output_root = cwd / ".codex-runtime" / "release-evidence-pilot"
    output_root.mkdir(parents=True, exist_ok=True)
    report_md = output_root / "release-evidence-pilot-report.md"
    report_json = output_root / "release-evidence-pilot-report.json"
    index_path = output_root / "release-evidence-index.md"
    cmd = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        "none",
        "--project",
        getattr(args, "release_evidence_project", "") or cwd.name,
        "--release-version",
        getattr(args, "release_evidence_version", "") or "pilot-release",
        "--environment",
        getattr(args, "release_evidence_environment", "") or "delivery-pilot",
        "--owner",
        getattr(args, "release_evidence_owner", "") or "codex",
        "--output-dir",
        str(output_root),
        "--output-md",
        str(index_path),
        "--report-md",
        str(report_md),
        "--report-json",
        str(report_json),
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for source in source_values:
        cmd.extend(["--source", source])
    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)
    warnings: list[str] = []
    if result.returncode not in (0, 1):
        warnings.append(
            f"release-evidence-packager pilot returned unexpected code ({result.returncode}). Review evidence packaging flow before widening the pilot."
        )
    return ToolingPilotResult(
        enabled=True,
        name="release-evidence-packager",
        reason="Release-evidence signal and explicit evidence source were both provided, so a runtime-scoped evidence bundle was generated automatically.",
        target=Path(source_values[0]).expanduser(),
        output_path=index_path,
        summary_path=report_md,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def build_warnings(
    phase: str,
    matched_triggers: list[str],
    changed_files: list[Path],
    had_raw_changes: bool,
    domains: dict[str, bool],
    surfaces: dict[str, bool],
    task: str,
) -> list[GuardWarning]:
    warnings: list[GuardWarning] = []
    lowered_task = task.lower()
    doc_text = "\n".join(
        read_text(path, limit=20_000)
        for path in changed_files
        if is_documentation_path(path)
    ).lower()
    has_contract_stability_evidence = any(
        token in doc_text
        for token in (
            "只读接口",
            "不修改接口结构",
            "不新增后端写接口",
            "本次未新增数据库表",
            "canonical contract",
            "read-only",
        )
    )
    skill_support_only_update = bool(changed_files) and all(
        is_skill_support_path(path) for path in changed_files
    )
    test_support_only_update = bool(changed_files) and all(
        is_skill_support_path(path) or is_test_support_path(path) for path in changed_files
    )

    if phase == "start" and not matched_triggers:
        warnings.append(
            GuardWarning(
                code="trigger-not-explicit",
                severity="low",
                message="No explicit auto-trigger phrase was detected in the task text. Confirm this skill is the right orchestrator if the request is not clearly full-stack.",
            )
        )

    if not changed_files and phase in {"batch", "final"}:
        warnings.append(
            GuardWarning(
                code="no-changed-files",
                severity="low" if had_raw_changes else "high",
                message=(
                    "Only noise-like changes were detected after filtering. Confirm this batch intentionally avoids code/doc/test changes."
                    if had_raw_changes
                    else "No changed files were detected from git status. The guard cannot verify cross-layer alignment until edits are visible in the worktree."
                ),
            )
        )

    if skill_support_only_update or test_support_only_update:
        return dedupe_warning_items(warnings)

    if surfaces["persistence"] and not surfaces["backend"]:
        warnings.append(
            GuardWarning(
                code="persistence-without-backend",
                severity="medium",
                message="Persistence-like files changed without matching backend service or API changes. Confirm schema changes are not drifting away from the service contract.",
            )
        )

    if (surfaces["backend"] or domains["api"]) and not surfaces["frontend"]:
        warnings.append(
            GuardWarning(
                code="backend-api-without-frontend",
                severity="low",
                message="Backend or API files changed without visible frontend/page updates. Confirm this request is intentionally backend-only and not a missing UI alignment.",
            )
        )

    if surfaces["frontend"] and not (surfaces["backend"] or domains["api"]) and not has_contract_stability_evidence:
        warnings.append(
            GuardWarning(
                code="frontend-without-backend-api",
                severity="low",
                message="Frontend/page files changed without visible backend or API updates. Confirm the canonical contract already existed and no API drift was introduced.",
            )
        )

    if (surfaces["backend"] or surfaces["frontend"] or surfaces["persistence"]) and not surfaces["docs"]:
        warnings.append(
            GuardWarning(
                code="docs-not-updated",
                severity="medium",
                message="Implementation files changed without documentation updates. Confirm docs are intentionally unchanged or add the required field/API/page/status docs.",
            )
        )

    if (surfaces["backend"] or surfaces["frontend"] or surfaces["persistence"]) and not surfaces["tests"]:
        warnings.append(
            GuardWarning(
                code="tests-not-updated",
                severity="medium",
                message="Implementation files changed without test updates. Add or confirm normal, error, boundary, permission, and performance-sensitive coverage as needed.",
            )
        )

    if domains["permission"] and not (surfaces["backend"] and surfaces["frontend"]):
        warnings.append(
            GuardWarning(
                code="permission-cross-layer-evidence",
                severity="medium",
                message="Permission-related changes were detected without both backend and frontend evidence. Confirm API guards and UI gating stay identical.",
            )
        )

    if (
        domains["validation"]
        and not (surfaces["backend"] and surfaces["frontend"])
        and not (surfaces["frontend"] and not surfaces["backend"] and has_contract_stability_evidence)
    ):
        warnings.append(
            GuardWarning(
                code="validation-cross-layer-evidence",
                severity="medium",
                message="Validation-related changes were detected without both backend and frontend evidence. Confirm required, format, length, and range rules remain unified.",
            )
        )

    if domains["status"] and not (surfaces["docs"] and surfaces["tests"]):
        warnings.append(
            GuardWarning(
                code="status-without-docs-tests",
                severity="medium",
                message="Status-related changes were detected without both docs and tests. Confirm status labels, transitions, colors, and assertions are aligned.",
            )
        )

    if surfaces["persistence"] and not domains["extension"]:
        warnings.append(
            GuardWarning(
                code="persistence-without-extension-evidence",
                severity="low",
                message="Structural files changed without any extension-strategy evidence. Confirm reserved extension fields were considered before changing schema or columns.",
            )
        )

    if "question-bank" in lowered_task or any(module.lower() in lowered_task for module in QUESTION_BANK_MODULES):
        warnings.append(
            GuardWarning(
                code="question-bank-context-detected",
                severity="low",
                message="Question-bank context detected. Ensure this unified entry switches to questionBank contract mode before deeper edits.",
            )
        )

    return dedupe_warning_items(warnings)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def suppress_overlapping_core_warnings(
    core_warnings: list[GuardWarning],
    *,
    has_rbac_guard: bool,
    has_state_machine_guard: bool,
    has_test_matrix_guard: bool,
    has_delivery_doc_sync_guard: bool,
    has_question_bank_guard: bool,
) -> list[GuardWarning]:
    suppressed_codes: set[str] = set()
    if has_rbac_guard:
        suppressed_codes.add("permission-cross-layer-evidence")
    if has_state_machine_guard:
        suppressed_codes.add("status-without-docs-tests")
    if has_test_matrix_guard:
        suppressed_codes.add("tests-not-updated")
    if has_delivery_doc_sync_guard:
        suppressed_codes.add("docs-not-updated")
    if has_question_bank_guard:
        suppressed_codes.add("question-bank-context-detected")
    return [warning for warning in core_warnings if warning.code not in suppressed_codes]


def sub_guard_warning_items(guard: SubGuardResult) -> list[GuardWarning]:
    if not guard.warnings:
        return []
    return [
        GuardWarning(
            code=f"{guard.name}-warning",
            severity="high",
            message=warning,
            source=guard.name,
        )
        for warning in guard.warnings
    ]


def indent_block(text: str, prefix: str = "    ") -> list[str]:
    return [f"{prefix}{line}" for line in text.splitlines()]


def append_sub_guard(lines: list[str], guard: SubGuardResult) -> None:
    lines.append("Integrated sub-guard:")
    lines.append(f"  - name: {guard.name}")
    lines.append(f"  - enabled: {'yes' if guard.enabled else 'no'}")
    if guard.script_path:
        lines.append(f"  - script: {guard.script_path}")
    if guard.returncode is not None:
        lines.append(f"  - returncode: {guard.returncode}")
    if guard.command:
        lines.append("  - command:")
        lines.extend(indent_block(" ".join(guard.command), prefix="      "))
    if guard.output:
        lines.append("  - output:")
        lines.extend(indent_block(guard.output, prefix="      "))
    if guard.warnings:
        lines.append("  - warnings:")
        for warning in guard.warnings:
            lines.append(f"      - {warning}")


def append_tooling_pilot(lines: list[str], pilot: ToolingPilotResult) -> None:
    lines.append("Conditional tooling pilot:")
    lines.append(f"  - name: {pilot.name}")
    lines.append(f"  - enabled: {'yes' if pilot.enabled else 'no'}")
    lines.append(f"  - reason: {pilot.reason}")
    if pilot.target:
        lines.append(f"  - target: {pilot.target}")
    if pilot.output_path:
        lines.append(f"  - output: {pilot.output_path}")
    if pilot.summary_path:
        lines.append(f"  - summary: {pilot.summary_path}")
    if pilot.command:
        lines.append("  - command:")
        lines.extend(indent_block(" ".join(pilot.command), prefix="      "))
    if pilot.returncode is not None:
        lines.append(f"  - returncode: {pilot.returncode}")
    if pilot.output:
        lines.append("  - output:")
        lines.extend(indent_block(pilot.output, prefix="      "))
    if pilot.warnings:
        lines.append("  - warnings:")
        for warning in pilot.warnings:
            lines.append(f"      - {warning}")


def resolve_api_schema_guard_script() -> Path | None:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    candidate = skills_root / "api-schema-drift-checker" / "scripts" / "schema_drift_guard.py"
    return candidate if candidate.exists() else None


def resolve_question_bank_guard_script() -> Path | None:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    candidate = skills_root / "question-bank-contract-enforcer" / "scripts" / "question_bank_contract_guard.py"
    return candidate if candidate.exists() else None


def resolve_rbac_guard_script() -> Path | None:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    candidate = skills_root / "rbac-alignment-guard" / "scripts" / "rbac_alignment_guard.py"
    return candidate if candidate.exists() else None


def resolve_state_machine_guard_script() -> Path | None:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    candidate = skills_root / "state-machine-alignment" / "scripts" / "state_machine_guard.py"
    return candidate if candidate.exists() else None


def resolve_error_code_guard_script() -> Path | None:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    candidate = skills_root / "error-code-governor" / "scripts" / "error_code_guard.py"
    return candidate if candidate.exists() else None


def resolve_test_matrix_guard_script() -> Path | None:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    candidate = skills_root / "fullstack-test-matrix" / "scripts" / "fullstack_test_matrix_guard.py"
    return candidate if candidate.exists() else None


def resolve_delivery_doc_sync_guard_script() -> Path | None:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    candidate = skills_root / "delivery-doc-sync" / "scripts" / "delivery_doc_sync_guard.py"
    return candidate if candidate.exists() else None


def resolve_component_reuse_guard_script() -> Path | None:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    candidate = skills_root / "component-reuse-shared-logic-guard" / "scripts" / "component_reuse_guard.py"
    return candidate if candidate.exists() else None


def resolve_cache_consistency_guard_script() -> Path | None:
    script_path = Path(__file__).resolve()
    skills_root = script_path.parents[2]
    candidate = skills_root / "cache-consistency-guard" / "scripts" / "cache_consistency_guard.py"
    return candidate if candidate.exists() else None


def run_api_schema_guard(args: argparse.Namespace, cwd: Path, guard_changed_files: list[Path]) -> SubGuardResult:
    name = "api-schema-drift-checker"
    if args.skip_api_schema_guard:
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped by --skip-api-schema-guard.",
            warnings=[],
        )

    script_path = resolve_api_schema_guard_script()
    if not script_path:
        return SubGuardResult(
            enabled=True,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="",
            warnings=[
                "api-schema-drift-checker was not found. Install / link the sibling skill or rerun with --skip-api-schema-guard if temporarily unavoidable."
            ],
        )

    cmd: list[str] = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
        "--max-files",
        str(args.api_max_files),
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in guard_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    for item in args.api_openapi:
        cmd.extend(["--openapi", item])
    for item in args.api_producer:
        cmd.extend(["--producer", item])
    for item in args.api_consumer:
        cmd.extend(["--consumer", item])
    for item in args.api_strip_prefix:
        cmd.extend(["--strip-prefix", item])
    if args.api_alias_map:
        cmd.extend(["--alias-map", args.api_alias_map])
    if args.api_report_md:
        cmd.extend(["--report-md", args.api_report_md])
    if args.api_report_json:
        cmd.extend(["--report-json", args.api_report_json])

    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"api-schema-drift-checker returned non-zero ({result.returncode}). Resolve schema drift or explicitly justify blocking issues."
        )

    return SubGuardResult(
        enabled=True,
        name=name,
        script_path=script_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_question_bank_guard(args: argparse.Namespace, cwd: Path, guard_changed_files: list[Path]) -> SubGuardResult:
    name = "question-bank-contract-enforcer"
    if args.skip_question_bank_guard:
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped by --skip-question-bank-guard.",
            warnings=[],
        )

    script_path = resolve_question_bank_guard_script()
    if not script_path:
        return SubGuardResult(
            enabled=True,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="",
            warnings=[
                "question-bank-contract-enforcer was not found. Install / link the sibling skill or rerun with --skip-question-bank-guard if temporarily unavoidable."
            ],
        )

    cmd: list[str] = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in guard_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    for item in args.qb_module:
        cmd.extend(["--module", item])
    if args.qb_force:
        cmd.append("--force")
    if args.qb_report_md:
        cmd.extend(["--report-md", args.qb_report_md])
    if args.qb_report_json:
        cmd.extend(["--report-json", args.qb_report_json])

    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"question-bank-contract-enforcer returned non-zero ({result.returncode}). Resolve question-bank contract drift or explicitly justify blocking issues."
        )

    return SubGuardResult(
        enabled=True,
        name=name,
        script_path=script_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_rbac_guard(args: argparse.Namespace, cwd: Path, guard_changed_files: list[Path]) -> SubGuardResult:
    name = "rbac-alignment-guard"
    if args.skip_rbac_guard:
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped by --skip-rbac-guard.",
            warnings=[],
        )

    script_path = resolve_rbac_guard_script()
    if not script_path:
        return SubGuardResult(
            enabled=True,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="",
            warnings=[
                "rbac-alignment-guard was not found. Install / link the sibling skill or rerun with --skip-rbac-guard if temporarily unavoidable."
            ],
        )

    cmd: list[str] = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in guard_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    for item in args.rbac_role:
        cmd.extend(["--role", item])
    for item in args.rbac_permission_key:
        cmd.extend(["--permission-key", item])
    if args.rbac_force:
        cmd.append("--force")
    if args.rbac_report_md:
        cmd.extend(["--report-md", args.rbac_report_md])
    if args.rbac_report_json:
        cmd.extend(["--report-json", args.rbac_report_json])

    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"rbac-alignment-guard returned non-zero ({result.returncode}). Resolve RBAC alignment drift or explicitly justify blocking issues."
        )

    return SubGuardResult(
        enabled=True,
        name=name,
        script_path=script_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_state_machine_guard(args: argparse.Namespace, cwd: Path, guard_changed_files: list[Path]) -> SubGuardResult:
    name = "state-machine-alignment"
    if args.skip_state_machine_guard:
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped by --skip-state-machine-guard.",
            warnings=[],
        )

    script_path = resolve_state_machine_guard_script()
    if not script_path:
        return SubGuardResult(
            enabled=True,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="",
            warnings=[
                "state-machine-alignment was not found. Install / link the sibling skill or rerun with --skip-state-machine-guard if temporarily unavoidable."
            ],
        )

    cmd: list[str] = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in guard_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    for item in args.sm_state:
        cmd.extend(["--state", item])
    for item in args.sm_transition:
        cmd.extend(["--transition", item])
    if args.sm_force:
        cmd.append("--force")
    if args.sm_report_md:
        cmd.extend(["--report-md", args.sm_report_md])
    if args.sm_report_json:
        cmd.extend(["--report-json", args.sm_report_json])

    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"state-machine-alignment returned non-zero ({result.returncode}). Resolve state-machine drift or explicitly justify blocking issues."
        )

    return SubGuardResult(
        enabled=True,
        name=name,
        script_path=script_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_error_code_guard(args: argparse.Namespace, cwd: Path, guard_changed_files: list[Path]) -> SubGuardResult:
    name = "error-code-governor"
    if args.skip_error_code_guard:
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped by --skip-error-code-guard.",
            warnings=[],
        )

    script_path = resolve_error_code_guard_script()
    if not script_path:
        return SubGuardResult(
            enabled=True,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="",
            warnings=[
                "error-code-governor was not found. Install / link the sibling skill or rerun with --skip-error-code-guard if temporarily unavoidable."
            ],
        )

    cmd: list[str] = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in guard_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    for item in args.ec_code:
        cmd.extend(["--code", item])
    for item in args.ec_namespace:
        cmd.extend(["--namespace", item])
    if args.ec_force:
        cmd.append("--force")
    if args.ec_report_md:
        cmd.extend(["--report-md", args.ec_report_md])
    if args.ec_report_json:
        cmd.extend(["--report-json", args.ec_report_json])

    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"error-code-governor returned non-zero ({result.returncode}). Resolve error-code governance drift or explicitly justify blocking issues."
        )

    return SubGuardResult(
        enabled=True,
        name=name,
        script_path=script_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_test_matrix_guard(args: argparse.Namespace, cwd: Path, guard_changed_files: list[Path]) -> SubGuardResult:
    name = "fullstack-test-matrix"
    if args.skip_test_matrix_guard:
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped by --skip-test-matrix-guard.",
            warnings=[],
        )

    script_path = resolve_test_matrix_guard_script()
    if not script_path:
        return SubGuardResult(
            enabled=True,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="",
            warnings=[
                "fullstack-test-matrix was not found. Install / link the sibling skill or rerun with --skip-test-matrix-guard if temporarily unavoidable."
            ],
        )

    cmd: list[str] = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in guard_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    for item in args.tm_scenario:
        cmd.extend(["--scenario", item])
    if args.tm_force:
        cmd.append("--force")
    if args.tm_report_md:
        cmd.extend(["--report-md", args.tm_report_md])
    if args.tm_report_json:
        cmd.extend(["--report-json", args.tm_report_json])

    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"fullstack-test-matrix returned non-zero ({result.returncode}). Resolve high-risk test matrix gaps or explicitly justify blocking issues."
        )

    return SubGuardResult(
        enabled=True,
        name=name,
        script_path=script_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_delivery_doc_sync_guard(args: argparse.Namespace, cwd: Path, guard_changed_files: list[Path]) -> SubGuardResult:
    name = "delivery-doc-sync"
    if args.skip_delivery_doc_sync_guard:
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped by --skip-delivery-doc-sync-guard.",
            warnings=[],
        )

    script_path = resolve_delivery_doc_sync_guard_script()
    if not script_path:
        return SubGuardResult(
            enabled=True,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="",
            warnings=[
                "delivery-doc-sync was not found. Install / link the sibling skill or rerun with --skip-delivery-doc-sync-guard if temporarily unavoidable."
            ],
        )

    cmd: list[str] = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in guard_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    for item in args.ds_doc_target:
        cmd.extend(["--doc-target", item])
    if args.ds_force:
        cmd.append("--force")
    if args.ds_report_md:
        cmd.extend(["--report-md", args.ds_report_md])
    if args.ds_report_json:
        cmd.extend(["--report-json", args.ds_report_json])

    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"delivery-doc-sync returned non-zero ({result.returncode}). Resolve delivery document sync drift or explicitly justify blocking issues."
        )

    return SubGuardResult(
        enabled=True,
        name=name,
        script_path=script_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_component_reuse_guard(args: argparse.Namespace, cwd: Path, guard_changed_files: list[Path]) -> SubGuardResult:
    name = "component-reuse-shared-logic-guard"
    if args.skip_component_reuse_guard:
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped by --skip-component-reuse-guard.",
            warnings=[],
        )

    script_path = resolve_component_reuse_guard_script()
    if not script_path:
        return SubGuardResult(
            enabled=True,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="",
            warnings=[
                "component-reuse-shared-logic-guard was not found. Install / link the sibling skill or rerun with --skip-component-reuse-guard if temporarily unavoidable."
            ],
        )

    cmd: list[str] = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in guard_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    if args.cr_force:
        cmd.append("--force")
    if args.cr_report_md:
        cmd.extend(["--report-md", args.cr_report_md])
    if args.cr_report_json:
        cmd.extend(["--report-json", args.cr_report_json])

    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"component-reuse-shared-logic-guard returned non-zero ({result.returncode}). Resolve implementation-layer reuse drift or explicitly justify blocking issues."
        )

    return SubGuardResult(
        enabled=True,
        name=name,
        script_path=script_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def run_cache_consistency_guard(args: argparse.Namespace, cwd: Path, guard_changed_files: list[Path]) -> SubGuardResult:
    name = "cache-consistency-guard"
    if args.skip_cache_consistency_guard:
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped by --skip-cache-consistency-guard.",
            warnings=[],
        )
    if not detect_cache_context(guard_changed_files, args.task):
        return SubGuardResult(
            enabled=False,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="Skipped because no cache or cutover-related context was detected.",
            warnings=[],
        )

    script_path = resolve_cache_consistency_guard_script()
    if not script_path:
        return SubGuardResult(
            enabled=True,
            name=name,
            script_path=None,
            command=[],
            returncode=None,
            output="",
            warnings=[
                "cache-consistency-guard was not found. Install / link the sibling skill or rerun with --skip-cache-consistency-guard if temporarily unavoidable."
            ],
        )

    cmd: list[str] = [
        sys.executable,
        str(script_path),
        "--phase",
        args.phase,
        "--cwd",
        str(cwd),
        "--fail-on",
        args.fail_on,
    ]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in guard_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    if args.cache_key_pattern:
        cmd.extend(["--key-pattern", args.cache_key_pattern])
    if args.cache_ttl > 0:
        cmd.extend(["--ttl", str(args.cache_ttl)])
    if args.cache_report_md:
        cmd.extend(["--report-md", args.cache_report_md])
    if args.cache_report_json:
        cmd.extend(["--report-json", args.cache_report_json])

    result = run_cmd(cmd, cwd)
    output_parts = []
    if result.stdout.strip():
        output_parts.append(result.stdout.strip())
    if result.stderr.strip():
        output_parts.append("stderr:\n" + result.stderr.strip())
    output = "\n".join(output_parts)

    warnings: list[str] = []
    if result.returncode != 0:
        warnings.append(
            f"cache-consistency-guard returned non-zero ({result.returncode}). Resolve cache consistency drift or explicitly justify blocking issues."
        )

    return SubGuardResult(
        enabled=True,
        name=name,
        script_path=script_path,
        command=cmd,
        returncode=result.returncode,
        output=output,
        warnings=warnings,
    )


def render(result: GuardResult) -> str:
    lines: list[str] = []
    lines.append(f"Unified Delivery Guard: {result.phase}")
    lines.append(f"Working directory: {result.cwd}")
    lines.append(f"Git root: {result.git_root if result.git_root else 'not detected'}")
    lines.append(f"Fail threshold: {result.fail_threshold}")
    lines.append(f"Matched triggers: {', '.join(result.matched_triggers) if result.matched_triggers else 'none'}")
    lines.append(f"Changed files: {len(result.changed_files)}")
    if result.ignored_noise_files:
        lines.append(f"Ignored noise files: {result.ignored_noise_files}")

    for path in result.changed_files[:20]:
        lines.append(f"  - {path}")
    if len(result.changed_files) > 20:
        lines.append(f"  - ... {len(result.changed_files) - 20} more")

    lines.append("Detected ten-standard coverage:")
    for key, label in DOMAIN_LABELS:
        lines.append(f"  - {label}: {'yes' if result.domains[key] else 'no evidence'}")

    lines.append("Detected surfaces:")
    for key in ("persistence", "backend", "frontend", "docs", "tests"):
        lines.append(f"  - {key}: {'yes' if result.surfaces[key] else 'no evidence'}")

    if result.warning_items:
        lines.append("Warnings:")
        for warning in result.warning_items:
            lines.append(f"  - {warning_text(warning)}")
    else:
        lines.append("Warnings: none")
    if result.recommended_skills:
        lines.append("Suggested explicit skills:")
        for item in result.recommended_skills:
            lines.append(f"  - {item}")
    for pilot in result.tooling_pilots:
        append_tooling_pilot(lines, pilot)

    append_sub_guard(lines, result.api_schema_guard)
    append_sub_guard(lines, result.question_bank_guard)
    append_sub_guard(lines, result.rbac_guard)
    append_sub_guard(lines, result.state_machine_guard)
    append_sub_guard(lines, result.error_code_guard)
    append_sub_guard(lines, result.test_matrix_guard)
    append_sub_guard(lines, result.delivery_doc_sync_guard)
    append_sub_guard(lines, result.component_reuse_guard)
    append_sub_guard(lines, result.cache_consistency_guard)

    if result.phase == "final":
        lines.append(
            "Final gate: pass" if not result.warning_items else "Final gate: warnings detected, resolve or explicitly explain before finishing."
        )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the unified delivery guard.")
    parser.add_argument(
        "--phase",
        choices=("start", "batch", "final"),
        default="final",
        help="Guard phase to run.",
    )
    parser.add_argument(
        "--task",
        default="",
        help="Optional user task text for trigger detection.",
    )
    parser.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="Working directory to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Optional explicit changed file path. Repeat for multiple files.",
    )
    parser.add_argument(
        "--fail-on",
        choices=("auto", "none", "high", "medium", "low"),
        default="auto",
        help="Unified failure threshold. auto: start uses none, batch/final use high.",
    )
    parser.add_argument(
        "--skip-api-schema-guard",
        action="store_true",
        help="Skip automatic api-schema-drift-checker invocation for this run.",
    )
    parser.add_argument(
        "--api-openapi",
        action="append",
        default=[],
        help="Forwarded --openapi path/glob for api-schema-drift-checker. Repeat for multiple values.",
    )
    parser.add_argument(
        "--api-producer",
        action="append",
        default=[],
        help="Forwarded --producer path/glob for api-schema-drift-checker. Repeat for multiple values.",
    )
    parser.add_argument(
        "--api-consumer",
        action="append",
        default=[],
        help="Forwarded --consumer path/glob for api-schema-drift-checker. Repeat for multiple values.",
    )
    parser.add_argument(
        "--api-alias-map",
        default="",
        help="Forwarded --alias-map file path for api-schema-drift-checker.",
    )
    parser.add_argument(
        "--api-strip-prefix",
        action="append",
        default=[],
        help="Forwarded --strip-prefix for api-schema-drift-checker. Repeat for multiple values.",
    )
    parser.add_argument(
        "--api-max-files",
        type=int,
        default=6000,
        help="Forwarded --max-files for api-schema-drift-checker discovery.",
    )
    parser.add_argument(
        "--api-report-md",
        default="",
        help="Forwarded --report-md path for api-schema-drift-checker output.",
    )
    parser.add_argument(
        "--api-report-json",
        default="",
        help="Forwarded --report-json path for api-schema-drift-checker output.",
    )
    parser.add_argument(
        "--skip-question-bank-guard",
        action="store_true",
        help="Skip automatic question-bank-contract-enforcer invocation for this run.",
    )
    parser.add_argument(
        "--qb-module",
        action="append",
        default=[],
        help="Forwarded --module for question-bank-contract-enforcer. Repeat for multiple values.",
    )
    parser.add_argument(
        "--qb-force",
        action="store_true",
        help="Forwarded --force for question-bank-contract-enforcer.",
    )
    parser.add_argument(
        "--qb-report-md",
        default="",
        help="Forwarded --report-md path for question-bank-contract-enforcer output.",
    )
    parser.add_argument(
        "--qb-report-json",
        default="",
        help="Forwarded --report-json path for question-bank-contract-enforcer output.",
    )
    parser.add_argument(
        "--skip-rbac-guard",
        action="store_true",
        help="Skip automatic rbac-alignment-guard invocation for this run.",
    )
    parser.add_argument(
        "--rbac-role",
        action="append",
        default=[],
        help="Forwarded --role for rbac-alignment-guard. Repeat for multiple values.",
    )
    parser.add_argument(
        "--rbac-permission-key",
        action="append",
        default=[],
        help="Forwarded --permission-key for rbac-alignment-guard. Repeat for multiple values.",
    )
    parser.add_argument(
        "--rbac-force",
        action="store_true",
        help="Forwarded --force for rbac-alignment-guard.",
    )
    parser.add_argument(
        "--rbac-report-md",
        default="",
        help="Forwarded --report-md path for rbac-alignment-guard output.",
    )
    parser.add_argument(
        "--rbac-report-json",
        default="",
        help="Forwarded --report-json path for rbac-alignment-guard output.",
    )
    parser.add_argument(
        "--skip-state-machine-guard",
        action="store_true",
        help="Skip automatic state-machine-alignment invocation for this run.",
    )
    parser.add_argument(
        "--sm-state",
        action="append",
        default=[],
        help="Forwarded --state for state-machine-alignment. Repeat for multiple values.",
    )
    parser.add_argument(
        "--sm-transition",
        action="append",
        default=[],
        help="Forwarded --transition for state-machine-alignment. Repeat for multiple values.",
    )
    parser.add_argument(
        "--sm-force",
        action="store_true",
        help="Forwarded --force for state-machine-alignment.",
    )
    parser.add_argument(
        "--sm-report-md",
        default="",
        help="Forwarded --report-md path for state-machine-alignment output.",
    )
    parser.add_argument(
        "--sm-report-json",
        default="",
        help="Forwarded --report-json path for state-machine-alignment output.",
    )
    parser.add_argument(
        "--skip-error-code-guard",
        action="store_true",
        help="Skip automatic error-code-governor invocation for this run.",
    )
    parser.add_argument(
        "--ec-code",
        action="append",
        default=[],
        help="Forwarded --code for error-code-governor. Repeat for multiple values.",
    )
    parser.add_argument(
        "--ec-namespace",
        action="append",
        default=[],
        help="Forwarded --namespace for error-code-governor. Repeat for multiple values.",
    )
    parser.add_argument(
        "--ec-force",
        action="store_true",
        help="Forwarded --force for error-code-governor.",
    )
    parser.add_argument(
        "--ec-report-md",
        default="",
        help="Forwarded --report-md path for error-code-governor output.",
    )
    parser.add_argument(
        "--ec-report-json",
        default="",
        help="Forwarded --report-json path for error-code-governor output.",
    )
    parser.add_argument(
        "--skip-test-matrix-guard",
        action="store_true",
        help="Skip automatic fullstack-test-matrix invocation for this run.",
    )
    parser.add_argument(
        "--tm-scenario",
        action="append",
        default=[],
        help="Forwarded --scenario for fullstack-test-matrix. Repeat for multiple values.",
    )
    parser.add_argument(
        "--tm-force",
        action="store_true",
        help="Forwarded --force for fullstack-test-matrix.",
    )
    parser.add_argument(
        "--tm-report-md",
        default="",
        help="Forwarded --report-md path for fullstack-test-matrix output.",
    )
    parser.add_argument(
        "--tm-report-json",
        default="",
        help="Forwarded --report-json path for fullstack-test-matrix output.",
    )
    parser.add_argument(
        "--skip-delivery-doc-sync-guard",
        action="store_true",
        help="Skip automatic delivery-doc-sync invocation for this run.",
    )
    parser.add_argument(
        "--ds-doc-target",
        action="append",
        default=[],
        help="Forwarded --doc-target for delivery-doc-sync. Repeat for multiple values.",
    )
    parser.add_argument(
        "--ds-force",
        action="store_true",
        help="Forwarded --force for delivery-doc-sync.",
    )
    parser.add_argument(
        "--ds-report-md",
        default="",
        help="Forwarded --report-md path for delivery-doc-sync output.",
    )
    parser.add_argument(
        "--ds-report-json",
        default="",
        help="Forwarded --report-json path for delivery-doc-sync output.",
    )
    parser.add_argument(
        "--skip-component-reuse-guard",
        action="store_true",
        help="Skip automatic component-reuse-shared-logic-guard invocation for this run.",
    )
    parser.add_argument(
        "--cr-force",
        action="store_true",
        help="Forwarded --force for component-reuse-shared-logic-guard.",
    )
    parser.add_argument(
        "--cr-report-md",
        default="",
        help="Forwarded --report-md path for component-reuse-shared-logic-guard output.",
    )
    parser.add_argument(
        "--cr-report-json",
        default="",
        help="Forwarded --report-json path for component-reuse-shared-logic-guard output.",
    )
    parser.add_argument(
        "--skip-cache-consistency-guard",
        action="store_true",
        help="Skip automatic cache-consistency-guard invocation for this run.",
    )
    parser.add_argument(
        "--cache-key-pattern",
        default="",
        help="Forwarded --key-pattern for cache-consistency-guard.",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=-1,
        help="Forwarded --ttl for cache-consistency-guard.",
    )
    parser.add_argument(
        "--cache-report-md",
        default="",
        help="Forwarded --report-md path for cache-consistency-guard output.",
    )
    parser.add_argument(
        "--cache-report-json",
        default="",
        help="Forwarded --report-json path for cache-consistency-guard output.",
    )
    parser.add_argument(
        "--dep-pilot-command",
        default="",
        help="Replay command for auto-install-missing-deps dry-run pilot, e.g. 'npm run dev'.",
    )
    parser.add_argument(
        "--ci-pilot-log",
        default="",
        help="Failure log path for ci-failure-triager pilot.",
    )
    parser.add_argument(
        "--ci-pilot-job-name",
        default="",
        help="Optional job name label for ci-failure-triager pilot.",
    )
    parser.add_argument(
        "--cutover-pilot-spec",
        default="",
        help="Migration spec path for cutover-backfill-executor pilot.",
    )
    parser.add_argument(
        "--cutover-pilot-batch-size",
        type=int,
        default=0,
        help="Optional batch size override for cutover-backfill-executor pilot.",
    )
    parser.add_argument(
        "--cutover-pilot-concurrency",
        type=int,
        default=0,
        help="Optional concurrency override for cutover-backfill-executor pilot.",
    )
    parser.add_argument(
        "--release-evidence-source",
        action="append",
        default=[],
        help="Evidence source path for release-evidence-packager pilot. Repeat for multiple sources.",
    )
    parser.add_argument(
        "--release-evidence-project",
        default="",
        help="Optional project label for release-evidence-packager pilot.",
    )
    parser.add_argument(
        "--release-evidence-version",
        default="",
        help="Optional release version for release-evidence-packager pilot.",
    )
    parser.add_argument(
        "--release-evidence-environment",
        default="",
        help="Optional environment label for release-evidence-packager pilot.",
    )
    parser.add_argument(
        "--release-evidence-owner",
        default="",
        help="Optional owner label for release-evidence-packager pilot.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).resolve()
    git_root = find_git_root(cwd)
    threshold = compute_threshold(args.phase, args.fail_on)

    raw_changed_files = [Path(path).resolve() for path in args.changed_file]
    auto_discovered_changed_files = shared_collect_changed_files(cwd, args.changed_file)
    if not raw_changed_files and git_root:
        raw_changed_files = parse_git_status(git_root)
    changed_files = auto_discovered_changed_files
    ignored_noise_files = max(0, len(raw_changed_files) - len(changed_files))
    guard_files = changed_files_for_subguards(changed_files, cwd)

    matched_triggers = detect_triggers(args.task)
    domains = detect_domains(changed_files)
    surfaces = detect_surfaces(changed_files)
    api_schema_guard = run_api_schema_guard(args, cwd, guard_files)
    question_bank_guard = run_question_bank_guard(args, cwd, guard_files)
    rbac_guard = run_rbac_guard(args, cwd, guard_files)
    state_machine_guard = run_state_machine_guard(args, cwd, guard_files)
    error_code_guard = run_error_code_guard(args, cwd, guard_files)
    test_matrix_guard = run_test_matrix_guard(args, cwd, guard_files)
    delivery_doc_sync_guard = run_delivery_doc_sync_guard(args, cwd, guard_files)
    component_reuse_guard = run_component_reuse_guard(args, cwd, guard_files)
    cache_consistency_guard = run_cache_consistency_guard(args, cwd, guard_files)
    test_code_generator_pilot = run_test_code_generator_pilot(args, cwd, changed_files, surfaces)
    auto_install_missing_deps_pilot = run_auto_install_missing_deps_pilot(args, cwd)
    ci_failure_triager_pilot = run_ci_failure_triager_pilot(args, cwd)
    cutover_backfill_executor_pilot = run_cutover_backfill_executor_pilot(args, cwd, changed_files)
    release_evidence_packager_pilot = run_release_evidence_packager_pilot(args, cwd, changed_files)

    core_warnings = build_warnings(
        args.phase,
        matched_triggers,
        changed_files,
        bool(raw_changed_files),
        domains,
        surfaces,
        args.task,
    )
    if len(changed_files) > MAX_SUBGUARD_CHANGED_FILES:
        core_warnings.append(
            GuardWarning(
                code="subguard-file-list-truncated",
                severity="low",
                message=f"Sub-guard changed-file list was truncated to {MAX_SUBGUARD_CHANGED_FILES} items to keep execution stable.",
            )
        )
    core_warnings = suppress_overlapping_core_warnings(
        core_warnings,
        has_rbac_guard=rbac_guard.enabled and rbac_guard.script_path is not None,
        has_state_machine_guard=state_machine_guard.enabled and state_machine_guard.script_path is not None,
        has_test_matrix_guard=test_matrix_guard.enabled and test_matrix_guard.script_path is not None,
        has_delivery_doc_sync_guard=delivery_doc_sync_guard.enabled and delivery_doc_sync_guard.script_path is not None,
        has_question_bank_guard=question_bank_guard.enabled and question_bank_guard.script_path is not None,
    )
    warning_items = dedupe_warning_items(
        core_warnings
        + sub_guard_warning_items(api_schema_guard)
        + sub_guard_warning_items(question_bank_guard)
        + sub_guard_warning_items(rbac_guard)
        + sub_guard_warning_items(state_machine_guard)
        + sub_guard_warning_items(error_code_guard)
        + sub_guard_warning_items(test_matrix_guard)
        + sub_guard_warning_items(delivery_doc_sync_guard)
        + sub_guard_warning_items(component_reuse_guard)
        + sub_guard_warning_items(cache_consistency_guard)
    )
    warnings = [warning_text(item) for item in warning_items]
    recommended_skills = recommend_execution_skills(changed_files, args.task, surfaces)

    result = GuardResult(
        phase=args.phase,
        cwd=cwd,
        git_root=git_root,
        matched_triggers=matched_triggers,
        changed_files=changed_files,
        ignored_noise_files=ignored_noise_files,
        domains=domains,
        surfaces=surfaces,
        fail_threshold=threshold,
        warning_items=warning_items,
        warnings=warnings,
        recommended_skills=recommended_skills,
        tooling_pilots=[
            test_code_generator_pilot,
            auto_install_missing_deps_pilot,
            ci_failure_triager_pilot,
            cutover_backfill_executor_pilot,
            release_evidence_packager_pilot,
        ],
        api_schema_guard=api_schema_guard,
        question_bank_guard=question_bank_guard,
        rbac_guard=rbac_guard,
        state_machine_guard=state_machine_guard,
        error_code_guard=error_code_guard,
        test_matrix_guard=test_matrix_guard,
        delivery_doc_sync_guard=delivery_doc_sync_guard,
        component_reuse_guard=component_reuse_guard,
        cache_consistency_guard=cache_consistency_guard,
    )

    print(render(result))
    has_blocking_warning = any(warning_meets_threshold(item.severity, threshold) for item in warning_items)
    return 1 if has_blocking_warning else 0


if __name__ == "__main__":
    sys.exit(main())
