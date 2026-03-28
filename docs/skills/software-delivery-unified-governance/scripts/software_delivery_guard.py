#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SKILLS_ROOT = SCRIPT_PATH.parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "shared-guard-runtime" / "scripts"))

from change_set import collect_changed_files, prepare_changed_files_for_subguards  # type: ignore
from guard_runtime import (  # type: ignore
    WarningItem,
    dedupe_warnings,
    summarize_warnings,
    warning_payload,
)
from report_writer import write_json_report, write_report  # type: ignore
from severity import compute_threshold, warning_meets_threshold  # type: ignore


@dataclass
class SubGuardResult:
    name: str
    enabled: bool
    command: list[str]
    returncode: int | None
    output: str
    warnings: list[str]


@dataclass
class GuardResult:
    phase: str
    cwd: Path
    fail_threshold: str
    changed_files: list[Path]
    warning_items: list[WarningItem]
    recommended_skills: list[str]
    subguards: list[SubGuardResult]


P0_GUARDS = {
    "requirements-freeze-guard",
    "release-preflight-guard",
    "rollback-readiness-guard",
    "database-migration-safety-guard",
    "deployment-config-alignment",
    "app-security-baseline-guard",
}

P1_GUARDS = {
    "fullstack-unified-development-standards",
    "acceptance-criteria-builder",
    "prd-ui-traceability-guard",
    "ux-state-completeness-checker",
    "release-quality-gate",
    "uat-handoff-guard",
    "observability-readiness-guard",
    "git-flow-enforcer",
    "release-branch-readiness-checker",
    "tooling-pilot-replay-gate",
}

P2_GUARDS = {
    "architecture-decision-recorder",
    "tech-stack-drift-guard",
    "secret-config-leak-guard",
    "performance-regression-guard",
    "capacity-and-hotspot-review",
    "incident-runbook-builder",
}

RESPONSIBILITY_MAP = {
    "requirements-freeze-guard": "产品",
    "acceptance-criteria-builder": "产品",
    "prd-ui-traceability-guard": "产品",
    "ux-state-completeness-checker": "产品",
    "fullstack-unified-development-standards": "研发",
    "release-preflight-guard": "运维",
    "rollback-readiness-guard": "运维",
    "deployment-config-alignment": "运维",
    "observability-readiness-guard": "运维",
    "database-migration-safety-guard": "研发",
    "app-security-baseline-guard": "研发",
    "git-flow-enforcer": "研发",
    "release-branch-readiness-checker": "研发",
    "release-quality-gate": "测试",
    "uat-handoff-guard": "测试",
    "architecture-decision-recorder": "研发",
    "tech-stack-drift-guard": "研发",
    "secret-config-leak-guard": "研发",
    "performance-regression-guard": "研发",
    "capacity-and-hotspot-review": "运维",
    "incident-runbook-builder": "运维",
    "tooling-pilot-replay-gate": "研发",
}

EXECUTION_SKILL_HINTS = {
    "ci-failure-triager": "推荐显式调用 `ci-failure-triager`，先归因 CI / 构建 / 测试失败，再决定提测或发布修复顺序。",
    "test-code-generator": "推荐显式调用 `test-code-generator`，为缺失的测试资产补骨架，降低发布前补测成本。",
    "cutover-backfill-executor": "推荐显式调用 `cutover-backfill-executor`，补齐切流、回填、审计和回滚资产后再发布。",
    "auto-install-missing-deps": "推荐显式调用 `auto-install-missing-deps`，先自动补齐缺失依赖并重试失败命令，再继续收口交付问题。",
    "release-evidence-packager": "推荐显式调用 `release-evidence-packager`，把 gate、rollback、UAT、replay 与关键日志收敛成统一发布证据包。",
}

CI_TRIAGE_TASK_SIGNALS = ("ci", "pipeline", "workflow", "流水线", "红灯", "构建失败", "测试失败")
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
RELEASE_EVIDENCE_TASK_SIGNALS = ("发布证据", "交付材料", "release evidence", "上线包", "handoff")
GENERIC_RELEASE_TASK_SIGNALS = ("发布", "上线", "交付", "交接", "release", "go live", "go-live", "handoff")
RELEASE_EVIDENCE_FILE_HINTS = (
    "release-gate",
    "release-dashboard",
    "gate-summary",
    "rollback",
    "uat",
    "replay",
    "quality-gate",
    "deploy",
    "preflight",
    "release-note",
    "release-notes",
    "delivery",
    "handoff",
)

TOOLING_PILOT_CONTEXT_KEYWORDS = (
    "pilot",
    "tooling",
    "skills",
    "skill 平台",
    "技能治理",
    "误报回放",
    "回放样例",
    "replay",
)


def run_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, check=False)


def resolve_script(skill_name: str, script_name: str) -> Path | None:
    candidate = SKILLS_ROOT / skill_name / "scripts" / script_name
    return candidate if candidate.exists() else None


def forwarded_report_args(report_md: str, report_json: str) -> list[str]:
    args: list[str] = []
    if report_md:
        args.extend(["--report-md", report_md])
    if report_json:
        args.extend(["--report-json", report_json])
    return args


def run_subguard(
    name: str,
    script_path: Path | None,
    args: argparse.Namespace,
    cwd: Path,
    changed_files: list[Path],
    skip: bool,
    extra_args: list[str] | None = None,
) -> SubGuardResult:
    if skip:
        return SubGuardResult(name, False, [], None, "Skipped", [])
    if not script_path:
        return SubGuardResult(name, True, [], None, "", [f"{name} 缺少脚本，无法执行。"])
    cmd = [sys.executable, str(script_path), "--phase", args.phase, "--cwd", str(cwd)]
    if not (extra_args and "--fail-on" in extra_args):
        cmd.extend(["--fail-on", args.fail_on])
    if args.task:
        cmd.extend(["--task", args.task])
    prepared_changed_files, truncation_warnings = prepare_changed_files_for_subguards(changed_files, cwd)
    for changed_file in prepared_changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    if extra_args:
        cmd.extend(extra_args)
    result = run_cmd(cmd, cwd)
    output = (result.stdout or "").strip()
    if truncation_warnings:
        prefix = "\n".join(f"- [LOW] {warning}" for warning in truncation_warnings)
        output = f"{prefix}\n{output}" if output else prefix
    warnings = []
    if result.returncode != 0:
        warnings.append(f"{name} 返回非零退出码 ({result.returncode})。")
    return SubGuardResult(name, True, cmd, result.returncode, output, warnings)


def detect_tooling_pilot_context(cwd: Path, changed_files: list[Path], task: str) -> bool:
    lowered_task = task.lower()
    if any(token.lower() in lowered_task for token in TOOLING_PILOT_CONTEXT_KEYWORDS):
        return True
    normalized_cwd = cwd.as_posix().lower()
    if "/.codex/skills" in normalized_cwd:
        return True
    normalized_files = [path.as_posix().lower() for path in changed_files]
    return any("/.codex/skills/" in item or "/skills/registry/" in item for item in normalized_files)


def resolve_tooling_pilot_replay_script() -> Path | None:
    candidate = SKILLS_ROOT / "registry" / "scripts" / "run_tooling_pilot_replay.py"
    return candidate if candidate.exists() else None


def run_tooling_pilot_replay_gate(args: argparse.Namespace, cwd: Path, changed_files: list[Path]) -> SubGuardResult:
    name = "tooling-pilot-replay-gate"
    if getattr(args, "skip_tooling_pilot_replay_gate", False):
        return SubGuardResult(name, False, [], None, "Skipped", [])
    if not detect_tooling_pilot_context(cwd, changed_files, args.task):
        return SubGuardResult(name, False, [], None, "Skipped because no tooling-pilot governance context was detected.", [])

    script_path = resolve_tooling_pilot_replay_script()
    if not script_path:
        return SubGuardResult(name, True, [], None, "", [f"{name} 缺少脚本，无法执行。"])

    runtime_root = cwd / ".codex-runtime" / "tooling-pilot-replay-gate"
    runtime_root.mkdir(parents=True, exist_ok=True)
    report_md = getattr(args, "tooling_pilot_replay_report_md", "") or str(runtime_root / f"tooling-pilot-replay-report-{date.today().isoformat()}.md")
    report_json = getattr(args, "tooling_pilot_replay_report_json", "") or str(runtime_root / f"tooling-pilot-replay-report-{date.today().isoformat()}.json")
    cmd = [
        sys.executable,
        str(script_path),
        "--as-of",
        date.today().isoformat(),
        "--output",
        report_md,
        "--output-json",
        report_json,
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
            f"{name} 返回非零退出码 ({result.returncode})。条件化 pilot 的真实回放未全部通过，当前不建议放宽发布门禁。"
        )
    return SubGuardResult(name, True, cmd, result.returncode, output, warnings)


def build_core_warnings(changed_files: list[Path]) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    normalized = [path.as_posix().lower() for path in changed_files]
    has_impl = any(token in item for item in normalized for token in ("frontend/", "backend/", "/app/", "/src/"))
    has_docs = any("/docs/" in item or item.endswith(".md") for item in normalized)
    has_db = any(token in item for item in normalized for token in ("migration", "schema", "sql", "prisma"))
    has_deploy = any(token in item for item in normalized for token in ("deploy", "docker", "helm", "k8s", ".env", "config"))

    if not changed_files:
        warnings.append(WarningItem("no-changed-files", "high", "未检测到可供分析的改动文件，无法执行软件交付风险评估。"))
    if has_impl and not has_docs:
        warnings.append(WarningItem("delivery-docs-missing", "medium", "实现改动存在，但未发现需求/发布/部署文档更新。"))
    if has_db and not has_deploy:
        warnings.append(WarningItem("db-change-without-deploy-evidence", "medium", "检测到数据库相关改动，但未发现发布/配置/部署证据。"))
    return dedupe_warnings(warnings)


def detect_ci_triage_recommendation_context(changed_files: list[Path], task: str) -> bool:
    lowered_task = task.lower()
    if any(token in lowered_task for token in CI_TRIAGE_TASK_SIGNALS):
        return True
    normalized = [path.as_posix().lower() for path in changed_files]
    return any(token in item for item in normalized for token in CI_TRIAGE_FILE_HINTS)


def detect_release_evidence_recommendation_context(changed_files: list[Path], task: str) -> bool:
    lowered_task = task.lower()
    if any(token in lowered_task for token in RELEASE_EVIDENCE_TASK_SIGNALS):
        return True
    if not any(token in lowered_task for token in GENERIC_RELEASE_TASK_SIGNALS):
        return False
    normalized = [path.as_posix().lower() for path in changed_files]
    return any(token in item for item in normalized for token in RELEASE_EVIDENCE_FILE_HINTS)


def recommend_execution_skills(changed_files: list[Path], task: str) -> list[str]:
    recommendations: list[str] = []
    lowered_task = task.lower()
    normalized = [path.as_posix().lower() for path in changed_files]
    has_impl = any(token in item for item in normalized for token in ("frontend/", "backend/", "/app/", "/src/"))
    has_tests = any("/tests/" in item or ".test." in item or ".spec." in item for item in normalized)

    if detect_ci_triage_recommendation_context(changed_files, task):
        recommendations.append(EXECUTION_SKILL_HINTS["ci-failure-triager"])

    if (has_impl and not has_tests) or any(token in lowered_task for token in ("补测试", "回归测试", "测试骨架")):
        recommendations.append(EXECUTION_SKILL_HINTS["test-code-generator"])

    if any(token in lowered_task for token in ("回填", "切流", "backfill", "cutover", "迁移")) or any(
        token in item for item in normalized for token in ("migration", "schema", "sql", "prisma", "backfill", "cutover")
    ):
        recommendations.append(EXECUTION_SKILL_HINTS["cutover-backfill-executor"])

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

    return list(dict.fromkeys(recommendations))


def guard_level(name: str) -> str:
    if name in P0_GUARDS:
        return "P0"
    if name in P1_GUARDS:
        return "P1"
    if name in P2_GUARDS:
        return "P2"
    return "OTHER"


def flatten_subguard_findings(results: list[SubGuardResult]) -> list[WarningItem]:
    findings: list[WarningItem] = []
    for result in results:
        for warning in result.warnings:
            findings.append(
                WarningItem(
                    code=f"{result.name}-failed",
                    severity="high",
                    message=warning,
                    file=result.name,
                )
            )
        for line in result.output.splitlines():
            if not line.strip().startswith("- ["):
                continue
            stripped = line.strip()
            if "[HIGH]" in stripped:
                severity = "high"
            elif "[MEDIUM]" in stripped:
                severity = "medium"
            elif "[LOW]" in stripped:
                severity = "low"
            else:
                continue
            message = stripped.split("] ", 1)[1] if "] " in stripped else stripped
            findings.append(
                WarningItem(
                    code=f"{result.name}-finding",
                    severity=severity,
                    message=message,
                    file=result.name,
                )
            )
    return dedupe_warnings(findings)


def grouped_delivery_summary(results: list[SubGuardResult]) -> dict[str, list[str]]:
    p0_blockers: list[str] = []
    p1_gaps: list[str] = []
    fix_before_release: list[str] = []
    defer_later: list[str] = []
    p2_governance: list[str] = []

    for result in results:
        level = guard_level(result.name)
        if result.returncode and result.returncode != 0:
            if level == "P0":
                p0_blockers.append(f"{result.name} 存在阻断项")
            elif level == "P1":
                p1_gaps.append(f"{result.name} 存在上线前准备不足")
            elif level == "P2":
                p2_governance.append(f"{result.name} 存在治理建设项")

        for line in result.output.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- ["):
                continue
            if "] " not in stripped:
                continue
            message = stripped.split("] ", 1)[1]
            if "[HIGH]" in stripped:
                if level == "P0":
                    p0_blockers.append(f"{result.name}: {message}")
                elif level == "P1":
                    p1_gaps.append(f"{result.name}: {message}")
                elif level == "P2":
                    p2_governance.append(f"{result.name}: {message}")
            elif "[MEDIUM]" in stripped:
                if level == "P2":
                    p2_governance.append(f"{result.name}: {message}")
                else:
                    fix_before_release.append(f"{result.name}: {message}")
            elif "[LOW]" in stripped:
                defer_later.append(f"{result.name}: {message}")

    return {
        "p0_blockers": list(dict.fromkeys(p0_blockers)),
        "p1_gaps": list(dict.fromkeys(p1_gaps)),
        "fix_before_release": list(dict.fromkeys(fix_before_release)),
        "defer_later": list(dict.fromkeys(defer_later)),
        "p2_governance": list(dict.fromkeys(p2_governance)),
    }


def build_release_conclusion(layered: dict[str, list[str]]) -> dict[str, object]:
    p0_blockers = layered["p0_blockers"]
    p1_gaps = layered["p1_gaps"]
    fix_before_release = layered["fix_before_release"]
    defer_later = layered["defer_later"]
    p2_governance = layered.get("p2_governance", [])

    if p0_blockers:
        status = "不建议上线"
        action_code = "BLOCK_NOW"
        action_label = "立即阻断"
        reason = "存在 P0 阻断项，当前版本不满足安全上线条件。"
    elif p1_gaps:
        status = "有条件上线"
        action_code = "FIX_THEN_RELEASE"
        action_label = "补齐后上线"
        reason = "不存在 P0 阻断项，但存在 P1 准备不足，原则上应补齐后再上线。"
    elif fix_before_release:
        status = "基本可上线"
        action_code = "RECOMMEND_FIX_THEN_RELEASE"
        action_label = "建议补齐后上线"
        reason = "不存在阻断项，但仍有上线前建议补齐的中风险准备项。"
    else:
        status = "可上线"
        action_code = "ACCEPTABLE_TO_RELEASE"
        action_label = "可接受风险上线"
        reason = "未发现阻断上线的高风险问题。"

    return {
        "status": status,
        "actionCode": action_code,
        "actionLabel": action_label,
        "reason": reason,
        "blockingItems": p0_blockers,
        "mustFixBeforeRelease": p1_gaps + fix_before_release,
        "deferableItems": defer_later,
        "p2GovernanceItems": p2_governance,
    }


def summarize_responsibilities(results: list[SubGuardResult]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {"产品": [], "研发": [], "测试": [], "运维": []}
    for result in results:
        owner = RESPONSIBILITY_MAP.get(result.name)
        if not owner:
            continue
        if result.returncode and result.returncode != 0:
            buckets[owner].append(f"{result.name} 存在高风险或阻断项")
        for line in result.output.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- ["):
                continue
            if "] " not in stripped:
                continue
            message = stripped.split("] ", 1)[1]
            buckets[owner].append(f"{result.name}: {message}")
    return {
        owner: list(dict.fromkeys(items))
        for owner, items in buckets.items()
        if items
    }


def build_brief_summary(cwd: Path, conclusion: dict[str, object], recommended_skills: list[str] | None = None) -> str:
    blocking_items = list(conclusion.get("blockingItems", []))
    must_fix = list(conclusion.get("mustFixBeforeRelease", []))
    deferable = list(conclusion.get("deferableItems", []))
    p2_governance = list(conclusion.get("p2GovernanceItems", []))

    lines = [
        "软件交付评审摘要",
        f"工作区：{cwd}",
        f"结论：{conclusion.get('status', '')}",
        f"原因：{conclusion.get('reason', '')}",
        f"P0 阻断项：{len(blocking_items)}",
        f"上线前必须补齐：{len(must_fix)}",
        f"可延期治理：{len(deferable)}",
        f"P2 治理项：{len(p2_governance)}",
    ]
    if blocking_items:
        lines.append("阻断项：")
        for item in blocking_items[:3]:
            lines.append(f"- {item}")
    if must_fix:
        lines.append("必须补齐：")
        for item in must_fix[:5]:
            lines.append(f"- {item}")
    if recommended_skills:
        lines.append("建议调用：")
        for item in recommended_skills[:3]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def build_brief_summary_with_responsibility(
    cwd: Path,
    conclusion: dict[str, object],
    responsibility: dict[str, list[str]],
    recommended_skills: list[str] | None = None,
) -> str:
    lines = build_brief_summary(cwd, conclusion, recommended_skills).splitlines()
    if responsibility:
        lines.append("责任归属：")
        for owner in ["产品", "研发", "测试", "运维"]:
            items = responsibility.get(owner, [])
            if not items:
                continue
            lines.append(f"{owner}：")
            for item in items[:3]:
                lines.append(f"- {item}")
    return "\n".join(lines)


def build_one_screen_summary(
    cwd: Path,
    conclusion: dict[str, object],
    layered: dict[str, list[str]],
    responsibility: dict[str, list[str]],
    recommended_skills: list[str] | None = None,
) -> str:
    lines = [
        "发布评审一屏摘要",
        f"项目：{cwd.name}",
        f"结论：{conclusion.get('status', '')}",
        f"动作：{conclusion.get('actionLabel', '')}",
        f"P0阻断：{len(layered.get('p0_blockers', []))} | P1不足：{len(layered.get('p1_gaps', []))} | 必补：{len(conclusion.get('mustFixBeforeRelease', []))} | P2治理：{len(layered.get('p2_governance', []))}",
        f"原因：{conclusion.get('reason', '')}",
    ]
    if layered.get("p0_blockers"):
        lines.append("阻断：")
        for item in layered["p0_blockers"][:2]:
            lines.append(f"- {item}")
    if conclusion.get("mustFixBeforeRelease"):
        lines.append("必补：")
        for item in list(conclusion["mustFixBeforeRelease"])[:3]:
            lines.append(f"- {item}")
    if responsibility:
        lines.append("责任：")
        for owner in ["产品", "研发", "测试", "运维"]:
            items = responsibility.get(owner, [])
            if not items:
                continue
            lines.append(f"- {owner}：{items[0]}")
    if recommended_skills:
        lines.append("建议：")
        for item in recommended_skills[:2]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def render(result: GuardResult) -> str:
    layered = grouped_delivery_summary(result.subguards)
    conclusion = build_release_conclusion(layered)
    responsibility = summarize_responsibilities(result.subguards)
    lines = [
        f"Software Delivery Guard: {result.phase}",
        f"Working directory: {result.cwd}",
        f"Fail threshold: {result.fail_threshold}",
        f"Changed files: {len(result.changed_files)}",
    ]
    for path in result.changed_files[:20]:
        lines.append(f"  - {path}")
    if result.warning_items:
        lines.append("Warnings:")
        for item in result.warning_items:
            suffix = f" [{item.file}]" if item.file else ""
            lines.append(f"  - [{item.severity.upper()}] {item.message}{suffix}")
    else:
        lines.append("Warnings: none")
    if result.recommended_skills:
        lines.append("Suggested explicit skills:")
        for item in result.recommended_skills:
            lines.append(f"  - {item}")
    lines.append("Release Conclusion:")
    lines.append(f"  - 结论: {conclusion['status']}")
    lines.append(f"  - 建议动作: {conclusion['actionLabel']} ({conclusion['actionCode']})")
    lines.append(f"  - 原因: {conclusion['reason']}")
    lines.append("  - 上线阻断项:")
    if conclusion["blockingItems"]:
        for item in conclusion["blockingItems"]:
            lines.append(f"      - {item}")
    else:
        lines.append("      - 无")
    lines.append("  - 上线前必须补齐:")
    if conclusion["mustFixBeforeRelease"]:
        for item in conclusion["mustFixBeforeRelease"]:
            lines.append(f"      - {item}")
    else:
        lines.append("      - 无")
    lines.append("  - 可延期治理:")
    if conclusion["deferableItems"]:
        for item in conclusion["deferableItems"]:
            lines.append(f"      - {item}")
    else:
        lines.append("      - 无")
    lines.append("  - P2 治理项:")
    if conclusion["p2GovernanceItems"]:
        for item in conclusion["p2GovernanceItems"]:
            lines.append(f"      - {item}")
    else:
        lines.append("      - 无")
    lines.append("  - 责任归属:")
    if responsibility:
        for owner in ["产品", "研发", "测试", "运维"]:
            items = responsibility.get(owner, [])
            if not items:
                continue
            lines.append(f"      - {owner}:")
            for item in items[:3]:
                lines.append(f"          - {item}")
    else:
        lines.append("      - 无")
    lines.append("Layered Summary:")
    lines.append("  P0 阻断项:")
    if layered["p0_blockers"]:
        for item in layered["p0_blockers"]:
            lines.append(f"    - {item}")
    else:
        lines.append("    - 无")
    lines.append("  P1 准备不足项:")
    if layered["p1_gaps"]:
        for item in layered["p1_gaps"]:
            lines.append(f"    - {item}")
    else:
        lines.append("    - 无")
    lines.append("  建议上线前补齐:")
    if layered["fix_before_release"]:
        for item in layered["fix_before_release"]:
            lines.append(f"    - {item}")
    else:
        lines.append("    - 无")
    lines.append("  可延期治理:")
    if layered["defer_later"]:
        for item in layered["defer_later"]:
            lines.append(f"    - {item}")
    else:
        lines.append("    - 无")
    lines.append("  P2 治理项:")
    if layered["p2_governance"]:
        for item in layered["p2_governance"]:
            lines.append(f"    - {item}")
    else:
        lines.append("    - 无")
    for item in result.subguards:
        lines.append("Integrated sub-guard:")
        lines.append(f"  - name: {item.name}")
        lines.append(f"  - enabled: {'yes' if item.enabled else 'no'}")
        if item.command:
            lines.append(f"  - command: {' '.join(item.command)}")
        if item.returncode is not None:
            lines.append(f"  - returncode: {item.returncode}")
        if item.output:
            lines.append("  - output:")
            for line in item.output.splitlines():
                lines.append(f"      {line}")
        if item.warnings:
            lines.append("  - warnings:")
            for warning in item.warnings:
                lines.append(f"      - {warning}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="软件交付全流程总守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--skip-fullstack-unified-development-standards", action="store_true")
    parser.add_argument("--skip-requirements-freeze-guard", action="store_true")
    parser.add_argument("--skip-release-preflight-guard", action="store_true")
    parser.add_argument("--skip-rollback-readiness-guard", action="store_true")
    parser.add_argument("--skip-database-migration-safety-guard", action="store_true")
    parser.add_argument("--skip-deployment-config-alignment", action="store_true")
    parser.add_argument("--skip-app-security-baseline-guard", action="store_true")
    parser.add_argument("--skip-acceptance-criteria-builder", action="store_true")
    parser.add_argument("--skip-prd-ui-traceability-guard", action="store_true")
    parser.add_argument("--skip-ux-state-completeness-checker", action="store_true")
    parser.add_argument("--skip-release-quality-gate", action="store_true")
    parser.add_argument("--skip-uat-handoff-guard", action="store_true")
    parser.add_argument("--skip-observability-readiness-guard", action="store_true")
    parser.add_argument("--skip-git-flow-enforcer", action="store_true")
    parser.add_argument("--skip-release-branch-readiness-checker", action="store_true")
    parser.add_argument("--skip-tooling-pilot-replay-gate", action="store_true")
    parser.add_argument("--include-p2", action="store_true")
    parser.add_argument("--skip-architecture-decision-recorder", action="store_true")
    parser.add_argument("--skip-tech-stack-drift-guard", action="store_true")
    parser.add_argument("--skip-secret-config-leak-guard", action="store_true")
    parser.add_argument("--skip-performance-regression-guard", action="store_true")
    parser.add_argument("--skip-capacity-and-hotspot-review", action="store_true")
    parser.add_argument("--skip-incident-runbook-builder", action="store_true")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--brief-report-md", default="")
    parser.add_argument("--brief-report-txt", default="")
    parser.add_argument("--one-screen-report-md", default="")
    parser.add_argument("--one-screen-report-txt", default="")
    parser.add_argument("--fullstack-report-md", default="")
    parser.add_argument("--fullstack-report-json", default="")
    parser.add_argument("--requirements-report-md", default="")
    parser.add_argument("--requirements-report-json", default="")
    parser.add_argument("--preflight-report-md", default="")
    parser.add_argument("--preflight-report-json", default="")
    parser.add_argument("--rollback-report-md", default="")
    parser.add_argument("--rollback-report-json", default="")
    parser.add_argument("--db-migration-report-md", default="")
    parser.add_argument("--db-migration-report-json", default="")
    parser.add_argument("--config-report-md", default="")
    parser.add_argument("--config-report-json", default="")
    parser.add_argument("--security-report-md", default="")
    parser.add_argument("--security-report-json", default="")
    parser.add_argument("--acceptance-report-md", default="")
    parser.add_argument("--acceptance-report-json", default="")
    parser.add_argument("--prd-ui-report-md", default="")
    parser.add_argument("--prd-ui-report-json", default="")
    parser.add_argument("--ux-state-report-md", default="")
    parser.add_argument("--ux-state-report-json", default="")
    parser.add_argument("--quality-gate-report-md", default="")
    parser.add_argument("--quality-gate-report-json", default="")
    parser.add_argument("--uat-report-md", default="")
    parser.add_argument("--uat-report-json", default="")
    parser.add_argument("--observability-report-md", default="")
    parser.add_argument("--observability-report-json", default="")
    parser.add_argument("--git-flow-report-md", default="")
    parser.add_argument("--git-flow-report-json", default="")
    parser.add_argument("--release-branch-report-md", default="")
    parser.add_argument("--release-branch-report-json", default="")
    parser.add_argument("--tooling-pilot-replay-report-md", default="")
    parser.add_argument("--tooling-pilot-replay-report-json", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)

    subguards = [
        ("fullstack-unified-development-standards", "unified_delivery_guard.py", args.skip_fullstack_unified_development_standards, forwarded_report_args(args.fullstack_report_md, args.fullstack_report_json)),
        ("requirements-freeze-guard", "requirements_freeze_guard.py", args.skip_requirements_freeze_guard, forwarded_report_args(args.requirements_report_md, args.requirements_report_json)),
        ("release-preflight-guard", "release_preflight_guard.py", args.skip_release_preflight_guard, forwarded_report_args(args.preflight_report_md, args.preflight_report_json)),
        ("rollback-readiness-guard", "rollback_readiness_guard.py", args.skip_rollback_readiness_guard, forwarded_report_args(args.rollback_report_md, args.rollback_report_json)),
        ("database-migration-safety-guard", "database_migration_safety_guard.py", args.skip_database_migration_safety_guard, forwarded_report_args(args.db_migration_report_md, args.db_migration_report_json)),
        ("deployment-config-alignment", "deployment_config_alignment_guard.py", args.skip_deployment_config_alignment, forwarded_report_args(args.config_report_md, args.config_report_json)),
        ("app-security-baseline-guard", "app_security_baseline_guard.py", args.skip_app_security_baseline_guard, forwarded_report_args(args.security_report_md, args.security_report_json)),
        ("acceptance-criteria-builder", "acceptance_criteria_builder_guard.py", args.skip_acceptance_criteria_builder, forwarded_report_args(args.acceptance_report_md, args.acceptance_report_json)),
        ("prd-ui-traceability-guard", "prd_ui_traceability_guard.py", args.skip_prd_ui_traceability_guard, forwarded_report_args(args.prd_ui_report_md, args.prd_ui_report_json)),
        ("ux-state-completeness-checker", "ux_state_completeness_guard.py", args.skip_ux_state_completeness_checker, forwarded_report_args(args.ux_state_report_md, args.ux_state_report_json)),
        ("release-quality-gate", "release_quality_gate.py", args.skip_release_quality_gate, forwarded_report_args(args.quality_gate_report_md, args.quality_gate_report_json)),
        ("uat-handoff-guard", "uat_handoff_guard.py", args.skip_uat_handoff_guard, forwarded_report_args(args.uat_report_md, args.uat_report_json)),
        ("observability-readiness-guard", "observability_readiness_guard.py", args.skip_observability_readiness_guard, forwarded_report_args(args.observability_report_md, args.observability_report_json)),
        ("git-flow-enforcer", "git_flow_enforcer.py", args.skip_git_flow_enforcer, forwarded_report_args(args.git_flow_report_md, args.git_flow_report_json)),
        ("release-branch-readiness-checker", "release_branch_readiness_checker.py", args.skip_release_branch_readiness_checker, forwarded_report_args(args.release_branch_report_md, args.release_branch_report_json)),
    ]

    if args.include_p2:
        subguards.extend(
            [
                ("architecture-decision-recorder", "architecture_decision_recorder_guard.py", args.skip_architecture_decision_recorder, ["--fail-on", "none"]),
                ("tech-stack-drift-guard", "tech_stack_drift_guard.py", args.skip_tech_stack_drift_guard, ["--fail-on", "none"]),
                ("secret-config-leak-guard", "secret_config_leak_guard.py", args.skip_secret_config_leak_guard, ["--fail-on", "none"]),
                ("performance-regression-guard", "performance_regression_guard.py", args.skip_performance_regression_guard, ["--fail-on", "none"]),
                ("capacity-and-hotspot-review", "capacity_hotspot_guard.py", args.skip_capacity_and_hotspot_review, ["--fail-on", "none"]),
                ("incident-runbook-builder", "incident_runbook_builder.py", args.skip_incident_runbook_builder, ["--fail-on", "none"]),
            ]
        )

    results = [
        run_subguard(name, resolve_script(name, script_name), args, cwd, changed_files, skip, extra_args)
        for name, script_name, skip, extra_args in subguards
    ]
    results.append(run_tooling_pilot_replay_gate(args, cwd, changed_files))
    core_warnings = build_core_warnings(changed_files)
    synthetic_warnings = dedupe_warnings(core_warnings + flatten_subguard_findings(results))
    guard_result = GuardResult(
        phase=args.phase,
        cwd=cwd,
        fail_threshold=threshold,
        changed_files=changed_files,
        warning_items=synthetic_warnings,
        recommended_skills=recommend_execution_skills(changed_files, args.task),
        subguards=results,
    )
    rendered = render(guard_result)
    print(rendered)
    write_report(args.report_md, rendered)
    layered = grouped_delivery_summary(results)
    conclusion = build_release_conclusion(layered)
    responsibility = summarize_responsibilities(results)
    brief_summary = build_brief_summary_with_responsibility(cwd, conclusion, responsibility, guard_result.recommended_skills)
    one_screen_summary = build_one_screen_summary(cwd, conclusion, layered, responsibility, guard_result.recommended_skills)
    write_report(args.brief_report_md, brief_summary)
    write_report(args.brief_report_txt, brief_summary)
    write_report(args.one_screen_report_md, one_screen_summary)
    write_report(args.one_screen_report_txt, one_screen_summary)
    write_json_report(
        args.report_json,
        {
            "phase": args.phase,
            "cwd": str(cwd),
            "failThreshold": threshold,
            "changedFiles": [str(path) for path in changed_files],
            "summary": summarize_warnings(synthetic_warnings),
            "releaseConclusion": conclusion,
            "responsibilitySummary": responsibility,
            "briefSummary": brief_summary,
            "oneScreenSummary": one_screen_summary,
            "layeredSummary": layered,
            "recommendedSkills": guard_result.recommended_skills,
            "warnings": warning_payload(synthetic_warnings),
            "subguards": [
                {
                    "name": result.name,
                    "enabled": result.enabled,
                    "command": result.command,
                    "returncode": result.returncode,
                    "warnings": result.warnings,
                }
                for result in results
            ],
        },
    )
    has_blocking = any(
        warning_meets_threshold(item.severity, threshold) and guard_level(item.file) != "P2"
        for item in synthetic_warnings
    )
    return 1 if has_blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
