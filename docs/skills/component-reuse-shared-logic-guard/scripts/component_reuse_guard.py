#!/usr/bin/env python3
"""
Lightweight guard for component-reuse-shared-logic-guard.

This script focuses on implementation-layer convergence:
- direct axios/fetch usage in page/component code
- pagination / time-field / extJson drift
- duplicated table/search/modal logic in changed frontend files

It is intentionally heuristic. Warnings indicate likely drift and the expected
public-layer extraction direction, not a full semantic proof.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
NOISE_DIR_PARTS = {
    ".codex-runtime",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".screenshots",
    "node_modules",
    "dist",
    "build",
    "coverage",
}
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
    ".lock",
}
FRONTEND_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".vue"}
BACKEND_EXTENSIONS = {".java", ".kt", ".py", ".go", ".ts", ".js"}
PAGE_PATH_HINTS = ("page", "pages", "view", "views", "component", "components")
REQUEST_ALLOWLIST_HINTS = (
    "/src/api/request.",
    "/src/utils/request.",
    "/api/request.",
    "/utils/request.",
    "/services/request.",
)
PAGINATION_DRIFT_PATTERNS = (
    re.compile(r"\.(rows|records|list)\b"),
    re.compile(r"\[['\"](rows|records|list)['\"]\]"),
    re.compile(r"\b(rows|records|list)\s*:"),
)


@dataclass
class WarningItem:
    code: str
    severity: str
    message: str
    category: str = ""
    file: str = ""
    suggestion: str = ""
    target_public_layer: str = ""
    evidence: str = ""


@dataclass
class MigrationItem:
    category: str
    module: str
    location: str
    current_drift: str
    target_public_layer: str
    risk: str
    blocking: bool
    next_batch: str
    suggestion: str


@dataclass
class PublicLayer:
    name: str
    path: str
    kind: str
    usage_count: int
    exists: bool = True
    prop_count: int = 0
    default_prop_count: int = 0
    emit_count: int = 0
    prop_names: list[str] | None = None
    emit_names: list[str] | None = None
    slot_names: list[str] | None = None
    has_internal_footer_template: bool = False
    has_model_value_bridge: bool = False
    overlay_tag: str = ""


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
        changed.append((root / line).resolve())
    return changed


def is_noise_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if any(part in parts for part in NOISE_DIR_PARTS):
        return True
    return path.suffix.lower() in NOISE_SUFFIXES


def read_text(path: Path, limit: int = 200_000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def compute_threshold(phase: str, fail_on: str) -> str:
    if fail_on != "auto":
        return fail_on
    return "none" if phase == "start" else "high"


def warning_meets_threshold(severity: str, threshold: str) -> bool:
    if threshold == "none":
        return False
    return SEVERITY_RANK[severity] <= SEVERITY_RANK[threshold]


def dedupe_warnings(items: list[WarningItem]) -> list[WarningItem]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[WarningItem] = []
    for item in items:
        key = (item.code, item.severity, item.message, item.file)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def count_component_usages(cwd: Path, component_name: str, component_path: Path) -> int:
    frontend_root = cwd / "frontend" / "src"
    if not frontend_root.exists():
        return 0
    count = 0
    for path in frontend_root.rglob("*"):
        if path == component_path or path.suffix.lower() not in FRONTEND_EXTENSIONS or not path.is_file():
            continue
        text = read_text(path, limit=80_000)
        if not text:
            continue
        if re.search(rf"\b{re.escape(component_name)}\b", text):
            count += 1
    return count


def extract_define_props_block(text: str) -> str:
    match = re.search(r"defineProps\s*\(\s*\{", text)
    if not match:
        return ""
    start = match.end() - 1
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return ""


def analyze_vue_component_capabilities(path: Path) -> tuple[int, int, int, list[str], list[str], list[str], bool, bool, str]:
    text = read_text(path)
    if not text:
        return 0, 0, 0, [], [], [], False, False, ""

    props_block = extract_define_props_block(text)
    prop_names = set()
    if props_block:
        for match in re.finditer(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*\{", props_block, re.MULTILINE):
            prop_names.add(match.group(1))
    default_prop_count = len(re.findall(r"\bdefault\s*:", props_block))

    emit_count = 0
    emit_names: list[str] = []
    emits_match = re.search(r"defineEmits\s*\(\s*\[([^\]]*)\]\s*\)", text, re.DOTALL)
    if emits_match:
        emit_names = [
            match.group(0).strip("'\"")
            for match in re.finditer(r"['\"]([^'\"]+)['\"]", emits_match.group(1))
        ]
        emit_count = len(emit_names)

    slot_names: list[str] = []
    for match in re.finditer(r"<slot(?:\s+name=[\"']([^\"']+)[\"'])?", text):
        slot_name = match.group(1) or "default"
        if slot_name not in slot_names:
            slot_names.append(slot_name)

    has_internal_footer_template = "<template #footer>" in text
    has_model_value_bridge = "props.modelValue" in text and "update:modelValue" in text
    overlay_tag = "dialog" if "<el-dialog" in text else "drawer" if "<el-drawer" in text else ""
    return (
        len(prop_names),
        default_prop_count,
        emit_count,
        sorted(prop_names),
        emit_names,
        slot_names,
        has_internal_footer_template,
        has_model_value_bridge,
        overlay_tag,
    )


def public_layer_capability_gaps(layer: PublicLayer) -> list[str]:
    gaps: list[str] = []
    if layer.prop_count > 0 and layer.default_prop_count < layer.prop_count:
        gaps.append("missing-defaults")
    if layer.emit_count == 0 and layer.kind not in {"request-wrapper", "composable"}:
        gaps.append("missing-events")
    if layer.kind in {"filter-panel", "business-dialog", "business-drawer", "question-card"} and not (layer.slot_names or []):
        gaps.append("missing-slots")
    return gaps


def capability_gap_labels(layer: PublicLayer) -> list[str]:
    mapping = {
        "missing-defaults": "default values",
        "missing-events": "emits/events",
        "missing-slots": "slots",
    }
    return [mapping[item] for item in public_layer_capability_gaps(layer)]


def discover_public_layers(cwd: Path) -> dict[str, PublicLayer]:
    candidates = {
        "BaseFilterPanel": ("frontend/src/components/common/BaseFilterPanel.vue", "filter-panel"),
        "FilterPanel": ("frontend/src/components/common/FilterPanel.vue", "filter-panel"),
        "QuestionCard": ("frontend/src/components/core/QuestionCard.vue", "question-card"),
        "AiGenerationDialog": ("frontend/src/components/papers/AiGenerationDialog.vue", "business-dialog"),
        "QuestionSelectionDrawer": ("frontend/src/components/papers/QuestionSelectionDrawer.vue", "business-drawer"),
        "request": ("frontend/src/api/request.js", "request-wrapper"),
        "useAiMarking": ("frontend/src/composables/useAiMarking.js", "composable"),
    }
    inventory: dict[str, PublicLayer] = {}
    for name, (relative_path, kind) in candidates.items():
        path = cwd / relative_path
        if not path.exists():
            continue
        usage_count = count_component_usages(cwd, name, path) if kind != "request-wrapper" else 0
        prop_count, default_prop_count, emit_count, prop_names, emit_names, slot_names, has_internal_footer_template, has_model_value_bridge, overlay_tag = (
            analyze_vue_component_capabilities(path) if path.suffix == ".vue" else (0, 0, 0, [], [], [], False, False, "")
        )
        inventory[name] = PublicLayer(
            name=name,
            path=str(path.resolve()),
            kind=kind,
            usage_count=usage_count,
            prop_count=prop_count,
            default_prop_count=default_prop_count,
            emit_count=emit_count,
            prop_names=prop_names,
            emit_names=emit_names,
            slot_names=slot_names,
            has_internal_footer_template=has_internal_footer_template,
            has_model_value_bridge=has_model_value_bridge,
            overlay_tag=overlay_tag,
        )
    return inventory


def imported_component_names(text: str) -> set[str]:
    names = set()
    for match in re.finditer(r"import\s+([A-Za-z0-9_]+)\s+from\s+[\"'][^\"']+[\"']", text):
        names.add(match.group(1))
    return names


def is_frontend_code_file(path: Path) -> bool:
    if path.suffix.lower() not in FRONTEND_EXTENSIONS:
        return False
    normalized = path.as_posix().lower()
    return "frontend" in normalized or any(hint in normalized for hint in PAGE_PATH_HINTS)


def is_backend_code_file(path: Path) -> bool:
    if path.suffix.lower() not in BACKEND_EXTENSIONS:
        return False
    normalized = path.as_posix().lower()
    return any(
        token in normalized
        for token in ("backend", "server", "service", "controller", "entity", "model", "dto", "vo", "app/")
    )


def looks_like_request_wrapper(path: Path) -> bool:
    normalized = path.as_posix().lower()
    return any(hint in normalized for hint in REQUEST_ALLOWLIST_HINTS)


def contains_direct_request_usage(text: str) -> bool:
    return bool(
        re.search(r'from\s+[\'"]axios[\'"]', text)
        or re.search(r"\baxios\.", text)
        or re.search(r"\bfetch\s*\(", text)
    )


def detect_duplicate_frontend_patterns(path: Path, text: str) -> tuple[bool, bool]:
    normalized = path.as_posix().lower()
    table_tokens = sum(
        1
        for token in (
            "currentPage",
            "pageSize",
            "total",
            "handleSearch",
            "handleReset",
            "loadList",
            "pagination",
        )
        if token in text
    )
    modal_tokens = sum(
        1
        for token in (
            "dialogVisible",
            "drawerVisible",
            "handleSubmit",
            "handleCancel",
            "resetForm",
            "submitForm",
        )
        if token in text
    )
    table_like = table_tokens >= 3 and any(
        token in normalized for token in ("page", "pages", "view", "views", "component")
    )
    modal_like = modal_tokens >= 3 and any(
        token in normalized for token in ("dialog", "drawer", "form", "page", "view", "component")
    )
    return table_like, modal_like


def detect_filter_panel_pattern(text: str) -> bool:
    has_actions = "handleSearch" in text and "handleReset" in text
    has_inputs = "<el-input" in text or "<el-select" in text
    has_layout = "filter-grid" in text or "filter-actions" in text or "filter-panel" in text
    return has_actions and has_inputs and has_layout


def choose_filter_reuse_target(
    inventory: dict[str, PublicLayer],
    *,
    text: str,
    imported_names: set[str],
) -> tuple[str, str]:
    filter_panel = inventory.get("FilterPanel")
    base_filter_panel = inventory.get("BaseFilterPanel")

    if "FilterPanel" in imported_names and filter_panel:
        return (
            filter_panel.path,
            f"Existing reusable filter shell already in use: FilterPanel ({filter_panel.usage_count} usages). Prefer extending it before introducing another page-local filter implementation.",
        )

    if filter_panel and any(token in text for token in ("examCategoryCode", "jointExamGroupCode", "subjectCode")):
        merge_note = ""
        if base_filter_panel:
            merge_note = f" Also note that {base_filter_panel.path} and {filter_panel.path} currently overlap and are candidates for a future BaseSearch merge."
        return (
            filter_panel.path,
            f"Reuse the richer FilterPanel for multi-select search forms with examCategoryCode/jointExamGroupCode/subjectCode support.{merge_note}",
        )

    if base_filter_panel and any(token in text for token in ("categoryId", "keyword")):
        return (
            base_filter_panel.path,
            f"Reuse BaseFilterPanel for lightweight keyword/category filters instead of re-implementing a page-local filter bar. Current usages: {base_filter_panel.usage_count}.",
        )

    if filter_panel:
        return (
            filter_panel.path,
            f"FilterPanel already exists and can likely absorb this filter shell. Current usages: {filter_panel.usage_count}.",
        )

    if base_filter_panel:
        return (
            base_filter_panel.path,
            f"BaseFilterPanel already exists and can likely absorb this filter shell. Current usages: {base_filter_panel.usage_count}.",
        )

    return ("BaseSearch (planned)", "No reusable filter-panel component was found; create a shared BaseSearch-style component before duplicating more filter shells.")


def filter_component_capability_guidance(inventory: dict[str, PublicLayer]) -> tuple[str, str, str, str] | None:
    base_filter_panel = inventory.get("BaseFilterPanel")
    filter_panel = inventory.get("FilterPanel")
    if not base_filter_panel or not filter_panel:
        return None

    base_gaps = capability_gap_labels(base_filter_panel)
    base_props = set(base_filter_panel.prop_names or [])
    rich_props = set(filter_panel.prop_names or [])
    base_emits = set(base_filter_panel.emit_names or [])
    rich_emits = set(filter_panel.emit_names or [])
    base_slots = set(base_filter_panel.slot_names or [])
    rich_slots = set(filter_panel.slot_names or [])

    prop_diff = [name for name in sorted(rich_props - base_props) if name in {"modelValue", "initiallyCollapsed", "enableSubjectCode", "subjectCodeOptions", "title", "examCategoryOptions"}]
    emit_diff = [name for name in sorted(rich_emits - base_emits) if name in {"update:modelValue", "search", "reset"}]
    slot_diff = [name for name in sorted(rich_slots - base_slots) if name in {"advanced", "default"}]

    if not base_gaps and not prop_diff and not emit_diff and not slot_diff:
        return None

    message = "An existing shared filter component appears too limited, which likely encourages new forks."
    suggestion_parts: list[str] = []
    if slot_diff:
        suggestion_parts.append(f"add {', '.join(slot_diff)} slot")
    if prop_diff:
        suggestion_parts.append(f"add props {', '.join(prop_diff)}")
    if emit_diff:
        suggestion_parts.append(f"add emits {', '.join(emit_diff)}")
    if base_gaps and not suggestion_parts:
        suggestion_parts.append(f"fill missing capabilities: {', '.join(base_gaps)}")

    if suggestion_parts:
        suggestion = "Extend BaseFilterPanel to " + ", ".join(suggestion_parts) + "."
    else:
        suggestion = "Formally converge BaseFilterPanel into FilterPanel instead of allowing more filter forks."
    return message, base_filter_panel.path, filter_panel.path, suggestion


def overlay_component_capability_guidance(layer: PublicLayer) -> tuple[str, str, str, str] | None:
    if layer.kind not in {"business-dialog", "business-drawer"}:
        return None

    prop_names = set(layer.prop_names or [])
    emit_names = set(layer.emit_names or [])
    slot_names = set(layer.slot_names or [])
    suggestions: list[str] = []

    if "footer" not in slot_names:
        if layer.has_internal_footer_template:
            suggestions.append("externalize hard-coded footer actions via footer slot")
        else:
            suggestions.append("add footer slot")
    if "default" not in slot_names:
        suggestions.append("expose body/default slot for custom content blocks")
    if "before-close" not in emit_names and "close" not in emit_names and "cancel" not in emit_names:
        suggestions.append("add beforeClose or cancel event")
    if not ({"loading", "submitting", "confirmLoading"} & prop_names):
        suggestions.append("expose loading/submitting prop")
    if not layer.has_model_value_bridge:
        suggestions.append("bridge visible state with modelValue/update:modelValue")

    if not suggestions:
        return None

    message = "A reusable dialog/drawer component exists but still lacks common extension points."
    target = layer.path
    suggestion = f"Extend {layer.name} to " + ", ".join(suggestions) + "."
    evidence = (
        f"props={', '.join(layer.prop_names or ['none'])}; "
        f"emits={', '.join(layer.emit_names or ['none'])}; "
        f"slots={', '.join(layer.slot_names or ['none'])}"
    )
    return message, target, target, suggestion + " " + evidence


def overlay_base_abstraction_guidance(layer: PublicLayer) -> tuple[str, str, str, str] | None:
    if layer.kind not in {"business-dialog", "business-drawer"}:
        return None
    if not layer.overlay_tag:
        return None
    if not layer.has_model_value_bridge:
        return None

    base_name = "BaseDialog" if layer.overlay_tag == "dialog" else "BaseDrawer"
    shell_features: list[str] = ["modelValue bridge"]
    if layer.has_internal_footer_template:
        shell_features.append("footer shell")
    if {"loading", "submitting", "confirmLoading"} & set(layer.prop_names or []):
        shell_features.append("loading prop surface")

    message = f"This business {layer.overlay_tag} already carries reusable shell concerns and is a candidate for {base_name} extraction."
    target = layer.path
    suggestion = (
        f"Split {layer.name} into a generic {base_name} shell for visibility, title, width/size, footer actions and close lifecycle, "
        f"then keep business form/content in a thin wrapper component."
    )
    evidence = f"detected shell features: {', '.join(shell_features)}"
    return message, target, base_name, suggestion + " " + evidence


def overlay_shell_contract(layer: PublicLayer) -> dict[str, object] | None:
    if layer.kind not in {"business-dialog", "business-drawer"} or not layer.overlay_tag:
        return None
    base_name = "BaseDialog" if layer.overlay_tag == "dialog" else "BaseDrawer"
    props = ["modelValue", "title"]
    if layer.overlay_tag == "dialog":
        props.append("width")
    else:
        props.append("size")
    props.extend(["loading", "closeOnClickModal", "destroyOnClose"])
    emits = ["update:modelValue", "confirm", "cancel", "beforeClose"]
    slots = ["default", "footer"]
    return {
        "source": layer.path,
        "baseName": base_name,
        "suggestedPath": f"frontend/src/components/common/{base_name}.vue",
        "props": props,
        "emits": emits,
        "slots": slots,
    }


def build_base_shell_blueprint(contract: dict[str, object]) -> dict[str, str]:
    base_name = str(contract["baseName"])
    prop_rows = [
        "  modelValue: { type: Boolean, default: false },",
        "  title: { type: String, default: '' },",
    ]
    if base_name == "BaseDialog":
        prop_rows.append("  width: { type: String, default: '680px' },")
    else:
        prop_rows.append("  size: { type: String, default: '60%' },")
    prop_rows.extend(
        [
            "  loading: { type: Boolean, default: false },",
            "  closeOnClickModal: { type: Boolean, default: true },",
            "  destroyOnClose: { type: Boolean, default: false },",
        ]
    )
    wrapper_tag = "el-dialog" if base_name == "BaseDialog" else "el-drawer"
    size_binding = ":width=\"width\"" if base_name == "BaseDialog" else ":size=\"size\""
    content = "\n".join(
        [
            "<script setup>",
            "import { computed } from 'vue'",
            "",
            "const props = defineProps({",
            *prop_rows,
            "})",
            "",
            "const emit = defineEmits(['update:modelValue', 'confirm', 'cancel', 'beforeClose'])",
            "",
            "const visible = computed({",
            "  get: () => props.modelValue,",
            "  set: (value) => emit('update:modelValue', value),",
            "})",
            "",
            "function handleCancel() {",
            "  emit('cancel')",
            "  visible.value = false",
            "}",
            "",
            "function handleConfirm() {",
            "  emit('confirm')",
            "}",
            "",
            "function handleBeforeClose(done) {",
            "  emit('beforeClose', done)",
            "  done()",
            "}",
            "</script>",
            "",
            "<template>",
            f"  <{wrapper_tag}",
            "    v-model=\"visible\"",
            "    :title=\"title\"",
            f"    {size_binding}",
            "    :close-on-click-modal=\"closeOnClickModal\"",
            "    :destroy-on-close=\"destroyOnClose\"",
            "    :before-close=\"handleBeforeClose\"",
            "  >",
            "    <slot />",
            "",
            "    <template #footer>",
            "      <slot name=\"footer\">",
            "        <el-button @click=\"handleCancel\">取消</el-button>",
            "        <el-button type=\"primary\" :loading=\"loading\" @click=\"handleConfirm\">确认</el-button>",
            "      </slot>",
            "    </template>",
            f"  </{wrapper_tag}>",
            "</template>",
            "",
        ]
    )
    return {
        "baseName": base_name,
        "suggestedPath": str(contract["suggestedPath"]),
        "language": "vue",
        "content": content,
    }


def hook_blueprint_catalog() -> dict[str, dict[str, str]]:
    return {
        "useRequest": {
            "name": "useRequest",
            "suggestedPath": "frontend/src/composables/useRequest.js",
            "language": "js",
            "content": "\n".join(
                [
                    "import { ref } from 'vue'",
                    "",
                    "export function useRequest(requester) {",
                    "  const loading = ref(false)",
                    "  const error = ref(null)",
                    "",
                    "  async function run(...args) {",
                    "    loading.value = true",
                    "    error.value = null",
                    "    try {",
                    "      return await requester(...args)",
                    "    } catch (err) {",
                    "      error.value = err",
                    "      throw err",
                    "    } finally {",
                    "      loading.value = false",
                    "    }",
                    "  }",
                    "",
                    "  return { loading, error, run }",
                    "}",
                    "",
                ]
            ),
        },
        "useModal": {
            "name": "useModal",
            "suggestedPath": "frontend/src/composables/useModal.js",
            "language": "js",
            "content": "\n".join(
                [
                    "import { ref } from 'vue'",
                    "",
                    "export function useModal(initialValue = false) {",
                    "  const visible = ref(Boolean(initialValue))",
                    "",
                    "  function open() {",
                    "    visible.value = true",
                    "  }",
                    "",
                    "  function close() {",
                    "    visible.value = false",
                    "  }",
                    "",
                    "  function toggle() {",
                    "    visible.value = !visible.value",
                    "  }",
                    "",
                    "  return { visible, open, close, toggle }",
                    "}",
                    "",
                ]
            ),
        },
        "useForm": {
            "name": "useForm",
            "suggestedPath": "frontend/src/composables/useForm.js",
            "language": "js",
            "content": "\n".join(
                [
                    "import { ref } from 'vue'",
                    "",
                    "export function useForm({ submitter, resetter } = {}) {",
                    "  const submitting = ref(false)",
                    "",
                    "  async function submit(...args) {",
                    "    if (typeof submitter !== 'function') return",
                    "    submitting.value = true",
                    "    try {",
                    "      return await submitter(...args)",
                    "    } finally {",
                    "      submitting.value = false",
                    "    }",
                    "  }",
                    "",
                    "  function reset(...args) {",
                    "    if (typeof resetter === 'function') {",
                    "      resetter(...args)",
                    "    }",
                    "  }",
                    "",
                    "  return { submitting, submit, reset }",
                    "}",
                    "",
                ]
            ),
        },
        "usePagination": {
            "name": "usePagination",
            "suggestedPath": "frontend/src/composables/usePagination.js",
            "language": "js",
            "content": "\n".join(
                [
                    "import { reactive } from 'vue'",
                    "",
                    "export function usePagination(initial = {}) {",
                    "  const pagination = reactive({",
                    "    page: Number(initial.page || 1),",
                    "    size: Number(initial.size || 20),",
                    "    total: Number(initial.total || 0),",
                    "  })",
                    "",
                    "  function setPage(nextPage) {",
                    "    pagination.page = Number(nextPage || 1)",
                    "  }",
                    "",
                    "  function setSize(nextSize) {",
                    "    pagination.size = Number(nextSize || 20)",
                    "    pagination.page = 1",
                    "  }",
                    "",
                    "  function setTotal(nextTotal) {",
                    "    pagination.total = Number(nextTotal || 0)",
                    "  }",
                    "",
                    "  return { pagination, setPage, setSize, setTotal }",
                    "}",
                    "",
                ]
            ),
        },
        "useTable": {
            "name": "useTable",
            "suggestedPath": "frontend/src/composables/useTable.js",
            "language": "js",
            "content": "\n".join(
                [
                    "import { ref } from 'vue'",
                    "import { usePagination } from './usePagination'",
                    "",
                    "export function useTable(fetcher, initialFilters = {}) {",
                    "  const rows = ref([])",
                    "  const filters = ref({ ...initialFilters })",
                    "  const { pagination, setPage, setSize, setTotal } = usePagination()",
                    "",
                    "  async function reload() {",
                    "    const pageData = await fetcher({ ...filters.value, page: pagination.page, size: pagination.size })",
                    "    rows.value = Array.isArray(pageData?.items) ? pageData.items : []",
                    "    setTotal(pageData?.total || 0)",
                    "    return pageData",
                    "  }",
                    "",
                    "  async function search(nextFilters = {}) {",
                    "    filters.value = { ...filters.value, ...nextFilters }",
                    "    setPage(1)",
                    "    return reload()",
                    "  }",
                    "",
                    "  async function reset(nextFilters = initialFilters) {",
                    "    filters.value = { ...nextFilters }",
                    "    setPage(1)",
                    "    return reload()",
                    "  }",
                    "",
                    "  return { rows, filters, pagination, setPage, setSize, reload, search, reset }",
                    "}",
                    "",
                ]
            ),
        },
    }


def normalize_hook_targets(target_text: str) -> list[str]:
    mapping = {
        "useRequest": ["useRequest"],
        "useModal": ["useModal"],
        "useForm": ["useForm"],
        "useModal + useForm": ["useModal", "useForm"],
        "useTable/usePagination": ["useTable", "usePagination"],
    }
    normalized = str(target_text or "").strip()
    return mapping.get(normalized, [])


def build_hook_blueprints(warnings: list[WarningItem]) -> list[dict[str, str]]:
    catalog = hook_blueprint_catalog()
    selected: list[str] = []
    for item in warnings:
        if warning_category(item) != "hook-extraction":
            continue
        for name in normalize_hook_targets(item.target_public_layer):
            if name not in selected and name in catalog:
                selected.append(name)
    return [catalog[name] for name in selected]


def analyze_page_logic_shape(text: str) -> dict[str, bool]:
    loading_ref_count = len(re.findall(r"const\s+[A-Za-z0-9_]*loading[A-Za-z0-9_]*\s*=\s*ref\(", text, re.IGNORECASE))
    return {
        "has_inline_filter_markup": detect_filter_panel_pattern(text),
        "has_filter_component": "<FilterPanel" in text or "<BaseFilterPanel" in text,
        "has_query_builder": "buildQueryParams" in text,
        "has_load_function": bool(re.search(r"\basync function load[A-Z]", text)),
        "has_pagination_state": "pagination = reactive" in text or "const pagination = reactive" in text,
        "has_pagination_handlers": "handlePageChange" in text and "handlePageSizeChange" in text,
        "has_search_handlers": "handleSearch" in text and "handleReset" in text,
        "has_table_markup": "<el-table" in text and "<el-pagination" in text,
        "has_error_state": "errorMessage" in text,
        "has_parallel_requests": "Promise.all" in text,
        "has_loading_guard": "runWithLoadingGuard" in text,
        "loading_ref_count": loading_ref_count > 0,
        "has_modal_visibility_state": "dialogVisible" in text or "drawerVisible" in text or "visible = computed" in text,
        "has_form_model": "formModel = reactive" in text or "const formModel = reactive" in text or "const aiForm = reactive" in text or "const editForm = reactive" in text,
        "has_form_submit": "handleSubmit" in text or "save" in text,
        "has_form_reset": "resetForm" in text or "handleReset" in text,
        "has_form_ref": "formRef" in text,
        "has_permission_logic": "hasPermission(" in text or "v-permission" in text or "ensureAccess(" in text or "role ||" in text,
        "uses_permission_directive": "v-permission" in text,
    }


def recommend_extraction_split(
    *,
    layer: PublicLayer | None,
    page_shape: dict[str, bool],
) -> str:
    component_parts: list[str] = []
    composable_parts: list[str] = []

    if layer and layer.name == "BaseFilterPanel":
        component_parts.append("expand BaseFilterPanel")
    elif layer and layer.name == "FilterPanel":
        component_parts.append("keep FilterPanel as the visual search shell")

    if page_shape["has_inline_filter_markup"]:
        component_parts.append("move filter fields/actions into the shared filter component")

    if page_shape["has_query_builder"] or page_shape["has_load_function"] or page_shape["has_pagination_state"] or page_shape["has_pagination_handlers"]:
        composable_parts.append("extract buildQueryParams/load*/pagination/search-reset state into useTable/usePagination")

    if composable_parts and component_parts:
        return f"{'; '.join(component_parts)}; {'; '.join(composable_parts)}."
    if composable_parts:
        return f"{'; '.join(composable_parts)}."
    if component_parts:
        return f"{'; '.join(component_parts)}."
    return "Review whether the shared component should absorb more view-shell logic or whether state should move into a composable."


def recommend_request_state_hook(page_shape: dict[str, bool]) -> str:
    if page_shape["has_pagination_state"] or page_shape["has_pagination_handlers"] or page_shape["has_table_markup"]:
        return "useTable/usePagination"
    if page_shape["has_load_function"] and (page_shape["has_error_state"] or page_shape["has_loading_guard"] or page_shape["has_parallel_requests"]):
        return "useRequest"
    return "manual-review"


def recommend_modal_form_hook(page_shape: dict[str, bool]) -> str:
    if page_shape["has_modal_visibility_state"] and not page_shape["has_table_markup"]:
        if page_shape["has_form_model"] or page_shape["has_form_submit"] or page_shape["has_form_reset"]:
            return "useModal + useForm"
        return "useModal"
    if page_shape["has_form_model"] and (page_shape["has_form_submit"] or page_shape["has_form_reset"]):
        return "useForm"
    return "manual-review"


def recommend_permission_hook(page_shape: dict[str, bool]) -> str:
    if not page_shape["has_permission_logic"]:
        return "manual-review"
    if page_shape["uses_permission_directive"]:
        return "manual-review"
    return "v-permission / usePermission"


def choose_table_reuse_target(
    inventory: dict[str, PublicLayer],
    duplicate_files: list[str],
) -> tuple[str, str]:
    filter_panel = inventory.get("FilterPanel")
    base_filter_panel = inventory.get("BaseFilterPanel")
    if filter_panel:
        merge_note = ""
        if base_filter_panel:
            merge_note = " FilterPanel/BaseFilterPanel should be evaluated for convergence into a single BaseSearch entry."
        return (
            f"{filter_panel.path} + useTable/usePagination (planned)",
            f"Start by reusing the existing FilterPanel for the shared search shell, then extract the repeated query/pagination state into useTable/usePagination.{merge_note}",
        )
    if base_filter_panel:
        return (
            f"{base_filter_panel.path} + useTable/usePagination (planned)",
            "Start from BaseFilterPanel for the search shell, then extract query/pagination state into planned useTable/usePagination helpers.",
        )
    return (
        "useTable / usePagination / BaseTable (planned)",
        "No reusable table shell was found. Extract the repeated query and pagination behavior into useTable/usePagination before adding more list pages.",
    )


def make_warning(
    *,
    code: str,
    severity: str,
    message: str,
    category: str = "",
    file: str = "",
    suggestion: str = "",
    target_public_layer: str = "",
    evidence: str = "",
) -> WarningItem:
    return WarningItem(
        code=code,
        severity=severity,
        message=message,
        category=category,
        file=file,
        suggestion=suggestion,
        target_public_layer=target_public_layer,
        evidence=evidence,
    )


def warning_category(item: WarningItem) -> str:
    if item.category:
        return item.category
    if "permission" in item.code:
        return "permission-convergence"
    if "hook" in item.code or item.code in {
        "duplicate-table-logic",
        "duplicate-modal-logic",
        "imported-shared-component-still-holds-page-logic",
    }:
        return "hook-extraction"
    if item.code in {
        "shared-component-capability-gap",
        "shared-overlay-component-capability-gap",
        "existing-filter-component-not-reused",
        "filter-panel-fork-detected",
        "base-overlay-abstraction-candidate",
    }:
        return "component-extension"
    return "other"


def warning_category_title(category: str) -> str:
    return {
        "component-extension": "Component Extensions",
        "hook-extraction": "Composable Extractions",
        "permission-convergence": "Permission Convergence",
        "other": "Other Findings",
    }.get(category, "Other Findings")


def group_warning_items(warnings: list[WarningItem]) -> list[tuple[str, list[WarningItem]]]:
    ordered_categories = [
        "component-extension",
        "hook-extraction",
        "permission-convergence",
        "other",
    ]
    grouped: list[tuple[str, list[WarningItem]]] = []
    for category in ordered_categories:
        items = [item for item in warnings if warning_category(item) == category]
        if items:
            grouped.append((category, items))
    return grouped


def build_split_plans(warnings: list[WarningItem]) -> list[dict[str, object]]:
    by_file: dict[str, list[WarningItem]] = {}
    for item in warnings:
        if not item.file:
            continue
        by_file.setdefault(item.file, []).append(item)

    plans: list[dict[str, object]] = []
    for file_path, items in sorted(by_file.items()):
        steps: list[str] = []
        target_layers: list[str] = []
        categories = {warning_category(item) for item in items}

        component_items = [item for item in items if warning_category(item) == "component-extension"]
        hook_items = [item for item in items if warning_category(item) == "hook-extraction"]
        permission_items = [item for item in items if warning_category(item) == "permission-convergence"]

        if component_items:
            component_targets = [item.target_public_layer for item in component_items if item.target_public_layer]
            target_layers.extend(component_targets)
            primary_target = component_targets[0] if component_targets else "shared component"
            steps.append(f"Align the view shell with `{primary_target}` and remove duplicated structural markup.")

        if hook_items:
            hook_targets = [item.target_public_layer for item in hook_items if item.target_public_layer]
            target_layers.extend(hook_targets)
            unique_hook_targets = []
            for target in hook_targets:
                if target not in unique_hook_targets:
                    unique_hook_targets.append(target)
            if unique_hook_targets:
                steps.append(f"Extract page-local state into `{', '.join(unique_hook_targets)}` and keep the page/component focused on rendering.")

        if permission_items:
            permission_targets = [item.target_public_layer for item in permission_items if item.target_public_layer]
            target_layers.extend(permission_targets)
            if permission_targets:
                steps.append(f"Replace inline permission branches with `{permission_targets[0]}`.")

        if not steps:
            steps.append("Review this file manually and converge it to the shared layer.")

        plans.append(
            {
                "file": file_path,
                "categories": sorted(categories),
                "targets": [target for index, target in enumerate(target_layers) if target and target not in target_layers[:index]],
                "steps": steps[:2],
            }
        )
    return plans


def build_warnings(changed_files: list[Path], force: bool, inventory: dict[str, PublicLayer], cwd: Path) -> list[WarningItem]:
    warnings: list[WarningItem] = []
    duplicate_table_files: list[str] = []
    duplicate_modal_files: list[str] = []
    filter_pattern_files: list[tuple[str, str, str]] = []
    imported_public_component_files: list[tuple[str, str, dict[str, bool]]] = []
    request_state_files: list[tuple[str, dict[str, bool]]] = []

    for path in changed_files:
        if is_noise_path(path):
            continue
        text = read_text(path)
        if not text:
            continue

        if is_frontend_code_file(path):
            imported_names = imported_component_names(text)
            page_shape = analyze_page_logic_shape(text)
            if page_shape["has_load_function"] and page_shape["loading_ref_count"]:
                request_state_files.append((str(path), page_shape))
            for imported_name in sorted(imported_names):
                if imported_name in inventory:
                    imported_public_component_files.append((str(path), imported_name, page_shape))
            if contains_direct_request_usage(text) and not looks_like_request_wrapper(path):
                warnings.append(
                    make_warning(
                        code="direct-request-in-page",
                        severity="high",
                        message="Frontend page/component code directly uses axios/fetch.",
                        category="other",
                        file=str(path),
                        target_public_layer="frontend/src/api/request.js",
                        suggestion="Move networking into the unified request wrapper and expose page calls through api service modules instead of page-local requests.",
                    )
                )

            for pattern in PAGINATION_DRIFT_PATTERNS:
                if pattern.search(text):
                    warnings.append(
                        make_warning(
                            code="pagination-shape-drift",
                            severity="medium",
                            message="Non-standard pagination field detected.",
                            category="other",
                            file=str(path),
                            target_public_layer="useTable / usePagination / BaseTable",
                            suggestion="Normalize the page result contract to { items, page, size, total } and remove page-local aliases such as rows/records/list.",
                        )
                    )
                    break

            if re.search(r"\bcreatedAt\b|\bupdatedAt\b", text):
                warnings.append(
                    make_warning(
                        code="time-field-alias-drift",
                        severity="medium",
                        message="Time field alias drift detected.",
                        category="other",
                        file=str(path),
                        target_public_layer="createTime / updateTime convention",
                        suggestion="Rename createdAt/updatedAt usage to createTime/updateTime and align related formatters or table columns.",
                    )
                )

            if re.search(r"\bextJson\b.{0,40}JSON\.stringify\s*\(", text, re.DOTALL) or re.search(
                r"extJson\s*:\s*[\"']", text
            ):
                warnings.append(
                    make_warning(
                        code="extjson-stringified",
                        severity="high",
                        message="extJson appears to be passed as a string.",
                        category="other",
                        file=str(path),
                        target_public_layer="extJson object contract",
                        suggestion="Keep extJson as an object in new code. Parse legacy string inputs at the boundary instead of propagating stringified JSON through business code.",
                    )
                )

            if detect_filter_panel_pattern(text):
                target_layer, target_suggestion = choose_filter_reuse_target(
                    inventory,
                    text=text,
                    imported_names=imported_names,
                )
                filter_pattern_files.append((str(path), target_layer, target_suggestion))

            table_like, modal_like = detect_duplicate_frontend_patterns(path, text)
            if table_like:
                duplicate_table_files.append(str(path))
            if modal_like:
                duplicate_modal_files.append(str(path))

        if is_backend_code_file(path):
            if re.search(r"\bcreatedAt\b|\bupdatedAt\b", text):
                warnings.append(
                    make_warning(
                        code="backend-time-field-alias-drift",
                        severity="medium",
                        message="Backend naming drift detected.",
                        category="other",
                        file=str(path),
                        target_public_layer="BaseEntity field convention",
                        suggestion="Converge new backend fields and serializers on createTime/updateTime instead of createdAt/updatedAt.",
                    )
                )
            if re.search(r"\bextJson\b.{0,40}String\b", text, re.DOTALL):
                warnings.append(
                    make_warning(
                        code="backend-extjson-string",
                        severity="high",
                        message="Backend extJson appears to use string semantics.",
                        category="other",
                        file=str(path),
                        target_public_layer="BaseEntity extJson object field",
                        suggestion="Keep extJson object-like in service/entity boundaries. If storage still serializes, convert only at persistence boundaries.",
                    )
                )

    filter_component_paths = {name: item.path for name, item in inventory.items() if item.kind == "filter-panel"}
    inline_filter_files = [
        (path_text, target_layer, target_suggestion)
        for path_text, target_layer, target_suggestion in filter_pattern_files
        if path_text not in filter_component_paths.values()
    ]

    for path_text, target_layer, target_suggestion in inline_filter_files:
        warnings.append(
            make_warning(
                code="existing-filter-component-not-reused",
                severity="medium",
                message="Inline filter panel logic was detected even though reusable filter components already exist.",
                category="component-extension",
                file=path_text,
                target_public_layer=target_layer,
                suggestion=target_suggestion,
            )
        )

    if inventory.get("BaseFilterPanel") and inventory.get("FilterPanel") and inline_filter_files:
        warnings.append(
            make_warning(
                code="filter-panel-fork-detected",
                severity="medium",
                message="BaseFilterPanel and FilterPanel currently coexist while inline filter shells are still being added.",
                category="component-extension",
                file=", ".join(path for path, _, _ in inline_filter_files[:3]),
                target_public_layer=f"{inventory['BaseFilterPanel'].path} <-> {inventory['FilterPanel'].path}",
                suggestion="Stop adding new filter variants. Choose one component as the primary search entry and schedule a convergence path toward a single BaseSearch-style filter shell.",
                evidence=(
                    f"BaseFilterPanel usages: {inventory['BaseFilterPanel'].usage_count}; "
                    f"FilterPanel usages: {inventory['FilterPanel'].usage_count}"
                ),
            )
        )

    capability_guidance = filter_component_capability_guidance(inventory)
    if capability_guidance:
        message, file_path, target_path, suggestion = capability_guidance
        warnings.append(
            make_warning(
                code="shared-component-capability-gap",
                severity="medium",
                message=message,
                category="component-extension",
                file=file_path,
                target_public_layer=target_path,
                suggestion=suggestion,
                evidence=(
                    f"BaseFilterPanel props/defaults/emits/slots: "
                    f"{inventory['BaseFilterPanel'].prop_count}/{inventory['BaseFilterPanel'].default_prop_count}/"
                    f"{inventory['BaseFilterPanel'].emit_count}/{','.join(inventory['BaseFilterPanel'].slot_names or ['none'])}; "
                    f"FilterPanel props/defaults/emits/slots: "
                    f"{inventory['FilterPanel'].prop_count}/{inventory['FilterPanel'].default_prop_count}/"
                    f"{inventory['FilterPanel'].emit_count}/{','.join(inventory['FilterPanel'].slot_names or ['none'])}"
                ),
            )
        )

    for layer in inventory.values():
        overlay_guidance = overlay_component_capability_guidance(layer)
        if not overlay_guidance:
            continue
        message, file_path, target_path, suggestion = overlay_guidance
        warnings.append(
            make_warning(
                code="shared-overlay-component-capability-gap",
                severity="medium",
                message=message,
                category="component-extension",
                file=file_path,
                target_public_layer=target_path,
                suggestion=suggestion,
            )
        )
        base_overlay_guidance = overlay_base_abstraction_guidance(layer)
        if base_overlay_guidance:
            base_message, base_file, base_target, base_suggestion = base_overlay_guidance
            warnings.append(
                make_warning(
                    code="base-overlay-abstraction-candidate",
                    severity="medium",
                    message=base_message,
                    category="component-extension",
                    file=base_file,
                    target_public_layer=base_target,
                    suggestion=base_suggestion,
                )
            )

    if len(duplicate_table_files) >= 2:
        target_layer, target_suggestion = choose_table_reuse_target(inventory, duplicate_table_files)
        warnings.append(
            make_warning(
                code="duplicate-table-logic",
                severity="high" if force or len(duplicate_table_files) >= 3 else "medium",
                message="Similar table/search/pagination logic appeared in multiple frontend files.",
                category="hook-extraction",
                file=", ".join(duplicate_table_files[:3]),
                target_public_layer=target_layer,
                suggestion=target_suggestion,
                evidence=f"Repeated files: {', '.join(duplicate_table_files[:5])}",
            )
        )

        duplicate_file_set = set(duplicate_table_files)
        for file_path, component_name, page_shape in imported_public_component_files:
            if file_path not in duplicate_file_set:
                continue
            layer = inventory.get(component_name)
            if not layer:
                continue
            if component_name not in {"FilterPanel", "BaseFilterPanel"}:
                continue
            guidance = recommend_extraction_split(layer=layer, page_shape=page_shape)
            warnings.append(
                make_warning(
                    code="imported-shared-component-still-holds-page-logic",
                    severity="medium",
                    message="A page already imports a shared component, but large repeated list/filter logic still remains in the page.",
                    category="hook-extraction",
                    file=file_path,
                    target_public_layer=layer.path,
                    suggestion=guidance,
                    evidence=(
                        f"Imported component: {component_name}; usages: {layer.usage_count}; "
                        f"queryBuilder={page_shape['has_query_builder']}; loadFunction={page_shape['has_load_function']}; "
                        f"paginationState={page_shape['has_pagination_state']}; inlineFilter={page_shape['has_inline_filter_markup']}"
                    ),
                )
            )

    for file_path, page_shape in request_state_files:
        hook_target = recommend_request_state_hook(page_shape)
        if hook_target == "manual-review":
            continue
        if hook_target == "useTable/usePagination" and file_path not in set(duplicate_table_files):
            continue
        if hook_target == "useRequest" and (page_shape["has_pagination_state"] or page_shape["has_table_markup"]):
            continue
        warnings.append(
            make_warning(
                code="request-state-machine-can-be-hooked",
                severity="medium",
                message="This file contains a repeatable request state machine that fits a shared hook better than page-local state.",
                category="hook-extraction",
                file=file_path,
                target_public_layer=hook_target,
                suggestion=(
                    "Extract loading/error/retry/task execution state into useRequest."
                    if hook_target == "useRequest"
                    else "Extract query params, pagination, search/reset and fetch lifecycle into useTable/usePagination."
                ),
                evidence=(
                    f"loadFunction={page_shape['has_load_function']}; "
                    f"errorState={page_shape['has_error_state']}; "
                    f"parallelRequests={page_shape['has_parallel_requests']}; "
                    f"paginationState={page_shape['has_pagination_state']}; "
                    f"tableMarkup={page_shape['has_table_markup']}"
                ),
            )
        )

    seen_modal_form_targets: set[str] = set()
    for file_path, page_shape in request_state_files:
        hook_target = recommend_modal_form_hook(page_shape)
        if hook_target == "manual-review" or file_path in seen_modal_form_targets:
            continue
        seen_modal_form_targets.add(file_path)
        warnings.append(
            make_warning(
                code="modal-form-state-can-be-hooked",
                severity="medium",
                message="This file contains reusable modal/form state that fits shared hooks better than local component state.",
                category="hook-extraction",
                file=file_path,
                target_public_layer=hook_target,
                suggestion=(
                    "Extract visible/open-close state into useModal and form submit/reset/validation state into useForm."
                    if hook_target == "useModal + useForm"
                    else "Extract visible/open-close state into useModal."
                    if hook_target == "useModal"
                    else "Extract submit/reset/validation state into useForm."
                ),
                evidence=(
                    f"modalVisibility={page_shape['has_modal_visibility_state']}; "
                    f"formModel={page_shape['has_form_model']}; "
                    f"formSubmit={page_shape['has_form_submit']}; "
                    f"formReset={page_shape['has_form_reset']}"
                ),
            )
        )

    seen_permission_targets: set[str] = set()
    for path in changed_files:
        if not is_frontend_code_file(path):
            continue
        text = read_text(path)
        if not text:
            continue
        page_shape = analyze_page_logic_shape(text)
        hook_target = recommend_permission_hook(page_shape)
        if hook_target == "manual-review" or str(path) in seen_permission_targets:
            continue
        seen_permission_targets.add(str(path))
        warnings.append(
            make_warning(
                code="permission-gating-can-be-hooked",
                severity="medium",
                message="Permission gating is implemented inline instead of via a shared permission primitive.",
                category="permission-convergence",
                file=str(path),
                target_public_layer=hook_target,
                suggestion="Move role/permission-based visibility checks to v-permission or a dedicated usePermission helper to avoid page-local branching drift.",
                evidence=(
                    f"hasPermissionLogic={page_shape['has_permission_logic']}; "
                    f"usesDirective={page_shape['uses_permission_directive']}"
                ),
            )
        )

    if len(duplicate_modal_files) >= 2:
        warnings.append(
            make_warning(
                code="duplicate-modal-logic",
                severity="medium",
                message="Similar modal/form control logic appeared in multiple frontend files.",
                category="hook-extraction",
                file=", ".join(duplicate_modal_files[:3]),
                target_public_layer="useModal / useForm / useRequest / BaseDialog / BaseDrawer",
                suggestion="Keep dialog/drawer shell concerns in shared components, and move submit/reset/loading/error task state into useModal/useForm/useRequest.",
                evidence=f"Repeated files: {', '.join(duplicate_modal_files[:5])}",
            )
        )

    return dedupe_warnings(warnings)


def summarize_changed_files(changed_files: list[Path]) -> dict[str, int]:
    summary = {
        "totalChangedFiles": len(changed_files),
        "frontendFiles": 0,
        "backendFiles": 0,
        "otherFiles": 0,
    }
    for path in changed_files:
        if is_frontend_code_file(path):
            summary["frontendFiles"] += 1
        elif is_backend_code_file(path):
            summary["backendFiles"] += 1
        else:
            summary["otherFiles"] += 1
    return summary


def summarize_public_layers(inventory: dict[str, PublicLayer]) -> dict[str, object]:
    return {
        "count": len(inventory),
        "items": [asdict(item) for item in sorted(inventory.values(), key=lambda item: item.name.lower())],
    }


def summarize_warnings(warnings: list[WarningItem]) -> dict[str, int]:
    return {
        "high": sum(1 for item in warnings if item.severity == "high"),
        "medium": sum(1 for item in warnings if item.severity == "medium"),
        "low": sum(1 for item in warnings if item.severity == "low"),
        "total": len(warnings),
    }


def summarize_warning_groups(warnings: list[WarningItem]) -> dict[str, int]:
    return {
        category: len(items)
        for category, items in group_warning_items(warnings)
    }


def infer_module(path_text: str, cwd: Path) -> str:
    if not path_text:
        return "unknown"
    first_path = path_text.split(" -> ", 1)[0].split(", ", 1)[0]
    try:
        relative = Path(first_path).resolve().relative_to(cwd)
        parts = relative.parts
        if not parts:
            return "root"
        return parts[0]
    except Exception:
        return Path(first_path).parts[0] if Path(first_path).parts else "unknown"


def normalize_location_text(path_text: str) -> str:
    if not path_text:
        return "-"
    if " -> " in path_text:
        return path_text.split(" -> ", 1)[0]
    return path_text


def build_migration_items(
    warnings: list[WarningItem],
    *,
    cwd: Path,
    threshold: str,
) -> list[MigrationItem]:
    items: list[MigrationItem] = []
    for item in warnings:
        items.append(
            MigrationItem(
                category=warning_category(item),
                module=infer_module(item.file, cwd),
                location=normalize_location_text(item.file),
                current_drift=item.message,
                target_public_layer=item.target_public_layer or "manual-review",
                risk=item.severity,
                blocking=warning_meets_threshold(item.severity, threshold),
                next_batch="current batch" if warning_meets_threshold(item.severity, threshold) else "next refactor batch",
                suggestion=item.suggestion or "Review and converge this implementation to the shared layer.",
            )
        )
    return items


def render_console_report(
    *,
    phase: str,
    cwd: Path,
    changed_files: list[Path],
    fail_threshold: str,
    warnings: list[WarningItem],
    migration_items: list[MigrationItem],
    inventory: dict[str, PublicLayer],
) -> str:
    file_summary = summarize_changed_files(changed_files)
    warning_summary = summarize_warnings(warnings)
    grouped_warnings = group_warning_items(warnings)
    shell_contracts = [contract for contract in (overlay_shell_contract(item) for item in inventory.values()) if contract]
    shell_blueprints = [build_base_shell_blueprint(contract) for contract in shell_contracts]
    hook_blueprints = build_hook_blueprints(warnings)
    split_plans = build_split_plans(warnings)

    lines: list[str] = []
    lines.append(f"Component Reuse Guard: {phase}")
    lines.append(f"Working directory: {cwd}")
    lines.append(f"Changed files: {len(changed_files)}")
    lines.append(f"Fail threshold: {fail_threshold}")
    lines.append(
        "Summary: "
        f"{warning_summary['high']} high, {warning_summary['medium']} medium, {warning_summary['low']} low "
        f"across {file_summary['frontendFiles']} frontend and {file_summary['backendFiles']} backend files."
    )
    if inventory:
        lines.append(
            "Detected reusable layers: "
            + ", ".join(f"{item.name}({item.usage_count})" for item in sorted(inventory.values(), key=lambda item: item.name.lower()))
        )
    for path in changed_files[:20]:
        lines.append(f"  - {path}")
    if len(changed_files) > 20:
        lines.append(f"  - ... {len(changed_files) - 20} more")

    if warnings:
        lines.append("Findings:")
        for category, items in grouped_warnings:
            lines.append(f"  {warning_category_title(category)}:")
            for item in items:
                suffix = f" [{item.file}]" if item.file else ""
                lines.append(f"    - [{item.severity.upper()}] {item.message}{suffix}")
                if item.target_public_layer:
                    lines.append(f"      target: {item.target_public_layer}")
                if item.suggestion:
                    lines.append(f"      suggestion: {item.suggestion}")
                if item.evidence:
                    lines.append(f"      evidence: {item.evidence}")
    else:
        lines.append("Findings: none")

    if migration_items:
        lines.append("Migration checklist:")
        for category in ["component-extension", "hook-extraction", "permission-convergence", "other"]:
            scoped_items = [item for item in migration_items if item.category == category]
            if not scoped_items:
                continue
            lines.append(f"  {warning_category_title(category)}:")
            for item in scoped_items[:10]:
                block_text = "blocking" if item.blocking else "non-blocking"
                lines.append(
                    f"    - [{item.risk.upper()}] {item.location} -> {item.target_public_layer} ({block_text}, {item.next_batch})"
                )

    if shell_contracts:
        lines.append("Recommended base shell contracts:")
        for contract in shell_contracts:
            lines.append(f"  - {contract['baseName']} <- {contract['source']}")
            lines.append(f"    props: {', '.join(contract['props'])}")
            lines.append(f"    emits: {', '.join(contract['emits'])}")
            lines.append(f"    slots: {', '.join(contract['slots'])}")

    if shell_blueprints:
        lines.append("Suggested base shell skeletons:")
        for blueprint in shell_blueprints:
            lines.append(f"  - {blueprint['baseName']} -> {blueprint['suggestedPath']}")

    if hook_blueprints:
        lines.append("Suggested hook skeletons:")
        for blueprint in hook_blueprints:
            lines.append(f"  - {blueprint['name']} -> {blueprint['suggestedPath']}")

    if split_plans:
        lines.append("Recommended split plans:")
        for plan in split_plans:
            lines.append(f"  - {plan['file']}")
            for index, step in enumerate(plan["steps"], start=1):
                lines.append(f"    {index}. {step}")

    return "\n".join(lines)


def escape_md(text: str) -> str:
    return text.replace("|", "\\|")


def render_markdown_report(
    *,
    phase: str,
    cwd: Path,
    changed_files: list[Path],
    fail_threshold: str,
    warnings: list[WarningItem],
    migration_items: list[MigrationItem],
    inventory: dict[str, PublicLayer],
) -> str:
    file_summary = summarize_changed_files(changed_files)
    warning_summary = summarize_warnings(warnings)
    grouped_warnings = group_warning_items(warnings)
    shell_contracts = [contract for contract in (overlay_shell_contract(item) for item in inventory.values()) if contract]
    shell_blueprints = [build_base_shell_blueprint(contract) for contract in shell_contracts]
    hook_blueprints = build_hook_blueprints(warnings)
    split_plans = build_split_plans(warnings)

    lines: list[str] = []
    lines.append(f"# Component Reuse Guard Report ({phase})")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Working directory: `{cwd}`")
    lines.append(f"- Fail threshold: `{fail_threshold}`")
    lines.append(f"- Changed files: `{file_summary['totalChangedFiles']}`")
    lines.append(f"- Frontend files: `{file_summary['frontendFiles']}`")
    lines.append(f"- Backend files: `{file_summary['backendFiles']}`")
    lines.append(
        f"- Findings: `{warning_summary['high']}` high / `{warning_summary['medium']}` medium / `{warning_summary['low']}` low"
    )
    lines.append(f"- Detected reusable layers: `{len(inventory)}`")
    lines.append("")
    lines.append("## Reusable Layer Inventory")
    if inventory:
        for item in sorted(inventory.values(), key=lambda value: value.name.lower()):
            capability_suffix = (
                f", props/defaults/emits: `{item.prop_count}/{item.default_prop_count}/{item.emit_count}`, "
                f"propNames: `{', '.join(item.prop_names or ['none'])}`, "
                f"emitNames: `{', '.join(item.emit_names or ['none'])}`, "
                f"slots: `{', '.join(item.slot_names or ['none'])}`"
                if item.kind != "request-wrapper"
                else ""
            )
            lines.append(f"- `{item.name}`: `{item.path}` (`{item.kind}`, usages: `{item.usage_count}`{capability_suffix})")
    else:
        lines.append("- No reusable layer inventory was detected.")
    lines.append("")
    lines.append("## Findings")
    if warnings:
        for category, items in grouped_warnings:
            lines.append(f"### {warning_category_title(category)}")
            for item in items:
                lines.append(f"- `{item.severity.upper()}` `{item.code}`: {item.message}")
                if item.file:
                    lines.append(f"  File: `{item.file}`")
                if item.target_public_layer:
                    lines.append(f"  Target public layer: `{item.target_public_layer}`")
                if item.suggestion:
                    lines.append(f"  Suggestion: {item.suggestion}")
                if item.evidence:
                    lines.append(f"  Evidence: {item.evidence}")
    else:
        lines.append("- No implementation-layer reuse drift detected in the current change set.")
    lines.append("")
    lines.append("## Migration Checklist")
    if migration_items:
        for category in ["component-extension", "hook-extraction", "permission-convergence", "other"]:
            scoped_items = [item for item in migration_items if item.category == category]
            if not scoped_items:
                continue
            lines.append(f"### {warning_category_title(category)}")
            lines.append("| Module | Location | Drift | Target Public Layer | Risk | Blocking | Next Batch |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            for item in scoped_items:
                lines.append(
                    "| "
                    + " | ".join(
                        (
                            escape_md(item.module),
                            escape_md(item.location),
                            escape_md(item.current_drift),
                            escape_md(item.target_public_layer),
                            escape_md(item.risk),
                            "yes" if item.blocking else "no",
                            escape_md(item.next_batch),
                        )
                    )
                    + " |"
                )
    else:
        lines.append("- No migration checklist items were generated.")
    lines.append("")
    lines.append("## Recommended Base Shell Contracts")
    if shell_contracts:
        for contract in shell_contracts:
            lines.append(f"### {contract['baseName']}")
            lines.append(f"- Source candidate: `{contract['source']}`")
            lines.append(f"- Suggested path: `{contract['suggestedPath']}`")
            lines.append(f"- Props: `{', '.join(contract['props'])}`")
            lines.append(f"- Emits: `{', '.join(contract['emits'])}`")
            lines.append(f"- Slots: `{', '.join(contract['slots'])}`")
    else:
        lines.append("- No BaseDialog/BaseDrawer extraction candidates were detected.")
    lines.append("")
    lines.append("## Suggested Base Shell Skeletons")
    if shell_blueprints:
        for blueprint in shell_blueprints:
            lines.append(f"### `{blueprint['suggestedPath']}`")
            lines.append(f"```{blueprint['language']}")
            lines.append(blueprint["content"].rstrip())
            lines.append("```")
    else:
        lines.append("- No base shell skeletons were generated.")
    lines.append("")
    lines.append("## Suggested Hook Skeletons")
    if hook_blueprints:
        for blueprint in hook_blueprints:
            lines.append(f"### `{blueprint['suggestedPath']}`")
            lines.append(f"```{blueprint['language']}")
            lines.append(blueprint["content"].rstrip())
            lines.append("```")
    else:
        lines.append("- No hook skeletons were generated.")
    lines.append("")
    lines.append("## Recommended Split Plans")
    if split_plans:
        for plan in split_plans:
            lines.append(f"### `{plan['file']}`")
            if plan["targets"]:
                lines.append(f"- Targets: `{', '.join(plan['targets'])}`")
            for index, step in enumerate(plan["steps"], start=1):
                lines.append(f"{index}. {step}")
    else:
        lines.append("- No file-level split plans were generated.")
    return "\n".join(lines)


def write_report(path_str: str, content: str) -> None:
    if not path_str:
        return
    path = Path(path_str).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def emit_blueprints(output_dir: str, blueprints: list[dict[str, str]]) -> list[str]:
    if not output_dir:
        return []
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    written_paths: list[str] = []
    for blueprint in blueprints:
        relative_path = str(blueprint.get("suggestedPath", "")).strip()
        content = str(blueprint.get("content", ""))
        if not relative_path or not content:
            continue
        target_path = root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        written_paths.append(str(target_path))
    return written_paths


def render_patch_plan(
    *,
    cwd: Path,
    shell_contracts: list[dict[str, object]],
    shell_blueprints: list[dict[str, str]],
    hook_blueprints: list[dict[str, str]],
    split_plans: list[dict[str, object]],
    migration_items: list[MigrationItem],
) -> str:
    lines: list[str] = []
    lines.append("# Component Reuse Patch Plan")
    lines.append("")
    lines.append(f"- Workspace: `{cwd}`")
    lines.append("")
    lines.append("## New Shared Files")
    if shell_blueprints or hook_blueprints:
        for blueprint in shell_blueprints:
            lines.append(f"- `{blueprint['suggestedPath']}`")
        for blueprint in hook_blueprints:
            lines.append(f"- `{blueprint['suggestedPath']}`")
    else:
        lines.append("- No scaffold files suggested.")
    lines.append("")
    lines.append("## Base Shell Contracts")
    if shell_contracts:
        for contract in shell_contracts:
            lines.append(f"### `{contract['baseName']}`")
            lines.append(f"- Source candidate: `{contract['source']}`")
            lines.append(f"- Suggested path: `{contract['suggestedPath']}`")
            lines.append(f"- Props: `{', '.join(contract['props'])}`")
            lines.append(f"- Emits: `{', '.join(contract['emits'])}`")
            lines.append(f"- Slots: `{', '.join(contract['slots'])}`")
    else:
        lines.append("- No BaseDialog/BaseDrawer contracts suggested.")
    lines.append("")
    lines.append("## File-by-File Steps")
    if split_plans:
        for plan in split_plans:
            lines.append(f"### `{plan['file']}`")
            if plan.get("targets"):
                lines.append(f"- Targets: `{', '.join(plan['targets'])}`")
            for index, step in enumerate(plan.get("steps", []), start=1):
                lines.append(f"{index}. {step}")
    else:
        lines.append("- No file-level split plans generated.")
    lines.append("")
    lines.append("## Migration Items")
    if migration_items:
        for item in migration_items:
            lines.append(
                f"- `{item.category}` `{item.location}` -> `{item.target_public_layer}` "
                f"(`{item.risk}`, {'blocking' if item.blocking else 'non-blocking'}, {item.next_batch})"
            )
    else:
        lines.append("- No migration items generated.")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the component reuse shared logic guard.")
    parser.add_argument("--phase", choices=("start", "batch", "final"), default="final")
    parser.add_argument("--task", default="")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--fail-on", choices=("auto", "none", "high", "medium", "low"), default="auto")
    parser.add_argument("--force", action="store_true", help="Treat repeated table/query logic as high risk more aggressively.")
    parser.add_argument("--report-md", default="")
    parser.add_argument("--report-json", default="")
    parser.add_argument("--emit-blueprints-dir", default="", help="Optional directory to materialize suggested shell/hook skeleton files.")
    parser.add_argument("--emit-patch-plan", default="", help="Optional markdown file path for the generated patch plan.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = Path(args.cwd).resolve()
    git_root = find_git_root(cwd)
    raw_changed_files = [Path(item).resolve() for item in args.changed_file]
    if not raw_changed_files and git_root:
        raw_changed_files = parse_git_status(git_root)
    changed_files = [path for path in raw_changed_files if not is_noise_path(path)]

    inventory = discover_public_layers(cwd)
    warnings = build_warnings(changed_files, args.force, inventory, cwd)
    threshold = compute_threshold(args.phase, args.fail_on)
    migration_items = build_migration_items(warnings, cwd=cwd, threshold=threshold)
    shell_contracts = [contract for contract in (overlay_shell_contract(item) for item in inventory.values()) if contract]
    shell_blueprints = [build_base_shell_blueprint(contract) for contract in shell_contracts]
    hook_blueprints = build_hook_blueprints(warnings)
    split_plans = build_split_plans(warnings)

    console_report = render_console_report(
        phase=args.phase,
        cwd=cwd,
        changed_files=changed_files,
        fail_threshold=threshold,
        warnings=warnings,
        migration_items=migration_items,
        inventory=inventory,
    )
    print(console_report)

    if args.report_md:
        write_report(
            args.report_md,
            render_markdown_report(
                phase=args.phase,
                cwd=cwd,
                changed_files=changed_files,
                fail_threshold=threshold,
                warnings=warnings,
                migration_items=migration_items,
                inventory=inventory,
            ),
        )
    if args.report_json:
        payload = {
            "phase": args.phase,
            "cwd": str(cwd),
            "failThreshold": threshold,
            "changedFiles": [str(path) for path in changed_files],
            "summary": {
                "files": summarize_changed_files(changed_files),
                "warnings": summarize_warnings(warnings),
                "warningGroups": summarize_warning_groups(warnings),
                "publicLayers": summarize_public_layers(inventory),
            },
            "warnings": [asdict(item) for item in warnings],
            "warningsByGroup": {
                category: [asdict(item) for item in items]
                for category, items in group_warning_items(warnings)
            },
            "migrationChecklist": [asdict(item) for item in migration_items],
            "recommendedBaseShellContracts": shell_contracts,
            "suggestedBaseShellSkeletons": shell_blueprints,
            "suggestedHookSkeletons": hook_blueprints,
            "recommendedSplitPlans": split_plans,
        }
        write_report(args.report_json, json.dumps(payload, ensure_ascii=False, indent=2))
    if args.emit_blueprints_dir:
        emit_blueprints(args.emit_blueprints_dir, shell_blueprints + hook_blueprints)
    if args.emit_patch_plan:
        write_report(
            args.emit_patch_plan,
            render_patch_plan(
                cwd=cwd,
                shell_contracts=shell_contracts,
                shell_blueprints=shell_blueprints,
                hook_blueprints=hook_blueprints,
                split_plans=split_plans,
                migration_items=migration_items,
            ),
        )

    has_blocking = any(warning_meets_threshold(item.severity, threshold) for item in warnings)
    return 1 if has_blocking else 0


if __name__ == "__main__":
    sys.exit(main())
