#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


EXPECTED_QUESTION_FIELDS = (
    "id",
    "knowledgeId",
    "userId",
    "type",
    "stem",
    "optionsJson",
    "answer",
    "status",
    "extJson",
    "createTime",
    "updateTime",
)

EXPECTED_TASK_FIELDS = (
    "id",
    "userId",
    "type",
    "status",
    "progress",
    "extJson",
    "createTime",
    "updateTime",
)

EXPECTED_QUESTION_BANK_MODULE_FIELDS = {
    "user": (
        "id",
        "phone",
        "password",
        "status",
        "extJson",
        "createTime",
        "updateTime",
    ),
    "userAuth": (
        "id",
        "userId",
        "type",
        "openid",
        "unionid",
        "extJson",
        "createTime",
        "updateTime",
    ),
    "knowledge": (
        "id",
        "parentId",
        "name",
        "sort",
        "status",
        "extJson",
        "createTime",
        "updateTime",
    ),
    "question": EXPECTED_QUESTION_FIELDS,
    "task": EXPECTED_TASK_FIELDS,
}

EXPECTED_SUCCESS_KEYS = ("code", "message", "data")
EXPECTED_PAGINATION_KEYS = ("items", "page", "size", "total")
EXPECTED_QUESTION_STATUSES = (
    "DRAFT",
    "QA_IN_PROGRESS",
    "REVIEW_PENDING",
    "PUBLISHED",
    "REJECTED",
)
EXPECTED_ALLOWED_TRANSITIONS = {
    "DRAFT": {"QA_IN_PROGRESS", "REVIEW_PENDING", "REJECTED"},
    "QA_IN_PROGRESS": {"REVIEW_PENDING", "REJECTED"},
    "REVIEW_PENDING": {"PUBLISHED", "REJECTED"},
    "REJECTED": {"DRAFT"},
    "PUBLISHED": set(),
}
EXPECTED_ALL_ROLES = (
    "super_admin",
    "teacher",
    "student",
)
EXPECTED_MANAGED_PERMISSION_KEYS = (
    "question:manage",
    "paper:manage",
    "analytics:view",
    "student:manage",
    "settings:manage",
    "message:send",
)
EXPECTED_QUESTION_ERROR_CODES = {
    "NOT_FOUND": "QUESTION_NOT_FOUND",
    "FORBIDDEN": "QUESTION_FORBIDDEN",
    "VALIDATION_FAILED": "QUESTION_VALIDATION_FAILED",
    "INVALID_STATUS": "QUESTION_INVALID_STATUS",
    "DATABASE_ERROR": "QUESTION_DATABASE_ERROR",
}

EXPECTED_BOOTSTRAP_PAGE_ROUTES = (
    "/",
    "/teacher/questions",
    "/login",
    "/student/practice",
    "/student/home",
    "/student/wrong-book",
    "/student/personal-bank",
    "/teacher/papers",
    "/teacher/analytics",
    "/teacher/content-system",
    "/teacher/knowledge",
    "/admin/control-center",
    "/messages",
)

QUESTION_PAGE_TOKENS = (
    "knowledgeId",
    "userId",
    "type",
    "stem",
    "optionsJson",
    "answer",
    "status",
    "extJson",
    "createTime",
    "updateTime",
)

ACTIVE_FRONTEND_FILES = (
    "frontend/index.html",
    "frontend/src/main.js",
    "frontend/src/entries/bootstrap.js",
    "frontend/src/entries/main-student.js",
    "frontend/src/entries/main-teacher.js",
    "frontend/src/router/index.js",
    "frontend/src/router/studentRoutes.js",
    "frontend/src/router/teacherRoutes.js",
    "frontend/src/views/Teacher/QuestionManagement.vue",
    "frontend/src/views/Auth/Login.vue",
    "frontend/src/views/System/Messages.vue",
)

AUXILIARY_FRONTEND_FILES = (
    "frontend/src/views/Student/Practice.vue",
    "frontend/src/views/Teacher/Papers.vue",
    "frontend/src/views/Teacher/Analytics.vue",
)

TEN_DOMAIN_SPECS = (
    ("field", "Field Standards"),
    ("api", "API Standards"),
    ("page", "Page Standards"),
    ("status", "Status Standards"),
    ("permission", "Permission Standards"),
    ("validation", "Validation Standards"),
    ("error", "Error Standards"),
    ("extension", "Extension Standards"),
    ("documentation", "Documentation Standards"),
    ("test", "Test Standards"),
)

LOWER_CAMEL_RE = re.compile(r"^[a-z]+(?:[A-Z][a-zA-Z0-9]*)*$")
CREATE_TABLE_RE = re.compile(r"CREATE TABLE IF NOT EXISTS\s+([\"A-Za-z_][A-Za-z0-9_\"]*)\s*\((.*?)\);", re.DOTALL)
CREATE_UNIQUE_INDEX_RE = re.compile(
    r"CREATE\s+UNIQUE\s+INDEX(?:\s+IF\s+NOT\s+EXISTS)?\s+[\"A-Za-z_][A-Za-z0-9_\"]*\s+ON\s+([\"A-Za-z_][A-Za-z0-9_\"]*)\s*\((.*?)\);",
    re.IGNORECASE | re.DOTALL,
)
STALE_PASSED_COUNT_RE = re.compile(r"\b\d+\s+passed\b", re.IGNORECASE)
FRONTEND_SNAKE_CASE_EXPORT_RE = re.compile(r"export\s+(?:async\s+)?function\s+([a-z]+_[a-z0-9_]+)\s*\(")
FRONTEND_EXPORT_FUNCTION_RE = re.compile(r"export\s+(?:async\s+)?function\s+([A-Za-z][A-Za-z0-9_]*)\s*\(([^)]*)\)")
SNAKE_CASE_IDENTIFIER_RE = re.compile(r"^[a-z]+(?:_[a-z0-9]+)+$")
RAW_HEX_COLOR_RE = re.compile(r"(?<!var\()#(?:[A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})(?![A-Fa-f0-9])")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"^\s*//.*$", re.MULTILINE)
CSS_VAR_HEX_DEF_RE = re.compile(
    r"--[A-Za-z_][A-Za-z0-9_-]*\s*:\s*#(?:[A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})(?![A-Fa-f0-9])"
)
DEPRECATED_TIME_FIELD_NAMES = (
    "created" "At",
    "updated" "At",
)
DEPRECATED_TIME_FIELD_RE = re.compile(r"\b(" + "|".join(DEPRECATED_TIME_FIELD_NAMES) + r")\b")

DISALLOWED_COMPAT_SNAKE_KEYS = (
    "assignment_id",
    "question_id",
    "target_status",
    "paper_id",
    "paper_status",
    "template_id",
    "snapshot_id",
    "task_id",
    "session_id",
    "report_id",
    "message_id",
    "trace_id",
    "thread_id",
    "attachment_id",
    "knowledge_id",
    "question_ids",
    "student_user_id",
    "source_type",
    "attempt_id",
    "attempt_key",
    "submission_id",
    "point_code",
    "chapter_code",
    "knowledge_path_node_id",
)
DISALLOWED_COMPAT_KEY_ACCESS_RE = re.compile(
    r"\.(?:get|pop)\(\s*\"(" + "|".join(sorted((re.escape(item) for item in DISALLOWED_COMPAT_SNAKE_KEYS), key=len, reverse=True)) + r")\"\s*(?:,|\))"
)


@dataclass
class CheckResult:
    domain: str
    name: str
    ok: bool
    detail: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate unified alignment across this repository.")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="", help="Task summary recorded during the start or final guard phase.")
    parser.add_argument("--mode", choices=("auto", "global", "questionBank"), default="auto")
    parser.add_argument("--run-compile", action="store_true", help="Run py_compile against app/*.py.")
    parser.add_argument("--run-pytest", action="store_true", help="Run the canonical unit, integration, regression, and e2e suites after static checks.")
    parser.add_argument("--report-md", default="", help="Optional Markdown report path.")
    parser.add_argument("--report-json", default="", help="Optional JSON report path.")
    parser.add_argument("--waiver-file", default="", help="Optional waiver JSON file for time-boxed drift exemptions.")
    parser.add_argument("--contract-json", default="", help="Optional development readiness contract JSON path.")
    return parser.parse_args()


def parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def smart_extract_literals(node: ast.AST) -> object:
    try:
        return ast.literal_eval(node)
    except Exception:
        source = ast.unparse(node)
        return re.findall(r"['\"]([^'\"]+)['\"]", source)


def _is_enum_base(base: ast.expr) -> bool:
    if isinstance(base, ast.Name):
        return base.id in {"Enum", "StrEnum"}
    if isinstance(base, ast.Attribute):
        return base.attr in {"Enum", "StrEnum"}
    return False


def _collect_module_assignments(module: ast.Module) -> dict[str, ast.AST]:
    assignments: dict[str, ast.AST] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                assignments[target.id] = node.value
    return assignments


def _collect_enum_members(module: ast.Module) -> dict[str, tuple[dict[str, object], ...]]:
    enum_members: dict[str, tuple[dict[str, object], ...]] = {}
    for node in module.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_is_enum_base(base) for base in node.bases):
            continue
        members: list[dict[str, object]] = []
        for child in node.body:
            if not isinstance(child, ast.Assign):
                continue
            if len(child.targets) != 1 or not isinstance(child.targets[0], ast.Name):
                continue
            extracted = smart_extract_literals(child.value)
            if isinstance(extracted, list):
                if not extracted:
                    continue
                member_value = extracted[0]
            else:
                member_value = extracted
            if not isinstance(member_value, (str, int, float, bool)):
                continue
            members.append({"name": child.targets[0].id, "value": member_value})
        if members:
            enum_members[node.name] = tuple(members)
    return enum_members


def _bind_comprehension_target(target: ast.expr, value: object, scope: dict[str, object]) -> None:
    if isinstance(target, ast.Name):
        scope[target.id] = value
        return
    if isinstance(target, (ast.Tuple, ast.List)):
        if not isinstance(value, (tuple, list)):
            raise ValueError("Comprehension target expects a tuple/list value")
        if len(target.elts) != len(value):
            raise ValueError("Comprehension target/value length mismatch")
        for nested_target, nested_value in zip(target.elts, value):
            _bind_comprehension_target(nested_target, nested_value, scope)
        return
    raise ValueError(f"Unsupported comprehension target: {target.__class__.__name__}")


def _evaluate_ast_value(
    node: ast.AST,
    assignments: dict[str, ast.AST],
    enum_members: dict[str, tuple[dict[str, object], ...]],
    scope: dict[str, object],
    resolving: set[str],
) -> object:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Tuple):
        values: list[object] = []
        for element in node.elts:
            if isinstance(element, ast.Starred):
                starred = _evaluate_ast_value(element.value, assignments, enum_members, scope, resolving)
                if not isinstance(starred, (tuple, list, set)):
                    raise ValueError("Starred tuple element must resolve to an iterable")
                values.extend(list(starred))
                continue
            values.append(_evaluate_ast_value(element, assignments, enum_members, scope, resolving))
        return tuple(values)

    if isinstance(node, ast.List):
        values: list[object] = []
        for element in node.elts:
            if isinstance(element, ast.Starred):
                starred = _evaluate_ast_value(element.value, assignments, enum_members, scope, resolving)
                if not isinstance(starred, (tuple, list, set)):
                    raise ValueError("Starred list element must resolve to an iterable")
                values.extend(list(starred))
                continue
            values.append(_evaluate_ast_value(element, assignments, enum_members, scope, resolving))
        return values

    if isinstance(node, ast.Set):
        return {
            _evaluate_ast_value(element, assignments, enum_members, scope, resolving)
            for element in node.elts
        }

    if isinstance(node, ast.Name):
        if node.id in scope:
            return scope[node.id]
        if node.id in enum_members:
            return list(enum_members[node.id])
        if node.id in resolving:
            raise ValueError(f"Circular reference while resolving {node.id}")
        rhs = assignments.get(node.id)
        if rhs is None:
            raise ValueError(f"Name {node.id} is not resolvable from module assignments")
        resolving.add(node.id)
        try:
            return _evaluate_ast_value(rhs, assignments, enum_members, scope, resolving)
        finally:
            resolving.remove(node.id)

    if isinstance(node, ast.Attribute):
        base_value = _evaluate_ast_value(node.value, assignments, enum_members, scope, resolving)
        if isinstance(base_value, list):
            for item in base_value:
                if isinstance(item, dict) and str(item.get("name", "")) == node.attr:
                    return item
        if isinstance(base_value, dict) and node.attr in base_value:
            return base_value[node.attr]
        raise ValueError(f"Unsupported attribute access: .{node.attr}")

    if isinstance(node, ast.GeneratorExp):
        if len(node.generators) != 1:
            raise ValueError("Only single-generator comprehensions are supported")
        comprehension = node.generators[0]
        if comprehension.is_async:
            raise ValueError("Async comprehensions are not supported")
        if comprehension.ifs:
            raise ValueError("Comprehension if-clauses are not supported")
        iterable_value = _evaluate_ast_value(comprehension.iter, assignments, enum_members, scope, resolving)
        if not isinstance(iterable_value, (tuple, list, set)):
            raise ValueError("Comprehension iterable must resolve to tuple/list/set")
        generated: list[object] = []
        for item in iterable_value:
            nested_scope = dict(scope)
            _bind_comprehension_target(comprehension.target, item, nested_scope)
            generated.append(
                _evaluate_ast_value(node.elt, assignments, enum_members, nested_scope, resolving)
            )
        return generated

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in {"tuple", "list", "set"}:
            if len(node.args) != 1 or node.keywords:
                raise ValueError(f"Unsupported call signature for {node.func.id}")
            iterable_value = _evaluate_ast_value(node.args[0], assignments, enum_members, scope, resolving)
            if not isinstance(iterable_value, (tuple, list, set)):
                raise ValueError(f"{node.func.id}() argument must resolve to tuple/list/set")
            if node.func.id == "tuple":
                return tuple(iterable_value)
            if node.func.id == "list":
                return list(iterable_value)
            return set(iterable_value)
        raise ValueError("Only tuple/list/set constructor calls are supported")

    raise ValueError(f"Unsupported AST node: {node.__class__.__name__}")


def extract_tuple_constant(module: ast.Module, name: str) -> tuple[str, ...]:
    assignments = _collect_module_assignments(module)
    if name not in assignments:
        raise ValueError(f"Missing constant {name}")
    rhs = assignments[name]

    literal_value = smart_extract_literals(rhs)
    if isinstance(literal_value, tuple):
        return tuple(str(item) for item in literal_value)
    if isinstance(literal_value, list) and literal_value and all(isinstance(item, str) for item in literal_value):
        return tuple(str(item) for item in literal_value)

    resolved_value = _evaluate_ast_value(
        rhs,
        assignments=assignments,
        enum_members=_collect_enum_members(module),
        scope={},
        resolving={name},
    )
    if not isinstance(resolved_value, tuple):
        raise ValueError(f"{name} is not a tuple")
    return tuple(str(item) for item in resolved_value)


def extract_tuple_constant_resolved(module: ast.Module, name: str) -> tuple[str, ...]:
    scalar_strings: dict[str, str] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        target_name = node.targets[0].id
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            scalar_strings[target_name] = node.value.value

    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id != name:
            continue
        if not isinstance(node.value, ast.Tuple):
            raise ValueError(f"{name} is not a tuple")
        resolved: list[str] = []
        for element in node.value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                resolved.append(element.value)
                continue
            if isinstance(element, ast.Name) and element.id in scalar_strings:
                resolved.append(scalar_strings[element.id])
                continue
            raise ValueError(f"{name} contains a non-resolvable value")
        return tuple(resolved)
    raise ValueError(f"Missing constant {name}")


def extract_dict_keys_from_function(module: ast.Module, function_name: str) -> tuple[str, ...]:
    def _extract_keyword_keys(node: ast.AST) -> tuple[str, ...]:
        if isinstance(node, ast.Call):
            keyword_keys = tuple(keyword.arg for keyword in node.keywords if keyword.arg)
            if keyword_keys:
                return keyword_keys
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Call):
                return _extract_keyword_keys(node.func.value)
        return tuple()

    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for child in node.body:
                if not isinstance(child, ast.Return):
                    continue
                if isinstance(child.value, ast.Dict):
                    keys: list[str] = []
                    for key in child.value.keys:
                        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                            raise ValueError(f"{function_name} has a non-literal dict key")
                        keys.append(key.value)
                    return tuple(keys)
                call_keys = _extract_keyword_keys(child.value)
                if call_keys:
                    return call_keys
    raise ValueError(f"Missing function {function_name}")


def extract_class_fields(module: ast.Module, class_name: str) -> tuple[str, ...]:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            fields: list[str] = []
            for child in node.body:
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    fields.append(child.target.id)
            return tuple(fields)
    raise ValueError(f"Missing class {class_name}")


def _extract_base_name(base: ast.expr) -> str:
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return ""


def collect_module_class_defs(module: ast.Module) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in module.body
        if isinstance(node, ast.ClassDef)
    }


def _class_is_pydantic_model(
    class_name: str,
    class_defs: dict[str, ast.ClassDef],
    cache: dict[str, bool],
    resolving: set[str],
) -> bool:
    if class_name in cache:
        return cache[class_name]
    if class_name in resolving:
        return False
    class_node = class_defs.get(class_name)
    if class_node is None:
        cache[class_name] = False
        return False

    resolving.add(class_name)
    try:
        for base in class_node.bases:
            base_name = _extract_base_name(base)
            if not base_name:
                continue
            if base_name == "BaseModel":
                cache[class_name] = True
                return True
            if base_name in class_defs and _class_is_pydantic_model(base_name, class_defs, cache, resolving):
                cache[class_name] = True
                return True
        cache[class_name] = False
        return False
    finally:
        resolving.remove(class_name)


def collect_pydantic_model_subclasses(module: ast.Module) -> tuple[str, ...]:
    class_defs = collect_module_class_defs(module)
    cache: dict[str, bool] = {}
    model_classes = [
        class_name
        for class_name in class_defs
        if _class_is_pydantic_model(class_name, class_defs, cache, set())
    ]
    return tuple(sorted(model_classes))


def _class_model_config_assignment_name(class_node: ast.ClassDef) -> str:
    for child in class_node.body:
        if not isinstance(child, ast.Assign):
            continue
        for target in child.targets:
            if not isinstance(target, ast.Name) or target.id != "model_config":
                continue
            if isinstance(child.value, ast.Name):
                return child.value.id
            if isinstance(child.value, ast.Attribute):
                return child.value.attr
            return ast.unparse(child.value)
    return ""


def resolve_pydantic_model_config_source(
    class_name: str,
    class_defs: dict[str, ast.ClassDef],
    cache: dict[str, str],
    resolving: set[str],
) -> str:
    if class_name in cache:
        return cache[class_name]
    if class_name in resolving:
        return ""
    class_node = class_defs.get(class_name)
    if class_node is None:
        cache[class_name] = ""
        return ""

    local_assignment = _class_model_config_assignment_name(class_node)
    if local_assignment:
        cache[class_name] = local_assignment
        return local_assignment

    resolving.add(class_name)
    try:
        for base in class_node.bases:
            base_name = _extract_base_name(base)
            if not base_name:
                continue
            if base_name in class_defs:
                inherited_assignment = resolve_pydantic_model_config_source(
                    base_name,
                    class_defs,
                    cache,
                    resolving,
                )
                if inherited_assignment:
                    cache[class_name] = inherited_assignment
                    return inherited_assignment
        cache[class_name] = ""
        return ""
    finally:
        resolving.remove(class_name)


def is_valid_contract_model_config(config_source: str) -> tuple[bool, str]:
    normalized = str(config_source or "").strip()
    if not normalized:
        return False, "MISSING"
    if normalized == "REQUEST_MODEL_CONFIG":
        return True, "REQUEST_MODEL_CONFIG"
    compact = normalized.replace(" ", "")
    if compact.startswith("ConfigDict("):
        has_populate = "populate_by_name=False" in compact
        has_alias = "alias_generator=to_camel" in compact
        if has_populate and has_alias:
            return True, "ConfigDict(alias_generator=to_camel,populate_by_name=False)"
    return False, normalized


def extract_literal_constant(module: ast.Module, name: str) -> object:
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return smart_extract_literals(node.value)
    raise ValueError(f"Missing constant {name}")


def extract_function_names(module: ast.Module) -> set[str]:
    return {node.name for node in module.body if isinstance(node, ast.FunctionDef)}


def contains_in_order(text: str, tokens: tuple[str, ...], decorate: bool = False) -> bool:
    cursor = 0
    for token in tokens:
        needle = f"`{token}`" if decorate else token
        found = text.find(needle, cursor)
        if found < 0:
            return False
        cursor = found + len(needle)
    return True


def run_subprocess(command: list[str], cwd: Path) -> tuple[bool, str]:
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, check=False)
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output or "completed"


def add_result(results: list[CheckResult], domain: str, name: str, ok: bool, detail: str) -> None:
    results.append(CheckResult(domain=domain, name=name, ok=ok, detail=detail))


def infer_mode(root: Path, explicit_mode: str) -> str:
    if explicit_mode != "auto":
        return explicit_mode
    contract_doc = root / "docs/question-bank-contract.md"
    schema_path = root / "data/schema.sql"
    if contract_doc.exists() and schema_path.exists():
        return "questionBank"
    return "global"


def load_waiver_payload(path_str: str) -> dict[str, object]:
    if not path_str:
        return {"checks": {}, "domains": {}}
    path = Path(path_str).resolve()
    if not path.exists():
        raise ValueError(f"Waiver file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    checks: dict[str, str] = {}
    domains: dict[str, str] = {}
    for item in payload.get("checks", []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        reason = str(item.get("reason", "")).strip() or "waived"
        owner = str(item.get("owner", "")).strip()
        expires_at = str(item.get("expiresAt", "")).strip()
        scope = str(item.get("scope", "")).strip()
        metadata_parts = [part for part in (f"owner={owner}" if owner else "", f"expiresAt={expires_at}" if expires_at else "", f"scope={scope}" if scope else "") if part]
        if metadata_parts:
            reason = f"{reason} ({', '.join(metadata_parts)})"
        if name:
            checks[name] = reason
    for item in payload.get("domains", []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        reason = str(item.get("reason", "")).strip() or "waived"
        owner = str(item.get("owner", "")).strip()
        expires_at = str(item.get("expiresAt", "")).strip()
        scope = str(item.get("scope", "")).strip()
        metadata_parts = [part for part in (f"owner={owner}" if owner else "", f"expiresAt={expires_at}" if expires_at else "", f"scope={scope}" if scope else "") if part]
        if metadata_parts:
            reason = f"{reason} ({', '.join(metadata_parts)})"
        if name:
            domains[name] = reason
    return {"checks": checks, "domains": domains}


def resolve_waiver_reason(result: CheckResult, waiver_payload: dict[str, object]) -> str:
    check_waivers = waiver_payload.get("checks", {})
    domain_waivers = waiver_payload.get("domains", {})
    if isinstance(check_waivers, dict) and result.name in check_waivers:
        return str(check_waivers[result.name])
    if isinstance(domain_waivers, dict) and result.domain in domain_waivers:
        return str(domain_waivers[result.domain])
    return ""


def classify_results(
    results: list[CheckResult],
    waiver_payload: dict[str, object],
) -> tuple[list[CheckResult], list[tuple[CheckResult, str]], list[str]]:
    failed_checks: list[CheckResult] = []
    waived_checks: list[tuple[CheckResult, str]] = []
    missing_domains: list[str] = []
    grouped: dict[str, list[CheckResult]] = {}
    for result in results:
        grouped.setdefault(result.domain, []).append(result)

    for domain_key, _ in TEN_DOMAIN_SPECS:
        checks = grouped.get(domain_key, [])
        if not checks:
            missing_domains.append(domain_key)
            continue
        for result in checks:
            if result.ok:
                continue
            waiver_reason = resolve_waiver_reason(result, waiver_payload)
            if waiver_reason:
                waived_checks.append((result, waiver_reason))
                continue
            failed_checks.append(result)
    return failed_checks, waived_checks, missing_domains


def extract_question_bank_module_report(root: Path) -> list[dict[str, object]]:
    schema_path = root / "data/schema.sql"
    contract_doc_path = root / "docs/question-bank-contract.md"
    schema_tables = parse_table_columns(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else {}
    contract_text = contract_doc_path.read_text(encoding="utf-8") if contract_doc_path.exists() else ""
    report: list[dict[str, object]] = []
    for module_name, expected_fields in EXPECTED_QUESTION_BANK_MODULE_FIELDS.items():
        table_columns = schema_tables.get(module_name, set())
        schema_ok = set(expected_fields).issubset(table_columns)
        contract_ok = all(f"`{field}`" in contract_text for field in expected_fields)
        extjson_ok = "extJson" in table_columns
        report.append(
            {
                "module": module_name,
                "schemaOk": schema_ok,
                "contractDocOk": contract_ok,
                "extJsonOk": extjson_ok,
                "status": "PASS" if schema_ok and contract_ok and extjson_ok else "DRIFT",
            }
        )
    return report


def build_report_payload(
    *,
    phase: str,
    task: str,
    mode: str,
    results: list[CheckResult],
    failed_checks: list[CheckResult],
    waived_checks: list[tuple[CheckResult, str]],
    missing_domains: list[str],
    question_bank_modules: list[dict[str, object]],
) -> dict[str, object]:
    domain_summary: list[dict[str, object]] = []
    grouped: dict[str, list[CheckResult]] = {}
    for result in results:
        grouped.setdefault(result.domain, []).append(result)
    for domain_key, domain_label in TEN_DOMAIN_SPECS:
        checks = grouped.get(domain_key, [])
        domain_failed = [item for item in failed_checks if item.domain == domain_key]
        domain_waived = [item for item, _ in waived_checks if item.domain == domain_key]
        domain_summary.append(
            {
                "domain": domain_key,
                "label": domain_label,
                "configuredChecks": len(checks),
                "failedChecks": len(domain_failed),
                "waivedChecks": len(domain_waived),
                "status": "MISSING" if domain_key in missing_domains else ("FAIL" if domain_failed else "PASS"),
            }
        )
    return {
        "phase": phase,
        "task": task,
        "mode": mode,
        "summary": {
            "totalChecks": len(results),
            "failedChecks": len(failed_checks),
            "waivedChecks": len(waived_checks),
            "missingDomains": missing_domains,
            "status": "FAIL" if failed_checks or missing_domains else "PASS",
        },
        "failedChecks": [
            {"domain": item.domain, "name": item.name, "detail": item.detail}
            for item in failed_checks
        ],
        "waivedChecks": [
            {"domain": item.domain, "name": item.name, "detail": item.detail, "reason": reason}
            for item, reason in waived_checks
        ],
        "domainSummary": domain_summary,
        "questionBankModules": question_bank_modules,
    }


def load_contract_package(root: Path, contract_json_arg: str) -> dict[str, object]:
    candidate = Path(contract_json_arg).resolve() if contract_json_arg else root / "docs" / "contracts" / "current" / "contract.json"
    if not candidate.exists():
        return {}
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_path": str(candidate), "_invalid": True}
    if isinstance(payload, dict):
        payload["_path"] = str(candidate)
        return payload
    return {"_path": str(candidate), "_invalid": True}


def contract_package_checks(root: Path, mode: str, contract_payload: dict[str, object]) -> list[CheckResult]:
    results: list[CheckResult] = []
    exists = bool(contract_payload)
    invalid = bool(contract_payload.get("_invalid")) if exists else False
    add_result(
        results,
        "documentation",
        "docs:development-readiness-contract",
        exists and not invalid,
        str(contract_payload.get("_path", root / "docs/contracts/current/contract.json")),
    )
    if not exists or invalid:
        return results

    contract_mode = str(contract_payload.get("mode", "")).strip()
    add_result(
        results,
        "api",
        "contract:mode-alignment",
        not contract_mode or contract_mode == mode,
        f"contract mode={contract_mode or 'missing'}, guard mode={mode}",
    )

    scope = contract_payload.get("scope", {})
    in_scope_modules = scope.get("inScopeModules", []) if isinstance(scope, dict) else []
    add_result(
        results,
        "documentation",
        "contract:in-scope-modules-defined",
        isinstance(in_scope_modules, list) and bool(in_scope_modules),
        f"inScopeModules={in_scope_modules}",
    )

    contracts = contract_payload.get("contracts", {})
    api_payload = contracts.get("api", {}) if isinstance(contracts, dict) else {}
    response_envelope = api_payload.get("responseEnvelope", []) if isinstance(api_payload, dict) else []
    if mode == "questionBank":
        add_result(
            results,
            "api",
            "contract:questionbank-response-envelope",
            tuple(response_envelope) == EXPECTED_SUCCESS_KEYS,
            f"responseEnvelope={response_envelope}",
        )

    permissions_payload = contracts.get("permissions", {}) if isinstance(contracts, dict) else {}
    permission_keys = permissions_payload.get("permissionKeys", []) if isinstance(permissions_payload, dict) else []
    add_result(
        results,
        "permission",
        "contract:permission-keys-defined",
        isinstance(permission_keys, list) and bool(permission_keys),
        f"permissionKeys={permission_keys}",
    )
    return results


def render_markdown_report(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# Unified Delivery Guard Report",
        "",
        f"- Phase: `{payload['phase']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Status: `{summary['status']}`",
    ]
    if payload.get("task"):
        lines.append(f"- Task: {payload['task']}")
    lines.extend(
        [
            f"- Failed Checks: `{summary['failedChecks']}`",
            f"- Waived Checks: `{summary['waivedChecks']}`",
            f"- Missing Domains: `{', '.join(summary['missingDomains']) if summary['missingDomains'] else 'none'}`",
            "",
            "## Domain Summary",
        ]
    )
    for item in payload["domainSummary"]:
        lines.append(
            f"- `{item['label']}`: `{item['status']}` "
            f"(configured={item['configuredChecks']}, failed={item['failedChecks']}, waived={item['waivedChecks']})"
        )
    if payload["failedChecks"]:
        lines.append("")
        lines.append("## Failed Checks")
        for item in payload["failedChecks"]:
            lines.append(f"- `{item['domain']}` / `{item['name']}`: {item['detail']}")
    if payload["waivedChecks"]:
        lines.append("")
        lines.append("## Waived Checks")
        for item in payload["waivedChecks"]:
            lines.append(f"- `{item['domain']}` / `{item['name']}`: {item['reason']}")
    if payload["mode"] == "questionBank":
        lines.append("")
        lines.append("## questionBank Module Summary")
        for item in payload["questionBankModules"]:
            lines.append(
                f"- `{item['module']}`: `{item['status']}` "
                f"(schema={item['schemaOk']}, contractDoc={item['contractDocOk']}, extJson={item['extJsonOk']})"
            )
    return "\n".join(lines)


def write_report_file(path_str: str, content: str) -> None:
    if not path_str:
        return
    path = Path(path_str).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def is_lower_camel_case(value: str) -> bool:
    return LOWER_CAMEL_RE.match(value) is not None


def parse_table_columns(schema_text: str) -> dict[str, set[str]]:
    tables: dict[str, set[str]] = {}
    for match in CREATE_TABLE_RE.finditer(schema_text):
        table_name = match.group(1).strip('"')
        body = match.group(2)
        columns: set[str] = set()
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line:
                continue
            upper_line = line.upper()
            if upper_line.startswith(("FOREIGN KEY", "PRIMARY KEY", "UNIQUE", "CONSTRAINT", "CHECK")):
                continue
            column_name = line.split()[0].strip('"')
            columns.add(column_name)
        tables[table_name] = columns
    return tables


def parse_unique_constraints(schema_text: str) -> list[tuple[str, str]]:
    constraints: list[tuple[str, str]] = []
    for table_name, clause in CREATE_UNIQUE_INDEX_RE.findall(schema_text):
        constraints.append((table_name.strip('"').lower(), clause.lower()))
    for match in CREATE_TABLE_RE.finditer(schema_text):
        table_name = match.group(1).strip('"').lower()
        body = match.group(2)
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line:
                continue
            if "UNIQUE" not in line.upper():
                continue
            constraints.append((table_name, line.lower()))
    return constraints


def read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def collect_token_hits(file_texts: dict[str, str], token_specs: tuple[tuple[str, tuple[str, ...]], ...]) -> list[str]:
    hits: list[str] = []
    for relative_path, tokens in token_specs:
        text = file_texts.get(relative_path, "")
        matched = [token for token in tokens if token in text]
        if matched:
            hits.append(f"{relative_path} -> {', '.join(matched)}")
    return hits


def schema_has_any_table(schema_tables: dict[str, set[str]], candidate_tables: tuple[str, ...]) -> bool:
    return any(table in schema_tables for table in candidate_tables)


def schema_has_unique_constraint(
    unique_constraints: list[tuple[str, str]],
    candidate_tables: tuple[str, ...],
    candidate_tokens: tuple[str, ...],
) -> bool:
    table_set = {item.lower() for item in candidate_tables}
    token_set = tuple(item.lower() for item in candidate_tokens)
    for table_name, clause in unique_constraints:
        if table_name in table_set and any(token in clause for token in token_set):
            return True
    return False


def collect_deprecated_time_field_hits(root: Path) -> list[str]:
    hits: list[str] = []
    target_dirs = (
        root / "app",
        root / "frontend/src",
        root / "tests",
    )
    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        for path in target_dir.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                match = DEPRECATED_TIME_FIELD_RE.search(line)
                if not match:
                    continue
                hits.append(f"{path.relative_to(root).as_posix()}:{line_number}:{match.group(1)}")
                if len(hits) >= 20:
                    return hits
    return hits


def check_frontend_naming_convention(file_content: str) -> tuple[bool, str]:
    # 查找 export function 后面跟着 snake_case 的情况
    matches = sorted(set(FRONTEND_SNAKE_CASE_EXPORT_RE.findall(file_content)))
    snake_case_params: list[str] = []
    for function_match in FRONTEND_EXPORT_FUNCTION_RE.finditer(file_content):
        function_name = function_match.group(1)
        raw_params = function_match.group(2)
        for raw_param in raw_params.split(","):
            normalized_param = raw_param.split("=")[0].strip().lstrip("...")
            if not normalized_param:
                continue
            if normalized_param.startswith("{") or normalized_param.startswith("["):
                continue
            if ":" in normalized_param:
                normalized_param = normalized_param.split(":", 1)[0].strip()
            if SNAKE_CASE_IDENTIFIER_RE.match(normalized_param):
                snake_case_params.append(f"{function_name}({normalized_param})")
    if matches or snake_case_params:
        detail_parts: list[str] = []
        if matches:
            detail_parts.append(f"发现非标准命名函数: {matches}")
        if snake_case_params:
            detail_parts.append(f"发现 snake_case 参数: {sorted(set(snake_case_params))}")
        return False, "；".join(detail_parts) + "。前端 API 请统一使用 camelCase。"
    return True, "命名规范检查通过"


def collect_compatibility_key_access_hits(root: Path) -> list[str]:
    target_paths = (
        root / "app/main.py",
        root / "app/contracts.py",
        root / "app/service_modules",
        root / "frontend/src/api/services",
    )
    hits: list[str] = []
    for target_path in target_paths:
        if not target_path.exists():
            continue
        file_candidates: list[Path]
        if target_path.is_file():
            file_candidates = [target_path]
        else:
            file_candidates = [path for path in sorted(target_path.rglob("*")) if path.is_file()]
        for file_path in file_candidates:
            if file_path.suffix not in {".py", ".js"}:
                continue
            try:
                file_text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(file_text.splitlines(), start=1):
                matched = DISALLOWED_COMPAT_KEY_ACCESS_RE.search(line)
                if not matched:
                    continue
                hits.append(f"{file_path.relative_to(root).as_posix()}:{line_number}:{matched.group(1)}")
                if len(hits) >= 50:
                    return hits
    return hits


def check_no_raw_hex_colors(file_path: Path, content: str) -> tuple[bool, str]:
    if file_path.suffix not in {".vue", ".css", ".scss"}:
        return True, "非样式文件，跳过检查。"

    sanitized_content = BLOCK_COMMENT_RE.sub("", content)
    sanitized_content = HTML_COMMENT_RE.sub("", sanitized_content)
    sanitized_content = LINE_COMMENT_RE.sub("", sanitized_content)

    violations: list[str] = []
    for line_number, line in enumerate(sanitized_content.splitlines(), start=1):
        sanitized_line = CSS_VAR_HEX_DEF_RE.sub("", line)
        matches = RAW_HEX_COLOR_RE.findall(sanitized_line)
        if not matches:
            continue
        for match in matches:
            violations.append(f"{match}@L{line_number}")
            if len(violations) >= 10:
                break
        if len(violations) >= 10:
            break

    if violations:
        return (
            False,
            f"发现硬编码颜色 {violations}。请使用 var(--qb-*) 设计变量。",
        )
    return True, "未发现硬编码 hex 颜色。"


def static_checks(root: Path, phase: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    paths = {
        "contracts": root / "app/contracts.py",
        "models": root / "app/models.py",
        "main": root / "app/main.py",
        "service": root / "app/service.py",
        "auth": root / "app/auth.py",
        "exceptions": root / "app/exceptions.py",
        "repository": root / "app/repository.py",
        "schema": root / "data/schema.sql",
        "readme": root / "README.md",
        "contract_doc": root / "docs/question-bank-contract.md",
        "knowledge_doc": root / "docs/knowledge-module.md",
        "self_check": root / "docs/alignment-self-check.md",
        "question_page": root / "frontend/src/views/Teacher/QuestionManagement.vue",
        "tests_main": root / "tests/test_question_bank.py",
        "tests_unit": root / "tests/unit/test_auth_contracts.py",
        "tests_integration": root / "tests/integration/test_http_contracts.py",
        "tests_scope_isolation": root / "tests/integration/test_scope_isolation_2026.py",
        "tests_e2e": root / "tests/e2e/test_question_bank_journey.py",
        "test_runner": root / "tools/python/test_suite_runner.py",
    }

    # 1) Field standards
    for key in ("contracts", "models", "schema"):
        path = paths[key]
        add_result(results, "field", f"exists:{path.relative_to(root).as_posix()}", path.exists(), str(path))

    # 2) API standards
    for key in ("contracts", "main", "exceptions"):
        path = paths[key]
        add_result(results, "api", f"exists:{path.relative_to(root).as_posix()}", path.exists(), str(path))

    # 3) Page standards
    for relative_path in (*ACTIVE_FRONTEND_FILES, *AUXILIARY_FRONTEND_FILES):
        path = root / relative_path
        add_result(results, "page", f"exists:{relative_path}", path.exists(), str(path))

    # 4) Status standards
    for key in ("contracts", "service", "question_page", "tests_main"):
        path = paths[key]
        add_result(results, "status", f"exists:{path.relative_to(root).as_posix()}", path.exists(), str(path))

    # 5) Permission standards
    for key in ("contracts", "auth", "main", "service", "tests_unit"):
        path = paths[key]
        add_result(results, "permission", f"exists:{path.relative_to(root).as_posix()}", path.exists(), str(path))

    # 6) Validation standards
    for key in ("models", "service", "tests_main"):
        path = paths[key]
        add_result(results, "validation", f"exists:{path.relative_to(root).as_posix()}", path.exists(), str(path))

    # 7) Error standards
    for key in ("contracts", "exceptions", "tests_main", "tests_integration"):
        path = paths[key]
        add_result(results, "error", f"exists:{path.relative_to(root).as_posix()}", path.exists(), str(path))

    # 8) Extension standards
    for key in ("schema", "service", "repository", "contract_doc"):
        path = paths[key]
        add_result(results, "extension", f"exists:{path.relative_to(root).as_posix()}", path.exists(), str(path))

    # 9) Documentation standards
    for key in ("readme", "contract_doc", "knowledge_doc", "self_check"):
        path = paths[key]
        add_result(results, "documentation", f"exists:{path.relative_to(root).as_posix()}", path.exists(), str(path))

    # 10) Test standards
    for key in ("tests_main", "tests_unit", "tests_integration", "tests_scope_isolation", "tests_e2e", "test_runner"):
        path = paths[key]
        add_result(results, "test", f"exists:{path.relative_to(root).as_posix()}", path.exists(), str(path))
    for relative_path in (
        "tools/bin/run-tests.sh",
        "tools/bin/run-unit-tests.sh",
        "tools/bin/run-integration-tests.sh",
        "tools/bin/run-regression-tests.sh",
        "tools/bin/run-e2e-tests.sh",
    ):
        path = root / relative_path
        add_result(results, "test", f"exists:{relative_path}", path.exists(), str(path))

    critical_paths = (
        paths["contracts"],
        paths["models"],
        paths["main"],
        paths["service"],
        paths["auth"],
        paths["exceptions"],
        paths["repository"],
        paths["schema"],
        paths["readme"],
        paths["contract_doc"],
        paths["knowledge_doc"],
        paths["self_check"],
        paths["question_page"],
        paths["tests_main"],
        paths["tests_unit"],
        paths["tests_integration"],
        paths["tests_scope_isolation"],
        paths["tests_e2e"],
        paths["test_runner"],
    )
    if any(not path.exists() for path in critical_paths):
        return results

    contracts_module = parse_module(paths["contracts"])
    models_module = parse_module(paths["models"])
    service_module = parse_module(paths["service"])
    auth_module = parse_module(paths["auth"])
    exceptions_module = parse_module(paths["exceptions"])

    readme_text = paths["readme"].read_text(encoding="utf-8")
    contract_doc_text = paths["contract_doc"].read_text(encoding="utf-8")
    knowledge_doc_text = paths["knowledge_doc"].read_text(encoding="utf-8")
    self_check_text = paths["self_check"].read_text(encoding="utf-8")
    main_text = paths["main"].read_text(encoding="utf-8")
    service_text = paths["service"].read_text(encoding="utf-8")
    models_text = paths["models"].read_text(encoding="utf-8")
    exceptions_text = paths["exceptions"].read_text(encoding="utf-8")
    repository_text = paths["repository"].read_text(encoding="utf-8")
    question_page_text = paths["question_page"].read_text(encoding="utf-8")
    frontend_main_text = (root / "frontend/src/main.js").read_text(encoding="utf-8")
    router_index_text = (root / "frontend/src/router/index.js").read_text(encoding="utf-8")
    teacher_routes_text = (root / "frontend/src/router/teacherRoutes.js").read_text(encoding="utf-8")
    student_routes_text = (root / "frontend/src/router/studentRoutes.js").read_text(encoding="utf-8")
    login_view_text = (root / "frontend/src/views/Auth/Login.vue").read_text(encoding="utf-8")
    tests_text = paths["tests_main"].read_text(encoding="utf-8")
    unit_tests_text = paths["tests_unit"].read_text(encoding="utf-8")
    integration_tests_text = paths["tests_integration"].read_text(encoding="utf-8")
    scope_isolation_tests_text = paths["tests_scope_isolation"].read_text(encoding="utf-8")
    e2e_tests_text = paths["tests_e2e"].read_text(encoding="utf-8")
    test_runner_text = paths["test_runner"].read_text(encoding="utf-8")
    schema_text = paths["schema"].read_text(encoding="utf-8")
    extension_guard_texts = {
        "app/repository.py": repository_text,
        "app/service_modules/internal_student.py": read_optional_text(root / "app/service_modules/internal_student.py"),
        "app/service_modules/internal_system_admin.py": read_optional_text(root / "app/service_modules/internal_system_admin.py"),
        "app/service_modules/messages.py": read_optional_text(root / "app/service_modules/messages.py"),
    }

    # Field standards
    question_fields = extract_tuple_constant(contracts_module, "QUESTION_FIELDS")
    task_fields = extract_tuple_constant(contracts_module, "TASK_FIELDS")
    question_model_fields = extract_class_fields(models_module, "QuestionWriteModel")
    add_result(results, "field", "contracts:question-fields", question_fields == EXPECTED_QUESTION_FIELDS, f"QUESTION_FIELDS={question_fields}")
    add_result(results, "field", "contracts:task-fields", task_fields == EXPECTED_TASK_FIELDS, f"TASK_FIELDS={task_fields}")
    add_result(results, "field", "models:question-write-model", question_model_fields == EXPECTED_QUESTION_FIELDS, f"QuestionWriteModel fields={question_model_fields}")
    add_result(
        results,
        "field",
        "contracts:lower-camel-case",
        all(is_lower_camel_case(field) for field in question_fields + task_fields),
        f"question+task fields={question_fields + task_fields}",
    )
    schema_tables = parse_table_columns(schema_text)
    question_table_columns = schema_tables.get("question", set())
    add_result(
        results,
        "field",
        "schema:question-table-columns",
        set(EXPECTED_QUESTION_FIELDS).issubset(question_table_columns),
        f"question table columns={sorted(question_table_columns)}",
    )
    deprecated_time_field_hits = collect_deprecated_time_field_hits(root)
    add_result(
        results,
        "field",
        "global:deprecated-time-field-names",
        not deprecated_time_field_hits,
        "请统一使用 createTime/updateTime。"
        + (f" 发现: {', '.join(deprecated_time_field_hits)}" if deprecated_time_field_hits else ""),
    )

    # API standards
    success_keys = extract_dict_keys_from_function(contracts_module, "success")
    pagination_keys = extract_dict_keys_from_function(contracts_module, "pagination")
    add_result(results, "api", "contracts:success-envelope", success_keys == EXPECTED_SUCCESS_KEYS, f"success() keys={success_keys}")
    add_result(results, "api", "contracts:pagination", pagination_keys == EXPECTED_PAGINATION_KEYS, f"pagination() keys={pagination_keys}")
    required_question_routes = (
        '/api/question-bank/questions',
        '/api/question-bank/questions/{questionId}',
        '/api/question-bank/questions/{questionId}/status/{targetStatus}',
        '/api/question-bank/imports/template',
        '/api/question-bank/imports/template/preview',
    )
    add_result(
        results,
        "api",
        "main:question-routes",
        all(token in main_text for token in required_question_routes),
        f"required routes={required_question_routes}",
    )
    add_result(
        results,
        "api",
        "main:success-wrapper-usage",
        "return success(" in main_text and "return success(pagination(" in main_text,
        "API handlers should use success()/pagination() wrappers",
    )
    contract_model_classes = collect_pydantic_model_subclasses(contracts_module)
    class_defs = collect_module_class_defs(contracts_module)
    model_config_cache: dict[str, str] = {}
    model_config_summary: list[str] = []
    invalid_contract_models: list[str] = []
    for class_name in contract_model_classes:
        config_source = resolve_pydantic_model_config_source(
            class_name,
            class_defs,
            model_config_cache,
            set(),
        )
        is_valid, normalized_source = is_valid_contract_model_config(config_source)
        model_config_summary.append(f"{class_name}:{normalized_source}")
        if not is_valid:
            invalid_contract_models.append(f"{class_name}:{normalized_source}")
    add_result(
        results,
        "api",
        "contracts:all-basemodel-subclasses-scanned",
        len(contract_model_classes) > 0,
        f"scanned classes={contract_model_classes}",
    )
    add_result(
        results,
        "api",
        "contracts:all-basemodel-subclasses-use-request-model-config",
        not invalid_contract_models,
        (
            "all scanned contract models resolve to REQUEST_MODEL_CONFIG"
            if not invalid_contract_models
            else f"invalid model_config source: {invalid_contract_models}"
        )
        + f"; summary={model_config_summary}",
    )
    add_result(
        results,
        "api",
        "contracts:no-legacy-normalize-payload-entry",
        "def normalize_legacy_payload(" not in paths["contracts"].read_text(encoding="utf-8"),
        "contracts.py 不允许保留 normalize_legacy_payload 兼容入口。",
    )
    compatibility_key_hits = collect_compatibility_key_access_hits(root)
    add_result(
        results,
        "api",
        "global:no-disallowed-compatibility-key-access",
        not compatibility_key_hits,
        "未发现兼容键读取。"
        if not compatibility_key_hits
        else "发现兼容键读取: " + "; ".join(compatibility_key_hits),
    )

    # Page standards
    uses_bootstrap_api = all(
        token in main_text for token in ("response_model=PageBootstrapResponse", "page_bootstrap(")
    ) and all(route in main_text for route in EXPECTED_BOOTSTRAP_PAGE_ROUTES)
    add_result(
        results,
        "page",
        "main:frontend-bootstrap-routing",
        uses_bootstrap_api,
        f"bootstrap routes={EXPECTED_BOOTSTRAP_PAGE_ROUTES}",
    )
    add_result(
        results,
        "page",
        "frontend:question-page-bindings",
        all(token in question_page_text for token in QUESTION_PAGE_TOKENS),
        "Question page binds canonical question fields",
    )
    add_result(
        results,
        "page",
        "frontend:status-action-buttons",
        all(
            token in question_page_text
            for token in (
                "label: '提审'",
                "label: '通过'",
                "label: '驳回'",
                "label: '退回草稿'",
                "targetStatus: 'PUBLISHED'",
                "targetStatus: 'REJECTED'",
            )
        ),
        "Question management view renders canonical review actions",
    )
    add_result(
        results,
        "page",
        "frontend:entry-topology",
        all(
            token in frontend_main_text
            for token in ("resolveRuntimeEntryType", "fetchManagementProfile", "bootstrapWithRouter")
        )
        and all(
            token in router_index_text
            for token in ("createWebHistory", "isRoutePathAllowedInEntry", "ElMessage.warning")
        )
        and all(token in teacher_routes_text for token in ("/teacher", "/admin", "/messages"))
        and all(token in student_routes_text for token in ("/student", "/messages")),
        "Vue entry topology keeps main bootstrap, scoped routers, and role partitions",
    )
    add_result(
        results,
        "page",
        "frontend:login-redirect-flow",
        all(
            token in login_view_text
            for token in ("resolveLocationRedirectPath", "normalizeRedirectPath", "window.location.assign(nextPath)")
        ),
        "Login view keeps redirect sanitization and cross-entry redirect flow",
    )
    frontend_service_dir = root / "frontend/src/api/services"
    if frontend_service_dir.exists():
        service_files = sorted(frontend_service_dir.glob("*.js"))
        naming_violations: list[str] = []
        for service_file in service_files:
            content = service_file.read_text(encoding="utf-8")
            ok, detail = check_frontend_naming_convention(content)
            if ok:
                continue
            naming_violations.append(f"{service_file.relative_to(root).as_posix()}: {detail}")
        add_result(
            results,
            "page",
            "frontend:api-function-naming-convention",
            not naming_violations,
            "命名规范检查通过"
            if not naming_violations
            else "; ".join(naming_violations),
        )
    else:
        add_result(
            results,
            "page",
            "frontend:api-function-naming-convention",
            False,
            "frontend/src/api/services 目录不存在，无法执行命名规范检查。",
        )
    frontend_src_dir = root / "frontend/src"
    if frontend_src_dir.exists():
        raw_hex_violations: list[str] = []
        scanned_files = 0
        for frontend_file in sorted(frontend_src_dir.rglob("*")):
            if not frontend_file.is_file() or frontend_file.suffix not in {".vue", ".css", ".scss"}:
                continue
            scanned_files += 1
            try:
                frontend_content = frontend_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            ok, detail = check_no_raw_hex_colors(frontend_file, frontend_content)
            if ok:
                continue
            raw_hex_violations.append(f"{frontend_file.relative_to(root).as_posix()}: {detail}")

        add_result(
            results,
            "page",
            "frontend:no-raw-hex-colors",
            not raw_hex_violations,
            f"scanned={scanned_files} files"
            if not raw_hex_violations
            else "; ".join(raw_hex_violations),
        )
    else:
        add_result(
            results,
            "page",
            "frontend:no-raw-hex-colors",
            False,
            "frontend/src 目录不存在，无法执行十六进制颜色检查。",
        )

    # Status standards
    question_statuses = extract_tuple_constant(contracts_module, "QUESTION_STATUSES")
    allowed_transitions = extract_literal_constant(service_module, "ALLOWED_TRANSITIONS")
    add_result(
        results,
        "status",
        "contracts:question-statuses",
        question_statuses == EXPECTED_QUESTION_STATUSES,
        f"QUESTION_STATUSES={question_statuses}",
    )
    add_result(
        results,
        "status",
        "service:allowed-transitions",
        allowed_transitions == EXPECTED_ALLOWED_TRANSITIONS,
        f"ALLOWED_TRANSITIONS={allowed_transitions}",
    )
    add_result(
        results,
        "status",
        "frontend:status-tokens",
        all(token in question_page_text for token in EXPECTED_QUESTION_STATUSES),
        f"question page status tokens={EXPECTED_QUESTION_STATUSES}",
    )
    add_result(
        results,
        "status",
        "tests:status-transition-coverage",
        all(token in tests_text for token in ("/status/QA_IN_PROGRESS", "/status/REVIEW_PENDING", "/status/PUBLISHED")),
        "Regression tests cover status transition endpoints",
    )

    # Permission standards
    all_roles = extract_tuple_constant_resolved(contracts_module, "ALL_ROLES")
    managed_permission_keys = extract_tuple_constant(contracts_module, "MANAGED_PERMISSION_KEYS")
    auth_function_names = extract_function_names(auth_module)
    add_result(results, "permission", "contracts:all-roles", all_roles == EXPECTED_ALL_ROLES, f"ALL_ROLES={all_roles}")
    add_result(
        results,
        "permission",
        "contracts:managed-permission-keys",
        managed_permission_keys == EXPECTED_MANAGED_PERMISSION_KEYS,
        f"MANAGED_PERMISSION_KEYS={managed_permission_keys}",
    )
    add_result(
        results,
        "permission",
        "auth:guard-functions",
        all(name in auth_function_names for name in ("require_question_operator", "require_paper_operator", "require_analytics_operator", "require_student", "require_super_admin")),
        f"auth functions={sorted(auth_function_names)}",
    )
    add_result(
        results,
        "permission",
        "main:permission-key-usage",
        all(key in main_text for key in EXPECTED_MANAGED_PERMISSION_KEYS),
        f"permission keys in app/main.py={EXPECTED_MANAGED_PERMISSION_KEYS}",
    )
    add_result(
        results,
        "permission",
        "tests:permission-coverage",
        "test_permission_validation_and_import_export_guards" in tests_text
        and "def test_role_guards_raise_fixed_forbidden_error" in unit_tests_text,
        "Regression and unit suites cover permission guards",
    )

    # Validation standards
    add_result(
        results,
        "validation",
        "models:strict-extra-forbid",
        models_text.count('ConfigDict(extra="forbid")') >= 8,
        'Pydantic models should enforce ConfigDict(extra="forbid")',
    )
    add_result(
        results,
        "validation",
        "models:question-validator-coverage",
        all(
            token in models_text
            for token in (
                '@field_validator("type")',
                '@field_validator("status")',
                '@field_validator("optionsJson")',
                '@field_validator("extJson")',
                "extJson.knowledgeTags 必须是 1-3 个知识点组成的数组。",
            )
        ),
        "QuestionWriteModel validators cover type/status/options/extJson",
    )
    add_result(
        results,
        "validation",
        "service:runtime-validation-guards",
        all(
            token in service_text
            for token in (
                "模板导入仅支持 txt 或 docx 文件。",
                "knowledgeId 不存在。",
                "startDate 不能晚于 endDate。",
            )
        ),
        "Service keeps canonical validation branches",
    )
    add_result(
        results,
        "validation",
        "tests:validation-coverage",
        "status_code == 422" in tests_text and 'ext["knowledgeTags"]' in tests_text,
        "Regression tests assert validation failures and extJson constraints",
    )

    # Error standards
    question_error_codes = extract_literal_constant(contracts_module, "QUESTION_ERROR_CODES")
    exception_function_names = extract_function_names(exceptions_module)
    error_code_keys = extract_dict_keys_from_function(exceptions_module, "_error_codes")
    add_result(
        results,
        "error",
        "contracts:question-error-codes",
        question_error_codes == EXPECTED_QUESTION_ERROR_CODES,
        f"QUESTION_ERROR_CODES={question_error_codes}",
    )
    add_result(
        results,
        "error",
        "exceptions:error-code-namespace",
        error_code_keys == ("NOT_FOUND", "FORBIDDEN", "VALIDATION_FAILED", "INVALID_STATUS", "DATABASE_ERROR"),
        f"_error_codes() keys={error_code_keys}",
    )
    add_result(
        results,
        "error",
        "exceptions:helper-functions",
        all(
            name in exception_function_names
            for name in (
                "not_found",
                "forbidden",
                "validation_failed",
                "invalid_status",
                "database_error",
                "task_not_found",
                "task_forbidden",
                "task_validation_failed",
            )
        ),
        f"exception helpers={sorted(exception_function_names)}",
    )
    add_result(
        results,
        "error",
        "exceptions:unified-error-envelope",
        (
            'payload = {"code": exc.code, "message": exc.message, "data": None}' in exceptions_text
            and "JSONResponse(payload" in exceptions_text
        )
        or (
            "BaseResponse(code=exc.code, message=exc.message, data=None).model_dump()" in exceptions_text
            and "JSONResponse(payload" in exceptions_text
        ),
        "Exception handler returns unified API envelope",
    )
    add_result(
        results,
        "error",
        "tests:error-code-coverage",
        all(token in tests_text for token in ("QUESTION_VALIDATION_FAILED", "QUESTION_FORBIDDEN", "TASK_FORBIDDEN"))
        and '"code"] == "OK"' in integration_tests_text,
        "Tests cover success and error code semantics",
    )

    # Extension standards
    required_extjson_tables = ("user", "userAuth", "knowledge", "question", "task")
    extjson_table_failures = [table for table in required_extjson_tables if "extJson" not in schema_tables.get(table, set())]
    unique_constraints = parse_unique_constraints(schema_text)
    student_records_hits = collect_token_hits(
        extension_guard_texts,
        (
            ("app/repository.py", ("studentRecords", "_save_student_records_map", "json_each(u.extJson, '$.studentRecords')")),
        ),
    )
    paper_reports_hits = collect_token_hits(
        extension_guard_texts,
        (
            ("app/service_modules/internal_student.py", ('system_state["paperReports"]',)),
            ("app/service_modules/internal_system_admin.py", ('return list(self._load_system_state()["paperReports"])',)),
        ),
    )
    message_history_hits = collect_token_hits(
        extension_guard_texts,
        (
            ("app/service_modules/messages.py", ('system_state["messageSendHistory"]', 'system_state.get("messageSendHistory", [])')),
            ("app/service_modules/internal_system_admin.py", ('return list(self._load_system_state().get("messageSendHistory", []))',)),
        ),
    )
    hot_state_failures: list[str] = []
    if student_records_hits:
        hot_state_failures.append(f"studentRecords={student_records_hits}")
    if paper_reports_hits:
        hot_state_failures.append(f"paperReports={paper_reports_hits}")
    if message_history_hits:
        hot_state_failures.append(f"messageSendHistory={message_history_hits}")
    concurrent_state_failures: list[str] = []
    if student_records_hits and not schema_has_any_table(schema_tables, ("student_question_record", "student_record", "student_answer_record")):
        concurrent_state_failures.append("studentRecords missing dedicated table(student_question_record/student_record/student_answer_record)")
    if paper_reports_hits and not schema_has_any_table(schema_tables, ("student_paper_report", "paper_report", "paper_reports")):
        concurrent_state_failures.append("paperReports missing dedicated table(student_paper_report/paper_report)")
    if message_history_hits and not schema_has_any_table(schema_tables, ("message_send_history", "message_send_log", "message_delivery_log")):
        concurrent_state_failures.append("messageSendHistory missing dedicated table(message_send_history/message_send_log)")
    idempotent_failures: list[str] = []
    if paper_reports_hits and not schema_has_unique_constraint(
        unique_constraints,
        ("student_paper_report", "paper_report", "paper_reports"),
        ("reportid", "requestid", "idempotencykey"),
    ):
        idempotent_failures.append("paper report write uses reportId-style dedupe but schema lacks UNIQUE(reportId/requestId/idempotencyKey)")
    report_json_failures: list[str] = []
    if student_records_hits and not schema_has_any_table(schema_tables, ("student_question_record", "student_record", "student_answer_record")):
        report_json_failures.append("studentRecords is queried via json_each for filtering/reporting but has no dedicated table")
    if paper_reports_hits and not schema_has_any_table(schema_tables, ("student_paper_report", "paper_report", "paper_reports")):
        report_json_failures.append("paperReports remains JSON-only while used as report/history data")
    if message_history_hits and not schema_has_any_table(schema_tables, ("message_send_history", "message_send_log", "message_delivery_log")):
        report_json_failures.append("messageSendHistory remains JSON-only while used as list/history data")
    add_result(
        results,
        "extension",
        "schema:extjson-core-tables",
        not extjson_table_failures,
        f"tables missing extJson={extjson_table_failures or 'none'}",
    )
    add_result(
        results,
        "extension",
        "docs:extjson-policy",
        "合同外业务数据统一进入 `extJson`" in contract_doc_text and "extJson" in knowledge_doc_text,
        "Contract docs describe extJson-only extension strategy",
    )
    add_result(
        results,
        "extension",
        "backend:extjson-write-paths",
        "reviewRemark" in service_text and service_text.count("extJson") >= 40 and repository_text.count("extJson") >= 40,
        "Service/repository keep extension payloads in extJson",
    )
    add_result(
        results,
        "extension",
        "guard:no-hot-business-state-in-extjson",
        not hot_state_failures,
        f"hot business state in extJson={hot_state_failures or 'none'}",
    )
    add_result(
        results,
        "extension",
        "guard:concurrent-state-backed-by-tables",
        not concurrent_state_failures,
        f"concurrent state table coverage={concurrent_state_failures or 'ok'}",
    )
    add_result(
        results,
        "extension",
        "guard:idempotent-write-has-unique-constraint",
        not idempotent_failures,
        f"idempotent uniqueness evidence={idempotent_failures or 'ok'}",
    )
    add_result(
        results,
        "extension",
        "guard:reporting-data-not-json-only",
        not report_json_failures,
        f"report data storage={report_json_failures or 'ok'}",
    )

    # Documentation standards
    add_result(
        results,
        "documentation",
        "docs:readme-question-fields",
        contains_in_order(readme_text, EXPECTED_QUESTION_FIELDS, decorate=True),
        "README includes canonical question field sequence",
    )
    add_result(
        results,
        "documentation",
        "docs:contract-question-fields",
        contains_in_order(contract_doc_text, EXPECTED_QUESTION_FIELDS, decorate=True),
        "Contract doc includes canonical question field sequence",
    )
    add_result(
        results,
        "documentation",
        "docs:contract-task-fields",
        contains_in_order(contract_doc_text, EXPECTED_TASK_FIELDS, decorate=True),
        "Contract doc includes canonical task field sequence",
    )
    add_result(
        results,
        "documentation",
        "docs:unified-envelope",
        all(token in contract_doc_text for token in EXPECTED_SUCCESS_KEYS) and all(token in self_check_text for token in EXPECTED_SUCCESS_KEYS),
        "Docs mention the unified response envelope",
    )
    add_result(
        results,
        "documentation",
        "docs:self-check-regression-entry",
        "## 自测命令" in self_check_text and "./tools/bin/check-alignment.sh" in self_check_text,
        "Self-check document includes regression command set",
    )
    add_result(
        results,
        "documentation",
        "docs:readme-no-stale-pass-count",
        STALE_PASSED_COUNT_RE.search(readme_text) is None,
        "README should avoid hard-coded '<n> passed' counts to prevent drift",
    )
    add_result(
        results,
        "documentation",
        "docs:self-check-no-stale-pass-count",
        STALE_PASSED_COUNT_RE.search(self_check_text) is None,
        "Self-check doc should avoid hard-coded '<n> passed' counts to prevent drift",
    )

    # Test standards
    add_result(
        results,
        "test",
        "tests:question-fields-asserted",
        "QUESTION_FIELDS" in tests_text and "assert tuple(question.keys()) == QUESTION_FIELDS" in tests_text,
        "Regression tests assert canonical question field order",
    )
    add_result(
        results,
        "test",
        "tests:task-fields-imported",
        "TASK_FIELDS" in tests_text,
        "Regression tests import canonical task contract",
    )
    add_result(
        results,
        "test",
        "tests:success-envelope-asserted",
        'body["code"] == "OK"' in tests_text and 'body["message"] == "success"' in tests_text,
        "Regression tests assert success envelope",
    )
    add_result(
        results,
        "test",
        "tests:suite-runner-canonical",
        all(token in test_runner_text for token in ('CANONICAL_SUITES = ("unit", "integration", "regression", "e2e")', '"auto"')),
        "test_suite_runner keeps canonical suite orchestration",
    )
    add_result(
        results,
        "test",
        "tests:integration-envelope",
        '"code"] == "OK"' in integration_tests_text and '"message"] == "success"' in integration_tests_text,
        "Integration tests assert API envelope contract",
    )
    add_result(
        results,
        "test",
        "tests:e2e-journey",
        "test_teacher_publish_student_complete_question_journey" in e2e_tests_text,
        "E2E journey coverage exists",
    )
    add_result(
        results,
        "test",
        "tests:cross-group-access-prevention",
        all(
            token in scope_isolation_tests_text
            for token in (
                "test_cross_group_access_prevention",
                "X-Joint-Group",
                "SCIENCE_ENGINEERING_3",
                "MANAGEMENT_PRINCIPLES",
                "status_code == 403",
            )
        ),
        "Cross-group access prevention and X-Joint-Group interceptor coverage exists",
    )

    return results


def print_results(
    results: list[CheckResult],
    phase: str,
    task: str,
    waiver_payload: dict[str, object],
) -> tuple[int, list[CheckResult], list[tuple[CheckResult, str]], list[str]]:
    grouped: dict[str, list[CheckResult]] = {}
    for result in results:
        grouped.setdefault(result.domain, []).append(result)
    failed_checks, waived_checks, missing_domains = classify_results(results, waiver_payload)

    print("Ten-domain alignment report")
    print(f"Phase: {phase}")
    if task:
        print(f"Task: {task}")

    passed_domains = 0

    for index, (domain_key, domain_label) in enumerate(TEN_DOMAIN_SPECS, start=1):
        checks = grouped.get(domain_key, [])
        if not checks:
            missing_domains.append(domain_key)
            print(f"[FAIL] {index:02d}. {domain_label}: no checks configured")
            print("  - DRIFT domain mapping is missing.")
            continue
        failed = [check for check in failed_checks if check.domain == domain_key]
        waived = [check for check, _ in waived_checks if check.domain == domain_key]
        passed = len(checks) - len(failed)
        status = "PASS" if not failed else "FAIL"
        print(f"[{status}] {index:02d}. {domain_label}: {passed}/{len(checks)} checks passed")
        for check in failed:
            print(f"  - DRIFT {check.name}: {check.detail}")
        for check, reason in waived_checks:
            if check.domain != domain_key:
                continue
            print(f"  - WAIVED {check.name}: {reason}")
        if not failed:
            passed_domains += 1

    print(
        f"Summary: {passed_domains}/{len(TEN_DOMAIN_SPECS)} domains passed, "
        f"{len(results) - len(failed_checks)}/{len(results)} checks passed, "
        f"{len(waived_checks)} waived"
    )
    return passed_domains, failed_checks, waived_checks, missing_domains


def main() -> int:
    args = parse_args()
    root = repo_root()
    waiver_payload = load_waiver_payload(args.waiver_file)
    results = static_checks(root, args.phase)

    if args.task.strip():
        task = args.task.strip()
    else:
        task = ""
    mode = infer_mode(root, args.mode)
    contract_payload = load_contract_package(root, args.contract_json)
    results.extend(contract_package_checks(root, mode, contract_payload))

    if args.run_compile:
        app_files = sorted((root / "app").glob("*.py"))
        command = [sys.executable, "-m", "py_compile", *[str(path) for path in app_files]]
        ok, detail = run_subprocess(command, root)
        add_result(results, "test", "runtime:py_compile", ok, detail)

    if args.run_pytest:
        ok, detail = run_subprocess([str(root / "tools/bin/run-tests.sh"), "--suite", "all"], root)
        add_result(results, "test", "runtime:pytest", ok, detail)

    _, failed_checks, waived_checks, missing_domains = print_results(results, args.phase, task, waiver_payload)
    payload = build_report_payload(
        phase=args.phase,
        task=task,
        mode=mode,
        results=results,
        failed_checks=failed_checks,
        waived_checks=waived_checks,
        missing_domains=missing_domains,
        question_bank_modules=extract_question_bank_module_report(root) if mode == "questionBank" else [],
    )
    payload["contractPackage"] = {
        "path": contract_payload.get("_path", ""),
        "available": bool(contract_payload) and not bool(contract_payload.get("_invalid")),
        "invalid": bool(contract_payload.get("_invalid")) if contract_payload else False,
        "mode": contract_payload.get("mode", "") if isinstance(contract_payload, dict) else "",
        "contractId": contract_payload.get("contractId", "") if isinstance(contract_payload, dict) else "",
    }
    if args.report_md:
        write_report_file(args.report_md, render_markdown_report(payload))
    if args.report_json:
        write_report_file(args.report_json, json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failed_checks or missing_domains else 0


if __name__ == "__main__":
    sys.exit(main())
