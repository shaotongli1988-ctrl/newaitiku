#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


STAGE_SKILLS = {
    "readiness": "software-development-readiness-governance",
    "implementation": "fullstack-unified-development-standards",
    "delivery": "software-delivery-unified-governance",
}

STAGE_LABELS = {
    "readiness": "开发前",
    "implementation": "开发中",
    "delivery": "开发后",
}

STAGE_PROMPTS = {
    "readiness": "用开发前总技能，先把需求、验收、PRD/UI、技术方案一次性定义清楚。",
    "implementation": "用开发中总技能开始做，边开发边对齐，别跑偏。",
    "delivery": "用开发后总技能检查一切，给我提测/上线前结论。",
}

STAGE_KEYWORDS = {
    "readiness": ("需求", "验收", "prd", "原型", "方案", "adr", "冻结", "开发前"),
    "implementation": ("实现", "联调", "开发中", "对齐", "新增字段", "新增接口", "新增页面", "状态", "权限", "css变量", "css 变量", "design token", "设计 token", "样式变量", "主题变量"),
    "delivery": ("提测", "上线", "门禁", "终检", "回滚", "发布", "开发后", "uat"),
}

GOVERNANCE_KEYWORDS = (
    "告警治理",
    "漂移收敛",
    "技术债",
    "守卫误报",
    "误报收敛",
    "误报回放",
    "回放样例",
    "试点治理",
    "pilot",
    "技能治理",
)

IMPLEMENTATION_ACTION_KEYWORDS = (
    "改代码",
    "改契约",
    "改文档",
    "补测试",
    "升级守卫",
    "升级守卫能力",
    "补齐矩阵",
    "验收矩阵",
    "回放",
    "样例",
    "继续推进",
    "修路由",
)


@dataclass
class RoutingDecision:
    status: str
    stage: str
    stage_label: str
    skill: str
    reason: str
    matched_signals: list[str]
    next_prompt: str


def score_stage(task: str, keywords: tuple[str, ...]) -> tuple[int, list[str]]:
    lowered = task.lower()
    matched = [keyword for keyword in keywords if keyword.lower() in lowered]
    return len(matched), matched


def governance_implementation_override(task: str) -> list[str]:
    lowered = task.lower()
    matched_governance = [keyword for keyword in GOVERNANCE_KEYWORDS if keyword.lower() in lowered]
    matched_actions = [keyword for keyword in IMPLEMENTATION_ACTION_KEYWORDS if keyword.lower() in lowered]
    if matched_governance and matched_actions:
        return matched_governance + matched_actions
    return []


def route_task(task: str, current_stage: str) -> RoutingDecision:
    if not task.strip():
        return RoutingDecision(
            status="needs_confirmation",
            stage="readiness",
            stage_label=STAGE_LABELS["readiness"],
            skill=STAGE_SKILLS["readiness"],
            reason="未提供任务描述，无法安全自动路由。",
            matched_signals=[],
            next_prompt="请补充当前需求，或明确说开发前、开发中、开发后。",
        )

    override_signals = governance_implementation_override(task)
    if override_signals:
        return RoutingDecision(
            status="routed",
            stage="implementation",
            stage_label=STAGE_LABELS["implementation"],
            skill=STAGE_SKILLS["implementation"],
            reason="命中告警治理路由原则：当前任务是在升级守卫能力与收敛误报，应进入开发中阶段先做真实修复。",
            matched_signals=override_signals,
            next_prompt=STAGE_PROMPTS["implementation"],
        )

    stage_scores: dict[str, int] = {}
    stage_matches: dict[str, list[str]] = {}
    for stage, keywords in STAGE_KEYWORDS.items():
        score, matched = score_stage(task, keywords)
        stage_scores[stage] = score
        stage_matches[stage] = matched

    if current_stage != "none":
        stage_scores[current_stage] += 2
        stage_matches[current_stage] = stage_matches[current_stage] + [f"current-stage:{current_stage}"]

    ranked = sorted(stage_scores.items(), key=lambda item: item[1], reverse=True)
    top_stage, top_score = ranked[0]
    second_score = ranked[1][1]

    if top_score == 0:
        return RoutingDecision(
            status="routed",
            stage="readiness",
            stage_label=STAGE_LABELS["readiness"],
            skill=STAGE_SKILLS["readiness"],
            reason="未命中明显阶段关键词，按安全默认值从开发前开始。",
            matched_signals=[],
            next_prompt=STAGE_PROMPTS["readiness"],
        )

    if top_score == second_score:
        return RoutingDecision(
            status="needs_confirmation",
            stage=top_stage,
            stage_label=STAGE_LABELS[top_stage],
            skill=STAGE_SKILLS[top_stage],
            reason="多个阶段同时命中且分值接近，无法安全自动路由。",
            matched_signals=stage_matches[top_stage],
            next_prompt="请明确当前是开发前、开发中还是开发后。",
        )

    return RoutingDecision(
        status="routed",
        stage=top_stage,
        stage_label=STAGE_LABELS[top_stage],
        skill=STAGE_SKILLS[top_stage],
        reason="根据任务语义与当前阶段信号完成自动路由。",
        matched_signals=stage_matches[top_stage],
        next_prompt=STAGE_PROMPTS[top_stage],
    )


def render(decision: RoutingDecision, current_stage: str) -> str:
    lines = [
        "Three Stage Skill Orchestrator",
        f"状态: {decision.status}",
        f"推荐阶段: {decision.stage_label} ({decision.stage})",
        f"推荐技能: {decision.skill}",
        f"当前阶段输入: {current_stage}",
        f"原因: {decision.reason}",
        "命中信号:",
    ]
    if decision.matched_signals:
        for signal in decision.matched_signals:
            lines.append(f"- {signal}")
    else:
        lines.append("- 无")
    lines.append(f"下一步建议: {decision.next_prompt}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="三阶段总技能统一路由器")
    parser.add_argument("--task", default="")
    parser.add_argument("--current-stage", choices=("none", "readiness", "implementation", "delivery"), default="none")
    parser.add_argument("--report-json", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    decision = route_task(args.task, args.current_stage)
    print(render(decision, args.current_stage))
    if args.report_json:
        with open(args.report_json, "w", encoding="utf-8") as handle:
            json.dump(asdict(decision), handle, ensure_ascii=False, indent=2)
    return 1 if decision.status == "needs_confirmation" else 0


if __name__ == "__main__":
    raise SystemExit(main())
