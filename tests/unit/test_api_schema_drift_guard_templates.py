from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_schema_drift_guard():
    module_path = Path.home() / ".codex/skills/api-schema-drift-checker/scripts/schema_drift_guard.py"
    spec = importlib.util.spec_from_file_location("schema_drift_guard", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_extract_endpoints_supports_template_literals_and_prefix_constants() -> None:
    guard = load_schema_drift_guard()
    text = """
const API_PREFIX = '/api/question-bank'
const ADMIN_API_PREFIX = `${API_PREFIX}/admin`

export function fetchAdminSettings() {
  return request({
    method: 'get',
    url: `${ADMIN_API_PREFIX}/settings`,
  })
}
"""

    endpoints = guard.extract_endpoints_from_text(text, [])
    assert guard.Endpoint(method="GET", path="/api/question-bank/admin/settings") in endpoints


def test_extract_endpoints_supports_replace_placeholders_and_generic_param_matching() -> None:
    guard = load_schema_drift_guard()
    text = """
export function saveWeights(versionId, data) {
  return request({
    method: 'post',
    url: '/api/question-bank/admin/syllabus/{versionId}/weights'.replace('{versionId}', encodeURIComponent(versionId)),
    data,
  })
}
"""

    endpoints = guard.extract_endpoints_from_text(text, [])
    assert guard.Endpoint(method="POST", path="/api/question-bank/admin/syllabus/{param}/weights") in endpoints


def test_extract_endpoints_supports_axios_concat_and_fetch_template_calls() -> None:
    guard = load_schema_drift_guard()
    text = """
const API_PREFIX = '/api/question-bank'
const PROFILE_URL = API_PREFIX + '/auth/me'
const STUDENT_PREFIX = `${API_PREFIX}/student`

axios.get(PROFILE_URL)
fetch(`${STUDENT_PREFIX}/syllabus/catalog`, {
  method: 'GET',
})
"""

    endpoints = guard.extract_endpoints_from_text(text, [])
    assert guard.Endpoint(method="GET", path="/api/question-bank/auth/me") in endpoints
    assert guard.Endpoint(method="GET", path="/api/question-bank/student/syllabus/catalog") in endpoints


def test_walk_files_ignores_docs_skills_and_test_assets(tmp_path: Path) -> None:
    guard = load_schema_drift_guard()
    producer_file = tmp_path / "app" / "models.py"
    docs_skill_file = tmp_path / "docs" / "skills" / "api-schema-drift-checker" / "scripts" / "schema_drift_guard.py"
    unit_test_file = tmp_path / "tests" / "unit" / "test_api_schema_drift_guard_templates.py"

    producer_file.parent.mkdir(parents=True, exist_ok=True)
    docs_skill_file.parent.mkdir(parents=True, exist_ok=True)
    unit_test_file.parent.mkdir(parents=True, exist_ok=True)

    producer_file.write_text("class UserModel:\n    pass\n", encoding="utf-8")
    docs_skill_file.write_text("class DriftIssue:\n    pass\n", encoding="utf-8")
    unit_test_file.write_text("class TestOnlySchema:\n    pass\n", encoding="utf-8")

    discovered = list(guard.walk_files(tmp_path, max_files=100))

    assert producer_file.resolve() in discovered
    assert docs_skill_file.resolve() not in discovered
    assert unit_test_file.resolve() not in discovered
