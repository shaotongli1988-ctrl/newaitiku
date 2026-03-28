from __future__ import annotations

from scripts.three_stage_orchestrator import (
    STAGE_IMPLEMENTATION,
    STAGE_READINESS,
    build_output,
    route_task,
)


def test_route_task_prefers_current_stage_when_explicit() -> None:
    result = route_task("继续完善学生端错题智能中心并联调页面表现", STAGE_IMPLEMENTATION)
    assert result["safe"] is True
    assert result["stage"] == STAGE_IMPLEMENTATION
    assert result["skillName"] == "fullstack-unified-development-standards"


def test_route_task_defaults_to_readiness_without_keywords() -> None:
    result = route_task("帮我看下这个需求下一步怎么做", "none")
    assert result["safe"] is True
    assert result["stage"] == STAGE_READINESS
    assert result["skillName"] == "software-development-readiness-governance"


def test_route_task_reports_conflict_for_explicit_stage() -> None:
    result = route_task("准备提测上线并做回滚检查", STAGE_IMPLEMENTATION)
    assert result["safe"] is False
    output = build_output(result)
    assert "无法安全自动路由" in output
    assert "提测" in output
