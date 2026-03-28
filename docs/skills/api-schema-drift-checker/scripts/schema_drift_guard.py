#!/usr/bin/env python3
"""
API schema drift guard.

Detects drift across:
- Producer contracts: OpenAPI/Swagger + backend model files
- Consumer contracts: frontend type files + API call sites

The script is conservative and heuristic-based: warnings signal likely
inconsistency and should be triaged, not blindly ignored.
"""

from __future__ import annotations

import argparse
import ast
import glob
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD")
SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    "target",
    ".idea",
    ".vscode",
    "__pycache__",
    ".venv",
    "venv",
    "site-packages",
}
IGNORE_PATH_MARKERS = (
    "/docs/skills/",
    "/tests/",
    "/__tests__/",
    "/.codex-runtime/",
)
IGNORE_FILE_SUFFIXES = (
    ".test.ts",
    ".test.tsx",
    ".test.js",
    ".test.jsx",
    ".spec.ts",
    ".spec.tsx",
    ".spec.js",
    ".spec.jsx",
)
OPENAPI_FILE_RE = re.compile(r"(openapi|swagger).*\.(json|ya?ml)$", re.IGNORECASE)
MODEL_HINT_RE = re.compile(
    r"(dto|vo|entity|schema|model|response|request|contract|api)",
    re.IGNORECASE,
)
CONSUMER_HINT_RE = re.compile(
    r"(frontend|web|ui|client|api|service|request|types?|models?)",
    re.IGNORECASE,
)

TS_INTERFACE_RE = re.compile(r"(?:export\s+)?interface\s+([A-Za-z_]\w*)\s*\{", re.MULTILINE)
TS_TYPE_RE = re.compile(r"(?:export\s+)?type\s+([A-Za-z_]\w*)\s*=\s*\{", re.MULTILINE)
TS_ENUM_RE = re.compile(r"(?:export\s+)?enum\s+([A-Za-z_]\w*)\s*\{", re.MULTILINE)
TS_FIELD_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*(\?)?\s*:")
TS_QUOTED_FIELD_RE = re.compile(r'^\s*["\']([^"\']+)["\']\s*(\?)?\s*:')
TS_ENUM_MEMBER_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*(?:=|,|$)")

JAVA_CLASS_RE = re.compile(r"(?:public\s+)?(?:class|record)\s+([A-Za-z_]\w*)")
JAVA_ENUM_RE = re.compile(r"(?:public\s+)?enum\s+([A-Za-z_]\w*)\s*\{")
JAVA_FIELD_RE = re.compile(
    r"^\s*(?:private|protected|public)\s+(?!static)(?:final\s+)?[\w<>, ?\[\].]+\s+([A-Za-z_]\w*)\s*(?:;|=)",
)
JAVA_RECORD_RE = re.compile(r"record\s+([A-Za-z_]\w*)\s*\(([^)]*)\)")

AXIOS_CALL_START_RE = re.compile(r"\baxios\.(get|post|put|patch|delete|options|head)\s*\(", re.IGNORECASE)
FETCH_CALL_START_RE = re.compile(r"\bfetch\s*\(", re.IGNORECASE)
REQUEST_CALL_START_RE = re.compile(r"\brequest\s*\(", re.IGNORECASE)
CONST_DECL_RE = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_]\w*)\s*=")
IDENT_RE = re.compile(r"^[A-Za-z_]\w*$")

DEFAULT_PRODUCER_GLOBS = ("**/*dto*.ts", "**/*vo*.ts", "**/*entity*.ts", "**/*model*.ts")
DEFAULT_CONSUMER_GLOBS = ("**/src/**/*.ts", "**/src/**/*.tsx", "**/src/**/*.js", "**/src/**/*.jsx")

NAME_SUFFIXES = (
    "dto",
    "vo",
    "req",
    "request",
    "resp",
    "response",
    "model",
    "entity",
    "schema",
    "data",
    "payload",
)


@dataclass
class SchemaInfo:
    name: str
    fields: set[str] = field(default_factory=set)
    required: set[str] = field(default_factory=set)
    source_files: set[str] = field(default_factory=set)

    def merge(self, other: "SchemaInfo") -> None:
        self.fields.update(other.fields)
        self.required.update(other.required)
        self.source_files.update(other.source_files)


@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str


@dataclass
class ParseBundle:
    schemas: dict[str, SchemaInfo] = field(default_factory=dict)
    enums: dict[str, set[str]] = field(default_factory=dict)
    endpoints: set[Endpoint] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)

    def merge(self, other: "ParseBundle") -> None:
        for name, schema in other.schemas.items():
            if name not in self.schemas:
                self.schemas[name] = schema
            else:
                self.schemas[name].merge(schema)
        for name, members in other.enums.items():
            self.enums.setdefault(name, set()).update(members)
        self.endpoints.update(other.endpoints)
        self.notes.extend(other.notes)


@dataclass
class DriftIssue:
    severity: str
    category: str
    title: str
    detail: str
    evidence: list[str] = field(default_factory=list)
    fix_hint: str = ""


def run_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, check=False)


def find_git_root(cwd: Path) -> Path | None:
    result = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd)
    if result.returncode != 0:
        return None
    root = result.stdout.strip()
    return Path(root) if root else None


def parse_git_changed_files(root: Path) -> list[Path]:
    result = run_cmd(["git", "status", "--porcelain", "--untracked-files=all"], root)
    if result.returncode != 0:
        return []
    changed: list[Path] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line:
            continue
        payload = raw_line[3:] if len(raw_line) > 3 else raw_line
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        changed.append((root / payload).resolve())
    return changed


def read_text(path: Path, limit: int = 300_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def should_ignore_dir(name: str) -> bool:
    return (
        name in IGNORE_DIRS
        or name.startswith(".cache")
        or name.startswith(".venv")
        or name.startswith("venv")
    )


def should_ignore_file(path: Path) -> bool:
    normalized = path.as_posix().lower()
    filename = path.name.lower()
    if any(marker in normalized for marker in IGNORE_PATH_MARKERS):
        return True
    if filename.endswith(IGNORE_FILE_SUFFIXES):
        return True
    if filename.startswith("test_") and path.suffix.lower() == ".py":
        return True
    return False


def walk_files(root: Path, max_files: int) -> Iterable[Path]:
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_ignore_dir(d)]
        for filename in filenames:
            path = (Path(dirpath) / filename).resolve()
            if not path.is_file():
                continue
            if should_ignore_file(path):
                continue
            yield path
            count += 1
            if count >= max_files:
                return


def resolve_targets(root: Path, raw_values: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in raw_values:
        as_path = Path(raw)
        candidates: list[Path] = []
        if as_path.is_absolute():
            if as_path.exists():
                candidates = [as_path]
        else:
            rel = (root / raw).resolve()
            if rel.exists():
                candidates = [rel]
            else:
                pattern = str((root / raw).resolve())
                candidates = [Path(p) for p in glob.glob(pattern, recursive=True)]
        for candidate in candidates:
            if candidate.is_file():
                files.append(candidate.resolve())
            elif candidate.is_dir():
                for child in walk_files(candidate, max_files=20000):
                    files.append(child.resolve())
    return unique_paths(files)


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        result.append(path.resolve())
    return result


def discover_openapi_files(root: Path, max_files: int) -> list[Path]:
    out: list[Path] = []
    for path in walk_files(root, max_files=max_files):
        lowered = path.name.lower()
        if OPENAPI_FILE_RE.search(lowered):
            out.append(path)
    return unique_paths(out)


def discover_producer_model_files(root: Path, max_files: int) -> list[Path]:
    out: list[Path] = []
    for path in walk_files(root, max_files=max_files):
        suffix = path.suffix.lower()
        if suffix not in {".ts", ".tsx", ".js", ".jsx", ".java", ".py"}:
            continue
        normalized = path.as_posix().lower()
        if MODEL_HINT_RE.search(normalized):
            out.append(path)
    return unique_paths(out)


def discover_consumer_files(root: Path, max_files: int) -> list[Path]:
    out: list[Path] = []
    for path in walk_files(root, max_files=max_files):
        suffix = path.suffix.lower()
        if suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        normalized = path.as_posix().lower()
        if CONSUMER_HINT_RE.search(normalized):
            out.append(path)
    return unique_paths(out)


def normalize_path(raw: str, strip_prefixes: list[str]) -> str:
    path = raw.strip()
    if not path:
        return path
    path = re.sub(r"^https?://[^/]+", "", path)
    path = path.split("?", 1)[0]
    path = path.replace("`", "")
    path = re.sub(r"\$\{[^}]+\}", "{param}", path)
    path = re.sub(r"\{[^}/]+\}", "{param}", path)
    path = re.sub(r":[A-Za-z_]\w*", "{param}", path)
    path = re.sub(r"/\d+(?=/|$)", "/{param}", path)
    path = re.sub(r"/+", "/", path)
    if not path.startswith("/"):
        path = "/" + path
    for prefix in strip_prefixes:
        pref = prefix if prefix.startswith("/") else f"/{prefix}"
        if path == pref:
            path = "/"
            continue
        if path.startswith(pref + "/"):
            path = path[len(pref) :]
    return path.rstrip("/") or "/"


def extract_brace_block(text: str, brace_index: int) -> tuple[str, int] | None:
    depth = 0
    i = brace_index
    start = brace_index + 1
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    return None


def skip_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def extract_expression_until(text: str, start_index: int, stop_chars: set[str]) -> tuple[str, int]:
    i = start_index
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    quote: str | None = None
    escape = False
    while i < len(text):
        ch = text[i]
        if quote is not None:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in {"'", '"', "`"}:
            quote = ch
            i += 1
            continue
        if ch == "(":
            paren_depth += 1
        elif ch == ")":
            if paren_depth == 0 and ")" in stop_chars and bracket_depth == 0 and brace_depth == 0:
                break
            paren_depth = max(0, paren_depth - 1)
        elif ch == "[":
            bracket_depth += 1
        elif ch == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif ch == "{":
            brace_depth += 1
        elif ch == "}":
            brace_depth = max(0, brace_depth - 1)
        elif (
            ch in stop_chars
            and paren_depth == 0
            and bracket_depth == 0
            and brace_depth == 0
        ):
            break
        i += 1
    return text[start_index:i].strip(), i


def split_top_level(expr: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    start = 0
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    quote: str | None = None
    escape = False
    for i, ch in enumerate(expr):
        if quote is not None:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch in {"'", '"', "`"}:
            quote = ch
            continue
        if ch == "(":
            paren_depth += 1
            continue
        if ch == ")":
            paren_depth = max(0, paren_depth - 1)
            continue
        if ch == "[":
            bracket_depth += 1
            continue
        if ch == "]":
            bracket_depth = max(0, bracket_depth - 1)
            continue
        if ch == "{":
            brace_depth += 1
            continue
        if ch == "}":
            brace_depth = max(0, brace_depth - 1)
            continue
        if ch == delimiter and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            parts.append(expr[start:i].strip())
            start = i + 1
    parts.append(expr[start:].strip())
    return [part for part in parts if part]


def trim_wrapping_parentheses(expr: str) -> str:
    normalized = expr.strip()
    while normalized.startswith("(") and normalized.endswith(")"):
        inner, end_index = extract_expression_until(normalized, 1, {")"})
        if end_index != len(normalized) - 1:
            break
        normalized = inner.strip()
    return normalized


def extract_template_expression(text: str, start_index: int) -> tuple[str, int] | None:
    i = start_index
    depth = 1
    quote: str | None = None
    escape = False
    while i < len(text):
        ch = text[i]
        if quote is not None:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in {"'", '"', "`"}:
            quote = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start_index:i], i + 1
        i += 1
    return None


def parse_template_literal(content: str, constants: dict[str, str], depth: int) -> str:
    result: list[str] = []
    i = 0
    while i < len(content):
        if content.startswith("${", i):
            extracted = extract_template_expression(content, i + 2)
            if not extracted:
                result.append("{param}")
                break
            expression, next_index = extracted
            resolved = evaluate_js_string_expression(expression, constants, depth + 1)
            result.append(resolved if resolved is not None else "{param}")
            i = next_index
            continue
        result.append(content[i])
        i += 1
    return "".join(result)


def evaluate_js_string_expression(expr: str | None, constants: dict[str, str], depth: int = 0) -> str | None:
    if expr is None:
        return None
    if depth > 8:
        return None
    normalized = trim_wrapping_parentheses(expr.strip().rstrip(","))
    if not normalized:
        return None

    if ".replace(" in normalized:
        normalized = trim_wrapping_parentheses(normalized.split(".replace(", 1)[0])

    if IDENT_RE.match(normalized):
        return constants.get(normalized)

    plus_parts = split_top_level(normalized, "+")
    if len(plus_parts) > 1:
        resolved_parts: list[str] = []
        for part in plus_parts:
            resolved = evaluate_js_string_expression(part, constants, depth + 1)
            if resolved is None:
                return None
            resolved_parts.append(resolved)
        return "".join(resolved_parts)

    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {"'", '"', "`"}:
        quote = normalized[0]
        inner = normalized[1:-1]
        if quote == "`":
            return parse_template_literal(inner, constants, depth + 1)
        return inner

    return None


def extract_js_property_expression(block: str, property_name: str) -> str | None:
    match = re.search(rf"\b{re.escape(property_name)}\s*:\s*", block)
    if not match:
        return None
    expression, _ = extract_expression_until(block, match.end(), {","})
    return expression or None


def collect_string_constants(text: str) -> dict[str, str]:
    raw_expressions: dict[str, str] = {}
    for match in CONST_DECL_RE.finditer(text):
        name = match.group(1)
        expression, _ = extract_expression_until(text, match.end(), {";", "\n"})
        if expression:
            raw_expressions[name] = expression

    resolved: dict[str, str] = {}
    for _ in range(len(raw_expressions) + 1):
        progress = False
        for name, expression in raw_expressions.items():
            if name in resolved:
                continue
            value = evaluate_js_string_expression(expression, resolved)
            if value is not None:
                resolved[name] = value
                progress = True
        if not progress:
            break
    return resolved


def parse_ts_models_and_endpoints(path: Path, strip_prefixes: list[str]) -> ParseBundle:
    text = read_text(path)
    bundle = ParseBundle()
    if not text:
        return bundle

    for match in TS_INTERFACE_RE.finditer(text):
        name = match.group(1)
        block = extract_brace_block(text, match.end() - 1)
        if not block:
            continue
        schema = SchemaInfo(name=name, source_files={str(path)})
        fields, required = extract_ts_fields(block[0])
        schema.fields.update(fields)
        schema.required.update(required)
        merge_schema(bundle.schemas, schema)

    for match in TS_TYPE_RE.finditer(text):
        name = match.group(1)
        block = extract_brace_block(text, match.end() - 1)
        if not block:
            continue
        schema = SchemaInfo(name=name, source_files={str(path)})
        fields, required = extract_ts_fields(block[0])
        schema.fields.update(fields)
        schema.required.update(required)
        merge_schema(bundle.schemas, schema)

    for match in TS_ENUM_RE.finditer(text):
        name = match.group(1)
        block = extract_brace_block(text, match.end() - 1)
        if not block:
            continue
        members = extract_ts_enum_members(block[0])
        if members:
            bundle.enums.setdefault(name, set()).update(members)

    should_parse_calls = "api" in path.as_posix().lower() or "service" in path.as_posix().lower()
    if should_parse_calls:
        bundle.endpoints.update(extract_endpoints_from_text(text, strip_prefixes))
    return bundle


def extract_ts_fields(block: str) -> tuple[set[str], set[str]]:
    fields: set[str] = set()
    required: set[str] = set()
    for line in block.splitlines():
        pure = line.split("//", 1)[0].strip()
        if not pure or pure.startswith("["):
            continue
        match = TS_FIELD_RE.match(pure)
        if not match:
            match = TS_QUOTED_FIELD_RE.match(pure)
        if not match:
            continue
        name = match.group(1)
        optional_mark = match.group(2)
        fields.add(name)
        if optional_mark != "?":
            required.add(name)
    return fields, required


def extract_ts_enum_members(block: str) -> set[str]:
    members: set[str] = set()
    for line in block.splitlines():
        pure = line.split("//", 1)[0].strip()
        if not pure:
            continue
        match = TS_ENUM_MEMBER_RE.match(pure)
        if match:
            members.add(match.group(1))
    return members


def parse_java_models(path: Path) -> ParseBundle:
    text = read_text(path)
    bundle = ParseBundle()
    if not text:
        return bundle

    for match in JAVA_ENUM_RE.finditer(text):
        name = match.group(1)
        block = extract_brace_block(text, match.end() - 1)
        if not block:
            continue
        members = set()
        head = block[0].split(";", 1)[0]
        for piece in head.split(","):
            token = piece.strip()
            if not token:
                continue
            token = re.sub(r"\(.*\)", "", token).strip()
            if re.match(r"^[A-Z_]\w*$", token):
                members.add(token)
        if members:
            bundle.enums.setdefault(name, set()).update(members)

    for record_match in JAVA_RECORD_RE.finditer(text):
        record_name = record_match.group(1)
        params = record_match.group(2)
        schema = SchemaInfo(name=record_name, source_files={str(path)})
        for token in params.split(","):
            token = token.strip()
            if not token:
                continue
            field_name = token.split()[-1]
            field_name = field_name.replace("...", "").strip()
            if re.match(r"^[A-Za-z_]\w*$", field_name):
                schema.fields.add(field_name)
        if schema.fields:
            merge_schema(bundle.schemas, schema)

    for class_match in JAVA_CLASS_RE.finditer(text):
        name = class_match.group(1)
        start = text.find("{", class_match.end())
        if start == -1:
            continue
        block = extract_brace_block(text, start)
        if not block:
            continue
        schema = SchemaInfo(name=name, source_files={str(path)})
        for line in block[0].splitlines():
            field_match = JAVA_FIELD_RE.match(line.strip())
            if field_match:
                schema.fields.add(field_match.group(1))
        if schema.fields:
            merge_schema(bundle.schemas, schema)
    return bundle


def parse_python_models(path: Path) -> ParseBundle:
    source = read_text(path)
    bundle = ParseBundle()
    if not source:
        return bundle
    try:
        tree = ast.parse(source)
    except SyntaxError:
        bundle.notes.append(f"Skip unparsable Python file: {path}")
        return bundle

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        class_name = node.name
        schema = SchemaInfo(name=class_name, source_files={str(path)})
        is_enum = any(getattr(base, "id", "") == "Enum" or getattr(base, "attr", "") == "Enum" for base in node.bases)
        if is_enum:
            members: set[str] = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            members.add(target.id)
            if members:
                bundle.enums.setdefault(class_name, set()).update(members)
            continue
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                schema.fields.add(item.target.id)
            elif isinstance(item, ast.Assign):
                if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                    target = item.targets[0]
                    if not target.id.startswith("_"):
                        schema.fields.add(target.id)
        if schema.fields:
            merge_schema(bundle.schemas, schema)
    return bundle


def extract_endpoints_from_text(text: str, strip_prefixes: list[str]) -> set[Endpoint]:
    endpoints: set[Endpoint] = set()
    constants = collect_string_constants(text)

    for match in AXIOS_CALL_START_RE.finditer(text):
        method = match.group(1).upper()
        argument_expr, _ = extract_expression_until(text, match.end(), {",", ")"})
        path_raw = evaluate_js_string_expression(argument_expr, constants)
        if not path_raw:
            continue
        endpoints.add(Endpoint(method=method, path=normalize_path(path_raw, strip_prefixes)))

    for match in FETCH_CALL_START_RE.finditer(text):
        path_expr, end_index = extract_expression_until(text, match.end(), {",", ")"})
        path_raw = evaluate_js_string_expression(path_expr, constants)
        if not path_raw:
            continue
        method = "GET"
        cursor = skip_whitespace(text, end_index)
        if cursor < len(text) and text[cursor] == ",":
            cursor = skip_whitespace(text, cursor + 1)
            if cursor < len(text) and text[cursor] == "{":
                options_block = extract_brace_block(text, cursor)
                if options_block:
                    method_expr = extract_js_property_expression(options_block[0], "method")
                    method_raw = evaluate_js_string_expression(method_expr, constants) if method_expr else None
                    if method_raw:
                        method = method_raw.upper()
        endpoints.add(Endpoint(method=method, path=normalize_path(path_raw, strip_prefixes)))

    for match in REQUEST_CALL_START_RE.finditer(text):
        cursor = skip_whitespace(text, match.end())
        if cursor >= len(text) or text[cursor] != "{":
            continue
        block = extract_brace_block(text, cursor)
        if not block:
            continue
        obj = block[0]
        url_expr = extract_js_property_expression(obj, "url")
        path_raw = evaluate_js_string_expression(url_expr, constants)
        if not path_raw:
            continue
        method_expr = extract_js_property_expression(obj, "method")
        method_raw = evaluate_js_string_expression(method_expr, constants) if method_expr else None
        method = (method_raw or "GET").upper()
        endpoints.add(Endpoint(method=method, path=normalize_path(path_raw, strip_prefixes)))

    return endpoints


def merge_schema(target: dict[str, SchemaInfo], incoming: SchemaInfo) -> None:
    if incoming.name not in target:
        target[incoming.name] = incoming
        return
    target[incoming.name].merge(incoming)


def parse_openapi_file(path: Path, strip_prefixes: list[str]) -> ParseBundle:
    bundle = ParseBundle()
    text = read_text(path)
    if not text:
        return bundle
    suffix = path.suffix.lower()
    data: dict | None = None
    try:
        if suffix == ".json":
            data = json.loads(text)
        elif suffix in {".yaml", ".yml"}:
            if yaml is None:
                bundle.notes.append(
                    f"Cannot parse YAML OpenAPI file without PyYAML: {path}. Install pyyaml to enable it."
                )
                return bundle
            loaded = yaml.safe_load(text)
            if isinstance(loaded, dict):
                data = loaded
        else:
            bundle.notes.append(f"Skip unsupported OpenAPI suffix: {path}")
            return bundle
    except Exception as exc:
        bundle.notes.append(f"Failed to parse OpenAPI file {path}: {exc}")
        return bundle

    if not isinstance(data, dict):
        bundle.notes.append(f"OpenAPI root is not an object: {path}")
        return bundle

    components = data.get("components", {})
    schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
    if isinstance(schemas, dict):
        for schema_name, node in schemas.items():
            if not isinstance(node, dict):
                continue
            schema = SchemaInfo(name=str(schema_name), source_files={str(path)})
            fields, required = parse_openapi_object_fields(node)
            schema.fields.update(fields)
            schema.required.update(required)
            if schema.fields:
                merge_schema(bundle.schemas, schema)
            enum_values = node.get("enum")
            if isinstance(enum_values, list):
                members = {str(x) for x in enum_values if isinstance(x, (str, int, float))}
                if members:
                    bundle.enums.setdefault(str(schema_name), set()).update(members)

    paths = data.get("paths", {})
    if isinstance(paths, dict):
        for raw_path, item in paths.items():
            if not isinstance(item, dict):
                continue
            for method in HTTP_METHODS:
                lower = method.lower()
                if lower in item:
                    bundle.endpoints.add(Endpoint(method=method, path=normalize_path(str(raw_path), strip_prefixes)))
    return bundle


def parse_openapi_object_fields(node: dict) -> tuple[set[str], set[str]]:
    fields: set[str] = set()
    required: set[str] = set()

    props = node.get("properties", {})
    if isinstance(props, dict):
        for key in props:
            fields.add(str(key))

    req = node.get("required", [])
    if isinstance(req, list):
        required.update(str(item) for item in req if isinstance(item, (str, int, float)))

    all_of = node.get("allOf", [])
    if isinstance(all_of, list):
        for part in all_of:
            if not isinstance(part, dict):
                continue
            sub_fields, sub_required = parse_openapi_object_fields(part)
            fields.update(sub_fields)
            required.update(sub_required)

    return fields, required


def parse_files_as_bundle(files: list[Path], strip_prefixes: list[str]) -> ParseBundle:
    bundle = ParseBundle()
    for path in files:
        suffix = path.suffix.lower()
        try:
            if suffix in {".ts", ".tsx", ".js", ".jsx"}:
                bundle.merge(parse_ts_models_and_endpoints(path, strip_prefixes))
            elif suffix == ".java":
                bundle.merge(parse_java_models(path))
            elif suffix == ".py":
                bundle.merge(parse_python_models(path))
        except Exception as exc:  # pragma: no cover
            bundle.notes.append(f"Error parsing {path}: {exc}")
    return bundle


def parse_openapi_files(files: list[Path], strip_prefixes: list[str]) -> ParseBundle:
    bundle = ParseBundle()
    for path in files:
        bundle.merge(parse_openapi_file(path, strip_prefixes))
    return bundle


def canonical_name(name: str) -> str:
    n = re.sub(r"[^A-Za-z0-9]", "", name).lower()
    for suffix in NAME_SUFFIXES:
        if n.endswith(suffix) and len(n) > len(suffix) + 2:
            n = n[: -len(suffix)]
            break
    return n


def load_alias_map(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    aliases: dict[str, str] = {}
    if not isinstance(data, dict):
        return aliases

    for key, value in data.items():
        if isinstance(value, str):
            aliases[key] = value
    if isinstance(data.get("producer_to_consumer"), dict):
        for key, value in data["producer_to_consumer"].items():
            if isinstance(key, str) and isinstance(value, str):
                aliases[key] = value
    if isinstance(data.get("consumer_to_producer"), dict):
        for key, value in data["consumer_to_producer"].items():
            if isinstance(key, str) and isinstance(value, str):
                aliases[value] = key
    return aliases


def match_schema_names(
    producer_names: set[str],
    consumer_names: set[str],
    aliases: dict[str, str],
) -> tuple[list[tuple[str, str, str]], set[str], set[str]]:
    pairs: list[tuple[str, str, str]] = []
    matched_producer: set[str] = set()
    matched_consumer: set[str] = set()

    for p, c in aliases.items():
        if p in producer_names and c in consumer_names:
            pairs.append((p, c, "alias"))
            matched_producer.add(p)
            matched_consumer.add(c)

    for name in sorted(producer_names):
        if name in matched_producer:
            continue
        if name in consumer_names and name not in matched_consumer:
            pairs.append((name, name, "exact"))
            matched_producer.add(name)
            matched_consumer.add(name)

    remaining_p = sorted(producer_names - matched_producer)
    remaining_c = sorted(consumer_names - matched_consumer)
    by_canonical_p: dict[str, list[str]] = {}
    by_canonical_c: dict[str, list[str]] = {}
    for name in remaining_p:
        by_canonical_p.setdefault(canonical_name(name), []).append(name)
    for name in remaining_c:
        by_canonical_c.setdefault(canonical_name(name), []).append(name)

    for key in sorted(by_canonical_p):
        p_items = by_canonical_p[key]
        c_items = by_canonical_c.get(key, [])
        if len(p_items) == 1 and len(c_items) == 1:
            p_name, c_name = p_items[0], c_items[0]
            pairs.append((p_name, c_name, "canonical"))
            matched_producer.add(p_name)
            matched_consumer.add(c_name)

    return pairs, producer_names - matched_producer, consumer_names - matched_consumer


def equivalent_endpoint(target: Endpoint, candidates: set[Endpoint]) -> bool:
    if target in candidates:
        return True
    for candidate in candidates:
        if candidate.method != target.method:
            continue
        if candidate.path.endswith(target.path) or target.path.endswith(candidate.path):
            return True
    return False


def add_issue(
    issues: list[DriftIssue],
    severity: str,
    category: str,
    title: str,
    detail: str,
    evidence: list[str] | None = None,
    fix_hint: str = "",
) -> None:
    issues.append(
        DriftIssue(
            severity=severity,
            category=category,
            title=title,
            detail=detail,
            evidence=evidence or [],
            fix_hint=fix_hint,
        )
    )


def compare_contracts(
    producer: ParseBundle,
    consumer: ParseBundle,
    openapi: ParseBundle,
    aliases: dict[str, str],
) -> list[DriftIssue]:
    issues: list[DriftIssue] = []

    producer_schemas = dict(producer.schemas)
    for name, schema in openapi.schemas.items():
        if name not in producer_schemas:
            producer_schemas[name] = schema
        else:
            producer_schemas[name].merge(schema)

    producer_enums = dict(producer.enums)
    for name, enum_values in openapi.enums.items():
        producer_enums.setdefault(name, set()).update(enum_values)

    if not producer_schemas:
        add_issue(
            issues,
            "high",
            "producer",
            "No producer schemas detected",
            "No backend/OpenAPI schema could be extracted. Drift check coverage is not reliable.",
            fix_hint="Provide --openapi or --producer paths that contain schema contracts.",
        )
    if not consumer.schemas:
        add_issue(
            issues,
            "high",
            "consumer",
            "No consumer schemas detected",
            "No frontend type schema was extracted. Unable to verify field-level drift.",
            fix_hint="Provide --consumer path pointing to frontend type/interface files.",
        )

    pairs, unmatched_p, unmatched_c = match_schema_names(
        set(producer_schemas.keys()), set(consumer.schemas.keys()), aliases
    )

    for producer_name, consumer_name, match_rule in pairs:
        p_schema = producer_schemas[producer_name]
        c_schema = consumer.schemas[consumer_name]
        missing_required = sorted(p_schema.required - c_schema.fields)
        missing_total = sorted(p_schema.fields - c_schema.fields)
        missing_optional = [field for field in missing_total if field not in p_schema.required]
        extra_consumer = sorted(c_schema.fields - p_schema.fields)

        if missing_required:
            add_issue(
                issues,
                "high",
                "field",
                f"Required fields missing in consumer ({producer_name} -> {consumer_name})",
                "Consumer schema misses fields marked as required by producer contract.",
                evidence=missing_required[:10],
                fix_hint="Update frontend type and parser logic to include all required fields.",
            )
        if missing_optional:
            add_issue(
                issues,
                "medium",
                "field",
                f"Optional fields missing in consumer ({producer_name} -> {consumer_name})",
                f"Producer has {len(missing_optional)} additional optional fields; potential stale typing. Match rule: {match_rule}.",
                evidence=missing_optional[:10],
                fix_hint="Decide whether fields should be consumed; if yes update consumer type, otherwise document intentional ignore.",
            )
        if extra_consumer:
            add_issue(
                issues,
                "medium",
                "field",
                f"Consumer has fields not in producer ({consumer_name})",
                "Consumer schema contains fields not found in producer contract; likely stale aliases or contract drift.",
                evidence=extra_consumer[:10],
                fix_hint="Remove stale fields or align producer contract if fields are still valid.",
            )

    if unmatched_p:
        add_issue(
            issues,
            "medium",
            "schema",
            "Producer schemas not matched by consumer",
            "Some producer models cannot be mapped to frontend types, causing blind spots.",
            evidence=sorted(unmatched_p)[:20],
            fix_hint="Add alias mapping via --alias-map or define corresponding consumer type models.",
        )
    if unmatched_c:
        add_issue(
            issues,
            "medium",
            "schema",
            "Consumer schemas not matched by producer",
            "Some consumer models do not map to any producer model; they may be stale or speculative.",
            evidence=sorted(unmatched_c)[:20],
            fix_hint="Delete obsolete consumer models or map them to real producer schemas.",
        )

    enum_pairs, _, _ = match_schema_names(set(producer_enums.keys()), set(consumer.enums.keys()), aliases)
    for producer_name, consumer_name, _ in enum_pairs:
        p_values = producer_enums.get(producer_name, set())
        c_values = consumer.enums.get(consumer_name, set())
        missing_values = sorted(p_values - c_values)
        extra_values = sorted(c_values - p_values)
        if missing_values:
            add_issue(
                issues,
                "high",
                "enum",
                f"Enum members missing in consumer ({producer_name} -> {consumer_name})",
                "Consumer enum misses producer members and can cause invalid status rendering or submit failures.",
                evidence=missing_values[:15],
                fix_hint="Sync enum members across backend and frontend in one commit.",
            )
        if extra_values:
            add_issue(
                issues,
                "medium",
                "enum",
                f"Consumer enum has extra members ({consumer_name})",
                "Consumer enum contains values not present in producer contract.",
                evidence=extra_values[:15],
                fix_hint="Remove deprecated enum values or ensure producer contract includes them.",
            )

    openapi_endpoints = openapi.endpoints
    consumer_endpoints = consumer.endpoints
    if openapi_endpoints and consumer_endpoints:
        unknown_calls = [ep for ep in sorted(consumer_endpoints, key=lambda x: (x.method, x.path)) if not equivalent_endpoint(ep, openapi_endpoints)]
        undocumented_apis = [ep for ep in sorted(openapi_endpoints, key=lambda x: (x.method, x.path)) if not equivalent_endpoint(ep, consumer_endpoints)]
        if unknown_calls:
            add_issue(
                issues,
                "high",
                "endpoint",
                "Consumer calls not found in OpenAPI",
                "Frontend request method/path cannot be matched in documented API contract.",
                evidence=[f"{ep.method} {ep.path}" for ep in unknown_calls[:20]],
                fix_hint="Fix wrong URL/method, or update OpenAPI and regenerate frontend contracts.",
            )
        if undocumented_apis:
            add_issue(
                issues,
                "low",
                "endpoint",
                "Documented APIs not referenced by consumer",
                "Some OpenAPI endpoints are not detected in frontend call sites.",
                evidence=[f"{ep.method} {ep.path}" for ep in undocumented_apis[:20]],
                fix_hint="If APIs are valid but unused, keep as low priority; if deprecated, clean docs/contracts.",
            )
    elif consumer_endpoints and not openapi_endpoints:
        add_issue(
            issues,
            "medium",
            "endpoint",
            "Consumer endpoints detected but OpenAPI endpoints missing",
            "Unable to validate URL/method drift without OpenAPI path definitions.",
            fix_hint="Provide parseable OpenAPI file with --openapi.",
        )

    return dedupe_issues(issues)


def dedupe_issues(issues: list[DriftIssue]) -> list[DriftIssue]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[DriftIssue] = []
    for issue in issues:
        key = (issue.severity, issue.category, issue.title, issue.detail)
        if key in seen:
            continue
        seen.add(key)
        result.append(issue)
    return result


def severity_meets_threshold(issue_severity: str, threshold: str) -> bool:
    if threshold == "none":
        return False
    return SEVERITY_RANK[issue_severity] <= SEVERITY_RANK[threshold]


def compute_threshold(phase: str, fail_on: str) -> str:
    if fail_on != "auto":
        return fail_on
    if phase == "start":
        return "none"
    return "high"


def render_report(
    phase: str,
    cwd: Path,
    git_root: Path | None,
    openapi_files: list[Path],
    producer_files: list[Path],
    consumer_files: list[Path],
    producer_bundle: ParseBundle,
    consumer_bundle: ParseBundle,
    openapi_bundle: ParseBundle,
    issues: list[DriftIssue],
    threshold: str,
) -> str:
    lines: list[str] = []
    lines.append(f"API Schema Drift Guard: {phase}")
    lines.append(f"Working directory: {cwd}")
    lines.append(f"Git root: {git_root if git_root else 'not detected'}")
    lines.append(f"Fail threshold: {threshold}")
    lines.append(
        "Inputs: "
        f"openapi={len(openapi_files)} producer-model-files={len(producer_files)} consumer-files={len(consumer_files)}"
    )
    lines.append(
        "Extracted: "
        f"producer-schemas={len(producer_bundle.schemas) + len(openapi_bundle.schemas)} "
        f"consumer-schemas={len(consumer_bundle.schemas)} "
        f"openapi-endpoints={len(openapi_bundle.endpoints)} "
        f"consumer-endpoints={len(consumer_bundle.endpoints)}"
    )

    notes = producer_bundle.notes + consumer_bundle.notes + openapi_bundle.notes
    if notes:
        lines.append("Notes:")
        for note in notes[:10]:
            lines.append(f"  - {note}")
        if len(notes) > 10:
            lines.append(f"  - ... {len(notes) - 10} more")

    if not issues:
        lines.append("Drift issues: none")
        return "\n".join(lines)

    lines.append("Drift issues:")
    for severity in ("high", "medium", "low"):
        chunk = [item for item in issues if item.severity == severity]
        if not chunk:
            continue
        lines.append(f"  [{severity.upper()}] {len(chunk)}")
        for item in chunk:
            lines.append(f"    - ({item.category}) {item.title}: {item.detail}")
            if item.evidence:
                lines.append(f"      evidence: {', '.join(item.evidence[:10])}")
            if item.fix_hint:
                lines.append(f"      fix: {item.fix_hint}")
    return "\n".join(lines)


def write_reports(markdown_path: Path | None, json_path: Path | None, content: str, issues: list[DriftIssue]) -> None:
    if markdown_path:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(content + "\n", encoding="utf-8")
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "severity": issue.severity,
                "category": issue.category,
                "title": issue.title,
                "detail": issue.detail,
                "evidence": issue.evidence,
                "fix_hint": issue.fix_hint,
            }
            for issue in issues
        ]
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect API schema drift across backend/OpenAPI/frontend.")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="", help="Optional user task text, for report context.")
    parser.add_argument("--cwd", default=os.getcwd(), help="Project root. Defaults to current directory.")

    parser.add_argument("--openapi", action="append", default=[], help="OpenAPI file/dir/glob. Repeatable.")
    parser.add_argument("--producer", action="append", default=[], help="Producer model file/dir/glob. Repeatable.")
    parser.add_argument("--consumer", action="append", default=[], help="Consumer file/dir/glob. Repeatable.")
    parser.add_argument("--changed-file", action="append", default=[], help="Explicit changed file path, repeatable.")
    parser.add_argument("--alias-map", default="", help="JSON mapping for producer/consumer schema names.")
    parser.add_argument("--strip-prefix", action="append", default=[], help="Strip URL prefix before endpoint matching.")

    parser.add_argument(
        "--fail-on",
        choices=("auto", "none", "high", "medium", "low"),
        default="auto",
        help="Severity threshold to fail with non-zero exit code.",
    )
    parser.add_argument("--max-files", type=int, default=6000, help="Max file walk size for discovery.")
    parser.add_argument("--report-md", default="", help="Optional markdown report output path.")
    parser.add_argument("--report-json", default="", help="Optional JSON report output path.")
    return parser.parse_args()


def build_default_files(root: Path, max_files: int) -> tuple[list[Path], list[Path], list[Path]]:
    openapi_files = discover_openapi_files(root, max_files=max_files)
    producer_files = discover_producer_model_files(root, max_files=max_files)
    consumer_files = discover_consumer_files(root, max_files=max_files)
    return openapi_files, producer_files, consumer_files


def select_files(
    root: Path,
    explicit: list[Path],
    defaults: list[Path],
    allowed_suffixes: set[str],
) -> list[Path]:
    selected = explicit if explicit else defaults
    return [path for path in unique_paths(selected) if path.suffix.lower() in allowed_suffixes]


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).resolve()
    git_root = find_git_root(cwd)
    threshold = compute_threshold(args.phase, args.fail_on)

    explicit_openapi = resolve_targets(cwd, args.openapi)
    explicit_producer = resolve_targets(cwd, args.producer)
    explicit_consumer = resolve_targets(cwd, args.consumer)

    default_openapi, default_producer, default_consumer = build_default_files(cwd, max_files=args.max_files)
    openapi_files = select_files(cwd, explicit_openapi, default_openapi, {".json", ".yaml", ".yml"})
    producer_files = select_files(
        cwd,
        explicit_producer,
        default_producer,
        {".ts", ".tsx", ".js", ".jsx", ".java", ".py"},
    )
    consumer_files = select_files(cwd, explicit_consumer, default_consumer, {".ts", ".tsx", ".js", ".jsx"})

    openapi_bundle = parse_openapi_files(openapi_files, strip_prefixes=args.strip_prefix)
    producer_bundle = parse_files_as_bundle(producer_files, strip_prefixes=args.strip_prefix)
    consumer_bundle = parse_files_as_bundle(consumer_files, strip_prefixes=args.strip_prefix)

    alias_path = Path(args.alias_map).resolve() if args.alias_map else None
    aliases = load_alias_map(alias_path)
    issues = compare_contracts(
        producer=producer_bundle,
        consumer=consumer_bundle,
        openapi=openapi_bundle,
        aliases=aliases,
    )

    report = render_report(
        phase=args.phase,
        cwd=cwd,
        git_root=git_root,
        openapi_files=openapi_files,
        producer_files=producer_files,
        consumer_files=consumer_files,
        producer_bundle=producer_bundle,
        consumer_bundle=consumer_bundle,
        openapi_bundle=openapi_bundle,
        issues=issues,
        threshold=threshold,
    )
    print(report)

    markdown_path = Path(args.report_md).resolve() if args.report_md else None
    json_path = Path(args.report_json).resolve() if args.report_json else None
    write_reports(markdown_path, json_path, report, issues)

    fail = any(severity_meets_threshold(issue.severity, threshold) for issue in issues)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
