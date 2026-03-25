from __future__ import annotations

from app.service_shared import *


class InternalStudentServiceMixin:
    CHALLENGE_POINT_AWARD_THRESHOLD = 10_000
    CHALLENGE_POINT_AWARD_CODE = "SUBJECT_CHALLENGE_STAR"
    CHALLENGE_POINT_AWARD_NAME = "学科练习之星"
    CHALLENGE_POINT_LEVELS = (
        {"code": "BRONZE", "name": "刷题青铜", "min": 0, "max": 999},
        {"code": "SILVER", "name": "刷题白银", "min": 1000, "max": 2499},
        {"code": "GOLD", "name": "刷题黄金", "min": 2500, "max": 4499},
        {"code": "PLATINUM", "name": "刷题铂金", "min": 4500, "max": 6499},
        {"code": "DIAMOND", "name": "刷题钻石", "min": 6500, "max": 7999},
        {"code": "STAR", "name": "刷题星耀", "min": 8000, "max": 9299},
        {"code": "GLORY_KING", "name": "荣耀王者", "min": 9300, "max": 9799},
        {"code": "LEGEND_KING", "name": "传奇王者", "min": 9800, "max": 10000},
    )

    def _build_challenge_point_level(self, total_points: int) -> Dict[str, object]:
        threshold = int(self.CHALLENGE_POINT_AWARD_THRESHOLD)
        normalized_total = max(0, int(total_points or 0))
        capped_total = min(normalized_total, threshold)
        levels = list(self.CHALLENGE_POINT_LEVELS)
        current_index = len(levels) - 1
        for index, level in enumerate(levels):
            if capped_total <= int(level.get("max", threshold)):
                current_index = index
                break

        current_level = levels[current_index]
        next_level = levels[current_index + 1] if current_index + 1 < len(levels) else None
        current_floor = int(current_level.get("min", 0))
        next_threshold = int(next_level.get("min", threshold)) if next_level else threshold
        current_progress_total = max(1, next_threshold - current_floor) if next_level else max(1, threshold - current_floor)
        current_progress = max(0, capped_total - current_floor)

        return {
            "scoreCap": threshold,
            "cappedTotal": capped_total,
            "scorePercent": int(round((capped_total / threshold) * 100)) if threshold else 0,
            "levelCode": str(current_level.get("code", "")).strip(),
            "levelName": str(current_level.get("name", "")).strip() or "刷题青铜",
            "levelFloor": current_floor,
            "levelCeil": int(current_level.get("max", threshold)),
            "levelProgress": current_progress,
            "levelProgressTotal": current_progress_total,
            "levelProgressPercent": 100 if not next_level else int(round((current_progress / current_progress_total) * 100)),
            "nextLevelCode": str(next_level.get("code", "")).strip() if next_level else "",
            "nextLevelName": str(next_level.get("name", "")).strip() if next_level else "",
            "nextLevelThreshold": next_threshold,
            "pointsToNextLevel": max(0, next_threshold - capped_total) if next_level else 0,
            "isTopLevel": next_level is None,
        }

    def _collect_adaptive_history_rows(
        self,
        student_user_id: str,
        scope_filters: Dict[str, str],
    ) -> List[Dict[str, object]]:
        records = self.repository.list_student_records_by_user(student_user_id)
        records = self._filter_questions_for_student_scope(records, student_user_id, scope_filters)
        history_rows: List[Dict[str, object]] = []
        for question in records:
            analytics_payload = self._extract_analytics_payload(question)
            if str(analytics_payload.get("studentUserId", "")).strip() != student_user_id:
                continue
            submitted_at = str(analytics_payload.get("submittedAt", "")).strip()
            knowledge_id = str(question.get("knowledgeId", "")).strip()
            if not submitted_at or not knowledge_id:
                continue
            history_rows.append(
                {
                    "knowledgeId": knowledge_id,
                    "isCorrect": bool(analytics_payload.get("isCorrect", False)),
                    "answerDurationSec": max(0, int(analytics_payload.get("answerDurationSec", 0))),
                    "difficulty": self._normalize_adaptive_difficulty(self._question_difficulty(question)),
                }
            )
        return history_rows

    def _build_adaptive_mastery_snapshot(
        self,
        question_pool: List[Dict[str, str]],
        history_rows: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        question_count_by_knowledge: Dict[str, int] = {}
        for question in question_pool:
            knowledge_id = str(question.get("knowledgeId", "")).strip()
            if not knowledge_id:
                continue
            question_count_by_knowledge[knowledge_id] = question_count_by_knowledge.get(knowledge_id, 0) + 1

        history_by_knowledge: Dict[str, List[Dict[str, object]]] = {}
        for row in history_rows:
            knowledge_id = str(row.get("knowledgeId", "")).strip()
            if not knowledge_id:
                continue
            history_by_knowledge.setdefault(knowledge_id, []).append(row)

        all_knowledge_ids = sorted(set(question_count_by_knowledge.keys()) | set(history_by_knowledge.keys()))
        global_average_duration = (
            sum(int(item.get("answerDurationSec", 0)) for item in history_rows) / len(history_rows)
            if history_rows
            else 60.0
        )
        if global_average_duration <= 0:
            global_average_duration = 60.0

        snapshot: List[Dict[str, object]] = []
        for knowledge_id in all_knowledge_ids:
            rows = history_by_knowledge.get(knowledge_id, [])
            answered = len(rows)
            correct = len([item for item in rows if item.get("isCorrect")])
            pool_total = max(1, int(question_count_by_knowledge.get(knowledge_id, 0)))
            if answered > 0:
                accuracy = correct / answered
                average_duration = sum(int(item.get("answerDurationSec", 0)) for item in rows) / answered
                speed = 1.0 if average_duration <= 0 else min(1.0, global_average_duration / average_duration)
                frequency = min(1.0, answered / pool_total)
            else:
                accuracy = 0.0
                speed = 0.0
                frequency = 0.0
            mastery = (accuracy * 0.6) + (speed * 0.2) + (frequency * 0.2)
            snapshot.append(
                {
                    "knowledgeId": knowledge_id,
                    "mastery": round(mastery, 4),
                    "accuracy": round(accuracy, 4),
                    "speed": round(speed, 4),
                    "frequency": round(frequency, 4),
                    "answered": answered,
                    "poolTotal": pool_total,
                }
            )

        snapshot.sort(key=lambda item: (float(item["mastery"]), int(item["answered"]), str(item["knowledgeId"])))
        return snapshot

    def _question_subject_code(self, question: Dict[str, str]) -> str:
        ext_json = self._question_ext_json(question)
        return str(ext_json.get("subjectCode", "")).strip()

    def _challenge_point_source_type(self, source_type: str) -> str:
        normalized = str(source_type or "").strip().upper()
        if normalized in {"FREE", "FREE_PRACTICE"}:
            return "FREE_PRACTICE"
        if normalized in {"MOCK", "MOCK_EXAM"}:
            return "MOCK_EXAM"
        return "CHAPTER_CHALLENGE"

    def _build_challenge_point_summary(
        self,
        student_user_id: str,
        subject_code: str,
        leaderboard_limit: int = 8,
    ) -> Dict[str, object]:
        normalized_subject_code = str(subject_code or "").strip()
        if not normalized_subject_code:
            return {
                "subjectCode": "",
                "total": 0,
                "todayDelta": 0,
                "correctSubmitCount": 0,
                "todayCorrectSubmitCount": 0,
                "rank": 0,
                "leaderboard": [],
                "awardUnlocked": False,
                "awardProgress": 0,
                "awardThreshold": int(self.CHALLENGE_POINT_AWARD_THRESHOLD),
                "award": {},
                **self._build_challenge_point_level(0),
            }
        today = datetime.now(timezone.utc).date().isoformat()
        summary = self.repository.get_challenge_point_subject(student_user_id, normalized_subject_code) or {}
        total = int(summary.get("totalPoints", 0) or 0)
        reached_at = str(summary.get("updateTime", "") or summary.get("lastAwardedAt", "") or "").strip()
        rank = (
            self.repository.get_challenge_point_rank(normalized_subject_code, total, reached_at, student_user_id)
            if total > 0 and reached_at
            else 0
        )
        leaderboard = self.repository.list_challenge_point_leaderboard(normalized_subject_code, leaderboard_limit)
        awards = self.repository.list_challenge_point_awards(student_user_id, normalized_subject_code)
        award = awards[0] if awards else {}
        award_progress = min(total, int(self.CHALLENGE_POINT_AWARD_THRESHOLD))
        level_payload = self._build_challenge_point_level(total)
        today_correct_submit_count = self.repository.count_today_challenge_point_correct_submits(
            student_user_id,
            normalized_subject_code,
            today,
        )
        correct_submit_count = self.repository.count_challenge_point_correct_submits(student_user_id, normalized_subject_code)
        return {
            "subjectCode": normalized_subject_code,
            "total": total,
            "todayDelta": self.repository.count_today_challenge_points(student_user_id, normalized_subject_code, today),
            "correctSubmitCount": correct_submit_count,
            "todayCorrectSubmitCount": today_correct_submit_count,
            "rank": rank,
            "leaderboard": leaderboard,
            "awardUnlocked": total >= int(self.CHALLENGE_POINT_AWARD_THRESHOLD),
            "awardProgress": award_progress,
            "awardThreshold": int(self.CHALLENGE_POINT_AWARD_THRESHOLD),
            "award": award if isinstance(award, dict) else {},
            **level_payload,
        }

    def _build_challenge_point_subject_rows(
        self,
        student_user_id: str,
        core_subjects: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        repository_rows = {
            str(item.get("subjectCode", "")).strip(): item
            for item in self.repository.list_challenge_point_subjects_by_student(student_user_id)
            if str(item.get("subjectCode", "")).strip()
        }
        today = datetime.now(timezone.utc).date().isoformat()
        rows: List[Dict[str, object]] = []
        seen: set[str] = set()
        for subject in core_subjects:
            subject_code = str(subject.get("subjectCode", "")).strip()
            if not subject_code or subject_code in seen:
                continue
            seen.add(subject_code)
            repository_row = repository_rows.get(subject_code, {})
            total = int(repository_row.get("totalPoints", 0) or 0)
            reached_at = str(repository_row.get("updateTime", "") or repository_row.get("lastAwardedAt", "") or "").strip()
            rank = (
                self.repository.get_challenge_point_rank(subject_code, total, reached_at, student_user_id)
                if total > 0 and reached_at
                else 0
            )
            rows.append(
                {
                    "subjectCode": subject_code,
                    "subjectName": str(subject.get("subjectName", subject_code)).strip() or subject_code,
                    "total": total,
                    "todayDelta": self.repository.count_today_challenge_points(student_user_id, subject_code, today),
                    "correctSubmitCount": self.repository.count_challenge_point_correct_submits(student_user_id, subject_code),
                    "todayCorrectSubmitCount": self.repository.count_today_challenge_point_correct_submits(
                        student_user_id,
                        subject_code,
                        today,
                    ),
                    "rank": rank,
                    "awardUnlocked": total >= int(self.CHALLENGE_POINT_AWARD_THRESHOLD),
                    "awardProgress": min(total, int(self.CHALLENGE_POINT_AWARD_THRESHOLD)),
                    "awardThreshold": int(self.CHALLENGE_POINT_AWARD_THRESHOLD),
                    **self._build_challenge_point_level(total),
                }
            )
        rows.sort(key=lambda item: (-int(item["total"]), int(item["rank"] or 10**9), str(item["subjectCode"])))
        return rows

    def _grant_challenge_point_for_question(
        self,
        question: Dict[str, str],
        student_user_id: str,
        source_type: str,
        attempt_key: str,
    ) -> Dict[str, object]:
        subject_code = self._question_subject_code(question)
        if not subject_code:
            return {
                "challengePointDelta": 0,
                "challengePointGranted": False,
                "challengePointTotal": 0,
                "subjectRank": 0,
                "challengePoints": self._build_challenge_point_summary(student_user_id, subject_code),
            }
        result = self.repository.grant_challenge_point(
            student_user_id,
            str(question.get("id", "")).strip(),
            subject_code,
            attempt_key,
            self._challenge_point_source_type(source_type),
            self._now_iso(),
            points=1,
            award_threshold=int(self.CHALLENGE_POINT_AWARD_THRESHOLD),
            award_code=str(self.CHALLENGE_POINT_AWARD_CODE),
            award_name=str(self.CHALLENGE_POINT_AWARD_NAME),
        )
        summary = self._build_challenge_point_summary(student_user_id, subject_code)
        return {
            "challengePointDelta": 1 if bool(result.get("granted")) else 0,
            "challengePointGranted": bool(result.get("granted")),
            "challengePointTotal": int(summary.get("total", 0) or 0),
            "subjectRank": int(summary.get("rank", 0) or 0),
            "challengePoints": summary,
            "challengeAwardGranted": bool(result.get("awardGranted")),
        }

    def _resolve_challenge_point_attempt_key(self, raw_attempt_key: object) -> str:
        normalized_attempt_key = str(raw_attempt_key or "").strip()
        if normalized_attempt_key:
            return normalized_attempt_key[:120]
        return uuid.uuid4().hex

    def _select_adaptive_target_knowledge_ids(
        self,
        mastery_snapshot: List[Dict[str, object]],
        top_n: int = 3,
        mastery_threshold: float = 0.4,
    ) -> List[str]:
        if top_n <= 0:
            return []
        weak_ids: List[str] = []
        seen: set[str] = set()
        for row in mastery_snapshot:
            knowledge_id = str(row.get("knowledgeId", "")).strip()
            if not knowledge_id or knowledge_id in seen:
                continue
            if float(row.get("mastery", 0.0)) < mastery_threshold:
                weak_ids.append(knowledge_id)
                seen.add(knowledge_id)
                if len(weak_ids) >= top_n:
                    return weak_ids
        for row in mastery_snapshot:
            knowledge_id = str(row.get("knowledgeId", "")).strip()
            if not knowledge_id or knowledge_id in seen:
                continue
            weak_ids.append(knowledge_id)
            seen.add(knowledge_id)
            if len(weak_ids) >= top_n:
                break
        return weak_ids

    def _allocate_adaptive_question_counts(
        self,
        target_knowledge_ids: List[str],
        mastery_snapshot: List[Dict[str, object]],
        requested_count: int,
    ) -> Dict[str, int]:
        if requested_count <= 0:
            return {}
        normalized_knowledge_ids = [str(item).strip() for item in target_knowledge_ids if str(item).strip()]
        if not normalized_knowledge_ids:
            return {}

        unique_knowledge_ids: List[str] = []
        seen_knowledge_ids: set[str] = set()
        for knowledge_id in normalized_knowledge_ids:
            if knowledge_id in seen_knowledge_ids:
                continue
            seen_knowledge_ids.add(knowledge_id)
            unique_knowledge_ids.append(knowledge_id)

        mastery_map = {
            str(item.get("knowledgeId", "")).strip(): float(item.get("mastery", 0.0))
            for item in mastery_snapshot
            if str(item.get("knowledgeId", "")).strip()
        }
        gaps: List[float] = [max(0.0, 1.0 - float(mastery_map.get(knowledge_id, 0.0))) for knowledge_id in unique_knowledge_ids]
        if not any(gap > 0 for gap in gaps):
            gaps = [1.0 for _ in unique_knowledge_ids]

        total_gap = sum(gaps)
        if total_gap <= 0:
            return {}

        raw_counts = [requested_count * (gap / total_gap) for gap in gaps]
        base_counts = [int(count) for count in raw_counts]
        allocated = sum(base_counts)
        remainder = max(0, requested_count - allocated)

        remainder_priority_indexes = sorted(
            range(len(unique_knowledge_ids)),
            key=lambda index: (gaps[index], raw_counts[index] - base_counts[index], -index),
            reverse=True,
        )
        for index in remainder_priority_indexes:
            if remainder <= 0:
                break
            base_counts[index] += 1
            remainder -= 1

        quota_map: Dict[str, int] = {}
        for index, knowledge_id in enumerate(unique_knowledge_ids):
            quota_map[knowledge_id] = max(0, int(base_counts[index]))
        return quota_map

    def _normalize_adaptive_difficulty(self, difficulty: object) -> str:
        normalized = str(difficulty or "").strip().lower()
        if normalized in {"easy", "medium", "hard"}:
            return normalized
        return "medium"

    def _resolve_adaptive_difficulty_cycle(self, history_rows: List[Dict[str, object]]) -> List[str]:
        score_map = {"easy": 1.0, "medium": 2.0, "hard": 3.0}
        scores = [
            score_map[str(item.get("difficulty", ""))]
            for item in history_rows
            if str(item.get("difficulty", "")) in score_map
        ]
        if not scores:
            return ["easy", "medium", "hard"]
        average_score = sum(scores) / len(scores)
        if average_score <= 1.6:
            return ["easy", "medium", "hard"]
        if average_score >= 2.4:
            return ["medium", "hard", "easy"]
        return ["medium", "easy", "hard"]

    def _select_adaptive_question_ids(
        self,
        question_pool: List[Dict[str, str]],
        target_knowledge_ids: List[str],
        difficulty_cycle: List[str],
        requested_count: int,
        target_knowledge_quota: Optional[Dict[str, int]] = None,
    ) -> List[str]:
        if requested_count <= 0:
            return []
        normalized_knowledge_ids = [str(item).strip() for item in target_knowledge_ids if str(item).strip()]
        knowledge_priority = {knowledge_id: index for index, knowledge_id in enumerate(normalized_knowledge_ids)}
        difficulty_rank = {difficulty: index for index, difficulty in enumerate(difficulty_cycle)}

        def sort_key(question: Dict[str, str]) -> Tuple[int, int, str]:
            knowledge_id = str(question.get("knowledgeId", "")).strip()
            difficulty = self._normalize_adaptive_difficulty(self._question_difficulty(question))
            return (
                knowledge_priority.get(knowledge_id, len(knowledge_priority) + 1),
                difficulty_rank.get(difficulty, len(difficulty_rank) + 1),
                str(question.get("id", "")),
            )

        candidate_pool = (
            [question for question in question_pool if str(question.get("knowledgeId", "")).strip() in set(normalized_knowledge_ids)]
            if normalized_knowledge_ids
            else list(question_pool)
        )
        if not candidate_pool:
            candidate_pool = list(question_pool)
        candidate_pool = sorted(candidate_pool, key=sort_key)

        selected_ids: List[str] = []
        selected_set: set[str] = set()

        normalized_cycle = [difficulty for difficulty in difficulty_cycle if difficulty in {"easy", "medium", "hard"}]
        if not normalized_cycle:
            normalized_cycle = ["easy", "medium", "hard"]

        knowledge_difficulty_buckets: Dict[str, Dict[str, List[Dict[str, str]]]] = {
            knowledge_id: {"easy": [], "medium": [], "hard": []}
            for knowledge_id in normalized_knowledge_ids
        }
        for question in candidate_pool:
            knowledge_id = str(question.get("knowledgeId", "")).strip()
            if knowledge_id not in knowledge_difficulty_buckets:
                continue
            difficulty = self._normalize_adaptive_difficulty(self._question_difficulty(question))
            knowledge_difficulty_buckets[knowledge_id][difficulty].append(question)

        quota_map = dict(target_knowledge_quota or {})
        for knowledge_id in normalized_knowledge_ids:
            quota = int(quota_map.get(knowledge_id, 0))
            if quota <= 0:
                continue
            buckets = knowledge_difficulty_buckets.get(knowledge_id, {"easy": [], "medium": [], "hard": []})
            while quota > 0 and len(selected_ids) < requested_count:
                progressed = False
                for difficulty in normalized_cycle:
                    queue = buckets.get(difficulty, [])
                    if not queue:
                        continue
                    question = queue.pop(0)
                    question_id = str(question.get("id", "")).strip()
                    if not question_id or question_id in selected_set:
                        continue
                    selected_ids.append(question_id)
                    selected_set.add(question_id)
                    quota -= 1
                    progressed = True
                    if quota <= 0 or len(selected_ids) >= requested_count:
                        break
                if progressed:
                    continue
                fallback_added = False
                for difficulty in ("easy", "medium", "hard"):
                    queue = buckets.get(difficulty, [])
                    if not queue:
                        continue
                    question = queue.pop(0)
                    question_id = str(question.get("id", "")).strip()
                    if not question_id or question_id in selected_set:
                        continue
                    selected_ids.append(question_id)
                    selected_set.add(question_id)
                    quota -= 1
                    fallback_added = True
                    break
                if not fallback_added:
                    break

        if len(selected_ids) < requested_count:
            for question in candidate_pool:
                question_id = str(question.get("id", "")).strip()
                if not question_id or question_id in selected_set:
                    continue
                selected_ids.append(question_id)
                selected_set.add(question_id)
                if len(selected_ids) >= requested_count:
                    return selected_ids[:requested_count]

        buckets: Dict[str, List[Dict[str, str]]] = {"easy": [], "medium": [], "hard": []}
        leftovers: List[Dict[str, str]] = []
        for question in candidate_pool:
            question_id = str(question.get("id", "")).strip()
            if not question_id or question_id in selected_set:
                continue
            difficulty = self._normalize_adaptive_difficulty(self._question_difficulty(question))
            if difficulty in buckets:
                buckets[difficulty].append(question)
            else:
                leftovers.append(question)

        while len(selected_ids) < requested_count:
            progressed = False
            for difficulty in normalized_cycle:
                queue = buckets.get(difficulty, [])
                if not queue:
                    continue
                question = queue.pop(0)
                question_id = str(question.get("id", "")).strip()
                if not question_id or question_id in selected_set:
                    continue
                selected_ids.append(question_id)
                selected_set.add(question_id)
                progressed = True
                if len(selected_ids) >= requested_count:
                    return selected_ids[:requested_count]
            if not progressed:
                break

        fallback_pool = leftovers + [question for queue in buckets.values() for question in queue]
        for question in fallback_pool:
            question_id = str(question.get("id", "")).strip()
            if not question_id or question_id in selected_set:
                continue
            selected_ids.append(question_id)
            selected_set.add(question_id)
            if len(selected_ids) >= requested_count:
                return selected_ids[:requested_count]

        if len(selected_ids) < requested_count:
            for question in sorted(question_pool, key=sort_key):
                question_id = str(question.get("id", "")).strip()
                if not question_id or question_id in selected_set:
                    continue
                selected_ids.append(question_id)
                selected_set.add(question_id)
                if len(selected_ids) >= requested_count:
                    break
        return selected_ids[:requested_count]

    def _build_student_dashboard_payload(self, profile: Dict[str, object], student_user_id: str) -> Dict[str, object]:
        self._assert_student_profile_complete(profile)
        exam_category_code = str(profile.get("examCategoryCode", "")).strip()
        joint_exam_group_code = str(profile.get("jointExamGroupCode", "")).strip()
        joint_exam_group = get_joint_exam_group(joint_exam_group_code)
        exam_category = get_exam_category(exam_category_code)
        available_exam_categories = self._build_student_dashboard_exam_categories()
        available_joint_exam_groups = self._build_student_dashboard_available_joint_exam_groups(
            available_exam_categories,
            exam_category_code,
        )
        core_subjects = self._build_student_core_subjects(joint_exam_group, student_user_id)
        check_in_dates = list(profile.get("checkInDates", []))
        today_progress = self._today_progress(profile)
        daily_tasks = self._build_student_daily_tasks(today_progress)
        ai_quota = self._build_student_dashboard_ai_quota(profile)
        streak_days = self._compute_check_in_streak(check_in_dates)
        challenge_point_subjects = self._build_challenge_point_subject_rows(student_user_id, core_subjects)
        onboarding_snapshot = (
            self._resolve_student_onboarding_snapshot(student_user_id)
            if hasattr(self, "_resolve_student_onboarding_snapshot")
            else {
                "completed": False,
                "completionSource": "NONE",
                "quickDiagnosisCompleted": False,
                "subscriptionActive": False,
                "latestQuickDiagnosisSession": {
                    "sessionId": "",
                    "status": "",
                    "submittedAt": "",
                    "answeredCount": 0,
                    "correctCount": 0,
                    "accuracy": 0.0,
                },
            }
        )
        return {
            "policyVersionCode": POLICY_VERSION_CODE,
            "examCategoryCode": exam_category_code,
            "jointExamGroupCode": joint_exam_group_code,
            "examCategoryName": exam_category["examCategoryName"] if exam_category else "",
            "jointExamGroupName": joint_exam_group["jointExamGroupName"] if joint_exam_group else "",
            # Selector source is single-path: front-end derives jointExamGroups from selected availableExamCategories item.
            "availableExamCategories": available_exam_categories,
            "availableJointExamGroups": available_joint_exam_groups,
            "coreSubjects": core_subjects,
            "points": int(profile.get("points", 0)),
            "title": profile.get("title", "备考新星"),
            "streakDays": streak_days,
            "dailyTasks": daily_tasks,
            "aiQuota": ai_quota,
            "challengePointSubjects": challenge_point_subjects,
            "recentPointsLedger": list(profile.get("pointsLedger", []))[-8:][::-1],
            "unlockedTitles": profile.get("unlockedTitles", [profile.get("title", "备考新星")]),
            "personalBankCount": self._count_personal_bank_questions(student_user_id),
            "messageUnreadCount": self._count_unread_messages(student_user_id),
            "examSession": dict(profile.get("examSession", {})),
            "onboarding": onboarding_snapshot,
            "studentState": self._build_student_state_snapshot(
                profile,
                daily_tasks,
                today_progress,
                ai_quota,
                streak_days,
                check_in_dates,
                challenge_point_subjects,
                onboarding_snapshot,
            ),
            "chapterPracticeTree": self._build_student_chapter_practice_tree(profile, student_user_id),
        }

    def _build_student_dashboard_exam_categories(self) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for category in build_content_baseline().get("examCategories", []):
            if not isinstance(category, dict):
                continue
            joint_exam_groups: List[Dict[str, object]] = []
            for group in category.get("jointExamGroups", []):
                if not isinstance(group, dict):
                    continue
                joint_exam_groups.append(
                    {
                        "jointExamGroupCode": str(group.get("jointExamGroupCode", "")),
                        "jointExamGroupName": str(group.get("jointExamGroupName", "")),
                    }
                )
            rows.append(
                {
                    "examCategoryCode": str(category.get("examCategoryCode", "")),
                    "examCategoryName": str(category.get("examCategoryName", "")),
                    "sortNo": int(category.get("sortNo", 0)),
                    "jointExamGroups": joint_exam_groups,
                }
            )
        return rows

    def _build_student_dashboard_available_joint_exam_groups(
        self,
        exam_categories: List[Dict[str, object]],
        exam_category_code: str,
    ) -> List[Dict[str, object]]:
        selected_code = str(exam_category_code or "").strip()
        if not selected_code:
            return []
        selected_category = next(
            (
                item
                for item in exam_categories
                if str(item.get("examCategoryCode", "")).strip() == selected_code
            ),
            None,
        )
        if not isinstance(selected_category, dict):
            return []
        groups: List[Dict[str, object]] = []
        for group in selected_category.get("jointExamGroups", []):
            if not isinstance(group, dict):
                continue
            group_code = str(group.get("jointExamGroupCode", "")).strip()
            if not group_code:
                continue
            groups.append(
                {
                    "jointExamGroupCode": group_code,
                    "jointExamGroupName": str(group.get("jointExamGroupName", "")),
                    "examCategoryCode": selected_code,
                }
            )
        return groups

    def _build_student_dashboard_ai_quota(self, profile: Dict[str, object]) -> Dict[str, object]:
        ai_quota = self._current_ai_quota(profile)
        return {
            "dailyLimit": int(ai_quota.get("dailyLimit", 0)),
            "usedCount": int(ai_quota.get("usedCount", 0)),
        }

    def _build_student_state_snapshot(
        self,
        profile: Dict[str, object],
        daily_tasks: List[Dict[str, object]],
        today_progress: Dict[str, object],
        ai_quota: Dict[str, object],
        streak_days: int,
        check_in_dates: List[str],
        challenge_point_subjects: List[Dict[str, object]],
        onboarding_snapshot: Dict[str, object],
    ) -> Dict[str, object]:
        today = datetime.now(timezone.utc).date().isoformat()
        return {
            "today": today,
            "checkInDone": today in check_in_dates,
            "todayProgress": today_progress,
            "dailyTasks": daily_tasks,
            "points": int(profile.get("points", 0)),
            "challengePointSubjects": challenge_point_subjects,
            "title": profile.get("title", "备考新星"),
            "streakDays": streak_days,
            "aiQuota": ai_quota,
            "examCategoryCode": str(profile.get("examCategoryCode", "")),
            "jointExamGroupCode": str(profile.get("jointExamGroupCode", "")),
            "onboardingCompleted": bool(onboarding_snapshot.get("completed", False)),
        }

    def _build_student_chapter_practice_tree(
        self,
        profile: Dict[str, object],
        student_user_id: str,
    ) -> List[Dict[str, object]]:
        exam_category_code = str(profile.get("examCategoryCode", "")).strip()
        joint_exam_group_code = str(profile.get("jointExamGroupCode", "")).strip()
        if not exam_category_code or not joint_exam_group_code:
            return []
        questions = self.repository.list_visible_published_questions(
            {"subjectId": "", "chapter": "", "type": "", "difficulty": ""},
            ROLE_SUPER_ADMIN,
            student_user_id,
        )
        questions = self._filter_questions_for_student_scope(
            questions,
            student_user_id,
            {
                "examCategoryCode": exam_category_code,
                "jointExamGroupCode": joint_exam_group_code,
                "subjectCode": "",
            },
        )
        by_subject: Dict[str, List[Dict[str, str]]] = {}
        for question in questions:
            subject_id = self._question_subject_id(question)
            if not subject_id:
                continue
            by_subject.setdefault(subject_id, []).append(question)
        if not by_subject:
            return []

        subject_items = self.repository.list_subjects()
        subject_order = [str(item.get("id", "")) for item in subject_items if not item.get("parentId")]
        subject_name_map = {
            str(item.get("id", "")): str(item.get("name", ""))
            for item in subject_items
            if not item.get("parentId")
        }
        ordered_subject_ids = [subject_id for subject_id in subject_order if subject_id in by_subject]
        for subject_id in sorted(by_subject.keys()):
            if subject_id not in ordered_subject_ids:
                ordered_subject_ids.append(subject_id)

        record_ext_cache: Dict[str, Dict[str, object]] = {}
        tree: List[Dict[str, object]] = []
        for subject_id in ordered_subject_ids:
            chapter_rows = self._build_dashboard_subject_chapter_rows(
                subject_id,
                by_subject.get(subject_id, []),
                student_user_id,
                record_ext_cache,
            )
            if not chapter_rows:
                continue
            tree.append(
                {
                    "subjectId": subject_id,
                    "subjectName": subject_name_map.get(subject_id, subject_id),
                    "chapterCount": len(chapter_rows),
                    "unlockedChapterCount": len([row for row in chapter_rows if row.get("isUnlocked")]),
                    "chapters": chapter_rows,
                }
            )
        return tree

    def _build_dashboard_subject_chapter_rows(
        self,
        subject_id: str,
        subject_questions: List[Dict[str, str]],
        student_user_id: str,
        record_ext_cache: Dict[str, Dict[str, object]],
    ) -> List[Dict[str, object]]:
        chapter_order = self._chapter_order_for_subject(subject_id, subject_questions)
        if not chapter_order:
            return []
        chapter_questions_map: Dict[str, List[Dict[str, str]]] = {}
        for question in subject_questions:
            chapter = self._question_chapter(question)
            if not chapter:
                continue
            chapter_questions_map.setdefault(chapter, []).append(question)
        if not chapter_questions_map:
            return []

        rows: List[Dict[str, object]] = []
        for chapter in chapter_order:
            chapter_questions = chapter_questions_map.get(chapter, [])
            if not chapter_questions:
                continue
            answered = 0
            correct = 0
            for question in chapter_questions:
                question_id = str(question.get("id", ""))
                if question_id not in record_ext_cache:
                    record = self.repository.get_student_question_bank(question_id, student_user_id)
                    record_ext_cache[question_id] = self._load_json_object(record["extJson"] if record else "{}")
                chapter_practice = record_ext_cache[question_id].get("chapterPractice", {})
                if chapter_practice:
                    answered += 1
                    if chapter_practice.get("isCorrect"):
                        correct += 1
            total = len(chapter_questions)
            accuracy = round(correct / answered, 4) if answered else 0.0
            previous_accuracy = float(rows[-1]["accuracy"]) if rows else 1.0
            is_unlocked = True if not rows else previous_accuracy >= 0.8
            rows.append(
                {
                    "subjectId": subject_id,
                    "chapter": chapter,
                    "answered": answered,
                    "total": total,
                    "accuracy": accuracy,
                    "accuracyPercent": int(round(accuracy * 100)),
                    "isUnlocked": is_unlocked,
                    "isLocked": not is_unlocked,
                }
            )

        current_chapter = ""
        for row in rows:
            if row["isUnlocked"] and row["answered"] < row["total"]:
                current_chapter = str(row["chapter"])
                break
        if not current_chapter:
            unlocked_rows = [row for row in rows if row["isUnlocked"]]
            if unlocked_rows:
                current_chapter = str(unlocked_rows[-1]["chapter"])
        for row in rows:
            row["isCurrent"] = str(row["chapter"]) == current_chapter
            if row["isCurrent"]:
                row["statusLabel"] = "正在闯关"
            elif row["isUnlocked"]:
                row["statusLabel"] = "已解锁"
            else:
                row["statusLabel"] = "未解锁"
        return rows

    def _assert_student_profile_complete(self, profile: Dict[str, object]) -> None:
        exam_category_code = str(profile.get("examCategoryCode", "")).strip()
        joint_exam_group_code = str(profile.get("jointExamGroupCode", "")).strip()
        if not exam_category_code or not joint_exam_group_code:
            raise profile_incomplete("请先完善学科门类与联考专业组信息。")
        exam_category = get_exam_category(exam_category_code)
        joint_exam_group = get_joint_exam_group(joint_exam_group_code)
        if not exam_category or not joint_exam_group:
            raise profile_incomplete("考生画像配置无效，请联系管理员修复后重试。")
        if str(joint_exam_group.get("examCategoryCode", "")) != exam_category_code:
            raise profile_incomplete("考生画像中的学科门类与联考专业组不一致。")

    def _validate_student_profile_selection(self, exam_category_code: str, joint_exam_group_code: str) -> None:
        normalized_exam_category_code = str(exam_category_code or "").strip()
        normalized_joint_exam_group_code = str(joint_exam_group_code or "").strip()
        exam_category = get_exam_category(normalized_exam_category_code)
        if not exam_category:
            raise validation_failed("examCategoryCode 不存在。")
        available_joint_exam_groups = self._build_student_dashboard_available_joint_exam_groups(
            self._build_student_dashboard_exam_categories(),
            normalized_exam_category_code,
        )
        available_group_codes = {str(item.get("jointExamGroupCode", "")).strip() for item in available_joint_exam_groups}
        if normalized_joint_exam_group_code not in available_group_codes:
            raise validation_failed("jointExamGroupCode 与 examCategoryCode 不匹配。")

    def _apply_student_profile_selection(
        self,
        profile: Dict[str, object],
        exam_category_code: str,
        joint_exam_group_code: str,
    ) -> Dict[str, object]:
        updated = dict(profile)
        updated["examCategoryCode"] = exam_category_code
        updated["jointExamGroupCode"] = joint_exam_group_code
        return updated

    def _apply_student_daily_check_in(
        self,
        profile: Dict[str, object],
        settings: Dict[str, object],
        today: str,
        student_user_id: str,
    ) -> int:
        check_in_dates = list(profile.get("checkInDates", []))
        if today in check_in_dates:
            raise validation_failed("今日已完成打卡。")
        now_iso = self._now_iso()
        hot_state_changed = False
        self.repository.append_student_profile_check_in_date(student_user_id, today, now_iso)
        self.repository.increment_student_daily_progress_metric(student_user_id, today, "checkInCount", 1, now_iso)
        self._grant_points(
            profile,
            student_user_id,
            int(settings["dailyCheckInPoints"]),
            "每日打卡",
            f"checkIn:{today}",
            now_iso,
        )
        self._refresh_profile_hot_state_from_formal(profile, student_user_id)
        streak_days = self._compute_check_in_streak(profile["checkInDates"])
        if streak_days % 7 == 0:
            self._grant_points(profile, student_user_id, 50, "连续打卡7天奖励", f"checkInStreak:{today}", now_iso)
        return streak_days

    def _notify_check_in_success(self, user_id: str, points: int) -> None:
        self._push_message(
            [user_id],
            "POINTS_NOTICE",
            "打卡成功",
            f"今日打卡已完成，当前积分 {points}。"
        )

    def _evaluate_student_paper_submission(
        self,
        paper_questions: List[Dict[str, str]],
        answers: List[object],
        paper_id: str,
        student_user_id: str,
    ) -> Dict[str, object]:
        answer_map = {item.questionId: item for item in answers}
        question_map = {question["id"]: question for question in paper_questions}
        total_score = 0
        score_obtained = 0
        type_accuracy: Dict[str, Dict[str, int]] = {}
        wrong_question_ids: List[str] = []
        pending_subjective_task_ids: List[str] = []
        question_results: List[Dict[str, object]] = []
        for question_id, question in question_map.items():
            item = answer_map.get(question_id)
            binding = self._get_binding_by_paper_id(question, paper_id)
            question_score = int(binding.get("questionScore", 0)) if binding else 0
            total_score += question_score
            if not item:
                wrong_question_ids.append(question_id)
                self._accumulate_question_type_accuracy(type_accuracy, question["type"], False)
                self._save_student_paper_attempt(
                    question_id,
                    student_user_id,
                    paper_id,
                    "",
                    "",
                    False,
                    0,
                    False,
                )
                question_results.append(
                    self._build_report_question_result(
                        question=question,
                        answer="",
                        normalized_answer="",
                        is_correct=False,
                        is_pending_ai_marking=False,
                        marked=False,
                        elapsed_sec=0,
                        score=0,
                        total_score=question_score,
                        ai_marking_task_id="",
                    )
                )
                continue
            normalized_answer = self._normalize_answer(question["type"], item.answer)
            if question["type"] == "subjective" and str(item.answer).strip():
                task = self._create_paper_subjective_marking_task(question_id, paper_id, student_user_id, str(item.answer).strip())
                pending_subjective_task_ids.append(str(task["id"]))
                wrong_question_ids.append(question_id)
                self._accumulate_question_type_accuracy(type_accuracy, question["type"], False)
                self._save_student_paper_attempt(
                    question_id,
                    student_user_id,
                    paper_id,
                    item.answer,
                    normalized_answer,
                    False,
                    item.elapsedSec,
                    item.marked,
                    is_pending_ai_marking=True,
                    ai_marking_task_id=str(task["id"]),
                )
                question_results.append(
                    self._build_report_question_result(
                        question=question,
                        answer=item.answer,
                        normalized_answer=normalized_answer,
                        is_correct=False,
                        is_pending_ai_marking=True,
                        marked=item.marked,
                        elapsed_sec=item.elapsedSec,
                        score=0,
                        total_score=question_score,
                        ai_marking_task_id=str(task["id"]),
                    )
                )
                continue
            is_correct = self._judge_answer(question, normalized_answer)
            if is_correct:
                score_obtained += question_score
            else:
                wrong_question_ids.append(question_id)
            self._accumulate_question_type_accuracy(type_accuracy, question["type"], is_correct)
            self._save_student_paper_attempt(
                question_id,
                student_user_id,
                paper_id,
                item.answer,
                normalized_answer,
                is_correct,
                item.elapsedSec,
                item.marked,
                is_pending_ai_marking=False,
                ai_marking_task_id="",
            )
            question_results.append(
                self._build_report_question_result(
                    question=question,
                    answer=item.answer,
                    normalized_answer=normalized_answer,
                    is_correct=is_correct,
                    is_pending_ai_marking=False,
                    marked=item.marked,
                    elapsed_sec=item.elapsedSec,
                    score=question_score if is_correct else 0,
                    total_score=question_score,
                    ai_marking_task_id="",
                )
            )
        return {
            "score": score_obtained,
            "totalScore": total_score,
            "typeAccuracy": self._build_type_accuracy_rows(type_accuracy),
            "wrongQuestionIds": wrong_question_ids,
            "pendingSubjectiveTaskIds": pending_subjective_task_ids,
            "questionResults": question_results,
        }

    def _accumulate_question_type_accuracy(
        self,
        type_accuracy: Dict[str, Dict[str, int]],
        question_type: str,
        is_correct: bool,
    ) -> None:
        stats = type_accuracy.setdefault(question_type, {"correct": 0, "total": 0})
        stats["total"] += 1
        if is_correct:
            stats["correct"] += 1

    def _build_report_question_result(
        self,
        question: Dict[str, str],
        answer: str,
        normalized_answer: str,
        is_correct: bool,
        is_pending_ai_marking: bool,
        marked: bool,
        elapsed_sec: int,
        score: int,
        total_score: int,
        ai_marking_task_id: str,
    ) -> Dict[str, object]:
        ext_json = self._load_json_object(question.get("extJson", "{}"))
        return {
            "questionId": str(question.get("id", "")),
            "type": str(question.get("type", "")),
            "stem": str(question.get("stem", "")),
            "optionsJson": str(question.get("optionsJson", "[]")),
            "correctAnswer": str(question.get("answer", "")),
            "analysis": str(ext_json.get("analysis", "")),
            "answer": str(answer),
            "normalizedAnswer": str(normalized_answer),
            "isCorrect": bool(is_correct),
            "isPendingAiMarking": bool(is_pending_ai_marking),
            "marked": bool(marked),
            "elapsedSec": int(elapsed_sec),
            "score": int(score),
            "totalScore": int(total_score),
            "aiMarkingTaskId": str(ai_marking_task_id),
        }

    def _save_student_paper_attempt(
        self,
        question_id: str,
        student_user_id: str,
        paper_id: str,
        answer: str,
        normalized_answer: str,
        is_correct: bool,
        elapsed_sec: int,
        marked: bool,
        is_pending_ai_marking: bool = False,
        ai_marking_task_id: str = "",
    ) -> None:
        record, record_ext = self._load_student_question_record_bundle(question_id, student_user_id, create_if_missing=True)
        attempts = record_ext.setdefault("simulationAttempts", {})
        attempts[paper_id] = {
            "lastAnswer": answer,
            "normalizedAnswer": normalized_answer,
            "isCorrect": is_correct,
            "answerDurationSec": elapsed_sec,
            "marked": marked,
            "isPendingAiMarking": is_pending_ai_marking,
            "aiMarkingTaskId": ai_marking_task_id,
            "submittedAt": self._now_iso(),
        }
        self._save_student_question_record_bundle(record, record_ext, student_user_id)

    def _build_type_accuracy_rows(self, type_accuracy: Dict[str, Dict[str, int]]) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for question_type, stats in type_accuracy.items():
            total = stats["total"] or 1
            rows.append(
                {
                    "type": question_type,
                    "accuracy": round(stats["correct"] / total, 4),
                    "correct": stats["correct"],
                    "total": stats["total"],
                }
            )
        return rows

    def _paper_subject_ids(self, paper_questions: List[Dict[str, str]]) -> List[str]:
        subject_ids = {
            self._question_subject_id(question)
            for question in paper_questions
            if self._question_subject_id(question)
        }
        return sorted(subject_ids)

    def _assert_daily_paper_subject_limit(self, student_user_id: str, subject_ids: List[str], today: str) -> None:
        if not subject_ids:
            return
        today_reports = [item for item in self._paper_reports() if str(item.get("studentUserId", "")) == student_user_id]
        for report in today_reports:
            submitted_day = str(report.get("submittedAt", ""))[:10]
            if submitted_day != today:
                continue
            existing_subject_ids = report.get("subjectIds")
            if isinstance(existing_subject_ids, list):
                report_subject_ids = [str(item) for item in existing_subject_ids if str(item).strip()]
            else:
                report_subject_id = str(report.get("subjectId", "")).strip()
                report_subject_ids = [report_subject_id] if report_subject_id else []
            if set(report_subject_ids).intersection(set(subject_ids)):
                raise validation_failed("每个科目每日最多完成 1 次全真模拟考试。")

    def _find_student_paper_report(self, student_user_id: str, paper_id: str, today: str) -> Optional[Dict[str, object]]:
        formal = self.repository.find_student_paper_report_by_paper_and_day(student_user_id, paper_id, today)
        return dict(formal) if formal else None

    def _find_student_paper_report_by_id(self, student_user_id: str, report_id: str) -> Optional[Dict[str, object]]:
        formal = self.repository.get_paper_report_payload(report_id)
        if formal and str(formal.get("studentUserId", "")) == student_user_id:
            return dict(formal)
        return None

    def _paper_submit_response_from_result(
        self,
        report_id: str,
        paper_id: str,
        subject_id: str,
        subject_ids: List[str],
        score: int,
        total_score: int,
        total_elapsed_sec: int,
        type_accuracy: List[Dict[str, object]],
        wrong_question_ids: List[str],
        pending_subjective_task_ids: List[str],
        submitted_at: str,
    ) -> Dict[str, object]:
        return {
            "reportId": report_id,
            "paperId": paper_id,
            "subjectId": subject_id,
            "subjectIds": subject_ids,
            "score": score,
            "totalScore": total_score,
            "totalElapsedSec": total_elapsed_sec,
            "typeAccuracy": type_accuracy,
            "wrongQuestionIds": wrong_question_ids,
            "pendingSubjectiveTaskIds": pending_subjective_task_ids,
            "pendingSubjectiveCount": len(pending_subjective_task_ids),
            "submittedAt": submitted_at,
        }

    def _paper_submit_response_from_report(self, report: Dict[str, object]) -> Dict[str, object]:
        detail = report.get("reportDetail", {})
        detail_type_accuracy = detail.get("typeAccuracy") if isinstance(detail, dict) else []
        type_accuracy = report.get("typeAccuracy")
        if not isinstance(type_accuracy, list):
            type_accuracy = detail_type_accuracy if isinstance(detail_type_accuracy, list) else []
        return self._paper_submit_response_from_result(
            self._paper_report_id(report),
            str(report.get("paperId", "")),
            str(report.get("subjectId", "")),
            list(report.get("subjectIds", [])) if isinstance(report.get("subjectIds"), list) else [],
            int(report.get("score", 0)),
            int(report.get("totalScore", 0)),
            int(report.get("totalElapsedSec", 0)),
            self._normalize_type_accuracy_rows(type_accuracy if isinstance(type_accuracy, list) else []),
            list(report.get("wrongQuestionIds", [])) if isinstance(report.get("wrongQuestionIds"), list) else [],
            list(report.get("pendingSubjectiveTaskIds", [])) if isinstance(report.get("pendingSubjectiveTaskIds"), list) else [],
            str(report.get("submittedAt", "")),
        )

    def _normalize_student_paper_report_item(self, report: Dict[str, object]) -> Dict[str, object]:
        subject_ids_raw = report.get("subjectIds")
        if isinstance(subject_ids_raw, list):
            subject_ids = [str(item) for item in subject_ids_raw if str(item).strip()]
        else:
            subject_id_single = str(report.get("subjectId", "")).strip()
            subject_ids = [subject_id_single] if subject_id_single else []
        pending_task_ids_raw = report.get("pendingSubjectiveTaskIds")
        pending_task_ids = [str(item) for item in pending_task_ids_raw] if isinstance(pending_task_ids_raw, list) else []
        wrong_ids_raw = report.get("wrongQuestionIds")
        wrong_ids = [str(item) for item in wrong_ids_raw] if isinstance(wrong_ids_raw, list) else []
        return {
            "reportId": self._paper_report_id(report),
            "paperId": str(report.get("paperId", "")),
            "subjectId": str(report.get("subjectId", "")),
            "subjectIds": subject_ids,
            "score": int(report.get("score", 0)),
            "totalScore": int(report.get("totalScore", 0)),
            "scoreRate": float(report.get("scoreRate", 0.0)),
            "totalElapsedSec": int(report.get("totalElapsedSec", 0)),
            "submittedAt": str(report.get("submittedAt", "")),
            "wrongQuestionIds": wrong_ids,
            "pendingSubjectiveTaskIds": pending_task_ids,
            "pendingSubjectiveCount": len(pending_task_ids),
        }

    def _enrich_student_paper_report_item(self, report: Dict[str, object], student_user_id: str) -> Dict[str, object]:
        normalized = self._normalize_student_paper_report_item(report)
        summary = self._paper_subjective_marking_summary(normalized["pendingSubjectiveTaskIds"], student_user_id)
        normalized["subjectiveMarking"] = summary
        normalized["pendingSubjectiveCount"] = int(summary["pendingCount"])
        return normalized

    def _paper_subjective_marking_summary(self, task_ids: List[str], student_user_id: str) -> Dict[str, object]:
        actor = Actor(role=ROLE_STUDENT, user_id=student_user_id)
        tracked = 0
        queued = 0
        running = 0
        completed = 0
        failed = 0
        cancelled = 0
        scores: List[float] = []
        latest_completed_at = ""
        for task_id in task_ids:
            task = self.repository.get_task(str(task_id))
            if not task:
                continue
            if str(task.get("userId", "")) != student_user_id:
                continue
            task = self._refresh_task(task, actor)
            tracked += 1
            status = str(task.get("status", ""))
            if status == "QUEUED":
                queued += 1
            elif status == "RUNNING":
                running += 1
            elif status == "COMPLETED":
                completed += 1
                ext_json = self._load_json_object(str(task.get("extJson", "{}")))
                result = ext_json.get("result", {})
                if isinstance(result, dict):
                    try:
                        scores.append(float(result.get("totalScore", 0.0)))
                    except Exception:
                        pass
                queue = ext_json.get("queue", {})
                if isinstance(queue, dict):
                    latest_completed_at = max(latest_completed_at, str(queue.get("completedAt", "")))
            elif status == "FAILED":
                failed += 1
            elif status == "CANCELLED":
                cancelled += 1
        pending_count = queued + running
        average_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        return {
            "total": tracked,
            "pendingCount": pending_count,
            "queuedCount": queued,
            "runningCount": running,
            "completedCount": completed,
            "failedCount": failed,
            "cancelledCount": cancelled,
            "averageScore": average_score,
            "latestCompletedAt": latest_completed_at,
        }

    def _paper_report_id(self, report: Dict[str, object]) -> str:
        report_id = str(report.get("reportId", "")).strip()
        if report_id:
            return report_id
        return f"legacy::{str(report.get('paperId', '')).strip()}::{str(report.get('submittedAt', '')).strip()}"

    def _normalize_type_accuracy_rows(self, rows: List[object]) -> List[Dict[str, object]]:
        normalized: List[Dict[str, object]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "type": str(item.get("type", "")),
                    "accuracy": float(item.get("accuracy", 0.0)),
                    "correct": int(item.get("correct", 0)),
                    "total": int(item.get("total", 0)),
                }
            )
        return normalized

    def _normalize_question_results(self, rows: List[object]) -> List[Dict[str, object]]:
        normalized: List[Dict[str, object]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "questionId": str(item.get("questionId", "")),
                    "type": str(item.get("type", "")),
                    "stem": str(item.get("stem", "")),
                    "optionsJson": str(item.get("optionsJson", "[]")),
                    "correctAnswer": str(item.get("correctAnswer", "")),
                    "analysis": str(item.get("analysis", "")),
                    "answer": str(item.get("answer", "")),
                    "normalizedAnswer": str(item.get("normalizedAnswer", "")),
                    "isCorrect": bool(item.get("isCorrect", False)),
                    "isPendingAiMarking": bool(item.get("isPendingAiMarking", False)),
                    "marked": bool(item.get("marked", False)),
                    "elapsedSec": int(item.get("elapsedSec", 0)),
                    "score": int(item.get("score", 0)),
                    "totalScore": int(item.get("totalScore", 0)),
                    "aiMarkingTaskId": str(item.get("aiMarkingTaskId", "")),
                }
            )
        return normalized

    def _build_report_detail_summary(self, question_results: List[Dict[str, object]], wrong_question_ids: List[str]) -> Dict[str, object]:
        total_count = len(question_results)
        pending_count = len([item for item in question_results if item.get("isPendingAiMarking")])
        marked_count = len([item for item in question_results if item.get("marked")])
        wrong_set = {item for item in wrong_question_ids if item}
        wrong_count = len(wrong_set) if wrong_set else len([item for item in question_results if not item.get("isCorrect")])
        correct_count = max(0, total_count - wrong_count)
        return {
            "questionCount": total_count,
            "correctCount": correct_count,
            "wrongCount": wrong_count,
            "pendingSubjectiveCount": pending_count,
            "markedCount": marked_count,
        }

    def _refresh_report_question_results(self, question_results: List[Dict[str, object]], student_user_id: str) -> List[Dict[str, object]]:
        actor = Actor(role=ROLE_STUDENT, user_id=student_user_id)
        refreshed: List[Dict[str, object]] = []
        for item in question_results:
            row = dict(item)
            task_id = str(row.get("aiMarkingTaskId", "")).strip()
            if task_id:
                task = self.repository.get_task(task_id)
                if task and str(task.get("userId", "")) == student_user_id:
                    task = self._refresh_task(task, actor)
                    status = str(task.get("status", ""))
                    row["isPendingAiMarking"] = status in {"QUEUED", "RUNNING"}
                    if status == "COMPLETED":
                        ext_json = self._load_json_object(str(task.get("extJson", "{}")))
                        result = ext_json.get("result", {})
                        if isinstance(result, dict):
                            row["score"] = self._paper_ai_marking_awarded_score(
                                float(result.get("totalScore", 0.0)),
                                int(row.get("totalScore", 0)),
                            )
            refreshed.append(row)
        return refreshed

    def _paper_ai_marking_awarded_score(self, ai_total_score: float, question_total_score: int) -> int:
        if question_total_score <= 0:
            return 0
        bounded = max(0.0, min(100.0, float(ai_total_score)))
        return int(round((bounded / 100.0) * float(question_total_score)))

    def _build_synced_report_type_accuracy(self, question_results: List[Dict[str, object]]) -> List[Dict[str, object]]:
        stats: Dict[str, Dict[str, int]] = {}
        for row in question_results:
            question_type = str(row.get("type", ""))
            if not question_type:
                continue
            bucket = stats.setdefault(question_type, {"correct": 0, "total": 0})
            bucket["total"] += 1
            if int(row.get("score", 0)) >= int(row.get("totalScore", 0)):
                bucket["correct"] += 1
        return self._build_type_accuracy_rows(stats)

    def _derive_wrong_question_ids(self, question_results: List[Dict[str, object]]) -> List[str]:
        return [
            str(row.get("questionId", ""))
            for row in question_results
            if str(row.get("questionId", "")).strip()
            and int(row.get("score", 0)) < int(row.get("totalScore", 0))
        ]

    def _build_synced_report_detail(self, question_results: List[Dict[str, object]]) -> Dict[str, object]:
        return {
            "typeAccuracy": self._build_synced_report_type_accuracy(question_results),
            "questionResults": question_results,
        }

    def _enrich_question_for_student(
        self,
        question: Dict[str, str],
        student_user_id: str,
        paper_id: str = "",
        include_chapter_progress: bool = True,
        student_record: Optional[Dict[str, object]] = None,
    ) -> Dict[str, str]:
        enriched = dict(question)
        ext_json = self._load_json_object(enriched["extJson"])
        record = student_record or self.repository.get_student_question_bank(question["id"], student_user_id)
        record_ext = self._load_json_object(record["extJson"] if record else "{}")
        student_state = {
            "studentUserId": student_user_id,
            "chapterPractice": record_ext.get("chapterPractice", {}),
            "simulationAttempt": record_ext.get("simulationAttempts", {}).get(paper_id, {}) if paper_id else {},
            "chapterProgress": self._build_chapter_progress(
                self._question_subject_id(question),
                self._question_chapter(question),
                student_user_id,
            ) if include_chapter_progress else {},
            "wrongBook": self._build_formal_wrong_book_state(record, record_ext),
            "personalBank": self._build_formal_personal_bank_state(record, record_ext),
            "aiMarking": record_ext.get("aiMarking", {}),
            "aiTutor": record_ext.get("aiTutor", {}),
        }
        ext_json["studentState"] = student_state
        enriched["extJson"] = self._dump_json(ext_json)
        return enriched

    def _build_formal_wrong_book_state(
        self,
        record: Optional[Dict[str, object]],
        record_ext: Dict[str, object],
    ) -> Dict[str, object]:
        wrong_book = record_ext.get("wrongBook", {})
        if not isinstance(wrong_book, dict):
            wrong_book = {}
        normalized = dict(wrong_book)
        if not record:
            return normalized
        normalized["isCollected"] = bool(record.get("wrongBookFlag", 0))
        normalized["isArchived"] = bool(record.get("wrongBookArchivedFlag", 0))
        normalized["collectedAt"] = str(record.get("wrongBookCollectedAt", "")).strip()
        normalized["lastWrongAt"] = str(record.get("wrongBookLastWrongAt", "")).strip()
        normalized["reviewedAt"] = str(record.get("wrongBookReviewedAt", "")).strip()
        normalized["archivedAt"] = str(record.get("wrongBookArchivedAt", "")).strip()
        normalized["restoredAt"] = str(record.get("wrongBookRestoredAt", "")).strip()
        normalized["reviewCount"] = self._safe_int(record.get("wrongBookReviewCount", 0), 0)
        normalized["postWrongAttemptCount"] = self._safe_int(record.get("wrongBookPostWrongAttemptCount", 0), 0)
        normalized["postWrongCorrectCount"] = self._safe_int(record.get("wrongBookPostWrongCorrectCount", 0), 0)
        normalized["lastReasonCode"] = str(record.get("wrongBookLastReasonCode", "")).strip()
        normalized["lastReasonLabel"] = str(record.get("wrongBookLastReasonLabel", "")).strip()
        normalized["wrongCount"] = self._safe_int(record.get("wrongCount", normalized.get("wrongCount", 0)), 0)
        return normalized

    def _build_formal_personal_bank_state(
        self,
        record: Optional[Dict[str, object]],
        record_ext: Dict[str, object],
    ) -> Dict[str, object]:
        personal_bank = record_ext.get("personalBank", {})
        if not isinstance(personal_bank, dict):
            personal_bank = {}
        normalized = dict(personal_bank)
        if not record:
            return normalized
        normalized["isCollected"] = bool(record.get("personalBankFlag", 0))
        normalized["collectedAt"] = str(record.get("personalBankCollectedAt", "")).strip()
        normalized["sourceType"] = str(record.get("personalBankSourceType", "")).strip()
        normalized["sourceLabel"] = str(record.get("personalBankSourceLabel", "")).strip()
        return normalized

    def _build_chapter_progress(self, subject_id: str, chapter: str, student_user_id: str) -> Dict[str, object]:
        chapter_questions = self.repository.list_visible_published_questions(
            {"subjectId": subject_id, "chapter": chapter, "type": "", "difficulty": ""},
            ROLE_SUPER_ADMIN,
            student_user_id,
        )
        chapter_questions = [question for question in chapter_questions if self._is_question_visible_to_student(question, student_user_id)]
        answered = 0
        correct = 0
        for question in chapter_questions:
            record = self.repository.get_student_question_bank(question["id"], student_user_id)
            record_ext = self._load_json_object(record["extJson"] if record else "{}")
            chapter_practice = record_ext.get("chapterPractice", {})
            if chapter_practice:
                answered += 1
                if chapter_practice.get("isCorrect"):
                    correct += 1
        accuracy = round(correct / answered, 4) if answered else 0.0
        subject_questions = self.repository.list_visible_published_questions(
            {"subjectId": subject_id, "chapter": "", "type": "", "difficulty": ""},
            ROLE_SUPER_ADMIN,
            student_user_id,
        )
        subject_questions = [question for question in subject_questions if self._is_question_visible_to_student(question, student_user_id)]
        chapter_order = self._chapter_order_for_subject(subject_id, subject_questions)
        current_index = chapter_order.index(chapter) if chapter in chapter_order else 0
        if current_index == 0:
            unlocked = True
        else:
            previous_chapter = chapter_order[current_index - 1]
            previous_progress = self._build_chapter_progress(subject_id, previous_chapter, student_user_id) if previous_chapter != chapter else {}
            unlocked = bool(previous_progress.get("accuracy", 0) >= 0.8)
        return {
            "answered": answered,
            "total": len(chapter_questions),
            "accuracy": accuracy,
            "isUnlocked": unlocked,
        }

    def _chapter_order_for_subject(self, subject_id: str, subject_questions: List[Dict[str, str]]) -> List[str]:
        chapters = {self._question_chapter(item) for item in subject_questions if self._question_chapter(item)}
        if not chapters:
            return []
        chapter_code_rows: List[Tuple[str, str]] = []
        for question in subject_questions:
            chapter_name = self._question_chapter(question)
            ext_json = self._question_ext_json(question)
            chapter_code = str(ext_json.get("chapterCode", "")).strip()
            if chapter_name and chapter_code:
                chapter_code_rows.append((chapter_code, chapter_name))
        chapter_code_rows.sort(key=lambda item: (item[0], item[1]))
        ordered: List[str] = []
        seen_ordered: set[str] = set()
        for _, chapter_name in chapter_code_rows:
            if chapter_name in seen_ordered:
                continue
            ordered.append(chapter_name)
            seen_ordered.add(chapter_name)

        fallback_rows: List[Tuple[int, int, str, str]] = []
        for item in self.repository.list_knowledge(""):
            ext_json = self._load_json_object(str(item["extJson"]))
            if str(ext_json.get("subjectId", "")) != subject_id:
                continue
            level = int(ext_json.get("level", 0) or 0)
            if level < 2:
                continue
            chapter_name = str(item["name"])
            if chapter_name in chapters and chapter_name not in seen_ordered:
                fallback_rows.append((int(item["sort"]), level, str(item["createTime"]), chapter_name))
        fallback_rows.sort(key=lambda value: (value[0], value[1], value[2], value[3]))
        for _, _, _, chapter_name in fallback_rows:
            if chapter_name in seen_ordered:
                continue
            ordered.append(chapter_name)
            seen_ordered.add(chapter_name)

        leftovers = sorted(chapters.difference(seen_ordered))
        return ordered + leftovers

    def _default_student_profile(self) -> Dict[str, object]:
        return {
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "vocationalMajor": "",
            "prepStage": "",
            "checkInDates": [],
            "points": 0,
            "title": "备考新星",
            "unlockedTitles": ["备考新星"],
            "pointsLedger": [],
            "dailyProgress": {},
            "aiQuota": {"dailyLimit": 20, "usedCount": 0, "quotaDate": ""},
            "examSession": {"answeredCount": 0, "elapsedSec": 0, "updateTime": ""},
        }

    def _legacy_student_profile_snapshot(self, profile: Dict[str, object]) -> Dict[str, object]:
        return {
            "examCategoryCode": str(profile.get("examCategoryCode", "")).strip() or "SCIENCE_ENGINEERING",
            "jointExamGroupCode": str(profile.get("jointExamGroupCode", "")).strip() or "SCIENCE_ENGINEERING_3",
        }

    def _student_profile_snapshot_is_thin(self, payload: object) -> bool:
        if not isinstance(payload, dict):
            return False
        return dict(payload) == self._legacy_student_profile_snapshot(payload)

    def _persist_legacy_student_profile_snapshot(
        self,
        record: Dict[str, str],
        record_ext: Dict[str, object],
        profile: Dict[str, object],
        student_user_id: str,
    ) -> Tuple[Dict[str, str], Dict[str, object]]:
        legacy_snapshot = self._legacy_student_profile_snapshot(profile)
        if self._student_profile_snapshot_is_thin(record_ext.get("studentProfile", {})):
            return record, record_ext
        updated_record_ext = dict(record_ext)
        updated_record_ext["studentProfile"] = legacy_snapshot
        return self._save_student_profile_record_ext(record, updated_record_ext, student_user_id)

    def _save_student_profile_snapshot(
        self,
        record: Dict[str, str],
        record_ext: Dict[str, object],
        profile: Dict[str, object],
        student_user_id: str,
    ) -> Tuple[Dict[str, str], Dict[str, object]]:
        updated_record_ext = dict(record_ext)
        updated_record_ext["studentProfile"] = self._legacy_student_profile_snapshot(profile)
        return self._save_student_profile_record_ext(record, updated_record_ext, student_user_id)

    def _save_student_profile_record_ext(
        self,
        record: Dict[str, str],
        record_ext: Dict[str, object],
        student_user_id: str,
    ) -> Tuple[Dict[str, str], Dict[str, object]]:
        updated_record = self.repository.upsert_student_question_bank(
            {
                "id": record["id"],
                "questionId": record["questionId"],
                "studentUserId": student_user_id,
                "status": record.get("status", "ACTIVE"),
                "extJson": self._dump_json(record_ext),
            }
        )
        normalized_record = {
            "id": updated_record.get("id", record["id"]),
            "questionId": updated_record.get("questionId", record["questionId"]),
            "studentUserId": student_user_id,
            "status": updated_record.get("status", record.get("status", "ACTIVE")),
            "extJson": updated_record.get("extJson", self._dump_json(record_ext)),
        }
        return normalized_record, record_ext

    def _ensure_student_profile_formal_state(
        self,
        student_user_id: str,
        seed_profile: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        formal_profile_state = self.repository.get_student_profile_state(student_user_id)
        if formal_profile_state:
            return formal_profile_state
        return self.repository.upsert_student_profile_state(
            self._formal_profile_state_seed(student_user_id, seed_profile or self._default_student_profile())
        )

    def _sync_student_profile_cold_snapshot(
        self,
        student_user_id: str,
        exam_category_code: str,
        joint_exam_group_code: str,
    ) -> None:
        now_iso = self._now_iso()
        self.repository.set_student_profile_selection(
            student_user_id,
            exam_category_code,
            joint_exam_group_code,
            now_iso,
        )
        self._sync_student_directory_scope_projection(
            student_user_id,
            exam_category_code,
            joint_exam_group_code,
        )
        record = self._ensure_student_profile_record(student_user_id)
        record_ext = self._load_json_object(record["extJson"])
        desired_snapshot = self._legacy_student_profile_snapshot(
            {
                "examCategoryCode": exam_category_code,
                "jointExamGroupCode": joint_exam_group_code,
            }
        )
        current_snapshot = record_ext.get("studentProfile", {})
        if self._student_profile_snapshot_is_thin(current_snapshot) and dict(current_snapshot) == desired_snapshot:
            return
        updated_record_ext = dict(record_ext)
        updated_record_ext["studentProfile"] = desired_snapshot
        self._save_student_profile_record_ext(record, updated_record_ext, student_user_id)

    def _ensure_student_profile_record(self, student_user_id: str) -> Dict[str, str]:
        existing_record = self.repository.get_student_profile_record_row(student_user_id)
        if existing_record:
            return {
                "id": str(existing_record.get("id", "")),
                "questionId": str(existing_record.get("questionId", "")),
                "studentUserId": student_user_id,
                "status": str(existing_record.get("status", "ACTIVE")),
                "extJson": str(existing_record.get("extJson", "{}")),
            }
        anchor_question = self.repository.get_first_published_question()
        if not anchor_question:
            raise not_found("当前没有可用题目，无法初始化学生档案。")
        payload = {
            "id": f"student-bank-{uuid.uuid4().hex[:8]}",
            "questionId": anchor_question["id"],
            "studentUserId": student_user_id,
            "status": "ACTIVE",
            "extJson": self._dump_json({"studentProfile": self._legacy_student_profile_snapshot(self._default_student_profile())}),
        }
        self.repository.upsert_student_question_bank(payload)
        return payload

    def _load_student_profile_bundle(
        self,
        student_user_id: str,
    ) -> Tuple[Dict[str, str], Dict[str, object], Dict[str, object]]:
        record = self._ensure_student_profile_record(student_user_id)
        record_ext = self._load_json_object(record["extJson"])
        profile = self._default_student_profile()
        profile.update(record_ext.get("studentProfile", {}))
        profile.update(self._student_profile_identity_seed(student_user_id))
        formal_profile_state = self._ensure_student_profile_formal_state(student_user_id, profile)
        formal_daily_progress = self.repository.list_student_daily_progress(student_user_id)
        formal_points_ledger = self.repository.list_student_points_ledger(student_user_id)
        self._hydrate_profile_hot_state(
            profile,
            student_user_id,
            formal_profile_state=formal_profile_state,
            formal_daily_progress=formal_daily_progress,
            formal_points_ledger=formal_points_ledger,
        )
        record, record_ext = self._persist_legacy_student_profile_snapshot(record, record_ext, profile, student_user_id)
        return record, record_ext, profile

    def _refresh_profile_hot_state_from_formal(self, profile: Dict[str, object], student_user_id: str) -> Dict[str, object]:
        return self._hydrate_profile_hot_state(profile, student_user_id)

    def _formal_profile_state_seed(self, student_user_id: str, profile: Dict[str, object]) -> Dict[str, object]:
        now_iso = self._now_iso()
        return {
            "studentUserId": student_user_id,
            "examCategoryCode": str(profile.get("examCategoryCode", "")).strip() or "SCIENCE_ENGINEERING",
            "jointExamGroupCode": str(profile.get("jointExamGroupCode", "")).strip() or "SCIENCE_ENGINEERING_3",
            "vocationalMajor": str(profile.get("vocationalMajor", "")).strip(),
            "prepStage": str(profile.get("prepStage", "")).strip(),
            "points": int(profile.get("points", 0) or 0),
            "title": str(profile.get("title", "")).strip() or "备考新星",
            "unlockedTitles": list(profile.get("unlockedTitles", ["备考新星"])),
            "checkInDates": list(profile.get("checkInDates", [])),
            "aiQuota": dict(profile.get("aiQuota", {"dailyLimit": 20, "usedCount": 0, "quotaDate": ""})),
            "examSession": dict(profile.get("examSession", {"answeredCount": 0, "elapsedSec": 0, "updateTime": ""})),
            "createTime": now_iso,
            "updateTime": now_iso,
        }

    def _apply_formal_profile_state(self, profile: Dict[str, object], formal_profile_state: Optional[Dict[str, object]]) -> None:
        state = formal_profile_state or {}
        profile["examCategoryCode"] = str(state.get("examCategoryCode", "")).strip() or "SCIENCE_ENGINEERING"
        profile["jointExamGroupCode"] = str(state.get("jointExamGroupCode", "")).strip() or "SCIENCE_ENGINEERING_3"
        profile["vocationalMajor"] = str(state.get("vocationalMajor", "")).strip()
        profile["prepStage"] = str(state.get("prepStage", "")).strip()
        profile["checkInDates"] = list(state.get("checkInDates", []))
        profile["points"] = int(state.get("points", 0) or 0)
        profile["title"] = str(state.get("title", "")).strip() or "备考新星"
        profile["unlockedTitles"] = list(state.get("unlockedTitles", []))
        profile["aiQuota"] = dict(state.get("aiQuota", {}))
        profile["examSession"] = dict(state.get("examSession", {}))

    def _student_profile_identity_seed(self, student_user_id: str) -> Dict[str, str]:
        managed_user = self._get_managed_user(student_user_id) if hasattr(self, "_get_managed_user") else {}
        user = self.repository.get_user_by_id(student_user_id) or {}
        ext_json = self._load_json_object(str(user.get("extJson", "{}")))
        return {
            "vocationalMajor": str((managed_user or {}).get("vocationalMajor", "")).strip() or str(ext_json.get("vocationalMajor", "")).strip(),
            "prepStage": str((managed_user or {}).get("prepStage", "")).strip() or str(ext_json.get("prepStage", "")).strip(),
        }

    def _apply_formal_daily_progress(self, profile: Dict[str, object], formal_daily_progress: List[Dict[str, object]]) -> None:
        profile["dailyProgress"] = {
            str(item.get("progressDate", "")).strip(): {
                "checkInCount": int(item.get("checkInCount", 0) or 0),
                "practiceAnswers": int(item.get("practiceAnswers", 0) or 0),
                "papersCompleted": int(item.get("papersCompleted", 0) or 0),
                "wrongBookReviewed": int(item.get("wrongBookReviewed", 0) or 0),
                "rewardedKeys": list(item.get("rewardedKeys", [])) if isinstance(item.get("rewardedKeys", []), list) else [],
            }
            for item in formal_daily_progress
            if str(item.get("progressDate", "")).strip()
        }

    def _apply_formal_points_ledger(self, profile: Dict[str, object], formal_points_ledger: List[Dict[str, object]]) -> None:
        profile["pointsLedger"] = formal_points_ledger[-50:] if formal_points_ledger else []

    def _hydrate_profile_hot_state(
        self,
        profile: Dict[str, object],
        student_user_id: str,
        *,
        formal_profile_state: Optional[Dict[str, object]] = None,
        formal_daily_progress: Optional[List[Dict[str, object]]] = None,
        formal_points_ledger: Optional[List[Dict[str, object]]] = None,
    ) -> Dict[str, object]:
        if formal_profile_state is None:
            formal_profile_state = self.repository.get_student_profile_state(student_user_id) or {}
        if formal_daily_progress is None:
            formal_daily_progress = self.repository.list_student_daily_progress(student_user_id)
        if formal_points_ledger is None:
            formal_points_ledger = self.repository.list_student_points_ledger(student_user_id)
        self._apply_formal_profile_state(profile, formal_profile_state)
        self._apply_formal_daily_progress(profile, formal_daily_progress)
        self._apply_formal_points_ledger(profile, formal_points_ledger)
        return profile

    def _ensure_student_question_record(self, question_id: str, student_user_id: str) -> Dict[str, str]:
        record = self.repository.get_student_question_bank(question_id, student_user_id)
        if record:
            return record
        payload = {
            "id": f"student-bank-{uuid.uuid4().hex[:8]}",
            "questionId": question_id,
            "studentUserId": student_user_id,
            "status": "ACTIVE",
            "extJson": self._dump_json({}),
        }
        self.repository.upsert_student_question_bank(payload)
        return payload

    def _load_student_question_record_bundle(
        self,
        question_id: str,
        student_user_id: str,
        create_if_missing: bool = False,
    ) -> Tuple[Dict[str, str], Dict[str, object]]:
        record = (
            self._ensure_student_question_record(question_id, student_user_id)
            if create_if_missing
            else self.repository.get_student_question_bank(question_id, student_user_id)
        )
        if not record:
            raise not_found("学生题目记录不存在。")
        return record, self._load_json_object(record["extJson"])

    def _save_student_question_record_bundle(
        self,
        record: Dict[str, str],
        record_ext: Dict[str, object],
        student_user_id: str,
    ) -> None:
        self.repository.upsert_student_question_bank(
            {
                "id": record["id"],
                "questionId": record["questionId"],
                "studentUserId": student_user_id,
                "status": "ACTIVE",
                "extJson": self._dump_json(record_ext),
            }
        )

    def _build_subject_progress(self, subject_code: str, student_user_id: str) -> Dict[str, object]:
        questions = self.repository.list_visible_published_questions(
            {"subjectId": "", "chapter": "", "type": "", "difficulty": ""},
            ROLE_SUPER_ADMIN,
            student_user_id,
        )
        questions = self._filter_questions_for_student_scope(questions, student_user_id, {})
        subject_questions = [item for item in questions if self._question_matches_subject_code(item, subject_code)]
        answered = 0
        correct = 0
        for question in subject_questions:
            record = self.repository.get_student_question_bank(question["id"], student_user_id)
            record_ext = self._load_json_object(record["extJson"] if record else "{}")
            chapter_practice = record_ext.get("chapterPractice", {})
            if chapter_practice:
                answered += 1
                if chapter_practice.get("isCorrect"):
                    correct += 1
        accuracy = round(correct / answered, 4) if answered else 0.0
        return {"answered": answered, "total": len(subject_questions), "accuracy": accuracy}

    def _build_student_core_subjects(
        self,
        joint_exam_group: Optional[Dict[str, object]],
        student_user_id: str,
    ) -> List[Dict[str, object]]:
        if not joint_exam_group:
            return []
        core_subjects: List[Dict[str, object]] = []
        for subject in build_content_baseline()["publicSubjects"] + joint_exam_group["professionalSubjects"]:
            core_subjects.append(
                {
                    "subjectId": subject_id_from_subject_code(subject["subjectCode"]),
                    "subjectCode": subject["subjectCode"],
                    "subjectName": subject["subjectName"],
                    "subjectType": subject["subjectType"],
                    "progress": self._build_subject_progress(subject["subjectCode"], student_user_id),
                }
            )
        return core_subjects

    def _build_student_daily_tasks(self, today_progress: Dict[str, object]) -> List[Dict[str, object]]:
        reward_keys = today_progress.get("rewardedKeys", [])
        tasks = [
            {
                "taskKey": "practiceReward",
                "taskName": "章节刷题10道",
                "target": 10,
                "completed": int(today_progress.get("practiceAnswers", 0)),
                "rewarded": "practiceReward" in reward_keys,
                "actionLabel": "去做章节闯关",
                "actionPath": "/student/practice/chapter",
                "actionQuery": {
                    "module": "chapter",
                    "practiceSource": "TASK",
                    "practiceSourceLabel": "章节刷题10道",
                },
            },
            {
                "taskKey": "paperReward",
                "taskName": "完成1次模拟考试",
                "target": 1,
                "completed": int(today_progress.get("papersCompleted", 0)),
                "rewarded": "paperReward" in reward_keys,
                "actionLabel": "去做模拟考试",
                "actionPath": "/student/practice/mock",
                "actionQuery": {
                    "module": "mock",
                    "practiceSource": "TASK",
                    "practiceSourceLabel": "完成1次模拟考试",
                },
            },
            {
                "taskKey": "wrongBookReward",
                "taskName": "复习5道错题",
                "target": 5,
                "completed": int(today_progress.get("wrongBookReviewed", 0)),
                "rewarded": "wrongBookReward" in reward_keys,
                "actionLabel": "去复习错题",
                "actionPath": "/student/question-bank/repair",
                "actionQuery": {},
            },
        ]
        for task in tasks:
            task["isDone"] = int(task.get("completed", 0)) >= int(task.get("target", 0))
        return tasks

    def _count_personal_bank_questions(self, student_user_id: str) -> int:
        count = 0
        for question in self.repository.list_student_records_by_user(student_user_id):
            ext_json = self._load_json_object(question["extJson"])
            student_record = ext_json.get("studentRecord", {})
            record_ext = self._load_json_object(student_record.get("extJson", "{}"))
            if record_ext.get("personalBank", {}).get("isCollected"):
                count += 1
        return count

    def _today_progress(self, profile: Dict[str, object]) -> Dict[str, object]:
        today = datetime.now(timezone.utc).date().isoformat()
        daily_progress = dict(profile.get("dailyProgress", {}))
        return dict(daily_progress.get(today, {"rewardedKeys": []}))

    def _grant_points(
        self,
        profile: Dict[str, object],
        student_user_id: str,
        points: int,
        reason: str,
        event_key: str,
        create_time: str,
    ) -> bool:
        if not self.repository.insert_student_points_ledger_if_absent(
            student_user_id,
            event_key,
            reason,
            int(points),
            create_time,
            {
                "studentUserId": student_user_id,
                "eventKey": event_key,
                "reason": reason,
                "points": int(points),
                "createTime": create_time,
            },
        ):
            return False
        current_points = int(profile.get("points", 0) or 0) + int(points)
        titles = self._resolve_unlocked_titles(current_points)
        self.repository.increment_student_profile_points(
            student_user_id,
            int(points),
            titles[-1],
            titles,
            create_time,
        )
        self._refresh_profile_hot_state_from_formal(profile, student_user_id)
        return True

    def _append_student_daily_metric(self, student_user_id: str, key: str, delta: int) -> None:
        today = datetime.now(timezone.utc).date().isoformat()
        self.repository.increment_student_daily_progress_metric(
            student_user_id,
            today,
            key,
            delta,
            self._now_iso(),
        )

    def _grant_daily_task_points(self, student_user_id: str) -> None:
        settings = self._load_system_state()["systemSettings"]
        _, _, profile = self._load_student_profile_bundle(student_user_id)
        today_row = self._today_progress(profile)
        rewarded_keys = set(today_row.get("rewardedKeys", []))
        today = datetime.now(timezone.utc).date().isoformat()
        now_iso = self._now_iso()
        hot_state_changed = False
        if int(today_row.get("practiceAnswers", 0)) >= int(settings["practiceRewardThreshold"]) and "practiceReward" not in rewarded_keys:
            practice_reward_granted = self._grant_points(
                profile,
                student_user_id,
                int(settings["practiceRewardPoints"]),
                "完成章节刷题10道",
                f"practiceReward:{today}",
                now_iso,
            )
            self.repository.add_student_daily_progress_rewarded_key(student_user_id, today, "practiceReward", now_iso)
            rewarded_keys.add("practiceReward")
            hot_state_changed = True
            if practice_reward_granted:
                self._push_message([student_user_id], "POINTS_NOTICE", "任务积分到账", "你已完成章节刷题任务，系统已发放积分奖励。")
        if int(today_row.get("papersCompleted", 0)) >= 1 and "paperReward" not in rewarded_keys:
            paper_reward_granted = self._grant_points(
                profile,
                student_user_id,
                int(settings["paperRewardPoints"]),
                "完成1次模拟考试",
                f"paperReward:{today}",
                now_iso,
            )
            self.repository.add_student_daily_progress_rewarded_key(student_user_id, today, "paperReward", now_iso)
            rewarded_keys.add("paperReward")
            hot_state_changed = True
            if paper_reward_granted:
                self._push_message([student_user_id], "POINTS_NOTICE", "任务积分到账", "你已完成模拟考试任务，系统已发放积分奖励。")
        if int(today_row.get("wrongBookReviewed", 0)) >= int(settings["wrongBookRewardThreshold"]) and "wrongBookReward" not in rewarded_keys:
            wrong_book_reward_granted = self._grant_points(
                profile,
                student_user_id,
                int(settings["wrongBookRewardPoints"]),
                "复习5道错题",
                f"wrongBookReward:{today}",
                now_iso,
            )
            self.repository.add_student_daily_progress_rewarded_key(student_user_id, today, "wrongBookReward", now_iso)
            rewarded_keys.add("wrongBookReward")
            hot_state_changed = True
            if wrong_book_reward_granted:
                self._push_message([student_user_id], "POINTS_NOTICE", "任务积分到账", "你已完成错题复习任务，系统已发放积分奖励。")
        if hot_state_changed:
            self._refresh_profile_hot_state_from_formal(profile, student_user_id)

    def _resolve_unlocked_titles(self, points: int) -> List[str]:
        titles = ["备考新星"]
        if points >= 50:
            titles.append("连刷达人")
        if points >= 100:
            titles.append("打卡先锋")
        if points >= 200:
            titles.append("备考之星")
        return titles

    def _question_matches_subject_code(self, question: Dict[str, str], subject_code: str) -> bool:
        ext_json = self._load_json_object(question["extJson"])
        return str(ext_json.get("subjectCode", "")) == subject_code

    def _has_content_filter(self, filters: Dict[str, str]) -> bool:
        return any(self._content_filter_values(filters).values())

    def _content_filter_values(self, filters: Dict[str, str]) -> Dict[str, str]:
        return self._pick_filters(filters, ("examCategoryCode", "jointExamGroupCode", "subjectCode"))

    def _matches_question_content_tags(self, question: Dict[str, str], filters: Dict[str, str]) -> bool:
        ext_json = self._load_json_object(question["extJson"])
        content_filters = self._content_filter_values(filters)
        exam_category_code = content_filters["examCategoryCode"]
        if exam_category_code:
            if ext_json.get("subjectType") == "PUBLIC":
                allowed_group_codes = {
                    item["jointExamGroupCode"]
                    for item in list_joint_exam_groups(exam_category_code)
                }
                if not allowed_group_codes.intersection(set(ext_json.get("applicableGroups", []))):
                    return False
            elif ext_json.get("examCategoryCode") != exam_category_code:
                return False
        joint_exam_group_code = content_filters["jointExamGroupCode"]
        if joint_exam_group_code and joint_exam_group_code not in ext_json.get("applicableGroups", []):
            return False
        subject_code = content_filters["subjectCode"]
        if subject_code and ext_json.get("subjectCode") != subject_code:
            return False
        return True

    def _filter_questions_by_content_tags(self, questions: List[Dict[str, str]], filters: Dict[str, str]) -> List[Dict[str, str]]:
        return [question for question in questions if self._matches_question_content_tags(question, filters)]

    def _get_student_profile(self, student_user_id: str) -> Dict[str, object]:
        _, _, profile = self._load_student_profile_bundle(student_user_id)
        self._assert_student_profile_complete(profile)
        return profile

    def _is_question_visible_to_student(self, question: Dict[str, str], student_user_id: str) -> bool:
        profile = self._get_student_profile(student_user_id)
        return self._is_question_visible_by_profile(question, profile)

    def _is_question_visible_by_profile(self, question: Dict[str, str], profile: Dict[str, object]) -> bool:
        ext_json = self._load_json_object(question["extJson"])
        applicable_groups = ext_json.get("applicableGroups", [])
        subject_type = ext_json.get("subjectType", "")
        if subject_type == "PUBLIC":
            return True
        return profile.get("jointExamGroupCode", "") in applicable_groups

    def _assert_student_scope_filters(self, profile: Dict[str, object], filters: Dict[str, str]) -> None:
        profile_exam_category_code = str(profile.get("examCategoryCode", "")).strip()
        profile_joint_exam_group_code = str(profile.get("jointExamGroupCode", "")).strip()
        requested_exam_category_code = str(filters.get("examCategoryCode", "")).strip()
        requested_joint_exam_group_code = str(filters.get("jointExamGroupCode", "")).strip()
        if requested_exam_category_code and requested_exam_category_code != profile_exam_category_code:
            raise forbidden("学生端禁止跨学科门类访问题目。")
        if requested_joint_exam_group_code and requested_joint_exam_group_code != profile_joint_exam_group_code:
            raise forbidden("学生端禁止跨联考组访问题目。")

    def _filter_questions_for_student_scope(self, questions: List[Dict[str, str]], student_user_id: str, filters: Dict[str, str]) -> List[Dict[str, str]]:
        profile = self._get_student_profile(student_user_id)
        self._assert_student_scope_filters(profile, filters)
        scoped = [question for question in questions if self._is_question_visible_by_profile(question, profile)]
        return self._filter_questions_by_content_tags(scoped, filters)

    def _is_question_chapter_unlocked(self, question: Dict[str, str], student_user_id: str) -> bool:
        subject_id = self._question_subject_id(question)
        chapter = self._question_chapter(question)
        return bool(self._build_chapter_progress(subject_id, chapter, student_user_id).get("isUnlocked", False))

    def _filter_unlocked_chapter_questions(self, questions: List[Dict[str, str]], student_user_id: str) -> List[Dict[str, str]]:
        unlock_cache: Dict[Tuple[str, str], bool] = {}
        matched: List[Dict[str, str]] = []
        for question in questions:
            key = (self._question_subject_id(question), self._question_chapter(question))
            if key not in unlock_cache:
                unlock_cache[key] = bool(self._build_chapter_progress(key[0], key[1], student_user_id).get("isUnlocked", False))
            if unlock_cache[key]:
                matched.append(question)
        return matched

    def _question_time_limit_sec(self, question: Dict[str, str]) -> int:
        ext_json = self._load_json_object(question["extJson"])
        practice_config = ext_json.get("practiceConfig", {})
        if isinstance(practice_config, dict):
            try:
                candidate = int(practice_config.get("timeLimitSec", 0))
                if candidate > 0:
                    return candidate
            except Exception:
                pass
        return 180 if question["type"] == "subjective" else 60

    def _parse_optional_datetime(self, value: object) -> Optional[datetime]:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        try:
            if normalized.endswith("Z"):
                return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None

    def _matches_personal_bank_archive_window(
        self,
        record: Optional[Dict[str, object]],
        record_ext: Dict[str, object],
        archive_window: str,
    ) -> bool:
        normalized_window = str(archive_window or "").strip().upper()
        if not normalized_window:
            return True
        personal_bank = self._build_formal_personal_bank_state(record, record_ext)
        wrong_book = self._build_formal_wrong_book_state(record, record_ext)
        source_type = str(personal_bank.get("sourceType", "")).strip().upper()
        source_label = str(personal_bank.get("sourceLabel", "")).strip()
        is_archived = bool(wrong_book.get("isArchived")) or source_type == "HARVESTED_ARCHIVE" or source_label == "已斩获归档"
        if not is_archived:
            return False
        if normalized_window == "ARCHIVED":
            return True
        archived_at = self._parse_optional_datetime(wrong_book.get("archivedAt"))
        if archived_at is None:
            return False
        now = datetime.now(timezone.utc)
        days = (now - archived_at.astimezone(timezone.utc)).total_seconds() / (60 * 60 * 24)
        if normalized_window == "LAST_7_DAYS":
            return days <= 7
        if normalized_window == "LAST_30_DAYS":
            return days <= 30
        if normalized_window == "EARLIER":
            return days > 30
        return True

    def _filter_student_question_views(
        self,
        questions: List[Dict[str, str]],
        student_user_id: str,
        filters: Dict[str, str],
        student_record_map: Optional[Dict[str, Dict[str, object]]] = None,
    ) -> List[Dict[str, str]]:
        keyword = filters.get("keyword", "").strip()
        only_personal_bank = filters.get("onlyPersonalBank", "").strip().lower() == "true"
        source_type = filters.get("sourceType", "").strip()
        archive_window = str(filters.get("archiveWindow", "")).strip().upper()
        question_id_set = {
            str(item).strip()
            for item in str(filters.get("questionIds", "")).split(",")
            if str(item).strip()
        }
        knowledge_path_node_id = str(filters.get("knowledgePathNodeId") or "").strip()
        subject_code = str(filters.get("subjectCode", "")).strip()
        descendant_knowledge_ids = (
            self._resolve_wrong_book_path_node_descendants(knowledge_path_node_id, subject_code)
            if knowledge_path_node_id and hasattr(self, "_resolve_wrong_book_path_node_descendants")
            else set()
        )
        matched: List[Dict[str, str]] = []
        for question in questions:
            ext_json = self._load_json_object(question["extJson"])
            analysis = self._question_analysis(question)
            knowledge_tags = ",".join(self._question_knowledge_tags(question))
            if keyword and keyword not in question["stem"] and keyword not in analysis and keyword not in knowledge_tags:
                continue
            if descendant_knowledge_ids and str(question.get("knowledgeId", "")).strip() not in descendant_knowledge_ids:
                continue
            question_id = str(question.get("id", "")).strip()
            if question_id_set and question_id not in question_id_set:
                continue
            if only_personal_bank:
                record = (student_record_map or {}).get(question_id) or self.repository.get_student_question_bank(question["id"], student_user_id)
                record_ext = self._load_json_object(record["extJson"] if record else "{}")
                if not bool((record or {}).get("personalBankFlag", 0)):
                    continue
                if source_type and str((record or {}).get("personalBankSourceType", "")).strip() != source_type:
                    continue
                if archive_window and not self._matches_personal_bank_archive_window(record, record_ext, archive_window):
                    continue
            elif source_type and ext_json.get("sourceType") != source_type:
                continue
            matched.append(question)
        return matched

    def _pick_filters(self, filters: Dict[str, str], keys: Tuple[str, ...]) -> Dict[str, str]:
        return {key: str(filters.get(key, "")).strip() for key in keys}

    def _resolve_actor_scope_filters(
        self,
        actor_role: str,
        actor_user_id: str,
        injected_joint_group_code: str = "",
    ) -> Dict[str, str]:
        if actor_role == ROLE_SUPER_ADMIN:
            return {
                "exam_category_code": "",
                "joint_exam_group_code": "",
            }
        scope = self.resolve_actor_assigned_scope(actor_user_id) if hasattr(self, "resolve_actor_assigned_scope") else {}
        exam_category_code = str(scope.get("exam_category_code", "")).strip()
        joint_exam_group_code = str(scope.get("joint_exam_group_code", "")).strip()
        normalized_injected_joint_group_code = str(injected_joint_group_code or "").strip()
        if normalized_injected_joint_group_code:
            if joint_exam_group_code and normalized_injected_joint_group_code != joint_exam_group_code:
                raise forbidden("X-Joint-Group 与账号分配专业组不一致。")
            joint_exam_group_code = normalized_injected_joint_group_code
        if joint_exam_group_code and not exam_category_code:
            joint_exam_group = get_joint_exam_group(joint_exam_group_code)
            if joint_exam_group:
                exam_category_code = str(joint_exam_group.get("examCategoryCode", "")).strip()
        return {
            "exam_category_code": exam_category_code,
            "joint_exam_group_code": joint_exam_group_code,
        }

    def _apply_required_list_scope(
        self,
        filters: Dict[str, str],
        actor_role: str,
        actor_user_id: str,
        injected_joint_group_code: str = "",
    ) -> Dict[str, str]:
        normalized_filters = {key: str(value or "").strip() for key, value in dict(filters or {}).items()}
        normalized_filters["policyVersion"] = POLICY_VERSION_CODE
        normalized_filters["policyVersionCode"] = POLICY_VERSION_CODE

        actor_scope = self._resolve_actor_scope_filters(
            actor_role,
            actor_user_id,
            injected_joint_group_code=injected_joint_group_code,
        )
        actor_exam_category_code = str(actor_scope.get("exam_category_code", "")).strip()
        actor_joint_exam_group_code = str(actor_scope.get("joint_exam_group_code", "")).strip()
        if not actor_joint_exam_group_code and not actor_exam_category_code:
            return normalized_filters

        requested_joint_exam_group_code = str(normalized_filters.get("jointExamGroupCode") or "").strip()
        requested_exam_category_code = str(normalized_filters.get("examCategoryCode") or "").strip()
        requested_subject_code = str(normalized_filters.get("subjectCode") or "").strip()

        if actor_joint_exam_group_code and requested_joint_exam_group_code and requested_joint_exam_group_code != actor_joint_exam_group_code:
            raise forbidden("当前账号禁止跨联考专业组访问题目。")
        if actor_exam_category_code and requested_exam_category_code and requested_exam_category_code != actor_exam_category_code:
            raise forbidden("当前账号禁止跨学科门类访问题目。")
        if actor_joint_exam_group_code and requested_subject_code:
            public_subject_codes = {
                str(item.get("subjectCode", "")).strip()
                for item in PUBLIC_SUBJECTS
                if isinstance(item, dict) and str(item.get("subjectCode", "")).strip()
            }
            if requested_subject_code not in public_subject_codes:
                actor_joint_group = get_joint_exam_group(actor_joint_exam_group_code)
                professional_subject_codes = {
                    str(item.get("subjectCode", "")).strip()
                    for item in (actor_joint_group or {}).get("professionalSubjects", [])
                    if isinstance(item, dict) and str(item.get("subjectCode", "")).strip()
                }
                if requested_subject_code not in professional_subject_codes:
                    raise forbidden("当前账号禁止跨联考专业组访问题目。")

        if actor_exam_category_code:
            normalized_filters["examCategoryCode"] = actor_exam_category_code
        if actor_joint_exam_group_code:
            normalized_filters["jointExamGroupCode"] = actor_joint_exam_group_code
        return normalized_filters

    def _build_student_error_book_scope_filters(
        self,
        actor: Actor,
        filters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        return self._build_error_book_scope_filters_for_student(
            actor.user_id,
            filters,
            viewer_actor=actor,
        )

    def _assert_error_book_student_access(
        self,
        viewer_actor: Actor,
        target_student_user_id: str,
    ) -> Dict[str, object]:
        normalized_student_user_id = str(target_student_user_id or "").strip()
        if not normalized_student_user_id:
            raise validation_failed("studentUserId 不能为空。")
        managed_user = self._get_managed_user(normalized_student_user_id)
        if not managed_user or normalize_role(str(managed_user.get("role", ""))) != ROLE_STUDENT:
            raise not_found("目标学生不存在。")
        if viewer_actor.role == ROLE_SUPER_ADMIN:
            return managed_user
        if viewer_actor.role == ROLE_STUDENT:
            if normalized_student_user_id != viewer_actor.user_id:
                raise forbidden("当前账号不可查看其他学生学情。")
            return managed_user
        actor_scope = self._resolve_actor_scope_filters(viewer_actor.role, viewer_actor.user_id)
        scoped_exam_category_code = str(actor_scope.get("exam_category_code", "")).strip()
        scoped_joint_exam_group_code = str(actor_scope.get("joint_exam_group_code", "")).strip()
        student_exam_category_code = str(managed_user.get("examCategoryCode", "")).strip()
        student_joint_exam_group_code = str(managed_user.get("jointExamGroupCode", "")).strip()
        if scoped_exam_category_code and student_exam_category_code != scoped_exam_category_code:
            raise forbidden("当前账号不可查看该学生学情。")
        if scoped_joint_exam_group_code and student_joint_exam_group_code != scoped_joint_exam_group_code:
            raise forbidden("当前账号不可查看该学生学情。")
        return managed_user

    def _build_error_book_target_actor(
        self,
        viewer_actor: Actor,
        target_student_user_id: str,
    ) -> Actor:
        managed_user = self._assert_error_book_student_access(viewer_actor, target_student_user_id)
        joint_exam_group_code = str(managed_user.get("jointExamGroupCode", "")).strip()
        return Actor(
            role=ROLE_STUDENT,
            user_id=str(target_student_user_id).strip(),
            assigned_joint_group_code=joint_exam_group_code,
        )

    def _build_error_book_scope_filters_for_student(
        self,
        student_user_id: str,
        filters: Optional[Dict[str, str]] = None,
        viewer_actor: Optional[Actor] = None,
    ) -> Dict[str, str]:
        normalized_student_user_id = str(student_user_id or "").strip()
        if viewer_actor:
            self._assert_error_book_student_access(viewer_actor, normalized_student_user_id)
        normalized_filters = {key: str(value or "").strip() for key, value in dict(filters or {}).items()}
        scoped_filters = self._apply_required_list_scope(
            normalized_filters,
            ROLE_STUDENT,
            normalized_student_user_id,
        )
        profile = self._get_student_profile(normalized_student_user_id)
        exam_category_code = str(scoped_filters.get("examCategoryCode", "")).strip() or str(profile.get("examCategoryCode", "")).strip()
        joint_exam_group_code = str(scoped_filters.get("jointExamGroupCode", "")).strip() or str(profile.get("jointExamGroupCode", "")).strip()
        subject_code = str(scoped_filters.get("subjectCode", "")).strip()
        scoped_filters["examCategoryCode"] = exam_category_code
        scoped_filters["jointExamGroupCode"] = joint_exam_group_code
        scoped_filters["subjectCode"] = subject_code
        scoped_filters["policyVersionCode"] = POLICY_VERSION_CODE
        scoped_filters["policyVersion"] = POLICY_VERSION_CODE
        return scoped_filters

    def _normalize_subject_codes_filter(self, filters: Optional[Dict[str, object]] = None) -> List[str]:
        normalized_filters = dict(filters or {}) if isinstance(filters, dict) else {}
        raw_subject_codes = normalized_filters.get("subjectCodes")
        subject_codes: List[str] = []
        if isinstance(raw_subject_codes, list):
            source_rows = raw_subject_codes
        else:
            source_rows = str(raw_subject_codes or "").split(",")
        for item in source_rows:
            subject_code = str(item or "").strip()
            if not subject_code or subject_code in subject_codes:
                continue
            subject_codes.append(subject_code)
        single_subject_code = str(normalized_filters.get("subjectCode") or "").strip()
        if single_subject_code and single_subject_code not in subject_codes:
            subject_codes.insert(0, single_subject_code)
        return subject_codes

    def _list_questions_with_optional_content_filter(
        self,
        db_filters: Dict[str, str],
        filters: Dict[str, str],
        page: int,
        size: int,
        actor: Actor,
    ) -> Tuple[List[Dict[str, str]], int]:
        scoped_filters = self._apply_required_list_scope(
            filters,
            actor.role,
            actor.user_id,
            injected_joint_group_code=actor.assigned_joint_group_code,
        )
        scoped_db_filters = dict(db_filters)
        scoped_db_filters["policy_version"] = POLICY_VERSION_CODE
        content_filters = self._content_filter_values(scoped_filters)
        scoped_db_filters["examCategoryCode"] = content_filters.get("examCategoryCode", "")
        scoped_db_filters["jointExamGroupCode"] = content_filters.get("jointExamGroupCode", "")
        scoped_db_filters["subjectCode"] = content_filters.get("subjectCode", "")
        scoped_db_filters["exam_category_code"] = content_filters.get("examCategoryCode", "")
        scoped_db_filters["joint_exam_group_code"] = content_filters.get("jointExamGroupCode", "")
        scoped_db_filters["subject_code"] = content_filters.get("subjectCode", "")
        if self._has_content_filter(scoped_filters):
            return self._paginate_questions_with_content_filters(scoped_db_filters, scoped_filters, page, size, actor)
        items, total = self.repository.list_questions(scoped_db_filters, page, size, actor.role, actor.user_id)
        return [self._public_question(item) for item in items], total

    def _paginate_questions_with_content_filters(
        self,
        db_filters: Dict[str, str],
        filters: Dict[str, str],
        page: int,
        size: int,
        actor: Actor,
    ) -> Tuple[List[Dict[str, str]], int]:
        batch_size = max(100, size)
        cursor_page = 1
        offset = (page - 1) * size
        matched_total = 0
        paged_items: List[Dict[str, str]] = []
        while True:
            batch, raw_total = self.repository.list_questions(db_filters, cursor_page, batch_size, actor.role, actor.user_id)
            if not batch:
                break
            for item in batch:
                if not self._matches_question_content_tags(item, filters):
                    continue
                if matched_total >= offset and len(paged_items) < size:
                    paged_items.append(self._public_question(item))
                matched_total += 1
            if cursor_page * batch_size >= raw_total:
                break
            cursor_page += 1
        return paged_items, matched_total

    def _list_published_questions_with_content_filters(
        self,
        db_filters: Dict[str, str],
        filters: Dict[str, str],
        role: str,
        user_id: str,
        injected_joint_group_code: str = "",
    ) -> List[Dict[str, str]]:
        scoped_filters = self._apply_required_list_scope(
            filters,
            role,
            user_id,
            injected_joint_group_code=injected_joint_group_code,
        )
        repository_filters = dict(db_filters)
        content_filters = self._content_filter_values(scoped_filters)
        repository_filters.update(content_filters)
        repository_filters["exam_category_code"] = content_filters.get("examCategoryCode", "")
        repository_filters["joint_exam_group_code"] = content_filters.get("jointExamGroupCode", "")
        repository_filters["subject_code"] = content_filters.get("subjectCode", "")
        repository_filters["policy_version"] = POLICY_VERSION_CODE
        questions = self.repository.list_visible_published_questions(repository_filters, role, user_id)
        return self._filter_questions_by_content_tags(questions, scoped_filters)

    def _student_review_plan_id(self, student_user_id: str, plan_type: str) -> str:
        return f"student-review-plan::{student_user_id}::{plan_type}"

    def _student_review_plan_item_id(self, student_user_id: str, plan_type: str, question_id: str) -> str:
        return f"student-review-plan-item::{student_user_id}::{plan_type}::{question_id}"

    def _load_student_review_plan_bundle(self, student_user_id: str, plan_id: str) -> Optional[Dict[str, object]]:
        plan = self.repository.get_student_review_plan(student_user_id, plan_id)
        if not plan:
            return None
        items = self.repository.list_student_review_plan_items(plan_id)
        payload = dict(plan)
        payload["items"] = items
        return payload

    def _list_student_review_plan_bundles(self, student_user_id: str) -> List[Dict[str, object]]:
        bundles: List[Dict[str, object]] = []
        for plan in self.repository.list_student_review_plans(student_user_id):
            bundles.append(
                {
                    **plan,
                    "items": self.repository.list_student_review_plan_items(str(plan.get("id", "")).strip()),
                }
            )
        return bundles

    def _build_formal_review_plan_rows(self, items: List[Dict[str, str]]) -> List[Dict[str, object]]:
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()
        due_review_ids: List[str] = []
        high_wrong_ids: List[str] = []
        unanswered_ids: List[str] = []
        for question in items:
            ext_json = self._load_json_object(question["extJson"])
            student_state = ext_json.get("studentState", {}) if isinstance(ext_json.get("studentState", {}), dict) else {}
            practice = student_state.get("chapterPractice", {}) if isinstance(student_state.get("chapterPractice", {}), dict) else {}
            wrong_book = student_state.get("wrongBook", {}) if isinstance(student_state.get("wrongBook", {}), dict) else {}
            question_id = str(question.get("id", "")).strip()
            if not question_id:
                continue
            if not practice:
                unanswered_ids.append(question_id)
            wrong_count = int(wrong_book.get("wrongCount", 0))
            reviewed_at = str(wrong_book.get("reviewedAt", "")).strip()
            needs_today_review = bool(wrong_count) and (not reviewed_at or reviewed_at[:10] < today)
            if needs_today_review:
                due_review_ids.append(question_id)
            if wrong_count >= 2:
                high_wrong_ids.append(question_id)
        return [
            {
                "planType": "todayDue",
                "planName": "今日优先复习",
                "description": "今日未复盘的错题，建议先做一轮回顾。",
                "questionIds": due_review_ids,
                "actionLabel": "开始今日复盘",
            },
            {
                "planType": "highWrong",
                "planName": "高频易错加练",
                "description": "累计错题次数较高，建议重点强化。",
                "questionIds": high_wrong_ids,
                "actionLabel": "开始高频加练",
            },
            {
                "planType": "unanswered",
                "planName": "未作答题目补齐",
                "description": "收藏后还未作答，建议先补首轮答案。",
                "questionIds": unanswered_ids,
                "actionLabel": "开始补齐首轮",
            },
        ]

    def _sync_student_review_plans(self, actor: Actor) -> List[Dict[str, object]]:
        now_iso = self._now_iso()
        all_items = self.list_all_personal_bank_questions({}, actor) if hasattr(self, "list_all_personal_bank_questions") else []
        computed_rows = self._build_formal_review_plan_rows(all_items)
        existing_bundles = {
            str(bundle.get("planType", "")).strip(): bundle
            for bundle in self._list_student_review_plan_bundles(actor.user_id)
        }
        synced_bundles: List[Dict[str, object]] = []
        for row in computed_rows:
            plan_type = str(row.get("planType", "")).strip()
            if not plan_type:
                continue
            existing_bundle = existing_bundles.get(plan_type, {})
            existing_plan = dict(existing_bundle) if isinstance(existing_bundle, dict) else {}
            existing_items = {
                str(item.get("questionId", "")).strip(): item
                for item in existing_plan.get("items", [])
                if isinstance(item, dict) and str(item.get("questionId", "")).strip()
            }
            plan_id = self._student_review_plan_id(actor.user_id, plan_type)
            question_ids = [str(item).strip() for item in row.get("questionIds", []) if str(item).strip()]
            item_payloads: List[Dict[str, object]] = []
            completed_count = 0
            for sort_index, question_id in enumerate(question_ids):
                existing_item = existing_items.get(question_id, {})
                item_status = str(existing_item.get("status", "")).strip() or "PENDING"
                completed_at = str(existing_item.get("completedAt", "")).strip()
                if item_status == "COMPLETED":
                    completed_count += 1
                item_payloads.append(
                    {
                        "id": self._student_review_plan_item_id(actor.user_id, plan_type, question_id),
                        "planId": plan_id,
                        "studentUserId": actor.user_id,
                        "questionId": question_id,
                        "status": item_status,
                        "sort": sort_index,
                        "completedAt": completed_at,
                        "extJson": self._dump_json({}),
                        "createTime": str(existing_item.get("createTime", "")).strip() or now_iso,
                        "updateTime": now_iso,
                    }
                )
            started_at = str(existing_plan.get("startedAt", "")).strip()
            last_executed_at = str(existing_plan.get("lastExecutedAt", "")).strip()
            if question_ids and completed_count >= len(question_ids):
                plan_status = "COMPLETED"
                completed_at = str(existing_plan.get("completedAt", "")).strip() or now_iso
            elif question_ids and (started_at or completed_count > 0):
                plan_status = "IN_PROGRESS"
                completed_at = ""
            else:
                plan_status = "PENDING"
                completed_at = ""
            plan_payload = {
                "id": plan_id,
                "studentUserId": actor.user_id,
                "planType": plan_type,
                "planName": str(row.get("planName", "")).strip() or plan_type,
                "status": plan_status,
                "generatedAt": now_iso,
                "startedAt": started_at,
                "completedAt": completed_at,
                "lastExecutedAt": last_executed_at,
                "extJson": self._dump_json(
                    {
                        "description": str(row.get("description", "")).strip(),
                        "actionLabel": str(row.get("actionLabel", "")).strip(),
                        "questionCount": len(question_ids),
                        "completedCount": completed_count,
                    }
                ),
                "createTime": str(existing_plan.get("createTime", "")).strip() or now_iso,
                "updateTime": now_iso,
            }
            self.repository.replace_student_review_plan(plan_payload, item_payloads)
            synced_bundles.append(self._load_student_review_plan_bundle(actor.user_id, plan_id) or {**plan_payload, "items": item_payloads})
        return synced_bundles

    def _project_review_plan_rows(
        self,
        plan_bundles: List[Dict[str, object]],
        filtered_question_ids: set[str],
    ) -> List[Dict[str, object]]:
        projected_rows: List[Dict[str, object]] = []
        for bundle in plan_bundles:
            plan_ext = self._load_json_object(bundle.get("extJson", "{}"))
            if not isinstance(plan_ext, dict):
                plan_ext = {}
            filtered_items = [
                item
                for item in bundle.get("items", [])
                if isinstance(item, dict) and str(item.get("questionId", "")).strip() in filtered_question_ids
            ]
            filtered_question_id_rows = [
                str(item.get("questionId", "")).strip()
                for item in filtered_items
                if str(item.get("questionId", "")).strip()
            ]
            projected_rows.append(
                {
                    "planId": str(bundle.get("id", "")).strip(),
                    "planKey": str(bundle.get("planType", "")).strip(),
                    "planName": str(bundle.get("planName", "")).strip(),
                    "description": str(plan_ext.get("description", "")).strip(),
                    "status": str(bundle.get("status", "")).strip() or "PENDING",
                    "questionCount": len(filtered_question_id_rows),
                    "questionIds": filtered_question_id_rows,
                    "completedCount": sum(
                        1
                        for item in filtered_items
                        if str(item.get("status", "")).strip() == "COMPLETED"
                    ),
                    "actionLabel": str(plan_ext.get("actionLabel", "")).strip() or "开始执行",
                    "startedAt": str(bundle.get("startedAt", "")).strip(),
                    "completedAt": str(bundle.get("completedAt", "")).strip(),
                    "lastExecutedAt": str(bundle.get("lastExecutedAt", "")).strip(),
                }
            )
        return projected_rows

    def _summarize_personal_bank_items(
        self,
        items: List[Dict[str, str]],
        review_plan_rows: Optional[List[Dict[str, object]]] = None,
    ) -> Dict[str, object]:
        subject_counts: Dict[str, int] = {}
        answered_count = 0
        correct_count = 0
        recent_collected_at = ""
        archived_count = 0
        archived_last_7_days_count = 0
        archived_last_30_days_count = 0
        archived_earlier_count = 0
        now = datetime.now(timezone.utc)
        for question in items:
            ext_json = self._load_json_object(question["extJson"])
            student_state = ext_json.get("studentState", {})
            practice = student_state.get("chapterPractice", {})
            personal_bank = student_state.get("personalBank", {})
            wrong_book = student_state.get("wrongBook", {})
            subject_id = self._question_subject_id(question)
            question_id = str(question.get("id", ""))
            subject_counts[subject_id] = subject_counts.get(subject_id, 0) + 1
            if practice:
                answered_count += 1
                if practice.get("isCorrect"):
                    correct_count += 1
            collected_at = str(personal_bank.get("collectedAt", ""))
            if collected_at and collected_at > recent_collected_at:
                recent_collected_at = collected_at
            source_type = str(personal_bank.get("sourceType", "")).strip().upper()
            source_label = str(personal_bank.get("sourceLabel", "")).strip()
            archived_at = self._parse_optional_datetime(wrong_book.get("archivedAt"))
            if bool(wrong_book.get("isArchived")) or source_type == "HARVESTED_ARCHIVE" or source_label == "已斩获归档":
                archived_count += 1
                if archived_at is not None:
                    days = (now - archived_at.astimezone(timezone.utc)).total_seconds() / (60 * 60 * 24)
                    if days <= 7:
                        archived_last_7_days_count += 1
                    if days <= 30:
                        archived_last_30_days_count += 1
                    else:
                        archived_earlier_count += 1
        subject_rankings = [
            {"subjectId": subject_id, "questionCount": count}
            for subject_id, count in sorted(subject_counts.items(), key=lambda item: (-item[1], item[0]))
        ]
        review_plan = review_plan_rows or []
        recommended_plan_key = ""
        for row in review_plan:
            if int(row["questionCount"]) > 0:
                recommended_plan_key = str(row["planKey"])
                break
        return {
            "totalCount": len(items),
            "answeredCount": answered_count,
            "correctCount": correct_count,
            "unansweredCount": max(0, len(items) - answered_count),
            "accuracy": round(correct_count / answered_count, 4) if answered_count else 0.0,
            "subjectRankings": subject_rankings[:6],
            "recentCollectedAt": recent_collected_at,
            "archivedCount": archived_count,
            "archivedLast7DaysCount": archived_last_7_days_count,
            "archivedLast30DaysCount": archived_last_30_days_count,
            "archivedEarlierCount": archived_earlier_count,
            "reviewPlan": review_plan,
            "recommendedPlanKey": recommended_plan_key,
        }

    def _resolve_wrong_reason_payload(self, question: Dict[str, str], normalized_answer: str, is_timeout: bool) -> Dict[str, str]:
        if is_timeout:
            return {"reasonCode": "TIMEOUT", "reasonLabel": "答题超时"}
        if not str(normalized_answer).strip():
            return {"reasonCode": "BLANK", "reasonLabel": "未作答"}
        if str(question.get("type", "")) == "subjective":
            return {"reasonCode": "EXPRESSION", "reasonLabel": "表达不完整"}
        return {"reasonCode": "KNOWLEDGE_GAP", "reasonLabel": "知识点掌握不牢"}

    def _upsert_wrong_reason_stats(
        self,
        reason_stats: object,
        reason_code: str,
        reason_label: str,
    ) -> List[Dict[str, object]]:
        normalized_rows: List[Dict[str, object]] = []
        found = False
        if isinstance(reason_stats, list):
            for row in reason_stats:
                if not isinstance(row, dict):
                    continue
                code = str(row.get("reasonCode", "")).strip()
                label = str(row.get("reasonLabel", "")).strip()
                count = int(row.get("count", 0))
                if not code:
                    continue
                if code == reason_code:
                    count += 1
                    label = reason_label
                    found = True
                normalized_rows.append({"reasonCode": code, "reasonLabel": label, "count": max(0, count)})
        if not found:
            normalized_rows.append({"reasonCode": reason_code, "reasonLabel": reason_label, "count": 1})
        normalized_rows.sort(key=lambda item: int(item.get("count", 0)), reverse=True)
        return normalized_rows

    def _question_matches_wrong_reason(self, question: Dict[str, str], reason_code: str) -> bool:
        ext_json = self._load_json_object(question.get("extJson", "{}"))
        wrong_book = (ext_json.get("studentState", {}) or {}).get("wrongBook", {})
        if not isinstance(wrong_book, dict):
            return False
        if str(wrong_book.get("lastReasonCode", "")).upper() == reason_code:
            return True
        reason_stats = wrong_book.get("reasonStats", [])
        if not isinstance(reason_stats, list):
            return False
        return any(str(item.get("reasonCode", "")).upper() == reason_code for item in reason_stats if isinstance(item, dict))

    def _compute_check_in_streak(self, check_in_dates: List[str]) -> int:
        if not check_in_dates:
            return 0
        date_values = sorted({datetime.fromisoformat(item).date() for item in check_in_dates})
        streak = 1
        for index in range(len(date_values) - 1, 0, -1):
            if (date_values[index] - date_values[index - 1]).days == 1:
                streak += 1
            else:
                break
        return streak

    def _resolve_title(self, points: int) -> str:
        if points >= 200:
            return "备考之星"
        if points >= 100:
            return "打卡先锋"
        if points >= 50:
            return "连刷达人"
        return "备考新星"

    def _current_ai_quota(self, profile: Dict[str, object]) -> Dict[str, object]:
        today = datetime.now(timezone.utc).date().isoformat()
        default_limit = int(self._system_settings()["aiDailyLimit"])
        ai_quota = dict(profile.get("aiQuota", {"dailyLimit": default_limit, "usedCount": 0, "quotaDate": today}))
        if ai_quota.get("quotaDate") != today:
            ai_quota["quotaDate"] = today
            ai_quota["usedCount"] = 0
            ai_quota["dailyLimit"] = default_limit
        return ai_quota

    def _count_completed_papers(self, student_user_id: str) -> int:
        records = self.repository.list_student_records_by_user(student_user_id)
        completed = 0
        seen = set()
        for question in records:
            ext_json = self._load_json_object(question["extJson"])
            student_record = ext_json.get("studentRecord", {})
            record_ext = self._load_json_object(student_record.get("extJson", "{}"))
            for paper_id in record_ext.get("simulationAttempts", {}).keys():
                seen.add(paper_id)
        completed += len(seen)
        return completed

    def _count_wrong_book_questions(self, student_user_id: str) -> int:
        _, total = self.list_wrong_book_questions(1, 100, Actor(role=ROLE_STUDENT, user_id=student_user_id))
        return total

    def _save_paper_report(self, student_user_id: str, paper_id: str, payload: Dict[str, object]) -> None:
        report_id = str(payload.get("reportId", "")).strip() or f"paper-report-{uuid.uuid4().hex[:10]}"
        pending_task_ids_raw = payload.get("pendingSubjectiveTaskIds")
        pending_task_ids = [str(item) for item in pending_task_ids_raw] if isinstance(pending_task_ids_raw, list) else []
        saved_payload = {"studentUserId": student_user_id, "reportId": report_id, **payload}
        self.repository.upsert_paper_report_payload(saved_payload)
        has_pending_subjective = len(pending_task_ids) > 0
        self._push_message(
            [student_user_id],
            "SYSTEM_NOTICE",
            "主观题批改中" if has_pending_subjective else "模拟卷已批改完成",
            (
                f"{paper_id} 客观题已完成判分，主观题批改完成后将再次通知。"
                if has_pending_subjective
                else f"{paper_id} 已生成成绩报告，可前往学情页查看。"
            ),
        )

    def _collect_paper_reports(self, paper_id: str) -> List[Dict[str, object]]:
        return [item for item in self._paper_reports() if item["paperId"] == paper_id]

    def _build_ai_marking_result(self, question: Dict[str, str], student_answer: str) -> Dict[str, object]:
        expected = question["answer"]
        overlap = 1.0 if expected in student_answer or student_answer in expected else 0.6 if student_answer else 0.0
        correctness = round(60 * overlap, 1)
        steps = round(30 * min(1.0, len(student_answer) / max(1, len(expected) * 2)), 1)
        format_score = 10.0 if len(student_answer.strip()) >= 6 else 6.0
        total_score = round(correctness + steps + format_score, 1)
        return {
            "totalScore": total_score,
            "correctnessScore": correctness,
            "stepsScore": steps,
            "formatScore": format_score,
            "comments": [
                "正确性按采分点覆盖度估算。",
                "步骤分关注论证层次和关键词完整度。",
                "规范性关注表达清晰度与结构完整性。",
            ],
            "sampleAnswer": self._question_analysis(question),
        }

    def _build_ai_tutor_response(self, question: Dict[str, str], prompt: str) -> str:
        return (
            f"先回到题干：{question['stem']}。"
            f" 你刚才关注的是“{prompt}”。"
            f" 建议先从知识点 {self._question_knowledge_tags(question)} 入手，再对照解析中的关键线索：{self._question_analysis(question)}。"
            " 先不要急着背答案，先说说你认为最关键的一步是什么。"
        )
