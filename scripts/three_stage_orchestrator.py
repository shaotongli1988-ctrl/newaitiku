#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Dict, List, Sequence


STAGE_READINESS = "readiness"
STAGE_IMPLEMENTATION = "implementation"
STAGE_DELIVERY = "delivery"
STAGE_NONE = "none"


@dataclass(frozen=True)
class StageProfile:
    stage: str
    label: str
    skill_name: str
    keywords: Sequence[str]
    suggestion: str


STAGE_PROFILES: Dict[str, StageProfile] = {
    STAGE_READINESS: StageProfile(
        stage=STAGE_READINESS,
        label="开发前",
        skill_name="software-development-readiness-governance",
        keywords=("需求", "验收", "prd", "原型", "方案", "adr", "冻结", "开发前"),
        suggestion="先进入开发前准备，冻结边界、验收口径和方案结论，再继续推进。",
    ),
    STAGE_IMPLEMENTATION: StageProfile(
        stage=STAGE_IMPLEMENTATION,
        label="开发中",
        skill_name="fullstack-unified-development-standards",
        keywords=("实现", "联调", "开发中", "对齐", "新增字段", "新增接口", "新增页面", "状态", "权限", "css 变量", "design token", "样式变量", "主题变量", "继续"),
        suggestion="继续按开发中总技能推进实现、联调、自测和守卫校验。",
    ),
    STAGE_DELIVERY: StageProfile(
        stage=STAGE_DELIVERY,
        label="开发后",
        skill_name="software-delivery-unified-governance",
        keywords=("提测", "上线", "门禁", "终检", "回滚", "发布", "开发后", "uat"),
        suggestion="切到开发后阶段，集中做终检、提测门禁、发布与回滚准备。",
    ),
}


def _normalize(text: str) -> str:
    return " ".join(str(text or "").strip().lower().split())


def _keyword_hits(task: str, profile: StageProfile) -> List[str]:
    normalized_task = _normalize(task)
    hits: List[str] = []
    for keyword in profile.keywords:
        normalized_keyword = _normalize(keyword)
        if normalized_keyword and normalized_keyword in normalized_task:
            hits.append(keyword)
    return hits


def route_task(task: str, current_stage: str = STAGE_NONE) -> Dict[str, object]:
    normalized_stage = _normalize(current_stage) or STAGE_NONE
    if normalized_stage not in {STAGE_NONE, *STAGE_PROFILES.keys()}:
        raise ValueError(f"Unsupported current stage: {current_stage}")

    stage_hits = {
        stage: _keyword_hits(task, profile)
        for stage, profile in STAGE_PROFILES.items()
    }
    stage_scores = {
        stage: len(hits)
        for stage, hits in stage_hits.items()
    }

    sorted_scores = sorted(stage_scores.items(), key=lambda item: item[1], reverse=True)
    best_stage, best_score = sorted_scores[0]
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0

    if normalized_stage != STAGE_NONE:
        if best_score >= 2 and best_stage != normalized_stage and stage_scores.get(normalized_stage, 0) == 0:
            suggested_profile = STAGE_PROFILES[best_stage]
            current_profile = STAGE_PROFILES[normalized_stage]
            return {
                "safe": False,
                "stage": "",
                "stageLabel": "",
                "skillName": "",
                "reason": f"当前阶段是{current_profile.label}，但任务更强烈命中{suggested_profile.label}关键词，存在阶段冲突。",
                "hits": stage_hits,
                "suggestion": "无法安全自动路由，请先确认当前到底是在做需求冻结、实现联调，还是提测上线。",
            }
        selected_stage = normalized_stage
        reason = f"已显式提供当前阶段 {normalized_stage}，按状态优先继续路由。"
    elif best_score == 0:
        selected_stage = STAGE_READINESS
        reason = "任务未命中明显阶段关键词，按规则默认从开发前开始。"
    elif best_score == second_score:
        return {
            "safe": False,
            "stage": "",
            "stageLabel": "",
            "skillName": "",
            "reason": "多个阶段关键词命中分值接近，无法安全自动路由。",
            "hits": stage_hits,
            "suggestion": "请先明确当前是在开发前、开发中还是开发后阶段，再继续执行对应总技能。",
        }
    else:
        selected_stage = best_stage
        reason = f"任务对 {STAGE_PROFILES[selected_stage].label} 的关键词命中更明显。"

    profile = STAGE_PROFILES[selected_stage]
    return {
        "safe": True,
        "stage": profile.stage,
        "stageLabel": profile.label,
        "skillName": profile.skill_name,
        "reason": reason,
        "hits": stage_hits,
        "suggestion": profile.suggestion,
    }


def _format_hits(hits: Dict[str, List[str]]) -> str:
    pieces: List[str] = []
    for stage in (STAGE_READINESS, STAGE_IMPLEMENTATION, STAGE_DELIVERY):
        profile = STAGE_PROFILES[stage]
        values = hits.get(stage, [])
        pieces.append(f"{profile.label}: {', '.join(values) if values else '无'}")
    return "；".join(pieces)


def build_output(result: Dict[str, object]) -> str:
    if not result.get("safe"):
        return "\n".join(
            [
                "路由结论：无法安全自动路由",
                f"原因：{result.get('reason', '')}",
                f"命中信号：{_format_hits(result.get('hits', {}))}",
                f"下一步建议：{result.get('suggestion', '')}",
            ]
        )

    return "\n".join(
        [
            f"推荐阶段：{result.get('stageLabel', '')}",
            f"对应总技能：{result.get('skillName', '')}",
            f"路由原因：{result.get('reason', '')}",
            f"命中信号：{_format_hits(result.get('hits', {}))}",
            f"下一步建议：{result.get('suggestion', '')}",
        ]
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="三阶段总技能路由脚本")
    parser.add_argument("--task", required=True, help="用户需求或当前任务描述")
    parser.add_argument(
        "--current-stage",
        default=STAGE_NONE,
        choices=(STAGE_NONE, STAGE_READINESS, STAGE_IMPLEMENTATION, STAGE_DELIVERY),
        help="当前已知阶段，默认 none",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = route_task(args.task, args.current_stage)
    print(build_output(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
