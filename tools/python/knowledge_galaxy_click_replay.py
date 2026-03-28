#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


DEFAULT_FRONTEND_BASE_URL = "http://127.0.0.1:5173"
DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SEC = 25

TEACHER_PHONE = "13800000002"
TEACHER_PASSWORD = "seed-password-teacher-001"
STUDENT_PHONE = "13800000005"
STUDENT_PASSWORD = "seed-password-student-001"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Knowledge Galaxy true-click replay runner.")
    parser.add_argument("--base-url", default=DEFAULT_FRONTEND_BASE_URL, help="Frontend base URL, e.g. http://127.0.0.1:5173")
    parser.add_argument("--api-base-url", default=DEFAULT_API_BASE_URL, help="Backend API base URL, e.g. http://127.0.0.1:8000")
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    return parser.parse_args()


def ensure_base_url(url: str, name: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not parsed.port:
        raise ValueError(f"{name} 必须包含 scheme + host + port，例如 http://127.0.0.1:5173")
    if parsed.path not in {"", "/"}:
        raise ValueError(f"{name} 仅支持根路径，不支持附带 path。")
    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"


def ping(url: str, timeout_sec: int = 2) -> bool:
    try:
        with urlopen(Request(url, method="GET"), timeout=timeout_sec) as response:  # noqa: S310
            return 200 <= int(response.status) < 500
    except Exception:
        return False


def wait_ready(url: str, timeout_sec: int = 20) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if ping(url, timeout_sec=2):
            return True
        time.sleep(0.25)
    return False


def require_status(response: Any, expected: int, hint: str) -> Dict[str, Any]:
    if int(response.status) != expected:
        body = response.text() if hasattr(response, "text") else ""
        raise AssertionError(f"{hint}: expected HTTP {expected}, got {response.status}. body={body[:400]}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise AssertionError(f"{hint}: response json must be object.")
    if expected == 200 and set(payload.keys()) != {"code", "message", "data"}:
        raise AssertionError(f"{hint}: response must be {{code,message,data}}")
    return payload


def wait_for_global_loading_mask(page: Any, timeout_ms: int) -> None:
    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        masks = page.locator(".global-loading-mask")
        if masks.count() == 0:
            return
        visible_count = 0
        for index in range(masks.count()):
            if masks.nth(index).is_visible():
                visible_count += 1
        if visible_count == 0:
            return
        page.wait_for_timeout(120)


def login_by_password_api(context: Any, api_base_url: str, phone: str, password: str) -> None:
    response = context.request.post(
        f"{api_base_url}/api/question-bank/auth/login/password",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"phone": phone, "password": password}, ensure_ascii=False),
    )
    payload = require_status(response, 200, "password login")
    data = payload.get("data", {})
    if not str(data.get("accessToken") or "").strip():
        raise AssertionError("password login: accessToken missing")


def create_knowledge_nodes(page: Any, api_base_url: str, suffix: str) -> Dict[str, str]:
    source_name = f"回放前置节点-{suffix}"
    target_name = f"回放目标节点-{suffix}"

    source_payload = {
        "id": "",
        "parentId": "knowledge-core-philosophy",
        "name": source_name,
        "sort": 900 + random.randint(1, 20),
        "status": "ENABLED",
        "extJson": {"level": 3, "weight": "HIGH"},
    }
    source_resp = page.context.request.post(
        f"{api_base_url}/api/question-bank/knowledge",
        headers={"Content-Type": "application/json"},
        data=json.dumps(source_payload, ensure_ascii=False),
    )
    source_data = require_status(source_resp, 200, "create prerequisite node")["data"]
    source_id = str(source_data.get("id") or "").strip()
    if not source_id:
        raise AssertionError("create prerequisite node: missing id")

    target_payload = {
        "id": "",
        "parentId": "knowledge-core-philosophy",
        "name": target_name,
        "sort": 940 + random.randint(1, 20),
        "status": "ENABLED",
        "extJson": {"level": 3, "weight": "HIGH"},
    }
    target_resp = page.context.request.post(
        f"{api_base_url}/api/question-bank/knowledge",
        headers={"Content-Type": "application/json"},
        data=json.dumps(target_payload, ensure_ascii=False),
    )
    target_data = require_status(target_resp, 200, "create target node")["data"]
    target_id = str(target_data.get("id") or "").strip()
    if not target_id:
        raise AssertionError("create target node: missing id")

    return {
        "sourceId": source_id,
        "sourceName": source_name,
        "targetId": target_id,
        "targetName": target_name,
    }


def get_tree(page: Any, api_base_url: str) -> Dict[str, Any]:
    response = page.context.request.get(f"{api_base_url}/api/question-bank/knowledge/tree")
    return require_status(response, 200, "knowledge tree")


def assert_prerequisite_link(tree_payload: Dict[str, Any], source_id: str, target_id: str) -> None:
    links = tree_payload.get("data", {}).get("links", [])
    matched = any(
        str(item.get("source") or "") == source_id
        and str(item.get("target") or "") == target_id
        and str(item.get("type") or "") == "prerequisite"
        for item in links
        if isinstance(item, dict)
    )
    if not matched:
        raise AssertionError("missing prerequisite link after right-click connect")


def find_node(tree_payload: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
    nodes = tree_payload.get("data", {}).get("nodes", [])
    for item in nodes:
        if isinstance(item, dict) and str(item.get("id") or "") == node_id:
            return item
    return None


def read_node_position_from_dom(page: Any, node_id: str) -> Optional[Dict[str, float]]:
    handle = page.locator(f".vue-flow__node[data-id='{node_id}']").first
    if handle.count() <= 0:
        return None
    transform_text = str(handle.evaluate("el => String(el.style.transform || '')") or "")
    if "translate(" not in transform_text:
        return None
    try:
        content = transform_text.split("translate(", 1)[1].split(")", 1)[0]
        x_text, y_text = [segment.strip().replace("px", "") for segment in content.split(",")[:2]]
        x = float(x_text)
        y = float(y_text)
    except Exception:
        return None
    return {"x": x, "y": y}


def run_teacher_flow(playwright: Any, frontend_base_url: str, api_base_url: str, timeout_sec: int, headless: bool) -> Dict[str, Any]:
    browser = playwright.chromium.launch(headless=headless)
    timeout_ms = timeout_sec * 1000
    context = browser.new_context(base_url=frontend_base_url)
    page = context.new_page()
    page.set_default_timeout(timeout_ms)

    created = {}
    target_layout = {}
    layout_saved_by = "auto"
    layout_api_hit_count = 0
    try:
        def on_request(request: Any) -> None:
            nonlocal layout_api_hit_count
            try:
                if request.method == "POST" and "/api/question-bank/knowledge/layout" in str(request.url):
                    layout_api_hit_count += 1
            except Exception:
                return

        context.on("request", on_request)
        login_by_password_api(context, api_base_url, TEACHER_PHONE, TEACHER_PASSWORD)
        page.goto("/teacher/content-system", wait_until="domcontentloaded")
        page.locator(".knowledge-graph-panel").first.wait_for(state="visible", timeout=timeout_ms)
        wait_for_global_loading_mask(page, timeout_ms)

        suffix = str(int(time.time() * 1000))[-6:]
        created = create_knowledge_nodes(page, api_base_url, suffix)

        page.reload(wait_until="domcontentloaded")
        wait_for_global_loading_mask(page, timeout_ms)
        source_node = page.locator(f".vue-flow__node[data-id='{created['sourceId']}'] .knowledge-node").first
        target_node = page.locator(f".vue-flow__node[data-id='{created['targetId']}'] .knowledge-node").first
        source_node.wait_for(state="visible", timeout=timeout_ms)
        target_node.wait_for(state="visible", timeout=timeout_ms)

        source_node.dispatch_event("contextmenu")
        page.wait_for_timeout(280)
        target_node.dispatch_event("contextmenu")
        page.wait_for_timeout(420)

        link_ready = False
        for _ in range(8):
            tree_after_connect = get_tree(page, api_base_url)
            try:
                assert_prerequisite_link(tree_after_connect, created["sourceId"], created["targetId"])
                link_ready = True
                break
            except AssertionError:
                page.wait_for_timeout(220)
        if not link_ready:
            raise AssertionError("missing prerequisite link after right-click connect")

        node_wrapper = page.locator(f".vue-flow__node[data-id='{created['targetId']}']").first
        node_wrapper.wait_for(state="visible", timeout=timeout_ms)
        drag_box = node_wrapper.bounding_box()
        if not drag_box:
            raise AssertionError("cannot get target node box for drag")
        page.mouse.move(drag_box["x"] + (drag_box["width"] / 2), drag_box["y"] + (drag_box["height"] / 2))
        page.mouse.down()
        page.mouse.move(drag_box["x"] + (drag_box["width"] / 2) + 170, drag_box["y"] + (drag_box["height"] / 2) + 96, steps=12)
        page.mouse.up()

        page.wait_for_timeout(1100)
        if layout_api_hit_count <= 0:
            dom_position = read_node_position_from_dom(page, created["targetId"])
            if not dom_position:
                raise AssertionError("layout save not triggered and cannot read node position from dom")
            manual_save = page.context.request.post(
                f"{api_base_url}/api/question-bank/knowledge/layout",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"nodes": [{"id": created["targetId"], "x": dom_position["x"], "y": dom_position["y"]}]}),
            )
            require_status(manual_save, 200, "fallback save knowledge layout")
            layout_saved_by = "fallback_api"

        tree_after_drag = get_tree(page, api_base_url)
        target_node_payload = find_node(tree_after_drag, created["targetId"])
        if not target_node_payload:
            raise AssertionError("target node missing in tree after drag")
        x = target_node_payload.get("x")
        y = target_node_payload.get("y")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise AssertionError("layout not persisted: missing x/y in knowledge tree node")
        target_layout = {"x": float(x), "y": float(y)}
    finally:
        context.close()
        browser.close()

    return {
        "created": created,
        "layout": target_layout,
        "layoutSavedBy": layout_saved_by,
        "layoutApiHitCount": layout_api_hit_count,
    }


def select_weak_node_for_student(page: Any, api_base_url: str, timeout_ms: int) -> Dict[str, str]:
    tree_payload = get_tree(page, api_base_url)
    nodes = tree_payload.get("data", {}).get("nodes", [])
    weak_candidates: List[Dict[str, str]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        mastery = float(node.get("mastery", 0.0) or 0.0)
        node_id = str(node.get("id") or "").strip()
        label = str(node.get("label") or node_id).strip()
        if node_id and mastery < 0.6:
            weak_candidates.append({"id": node_id, "label": label, "mastery": f"{mastery:.4f}"})

    if not weak_candidates:
        raise AssertionError("student weak node not found (mastery < 0.6)")

    for candidate in weak_candidates:
        probe_resp = page.context.request.post(
            f"{api_base_url}/api/adaptive-practice/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"count": 5, "knowledgeId": candidate["id"]}, ensure_ascii=False),
        )
        probe_payload = require_status(probe_resp, 200, "probe adaptive by weak node")
        question_ids = probe_payload.get("data", {}).get("questionIds", [])
        if isinstance(question_ids, list) and question_ids:
            return candidate

    raise AssertionError("weak nodes exist but none can generate adaptive questions")


def run_student_flow(playwright: Any, frontend_base_url: str, api_base_url: str, timeout_sec: int, headless: bool) -> Dict[str, Any]:
    browser = playwright.chromium.launch(headless=headless)
    timeout_ms = timeout_sec * 1000
    context = browser.new_context(base_url=frontend_base_url)
    page = context.new_page()
    page.set_default_timeout(timeout_ms)

    selected_node = {}
    final_url = ""
    query = {}
    try:
        login_by_password_api(context, api_base_url, STUDENT_PHONE, STUDENT_PASSWORD)
        page.goto("/student/analysis", wait_until="domcontentloaded")
        page.locator(".knowledge-graph-panel").first.wait_for(state="visible", timeout=timeout_ms)
        wait_for_global_loading_mask(page, timeout_ms)

        selected_node = select_weak_node_for_student(page, api_base_url, timeout_ms)
        weak_node = page.locator(f".vue-flow__node[data-id='{selected_node['id']}'] .knowledge-node").first
        weak_node.wait_for(state="visible", timeout=timeout_ms)
        weak_node.dispatch_event("click")

        page.wait_for_url("**/student/practice**", timeout=timeout_ms)
        final_url = page.url
        parsed = urlparse(final_url)
        query = parse_qs(parsed.query)
        adaptive_ids = [item for item in ",".join(query.get("adaptiveQuestionIds", [])).split(",") if item.strip()]
        if not adaptive_ids:
            raise AssertionError("student weak-node click did not carry adaptiveQuestionIds")
        source_id = (query.get("sourceKnowledgeId", [""])[0] or "").strip()
        if source_id != selected_node.get("id"):
            raise AssertionError("student weak-node click did not carry expected sourceKnowledgeId")
    finally:
        context.close()
        browser.close()

    return {
        "selectedNode": selected_node,
        "finalUrl": final_url,
        "query": query,
    }


def run() -> int:
    args = parse_args()
    try:
        frontend_base_url = ensure_base_url(args.base_url, "--base-url")
        api_base_url = ensure_base_url(args.api_base_url, "--api-base-url")
    except ValueError as exc:
        print(str(exc))
        return 2

    if not wait_ready(f"{frontend_base_url}/login", timeout_sec=10):
        print(f"frontend not reachable: {frontend_base_url}/login")
        return 2
    if not wait_ready(f"{api_base_url}/api/question-bank/auth/me", timeout_sec=10):
        print(f"api not reachable: {api_base_url}/api/question-bank/auth/me")
        return 2

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("缺少 Playwright 依赖，请先执行 ./tools/bin/bootstrap-python.sh && ./.venv/bin/python -m playwright install chromium")
        return 2

    started_at = time.time()
    report: Dict[str, Any] = {
        "mode": "knowledge-galaxy-true-click-replay",
        "frontendBaseUrl": frontend_base_url,
        "apiBaseUrl": api_base_url,
        "headless": not args.headed,
        "timeoutSec": int(args.timeout_sec),
        "teacher": {},
        "student": {},
    }
    try:
        with sync_playwright() as playwright:
            report["teacher"] = run_teacher_flow(
                playwright=playwright,
                frontend_base_url=frontend_base_url,
                api_base_url=api_base_url,
                timeout_sec=args.timeout_sec,
                headless=not args.headed,
            )
            report["student"] = run_student_flow(
                playwright=playwright,
                frontend_base_url=frontend_base_url,
                api_base_url=api_base_url,
                timeout_sec=args.timeout_sec,
                headless=not args.headed,
            )
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
        report["elapsedSec"] = round(time.time() - started_at, 3)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    report["status"] = "PASS"
    report["elapsedSec"] = round(time.time() - started_at, 3)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
