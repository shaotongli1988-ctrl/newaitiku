#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
LOCAL_SKILLS_ROOT = SCRIPT_PATH.parents[2]
GLOBAL_SKILLS_ROOT = Path.home() / ".codex" / "skills"
sys.path.insert(0, str(SCRIPT_PATH.parent))

from readiness_guard_common import (  # type: ignore
    WarningItem,
    collect_changed_files,
    compute_threshold,
    dedupe_warnings,
    render_guard_report,
    standard_guard_payload,
    summarize_warnings,
    warning_meets_threshold,
    write_json_report,
    write_report,
)


@dataclass(frozen=True)
class GuardSpec:
    name: str
    level: str
    script_name: str
    responsibility: str
    implemented: bool
    missing_severity: str
    missing_message: str


@dataclass
class SubGuardResult:
    spec: GuardSpec
    enabled: bool
    command: list[str]
    returncode: int | None
    output: str
    runtime_warnings: list[str]
    status: str
    script_path: str


QUESTION_BANK_HINTS = ("questionbank", "question-bank", "题库", "tiku")
QUESTION_BANK_MODULES = ("user", "userAuth", "knowledge", "question", "task")

GUARD_SPECS = {
    "requirements-freeze-guard": GuardSpec(
        "requirements-freeze-guard",
        "P0",
        "requirements_freeze_guard.py",
        "产品",
        True,
        "high",
        "需求冻结守卫缺失，无法确认是否具备进入开发的基本前提。",
    ),
    "acceptance-criteria-builder": GuardSpec(
        "acceptance-criteria-builder",
        "P0",
        "acceptance_criteria_builder_guard.py",
        "产品",
        True,
        "high",
        "验收标准守卫缺失，无法确认需求是否能被测试与签收。",
    ),
    "prd-ui-traceability-guard": GuardSpec(
        "prd-ui-traceability-guard",
        "P0",
        "prd_ui_traceability_guard.py",
        "产品",
        True,
        "high",
        "PRD 与页面追踪守卫缺失，无法确认设计与实现入口是否一致。",
    ),
    "api-schema-drift-checker": GuardSpec(
        "api-schema-drift-checker",
        "P0",
        "schema_drift_guard.py",
        "研发",
        True,
        "high",
        "API 契约守卫缺失，无法自动核对字段、结构与枚举的一致性。",
    ),
    "rbac-alignment-guard": GuardSpec(
        "rbac-alignment-guard",
        "P0",
        "rbac_alignment_guard.py",
        "研发",
        True,
        "high",
        "RBAC 对齐守卫缺失，无法自动核对角色、权限点与鉴权语义。",
    ),
    "state-machine-alignment": GuardSpec(
        "state-machine-alignment",
        "P0",
        "state_machine_guard.py",
        "研发",
        True,
        "high",
        "状态机守卫缺失，无法自动核对状态集合、流转边与按钮策略。",
    ),
    "error-code-governor": GuardSpec(
        "error-code-governor",
        "P0",
        "error_code_guard.py",
        "研发",
        True,
        "high",
        "错误码守卫缺失，无法自动核对异常映射与前后端错误语义。",
    ),
    "ux-state-completeness-checker": GuardSpec(
        "ux-state-completeness-checker",
        "P1",
        "ux_state_completeness_guard.py",
        "产品",
        True,
        "medium",
        "页面状态完整性守卫缺失，需人工补齐加载态、空态、错态与禁用态检查。",
    ),
    "architecture-decision-recorder": GuardSpec(
        "architecture-decision-recorder",
        "P1",
        "architecture_decision_recorder_guard.py",
        "架构",
        True,
        "high",
        "架构决策守卫缺失，无法自动检查技术方案、约束与 ADR 记录。",
    ),
    "tech-stack-drift-guard": GuardSpec(
        "tech-stack-drift-guard",
        "P1",
        "tech_stack_drift_guard.py",
        "架构",
        True,
        "high",
        "技术栈漂移守卫缺失，无法自动检查新依赖、新框架与构建链路变化。",
    ),
    "git-flow-enforcer": GuardSpec(
        "git-flow-enforcer",
        "P1",
        "git_flow_enforcer.py",
        "研发",
        True,
        "medium",
        "Git 流程守卫缺失，需人工确认分支、提交与协作规则。",
    ),
    "app-security-baseline-guard": GuardSpec(
        "app-security-baseline-guard",
        "P1",
        "app_security_baseline_guard.py",
        "安全",
        True,
        "medium",
        "安全基线守卫缺失，需人工确认鉴权、输入校验与敏感日志要求。",
    ),
    "question-bank-contract-enforcer": GuardSpec(
        "question-bank-contract-enforcer",
        "P1",
        "question_bank_contract_guard.py",
        "研发",
        True,
        "medium",
        "题库固定契约守卫缺失，题库模式下需人工确认固定响应包、extJson 与模块边界。",
    ),
}

DEFAULT_SEQUENCE = [
    "requirements-freeze-guard",
    "acceptance-criteria-builder",
    "prd-ui-traceability-guard",
    "api-schema-drift-checker",
    "rbac-alignment-guard",
    "state-machine-alignment",
    "error-code-governor",
    "ux-state-completeness-checker",
    "architecture-decision-recorder",
    "tech-stack-drift-guard",
    "git-flow-enforcer",
    "app-security-baseline-guard",
]

QUESTION_BANK_SEQUENCE = ["question-bank-contract-enforcer"]
CREATE_TABLE_NAME_RE = re.compile(r'CREATE TABLE IF NOT EXISTS\s+("?[\w]+"?)\s*\(', re.IGNORECASE)
CREATE_UNIQUE_INDEX_RE = re.compile(
    r'CREATE\s+UNIQUE\s+INDEX(?:\s+IF\s+NOT\s+EXISTS)?\s+"?[\w]+"?\s+ON\s+("?[\w]+"?)\s*\((.*?)\);',
    re.IGNORECASE | re.DOTALL,
)


def run_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, check=False)


def available_skill_roots() -> list[Path]:
    roots = [LOCAL_SKILLS_ROOT]
    if GLOBAL_SKILLS_ROOT.exists():
        roots.append(GLOBAL_SKILLS_ROOT)
    return roots


def resolve_script(spec: GuardSpec) -> Path | None:
    for root in available_skill_roots():
        candidate = root / spec.name / "scripts" / spec.script_name
        if candidate.exists():
            return candidate
    return None


def derive_mode(mode: str, task: str, changed_files: list[Path], qb_module: str) -> str:
    if mode != "auto":
        return mode
    if qb_module:
        return "questionBank"
    task_text = task.lower()
    if any(hint in task_text for hint in QUESTION_BANK_HINTS):
        return "questionBank"
    for path in changed_files:
        normalized = path.as_posix().lower()
        if any(hint in normalized for hint in QUESTION_BANK_HINTS):
            return "questionBank"
    return "global"


def read_repo_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def parse_schema_tables(schema_text: str) -> set[str]:
    return {match.group(1).strip('"').lower() for match in CREATE_TABLE_NAME_RE.finditer(schema_text)}


def parse_unique_constraints(schema_text: str) -> list[tuple[str, str]]:
    constraints: list[tuple[str, str]] = []
    for table_name, clause in CREATE_UNIQUE_INDEX_RE.findall(schema_text):
        constraints.append((table_name.strip('"').lower(), clause.lower()))
    return constraints


def collect_token_hits(file_texts: dict[str, str], token_specs: tuple[tuple[str, tuple[str, ...]], ...]) -> list[str]:
    hits: list[str] = []
    for relative_path, tokens in token_specs:
        text = file_texts.get(relative_path, "")
        matched = [token for token in tokens if token in text]
        if matched:
            hits.append(f"{relative_path} -> {', '.join(matched)}")
    return hits


def schema_has_any_table(schema_tables: set[str], candidates: tuple[str, ...]) -> bool:
    return any(candidate in schema_tables for candidate in candidates)


def schema_has_unique_constraint(
    unique_constraints: list[tuple[str, str]],
    table_candidates: tuple[str, ...],
    token_candidates: tuple[str, ...],
) -> bool:
    tables = {item.lower() for item in table_candidates}
    tokens = tuple(item.lower() for item in token_candidates)
    for table_name, clause in unique_constraints:
        if table_name in tables and any(token in clause for token in tokens):
            return True
    return False


def build_data_model_constraint_warnings(cwd: Path) -> list[WarningItem]:
    schema_text = read_repo_text(cwd / "data/schema.sql")
    schema_tables = parse_schema_tables(schema_text)
    unique_constraints = parse_unique_constraints(schema_text)
    file_texts = {
        "app/repository.py": read_repo_text(cwd / "app/repository.py"),
        "app/service_modules/internal_student.py": read_repo_text(cwd / "app/service_modules/internal_student.py"),
        "app/service_modules/internal_system_admin.py": read_repo_text(cwd / "app/service_modules/internal_system_admin.py"),
        "app/service_modules/messages.py": read_repo_text(cwd / "app/service_modules/messages.py"),
    }
    warnings: list[WarningItem] = []

    student_records_hits = collect_token_hits(
        file_texts,
        (
            ("app/repository.py", ("studentRecords", "_save_student_records_map", "json_each(u.extJson, '$.studentRecords')")),
        ),
    )
    paper_reports_hits = collect_token_hits(
        file_texts,
        (
            ("app/service_modules/internal_student.py", ('system_state["paperReports"]',)),
            ("app/service_modules/internal_system_admin.py", ('return list(self._load_system_state()["paperReports"])',)),
        ),
    )
    message_history_hits = collect_token_hits(
        file_texts,
        (
            ("app/service_modules/messages.py", ('system_state["messageSendHistory"]', 'system_state.get("messageSendHistory", [])')),
            ("app/service_modules/internal_system_admin.py", ('return list(self._load_system_state().get("messageSendHistory", []))',)),
        ),
    )

    hot_state_findings: list[str] = []
    if student_records_hits:
        hot_state_findings.append("studentRecords")
    if paper_reports_hits:
        hot_state_findings.append("paperReports")
    if message_history_hits:
        hot_state_findings.append("messageSendHistory")
    if hot_state_findings:
        warnings.append(
            WarningItem(
                "extjson-hot-business-state",
                "high",
                f"检测到 {', '.join(hot_state_findings)} 仍通过 extJson 整块读改写；按设计约束，extJson 不再承载高频业务状态。",
                "app/repository.py",
            )
        )

    concurrent_state_gaps: list[str] = []
    if student_records_hits and not schema_has_any_table(schema_tables, ("student_question_record", "student_record", "student_answer_record")):
        concurrent_state_gaps.append("studentRecords 未拆成专表")
    if paper_reports_hits and not schema_has_any_table(schema_tables, ("student_paper_report", "paper_report", "paper_reports")):
        concurrent_state_gaps.append("paperReports 未拆成专表")
    if message_history_hits and not schema_has_any_table(schema_tables, ("message_send_history", "message_send_log", "message_delivery_log")):
        concurrent_state_gaps.append("messageSendHistory 未拆成专表")
    if concurrent_state_gaps:
        warnings.append(
            WarningItem(
                "concurrent-state-without-table",
                "high",
                f"检测到需要并发写安全的状态仍未入表：{'; '.join(concurrent_state_gaps)}。设计阶段必须先完成实体建模，再进入实施。",
                "data/schema.sql",
            )
        )

    if paper_reports_hits and not schema_has_unique_constraint(
        unique_constraints,
        ("student_paper_report", "paper_report", "paper_reports"),
        ("reportid", "requestid", "idempotencykey"),
    ):
        warnings.append(
            WarningItem(
                "idempotent-write-without-unique",
                "high",
                "检测到 paper report 写路径使用 reportId 风格去重，但数据库未见对应专表唯一约束；任何需要幂等的写接口必须先落实数据库唯一约束。",
                "data/schema.sql",
            )
        )

    reporting_gaps: list[str] = []
    if student_records_hits and not schema_has_any_table(schema_tables, ("student_question_record", "student_record", "student_answer_record")):
        reporting_gaps.append("studentRecords 仍通过 JSON 做筛选/报表")
    if paper_reports_hits and not schema_has_any_table(schema_tables, ("student_paper_report", "paper_report", "paper_reports")):
        reporting_gaps.append("paperReports 仍只存 JSON")
    if message_history_hits and not schema_has_any_table(schema_tables, ("message_send_history", "message_send_log", "message_delivery_log")):
        reporting_gaps.append("messageSendHistory 仍只存 JSON")
    if reporting_gaps:
        warnings.append(
            WarningItem(
                "reporting-data-json-only",
                "high",
                f"检测到报告/列表型数据仍只存 JSON：{'; '.join(reporting_gaps)}。凡是要分页、统计、筛选的数据必须在设计时落成可查询表结构。",
                "app/repository.py",
            )
        )

    return warnings


def build_core_warnings(cwd: Path, changed_files: list[Path], task: str, mode: str) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    normalized = [path.as_posix().lower() for path in changed_files]
    has_code = any(
        any(token in item for token in ("/app/", "/static/", "/templates/", "/src/", "/backend/", "/frontend/"))
        for item in normalized
    )
    has_docs = any("/docs/" in item or item.endswith(".md") for item in normalized)
    has_db = any(any(token in item for token in ("schema", ".sql", "migration", "models.py", "repository.py")) for item in normalized)
    has_ui = any(any(token in item for token in ("/templates/", "/static/", ".css", ".html", ".tsx", ".jsx")) for item in normalized)
    has_auth = any(any(token in item for token in ("auth", "permission", "role", "rbac", "scope")) for item in normalized)

    if not changed_files and not task:
        warnings.append(WarningItem("no-scope", "medium", "未提供任务描述，也未检测到改动文件，开发前准备范围不清晰。"))
    if has_code and not has_docs:
        warnings.append(WarningItem("code-without-readiness-docs", "medium", "检测到实现相关改动，但未看到配套的开发前准备文档或清单。"))
    if has_db and not has_docs:
        warnings.append(WarningItem("db-without-model-docs", "medium", "检测到数据库/模型相关改动，但未看到字段语义、实体关系或建模说明。"))
    if has_ui and not has_docs:
        warnings.append(WarningItem("ui-without-standard-docs", "medium", "检测到页面或交互相关改动，但未看到视觉/交互标准说明。"))
    if has_auth and not has_docs:
        warnings.append(WarningItem("auth-without-scope-docs", "medium", "检测到权限相关改动，但未看到角色、权限点或数据作用域说明。"))
    if mode == "questionBank":
        warnings.append(WarningItem("question-bank-mode", "low", "当前处于题库固定契约模式，将额外核对响应包、extJson 与模块边界。"))
    warnings.extend(build_data_model_constraint_warnings(cwd))
    return dedupe_warnings(warnings)


def extra_args_for(spec_name: str, args: argparse.Namespace) -> list[str]:
    extra: list[str] = []
    if spec_name == "api-schema-drift-checker":
        if args.api_openapi:
            extra.extend(["--api-openapi", args.api_openapi])
        if args.api_producer:
            extra.extend(["--api-producer", args.api_producer])
        if args.api_consumer:
            extra.extend(["--api-consumer", args.api_consumer])
        if args.api_alias_map:
            extra.extend(["--api-alias-map", args.api_alias_map])
        if args.api_strip_prefix:
            extra.extend(["--api-strip-prefix", args.api_strip_prefix])
    elif spec_name == "rbac-alignment-guard":
        if args.rbac_role:
            extra.extend(["--rbac-role", args.rbac_role])
        if args.rbac_permission_key:
            extra.extend(["--rbac-permission-key", args.rbac_permission_key])
        if args.rbac_force:
            extra.append("--rbac-force")
    elif spec_name == "state-machine-alignment":
        if args.sm_state:
            extra.extend(["--sm-state", args.sm_state])
        if args.sm_transition:
            extra.extend(["--sm-transition", args.sm_transition])
        if args.sm_force:
            extra.append("--sm-force")
    elif spec_name == "error-code-governor":
        if args.ec_code:
            extra.extend(["--ec-code", args.ec_code])
        if args.ec_namespace:
            extra.extend(["--ec-namespace", args.ec_namespace])
        if args.ec_force:
            extra.append("--ec-force")
    elif spec_name == "question-bank-contract-enforcer":
        if args.qb_module:
            extra.extend(["--qb-module", args.qb_module])
        if args.qb_force:
            extra.append("--qb-force")
    return extra


def should_skip(spec_name: str, args: argparse.Namespace) -> bool:
    mapping = {
        "requirements-freeze-guard": args.skip_requirements_freeze_guard,
        "acceptance-criteria-builder": args.skip_acceptance_criteria_builder,
        "prd-ui-traceability-guard": args.skip_prd_ui_traceability_guard,
        "api-schema-drift-checker": args.skip_api_schema_guard,
        "rbac-alignment-guard": args.skip_rbac_guard,
        "state-machine-alignment": args.skip_state_machine_guard,
        "error-code-governor": args.skip_error_code_guard,
        "ux-state-completeness-checker": args.skip_ux_state_guard,
        "architecture-decision-recorder": args.skip_architecture_decision_guard,
        "tech-stack-drift-guard": args.skip_tech_stack_drift_guard,
        "git-flow-enforcer": args.skip_git_flow_enforcer,
        "app-security-baseline-guard": args.skip_app_security_baseline_guard,
        "question-bank-contract-enforcer": args.skip_question_bank_guard,
    }
    return mapping.get(spec_name, False)


def run_subguard(spec: GuardSpec, args: argparse.Namespace, cwd: Path, changed_files: list[Path]) -> SubGuardResult:
    if should_skip(spec.name, args):
        return SubGuardResult(spec, False, [], None, "Skipped", [], "skipped", "")

    script_path = resolve_script(spec)
    if not script_path:
        return SubGuardResult(spec, True, [], None, "", [], "missing", "")

    cmd = [sys.executable, str(script_path), "--phase", args.phase, "--cwd", str(cwd), "--fail-on", args.fail_on]
    if args.task:
        cmd.extend(["--task", args.task])
    for changed_file in changed_files:
        cmd.extend(["--changed-file", str(changed_file)])
    cmd.extend(extra_args_for(spec.name, args))
    result = run_cmd(cmd, cwd)
    output = (result.stdout or "").strip()
    runtime_warnings: list[str] = []
    if result.returncode != 0:
        runtime_warnings.append(f"{spec.name} 返回非零退出码 ({result.returncode})。")
    return SubGuardResult(spec, True, cmd, result.returncode, output, runtime_warnings, "ran", str(script_path))


def flatten_subguard_findings(results: list[SubGuardResult]) -> list[WarningItem]:
    findings: list[WarningItem] = []
    for result in results:
        spec = result.spec
        if result.status == "missing":
            findings.append(
                WarningItem(
                    code=f"{spec.name}-missing",
                    severity=spec.missing_severity,
                    message=spec.missing_message,
                    file=spec.name,
                )
            )
            continue
        for warning in result.runtime_warnings:
            findings.append(
                WarningItem(
                    code=f"{spec.name}-failed",
                    severity="high",
                    message=warning,
                    file=spec.name,
                )
            )
        for line in result.output.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- ["):
                continue
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
                    code=f"{spec.name}-finding",
                    severity=severity,
                    message=message,
                    file=spec.name,
                )
            )
    return dedupe_warnings(findings)


def layered_summary(warnings: list[WarningItem]) -> dict[str, list[str]]:
    p0_blockers: list[str] = []
    fix_before_coding: list[str] = []
    recommended_before_parallel: list[str] = []
    planned_manual: list[str] = []

    for item in warnings:
        file_name = item.file
        spec = GUARD_SPECS.get(file_name) if file_name else None
        level = spec.level if spec else "CORE"
        label = f"{file_name}: {item.message}" if file_name else item.message
        if item.code.endswith("-missing") and spec and not spec.implemented:
            planned_manual.append(label)
            continue
        if item.severity == "high" and level == "P0":
            p0_blockers.append(label)
        elif (item.severity == "medium" and level == "P0") or (item.severity == "high" and level == "P1"):
            fix_before_coding.append(label)
        else:
            recommended_before_parallel.append(label)

    return {
        "p0_blockers": list(dict.fromkeys(p0_blockers)),
        "fix_before_coding": list(dict.fromkeys(fix_before_coding)),
        "recommended_before_parallel": list(dict.fromkeys(recommended_before_parallel)),
        "planned_manual": list(dict.fromkeys(planned_manual)),
    }


def build_conclusion(layered: dict[str, list[str]]) -> tuple[str, str, str]:
    if layered["p0_blockers"]:
        return ("不建议进入开发", "BLOCK_BEFORE_CODING", "存在 P0 高风险缺口，当前不满足安全开工条件。")
    if layered["fix_before_coding"]:
        return ("建议补齐后进入开发", "FIX_THEN_START", "已发现应在编码前补齐的关键缺口，建议先收口再开工。")
    if layered["recommended_before_parallel"] or layered["planned_manual"]:
        return ("基本可进入开发", "START_WITH_VISIBLE_RISK", "未发现自动阻断项，但仍有建议项或人工补齐项需要跟踪。")
    return ("可进入开发", "READY_TO_START", "未发现阻断进入开发的高风险问题。")


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def detect_backend_stack(cwd: Path) -> str:
    if (cwd / "app" / "main.py").exists() and (cwd / "requirements.txt").exists():
        return "python-fastapi"
    return "unknown"


def detect_frontend_stack(cwd: Path) -> str:
    package_json = cwd / "frontend" / "package.json"
    if package_json.exists():
        text = package_json.read_text(encoding="utf-8", errors="ignore").lower()
        if '"vite"' in text and '"vue"' in text:
            return "vue-vite"
    if (cwd / "templates").exists() and (cwd / "static").exists():
        return "server-rendered-html-js"
    return "unknown"


def detect_database_stack(cwd: Path) -> str:
    if (cwd / "data" / "schema.sql").exists():
        return "sqlite"
    return "unknown"


def parse_python_dependencies(cwd: Path) -> list[str]:
    path = cwd / "requirements.txt"
    if not path.exists():
        return []
    deps: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-r "):
            continue
        name = line.split("==", 1)[0].split(">=", 1)[0].split("<=", 1)[0].strip()
        if name:
            deps.append(name)
    return sorted(dict.fromkeys(deps))


def parse_frontend_dependencies(cwd: Path) -> list[str]:
    path = cwd / "frontend" / "package.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    deps = list((payload.get("dependencies") or {}).keys())
    return sorted(dict.fromkeys(str(item) for item in deps))


def parse_contract_baselines(cwd: Path) -> dict[str, object]:
    path = cwd / "app" / "contracts.py"
    if not path.exists():
        return {"roles": [], "permissionKeys": [], "questionErrorCodes": [], "questionFields": [], "taskFields": []}
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, object] = {"roles": [], "permissionKeys": [], "questionErrorCodes": [], "questionFields": [], "taskFields": []}
    simple_assignments: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            try:
                simple_assignments[name] = ast.literal_eval(node.value)
            except Exception:
                pass
    role_names = []
    for key in ("ROLE_SUPER_ADMIN", "ROLE_TEACHER", "ROLE_STUDENT"):
        value = simple_assignments.get(key)
        if isinstance(value, str):
            role_names.append(value)
    found["roles"] = role_names
    permissions = simple_assignments.get("MANAGED_PERMISSION_KEYS")
    if isinstance(permissions, tuple):
        found["permissionKeys"] = [str(item) for item in permissions]
    error_codes = simple_assignments.get("QUESTION_ERROR_CODES")
    if isinstance(error_codes, dict):
        found["questionErrorCodes"] = list(error_codes.values())
    for source_name, target_key in (("QUESTION_FIELDS", "questionFields"), ("TASK_FIELDS", "taskFields")):
        values = simple_assignments.get(source_name)
        if isinstance(values, tuple):
            found[target_key] = [str(item) for item in values]
    return found


def infer_affected_layers(changed_files: list[Path]) -> list[str]:
    layers: list[str] = []
    normalized = [path.as_posix().lower() for path in changed_files]
    if any("/data/" in item or item.endswith(".sql") for item in normalized):
        layers.append("database")
    if any("/app/" in item for item in normalized):
        layers.append("backend")
    if any("/templates/" in item or "/static/" in item or "/frontend/" in item for item in normalized):
        layers.append("frontend")
    if any("/docs/" in item or item.endswith(".md") for item in normalized):
        layers.append("docs")
    if any("/tests/" in item or "/tools/python/" in item for item in normalized):
        layers.append("tests")
    if any("/app/main.py" in item or "/app/contracts.py" in item or "/app/models.py" in item for item in normalized):
        layers.append("api")
    return layers or ["database", "backend", "api", "frontend", "docs", "tests"]


def infer_scope_modules(mode: str, qb_module: str, changed_files: list[Path]) -> list[str]:
    if mode == "questionBank":
        if qb_module:
            return [qb_module]
        hits: list[str] = []
        normalized = [path.as_posix().lower() for path in changed_files]
        for module_name in QUESTION_BANK_MODULES:
            if any(module_name.lower() in item for item in normalized):
                hits.append(module_name)
        return hits or list(QUESTION_BANK_MODULES)
    inferred: list[str] = []
    for path in changed_files:
        normalized = path.as_posix().lower()
        if "/messages" in normalized:
            inferred.append("messages")
        elif "/knowledge" in normalized:
            inferred.append("knowledge")
        elif "/paper" in normalized or "/question" in normalized:
            inferred.append("question")
        elif "/auth" in normalized or "/user" in normalized:
            inferred.append("user")
    return sorted(dict.fromkeys(inferred)) or ["global"]


def infer_out_of_scope_modules(mode: str, in_scope_modules: list[str]) -> list[str]:
    if mode != "questionBank":
        return []
    return [module for module in QUESTION_BANK_MODULES if module not in in_scope_modules]


def build_question_bank_module_summary(in_scope_modules: list[str]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for module_name in QUESTION_BANK_MODULES:
        summary.append(
            {
                "module": module_name,
                "scope": "IN_SCOPE" if module_name in in_scope_modules else "OUT_OF_SCOPE",
                "responseEnvelope": ["code", "message", "data"],
                "extJsonPolicy": "contract-outside-fields-go-to-extJson",
                "idOnlyRelations": True,
            }
        )
    return summary


def build_contract_package(
    *,
    mode: str,
    task: str,
    cwd: Path,
    changed_files: list[Path],
    payload: dict[str, object],
    in_scope_modules: list[str],
) -> dict[str, object]:
    baselines = parse_contract_baselines(cwd)
    return {
        "contractVersion": "v1",
        "contractId": f"dr-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}",
        "generatedAt": now_iso(),
        "generatedBy": "software-development-readiness-governance",
        "phase": "development-readiness",
        "mode": mode,
        "projectProfile": {
            "name": cwd.name,
            "repoRoot": str(cwd),
            "backendStack": detect_backend_stack(cwd),
            "frontendStack": detect_frontend_stack(cwd),
            "database": detect_database_stack(cwd),
            "primaryGuard": "fullstack-unified-development-standards",
            "pythonDependencies": parse_python_dependencies(cwd),
            "frontendDependencies": parse_frontend_dependencies(cwd),
        },
        "scope": {
            "businessGoal": task or "开发前统一冻结本轮需求与实现约束",
            "inScopeModules": in_scope_modules,
            "outOfScopeModules": infer_out_of_scope_modules(mode, in_scope_modules),
            "affectedLayers": infer_affected_layers(changed_files),
            "actors": baselines.get("roles", []),
            "changedFilesCount": len(changed_files),
        },
        "contracts": {
            "fieldDictionary": {
                "questionFields": baselines.get("questionFields", []),
                "taskFields": baselines.get("taskFields", []),
            },
            "api": {
                "responseEnvelope": ["code", "message", "data"] if mode == "questionBank" else [],
                "paginationEnvelope": ["items", "page", "size", "total"],
            },
            "permissions": {
                "roles": baselines.get("roles", []),
                "permissionKeys": baselines.get("permissionKeys", []),
            },
            "errorSemantics": {
                "questionErrorCodes": baselines.get("questionErrorCodes", []),
            },
            "uiStandards": {
                "feedback": ["Toast", "message-box"],
                "containers": ["Drawer", "modal"],
                "filterRule": "Advanced Filter after 3 fields",
                "states": ["loading", "empty", "error", "disabled", "confirm"],
            },
            "questionBankModules": build_question_bank_module_summary(in_scope_modules) if mode == "questionBank" else [],
        },
        "governance": {
            "readinessStatus": payload["extra"]["status"],
            "action": payload["extra"]["action"],
            "reason": payload["extra"]["reason"],
            "subguards": payload["extra"]["subguards"],
            "references": [
                "docs/skills/software-development-readiness-governance/references/shared-contract-package.md",
                "docs/skills/software-development-readiness-governance/references/stage-invocation-templates.md",
            ],
        },
        "testPlan": {
            "categories": ["normal", "exception", "boundary", "permission", "state", "api", "frontend"],
            "automationTargets": ["pytest-unit", "pytest-integration", "pytest-regression", "playwright-e2e"],
            "mustCoverModules": in_scope_modules,
        },
        "releaseReadiness": {
            "rollbackRequired": True,
            "monitoringRequired": True,
            "uatRequired": True,
        },
        "waivers": [],
    }


def render_contract_markdown(package: dict[str, object]) -> str:
    scope = package["scope"]
    governance = package["governance"]
    lines = [
        "# Development Readiness Contract",
        "",
        f"- Contract ID: `{package['contractId']}`",
        f"- Generated At: `{package['generatedAt']}`",
        f"- Mode: `{package['mode']}`",
        f"- Business Goal: {scope['businessGoal']}",
        f"- In Scope Modules: `{', '.join(scope['inScopeModules']) or 'none'}`",
        f"- Out Of Scope Modules: `{', '.join(scope['outOfScopeModules']) or 'none'}`",
        f"- Affected Layers: `{', '.join(scope['affectedLayers'])}`",
        f"- Readiness Status: `{governance['readinessStatus']}`",
        f"- Action: `{governance['action']}`",
        f"- Reason: {governance['reason']}",
        "",
        "## Implementation Baselines",
        f"- Roles: `{', '.join(package['contracts']['permissions']['roles']) or 'none'}`",
        f"- Permission Keys: `{', '.join(package['contracts']['permissions']['permissionKeys']) or 'none'}`",
        f"- Question Error Codes: `{', '.join(package['contracts']['errorSemantics']['questionErrorCodes']) or 'none'}`",
        f"- UI Feedback: `{', '.join(package['contracts']['uiStandards']['feedback'])}`",
        f"- Automation Targets: `{', '.join(package['testPlan']['automationTargets'])}`",
    ]
    if package["mode"] == "questionBank":
        lines.extend(["", "## questionBank Modules"])
        for item in package["contracts"]["questionBankModules"]:
            lines.append(f"- `{item['module']}`: `{item['scope']}` / extJson=`{item['extJsonPolicy']}`")
    return "\n".join(lines)


def render_test_plan_markdown(package: dict[str, object]) -> str:
    lines = [
        "# Development Readiness Test Plan",
        "",
        "## Categories",
    ]
    lines.extend([f"- `{item}`" for item in package["testPlan"]["categories"]])
    lines.extend(["", "## Automation Targets"])
    lines.extend([f"- `{item}`" for item in package["testPlan"]["automationTargets"]])
    lines.extend(["", "## Must Cover Modules"])
    lines.extend([f"- `{item}`" for item in package["testPlan"]["mustCoverModules"]])
    return "\n".join(lines)


def render_module_summary_markdown(package: dict[str, object]) -> str:
    if package["mode"] != "questionBank":
        return "# Module Summary\n\n- `global` 模式下不输出题库五模块摘要。"
    lines = ["# questionBank Module Summary", ""]
    for item in package["contracts"]["questionBankModules"]:
        lines.append(
            f"- `{item['module']}`: `{item['scope']}` / responseEnvelope=`{', '.join(item['responseEnvelope'])}` / idOnlyRelations=`{item['idOnlyRelations']}`"
        )
    return "\n".join(lines)


def emit_contract_package(cwd: Path, package: dict[str, object], contract_dir: Path) -> None:
    contract_dir.mkdir(parents=True, exist_ok=True)
    write_json_report(str(contract_dir / "contract.json"), package)
    write_report(str(contract_dir / "contract.md"), render_contract_markdown(package))
    write_report(str(contract_dir / "test-plan.md"), render_test_plan_markdown(package))
    write_report(str(contract_dir / "module-summary.md"), render_module_summary_markdown(package))
    write_json_report(str(contract_dir / "waivers.json"), {"waivers": []})


def render_full_report(
    phase: str,
    mode: str,
    cwd: Path,
    threshold: str,
    changed_files: list[Path],
    warnings: list[WarningItem],
    results: list[SubGuardResult],
) -> str:
    base = render_guard_report("Development Readiness Guard", phase, cwd, threshold, changed_files, warnings)
    layered = layered_summary(warnings)
    status, action, reason = build_conclusion(layered)
    summary = summarize_warnings(warnings)
    lines = [
        base,
        "",
        "Readiness conclusion:",
        f"  - Mode: {mode}",
        f"  - Status: {status}",
        f"  - Action: {action}",
        f"  - Reason: {reason}",
        f"  - Totals: {summary['high']} high / {summary['medium']} medium / {summary['low']} low",
    ]
    for title, items in (
        ("P0 blockers", layered["p0_blockers"]),
        ("Fix before coding", layered["fix_before_coding"]),
        ("Recommended before parallel work", layered["recommended_before_parallel"]),
        ("Planned manual checks", layered["planned_manual"]),
    ):
        lines.append(f"{title}:")
        if items:
            lines.extend([f"  - {item}" for item in items])
        else:
            lines.append("  - none")

    lines.append("Subguards:")
    for result in results:
        location = f" @ {result.script_path}" if result.script_path else ""
        lines.append(
            f"  - [{result.spec.level}] {result.spec.name}: {result.status}{location}"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="软件开发前准备总守卫")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--mode", choices=("auto", "global", "questionBank"), default="auto")
    parser.add_argument("--qb-module", default="")
    parser.add_argument("--qb-force", action="store_true")
    parser.add_argument("--api-openapi", default="")
    parser.add_argument("--api-producer", default="")
    parser.add_argument("--api-consumer", default="")
    parser.add_argument("--api-alias-map", default="")
    parser.add_argument("--api-strip-prefix", default="")
    parser.add_argument("--rbac-role", default="")
    parser.add_argument("--rbac-permission-key", default="")
    parser.add_argument("--rbac-force", action="store_true")
    parser.add_argument("--sm-state", default="")
    parser.add_argument("--sm-transition", default="")
    parser.add_argument("--sm-force", action="store_true")
    parser.add_argument("--ec-code", default="")
    parser.add_argument("--ec-namespace", default="")
    parser.add_argument("--ec-force", action="store_true")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--contract-dir", default="")
    parser.add_argument("--skip-contract-package", action="store_true")

    parser.add_argument("--skip-requirements-freeze-guard", action="store_true")
    parser.add_argument("--skip-acceptance-criteria-builder", action="store_true")
    parser.add_argument("--skip-prd-ui-traceability-guard", action="store_true")
    parser.add_argument("--skip-api-schema-guard", action="store_true")
    parser.add_argument("--skip-rbac-guard", action="store_true")
    parser.add_argument("--skip-state-machine-guard", action="store_true")
    parser.add_argument("--skip-error-code-guard", action="store_true")
    parser.add_argument("--skip-ux-state-guard", action="store_true")
    parser.add_argument("--skip-architecture-decision-guard", action="store_true")
    parser.add_argument("--skip-tech-stack-drift-guard", action="store_true")
    parser.add_argument("--skip-git-flow-enforcer", action="store_true")
    parser.add_argument("--skip-app-security-baseline-guard", action="store_true")
    parser.add_argument("--skip-question-bank-guard", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).resolve()
    changed_files = collect_changed_files(cwd, args.changed_file)
    threshold = compute_threshold(args.phase, args.fail_on)
    mode = derive_mode(args.mode, args.task, changed_files, args.qb_module)
    sequence = list(DEFAULT_SEQUENCE)
    if mode == "questionBank":
        sequence.extend(QUESTION_BANK_SEQUENCE)

    results = [run_subguard(GUARD_SPECS[name], args, cwd, changed_files) for name in sequence]
    core_warnings = build_core_warnings(cwd, changed_files, args.task, mode)
    warnings = dedupe_warnings(core_warnings + flatten_subguard_findings(results))
    report = render_full_report(args.phase, mode, cwd, threshold, changed_files, warnings, results)
    print(report)

    layered = layered_summary(warnings)
    status, action, reason = build_conclusion(layered)
    payload = standard_guard_payload(
        guard_name="software-development-readiness-governance",
        phase=args.phase,
        cwd=cwd,
        threshold=threshold,
        changed_files=changed_files,
        warnings=warnings,
        extra={
            "mode": mode,
            "status": status,
            "action": action,
            "reason": reason,
            "subguards": [
                {
                    "name": result.spec.name,
                    "level": result.spec.level,
                    "implemented": result.spec.implemented,
                    "status": result.status,
                    "returncode": result.returncode,
                    "scriptPath": result.script_path,
                }
                for result in results
            ],
            "layeredSummary": layered,
        },
    )
    write_report(args.report_md, report)
    write_json_report(args.report_json, payload)
    if not args.skip_contract_package:
        contract_dir = Path(args.contract_dir).resolve() if args.contract_dir else (cwd / "docs" / "contracts" / "current")
        if args.phase == "final" or args.contract_dir:
            in_scope_modules = infer_scope_modules(mode, args.qb_module, changed_files)
            contract_package = build_contract_package(
                mode=mode,
                task=args.task,
                cwd=cwd,
                changed_files=changed_files,
                payload=payload,
                in_scope_modules=in_scope_modules,
            )
            emit_contract_package(cwd, contract_package, contract_dir)
    return 1 if any(warning_meets_threshold(item.severity, threshold) for item in warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
