from __future__ import annotations

from threading import Lock, Thread

from app.service_shared import *


class InternalAnalyticsServiceMixin:
    def _ensure_ai_analytics_report_state(self) -> None:
        if hasattr(self, "_ai_analytics_report_lock"):
            return
        self._ai_analytics_report_lock = Lock()
        self._ai_analytics_report_cache: Dict[str, str] = {}
        self._ai_analytics_report_jobs: set[str] = set()

    def _build_ai_analytics_report_cache_key(
        self,
        chapter_rankings: List[Dict[str, object]],
        mastery_rows: List[Dict[str, object]],
        weak_knowledge_tags: List[Dict[str, object]],
        low_activity_students: List[Dict[str, object]],
    ) -> str:
        summary_payload = {
            "chapterRankings": [
                {
                    "chapter": str(item.get("chapter", "")).strip(),
                    "wrongCount": int(item.get("wrongCount", 0) or 0),
                }
                for item in chapter_rankings[:5]
            ],
            "weakKnowledgeTags": [
                {
                    "knowledgeTag": str(item.get("knowledgeTag", "")).strip(),
                    "wrongCount": int(item.get("wrongCount", 0) or 0),
                }
                for item in weak_knowledge_tags[:5]
            ],
            "lowActivityStudents": [
                {
                    "studentUserId": str(item.get("studentUserId", "")).strip(),
                    "activityCount": int(item.get("activityCount", 0) or 0),
                }
                for item in low_activity_students[:5]
            ],
            "masteryCount": len(mastery_rows),
            "lowestMastery": min((float(item.get("mastery", 0.0) or 0.0) for item in mastery_rows), default=0.0),
        }
        payload_text = json.dumps(summary_payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha1(payload_text.encode("utf-8")).hexdigest()

    def _run_ai_analytics_report_job(
        self,
        cache_key: str,
        chapter_rankings: List[Dict[str, object]],
        mastery_rows: List[Dict[str, object]],
        weak_knowledge_tags: List[Dict[str, object]],
        low_activity_students: List[Dict[str, object]],
    ) -> None:
        report_text = ""
        try:
            report_text = str(
                self._build_ai_analytics_report(
                    chapter_rankings,
                    mastery_rows,
                    weak_knowledge_tags,
                    low_activity_students,
                )
                or ""
            ).strip()
        except Exception:
            report_text = ""
        self._ensure_ai_analytics_report_state()
        with self._ai_analytics_report_lock:
            self._ai_analytics_report_jobs.discard(cache_key)
            if report_text:
                self._ai_analytics_report_cache[cache_key] = report_text

    def _resolve_ai_analytics_report_async(
        self,
        chapter_rankings: List[Dict[str, object]],
        mastery_rows: List[Dict[str, object]],
        weak_knowledge_tags: List[Dict[str, object]],
        low_activity_students: List[Dict[str, object]],
    ) -> str:
        self._ensure_ai_analytics_report_state()
        cache_key = self._build_ai_analytics_report_cache_key(
            chapter_rankings,
            mastery_rows,
            weak_knowledge_tags,
            low_activity_students,
        )
        with self._ai_analytics_report_lock:
            cached_report = str(self._ai_analytics_report_cache.get(cache_key, "")).strip()
            if cached_report:
                return cached_report
            if cache_key not in self._ai_analytics_report_jobs:
                self._ai_analytics_report_jobs.add(cache_key)
                worker = Thread(
                    target=self._run_ai_analytics_report_job,
                    args=(
                        cache_key,
                        list(chapter_rankings[:8]),
                        list(mastery_rows),
                        list(weak_knowledge_tags[:8]),
                        list(low_activity_students[:5]),
                    ),
                    name=f"analytics-ai-report-{cache_key[:8]}",
                    daemon=True,
                )
                worker.start()
        return "班级干预摘要生成中，请稍后刷新查看。"

    def _load_filtered_analytics_records(self, filters: Dict[str, str]) -> List[Dict[str, str]]:
        self._validate_date_filters(filters)
        return self._list_all_analytics_records(filters)

    def _list_all_analytics_records(self, filters: Dict[str, str]) -> List[Dict[str, str]]:
        student_user_id = str(filters.get("studentUserId", "")).strip() or None
        return self.repository.list_all_student_records(student_user_id, filters)

    def _empty_analytics_summary(self, filters: Dict[str, str]) -> Dict[str, object]:
        return {
            "timeRangeLabel": self._format_time_range_label(filters),
            "studentCount": 0,
            "activeStudentCount": 0,
            "inactiveStudentCount": 0,
            "coverageRate": 0.0,
            "questionCount": 0,
            "averageAccuracy": 0.0,
            "averageAnswerDurationSec": 0.0,
            "masteredStudentCount": 0,
            "atRiskStudentCount": 0,
            "chapterRankings": [],
            "weakKnowledgeTags": [],
            "lowActivityStudents": [],
            "mastery": [],
            "studentRankings": [],
            "subjectCoverage": [],
            "aiReport": "",
        }

    def _partition_analytics_rollups(
        self,
        rollup_rows: List[Dict[str, object]],
    ) -> Tuple[
        List[Dict[str, object]],
        List[Dict[str, object]],
        List[Dict[str, object]],
        List[Dict[str, object]],
        List[Dict[str, object]],
    ]:
        point_rows: List[Dict[str, object]] = []
        chapter_rows: List[Dict[str, object]] = []
        student_subject_rows: List[Dict[str, object]] = []
        student_activity_rows: List[Dict[str, object]] = []
        tag_rows: List[Dict[str, object]] = []
        for row in rollup_rows:
            row_type = str(row.get("rowType", "")).strip()
            if row_type == "point":
                point_rows.append(row)
            elif row_type == "chapter":
                chapter_rows.append(row)
            elif row_type == "student_subject":
                student_subject_rows.append(row)
            elif row_type == "student_activity":
                student_activity_rows.append(row)
            elif row_type == "tag":
                tag_rows.append(row)
        return point_rows, chapter_rows, student_subject_rows, student_activity_rows, tag_rows

    def _build_mastery_rows_from_rollups(
        self,
        student_subject_rows: List[Dict[str, object]],
        question_count_by_subject: Dict[str, int],
        average_duration: float,
    ) -> List[Dict[str, object]]:
        mastery_rows: List[Dict[str, object]] = []
        for row in student_subject_rows:
            student_user_id = str(row.get("studentUserId", "")).strip()
            subject_id = str(row.get("subjectId", "")).strip()
            answered = max(0, int(row.get("answerCount", 0) or 0))
            correct = max(0, int(row.get("correctCount", 0) or 0))
            accuracy = correct / answered if answered else 0.0
            subject_average_duration = (
                float(row.get("totalAnswerDurationSec", 0) or 0) / answered
                if answered
                else average_duration
            )
            speed = 1.0 if subject_average_duration <= 0 else min(1.0, average_duration / subject_average_duration)
            pool_total = question_count_by_subject.get(subject_id, answered or 1)
            frequency = min(1.0, answered / pool_total) if pool_total else 0.0
            mastery_rows.append(
                {
                    "studentUserId": student_user_id,
                    "subjectId": subject_id,
                    "accuracy": round(accuracy, 4),
                    "speed": round(speed, 4),
                    "frequency": round(frequency, 4),
                    "mastery": round((accuracy * 0.6) + (speed * 0.2) + (frequency * 0.2), 4),
                }
            )
        return mastery_rows

    def _build_subject_coverage_rows(
        self,
        point_rows: List[Dict[str, object]],
        total_point_rows: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        covered_points_by_subject: Dict[Tuple[str, str], set[str]] = {}
        for row in point_rows:
            subject_id = str(row.get("subjectId", "")).strip()
            subject_code = str(row.get("subjectCode", "")).strip()
            point_code = str(row.get("pointCode", "")).strip()
            if not subject_id and not subject_code:
                continue
            if not point_code:
                continue
            covered_points_by_subject.setdefault((subject_id, subject_code), set()).add(point_code)

        total_points_by_subject: Dict[Tuple[str, str], int] = {}
        for row in total_point_rows:
            subject_id = str(row.get("subjectId", "")).strip()
            subject_code = str(row.get("subjectCode", "")).strip()
            total_points_by_subject[(subject_id, subject_code)] = max(0, int(row.get("totalPointCount", 0) or 0))

        subject_coverage_rows: List[Dict[str, object]] = []
        all_subject_keys = set(total_points_by_subject.keys()) | set(covered_points_by_subject.keys())
        for subject_id, subject_code in all_subject_keys:
            total_point_count = total_points_by_subject.get((subject_id, subject_code), 0)
            covered_point_count = len(covered_points_by_subject.get((subject_id, subject_code), set()))
            subject_coverage_rows.append(
                {
                    "subjectId": subject_id,
                    "subjectCode": subject_code,
                    "coveredPointCount": covered_point_count,
                    "totalPointCount": total_point_count,
                    "knowledgeCoverageRate": round(covered_point_count / total_point_count, 4) if total_point_count else 0.0,
                }
            )
        subject_coverage_rows.sort(key=lambda item: (str(item["subjectId"]), str(item["subjectCode"])))
        return subject_coverage_rows

    def _build_analytics_question_pool(self, filters: Dict[str, str], actor: Actor) -> List[Dict[str, str]]:
        return self._list_published_questions_with_content_filters(
            self._pick_filters(filters, ("subjectId",)),
            filters,
            actor.role,
            actor.user_id,
            injected_joint_group_code=actor.assigned_joint_group_code,
        )

    def _seed_analytics_question_pool(
        self,
        question_pool: List[Dict[str, str]],
    ) -> Tuple[Dict[str, int], Dict[str, int]]:
        question_count_by_subject: Dict[str, int] = {}
        weak_tag_counter: Dict[str, int] = {}
        for question in question_pool:
            subject_id = self._question_subject_id(question)
            question_count_by_subject[subject_id] = question_count_by_subject.get(subject_id, 0) + 1
            for tag in self._question_knowledge_tags(question):
                weak_tag_counter.setdefault(tag, 0)
        return question_count_by_subject, weak_tag_counter

    def _accumulate_analytics_metrics(
        self,
        analytics_records: List[Dict[str, object]],
        weak_tag_counter: Dict[str, int],
    ) -> Tuple[
        Dict[str, Dict[str, object]],
        Dict[Tuple[str, str], List[Dict[str, object]]],
        Dict[str, int],
        Dict[str, str],
        Dict[str, int],
    ]:
        chapter_rankings: Dict[str, Dict[str, object]] = {}
        student_subject_map: Dict[Tuple[str, str], List[Dict[str, object]]] = {}
        student_activity: Dict[str, int] = {}
        latest_submission_by_student: Dict[str, str] = {}
        for item in analytics_records:
            chapter_key = f"{item['subjectId']}::{item['chapter']}"
            chapter_row = chapter_rankings.setdefault(
                chapter_key,
                {"subjectId": item["subjectId"], "chapter": item["chapter"], "wrongCount": 0, "answerCount": 0, "wrongRate": 0.0},
            )
            chapter_row["answerCount"] += 1
            if not item["isCorrect"]:
                chapter_row["wrongCount"] += 1
                for tag in item["knowledgeTags"]:
                    weak_tag_counter[tag] = weak_tag_counter.get(tag, 0) + 1
            student_activity[item["studentUserId"]] = student_activity.get(item["studentUserId"], 0) + 1
            student_subject_map.setdefault((item["studentUserId"], item["subjectId"]), []).append(item)
            latest_submission_by_student[item["studentUserId"]] = max(
                latest_submission_by_student.get(item["studentUserId"], ""),
                str(item.get("submittedAt", "")),
            )
        return chapter_rankings, student_subject_map, student_activity, latest_submission_by_student, weak_tag_counter

    def _build_mastery_rows(
        self,
        student_subject_map: Dict[Tuple[str, str], List[Dict[str, object]]],
        question_count_by_subject: Dict[str, int],
        average_duration: float,
    ) -> List[Dict[str, object]]:
        mastery_rows: List[Dict[str, object]] = []
        for key, rows in student_subject_map.items():
            student_user_id, subject_id = key
            answered = len(rows)
            correct = len([row for row in rows if row["isCorrect"]])
            accuracy = correct / answered if answered else 0.0
            subject_average_duration = sum(row["answerDurationSec"] for row in rows) / answered if answered else average_duration
            speed = 1.0 if subject_average_duration <= 0 else min(1.0, average_duration / subject_average_duration)
            pool_total = question_count_by_subject.get(subject_id, answered or 1)
            frequency = min(1.0, answered / pool_total)
            mastery_rows.append(
                {
                    "studentUserId": student_user_id,
                    "subjectId": subject_id,
                    "accuracy": round(accuracy, 4),
                    "speed": round(speed, 4),
                    "frequency": round(frequency, 4),
                    "mastery": round((accuracy * 0.6) + (speed * 0.2) + (frequency * 0.2), 4),
                }
            )
        return mastery_rows

    def _ordered_chapter_rankings(self, chapter_rankings: Dict[str, Dict[str, object]]) -> List[Dict[str, object]]:
        for row in chapter_rankings.values():
            answer_count = int(row["answerCount"]) or 1
            row["wrongRate"] = round(int(row["wrongCount"]) / answer_count, 4)
        return sorted(
            chapter_rankings.values(),
            key=lambda item: (-int(item["wrongCount"]), item["subjectId"], item["chapter"]),
        )

    def _build_student_rankings(
        self,
        mastery_rows: List[Dict[str, object]],
        latest_submission_by_student: Dict[str, str],
    ) -> Tuple[List[Dict[str, object]], int, int]:
        student_rankings_map: Dict[str, Dict[str, object]] = {}
        for row in mastery_rows:
            target = student_rankings_map.setdefault(
                row["studentUserId"],
                {"studentUserId": row["studentUserId"], "masteryTotal": 0.0, "subjectCount": 0},
            )
            target["masteryTotal"] += float(row["mastery"])
            target["subjectCount"] += 1
        student_rankings: List[Dict[str, object]] = []
        mastered_student_count = 0
        at_risk_student_count = 0
        for student_user_id, row in student_rankings_map.items():
            subject_count = int(row["subjectCount"]) or 1
            average_mastery = round(float(row["masteryTotal"]) / subject_count, 4)
            if average_mastery >= 0.8:
                mastered_student_count += 1
            if average_mastery < 0.6:
                at_risk_student_count += 1
            student_rankings.append(
                {
                    "studentUserId": student_user_id,
                    "averageMastery": average_mastery,
                    "subjectCount": int(row["subjectCount"]),
                    "latestSubmittedAt": latest_submission_by_student.get(student_user_id, ""),
                }
            )
        student_rankings.sort(key=lambda item: (-float(item["averageMastery"]), item["studentUserId"]))
        return student_rankings, mastered_student_count, at_risk_student_count

    def _build_low_activity_students(
        self,
        student_activity: Dict[str, int],
        latest_submission_by_student: Dict[str, str],
    ) -> List[Dict[str, object]]:
        return [
            {
                "studentUserId": student_user_id,
                "activityCount": count,
                "latestSubmittedAt": latest_submission_by_student.get(student_user_id, ""),
            }
            for student_user_id, count in sorted(student_activity.items(), key=lambda item: (item[1], item[0]))[:5]
        ]

    def _build_weak_knowledge_tags(self, weak_tag_counter: Dict[str, int]) -> List[Dict[str, object]]:
        return [
            {"knowledgeTag": tag, "wrongCount": count}
            for tag, count in sorted(weak_tag_counter.items(), key=lambda item: (-item[1], item[0]))[:8]
            if count > 0
        ]

    def _build_analytics_export_lines(self, summary: Dict[str, object], export_format: str) -> List[str]:
        if export_format == "pdf":
            return [
                "学情分析报告",
                f"timeRangeLabel: {summary['timeRangeLabel']}",
                f"studentCount: {summary['studentCount']}",
                f"coverageRate: {summary['coverageRate']}",
                f"averageAccuracy: {summary['averageAccuracy']}",
                f"averageAnswerDurationSec: {summary['averageAnswerDurationSec']}",
                f"aiReport: {summary['aiReport']}",
            ]
        lines = [
            "metric,value",
            f"timeRangeLabel,{self._csv_cell(summary['timeRangeLabel'])}",
            f"studentCount,{summary['studentCount']}",
            f"activeStudentCount,{summary['activeStudentCount']}",
            f"coverageRate,{summary['coverageRate']}",
            f"averageAccuracy,{summary['averageAccuracy']}",
            f"averageAnswerDurationSec,{summary['averageAnswerDurationSec']}",
            "",
            "studentUserId,subjectId,accuracy,speed,frequency,mastery",
        ]
        for row in summary["mastery"]:
            lines.append(
                ",".join(
                    [
                        row["studentUserId"],
                        row["subjectId"],
                        str(row["accuracy"]),
                        str(row["speed"]),
                        str(row["frequency"]),
                        str(row["mastery"]),
                    ]
                )
            )
        return lines

    def _extract_analytics_payload(self, question: Dict[str, str]) -> Dict[str, object]:
        ext_json = self._load_json_object(question["extJson"])
        record = ext_json.get("studentRecord", {})
        record_ext = self._load_json_object(record.get("extJson", "{}"))
        chapter_practice = record_ext.get("chapterPractice", {})
        answer_duration = int(chapter_practice.get("answerDurationSec", 0))
        return {
            "studentUserId": record.get("studentUserId", ""),
            "subjectId": self._question_subject_id(question),
            "chapter": self._question_chapter(question),
            "examCategoryCode": ext_json.get("examCategoryCode", ""),
            "jointExamGroupCode": ext_json.get("jointExamGroupCode", ""),
            "subjectCode": ext_json.get("subjectCode", ""),
            "knowledgeTags": self._question_knowledge_tags(question),
            "isCorrect": bool(chapter_practice.get("isCorrect", False)),
            "answerDurationSec": answer_duration,
            "submittedAt": str(chapter_practice.get("submittedAt", "")),
        }

    def _enrich_analytics_record(self, question: Dict[str, str]) -> Dict[str, str]:
        enriched = dict(question)
        ext_json = self._load_json_object(enriched["extJson"])
        payload = self._extract_analytics_payload(question)
        ext_json["analytics"] = payload
        enriched["extJson"] = self._dump_json(ext_json)
        return enriched

    def _filter_analytics_by_dates(self, records: List[Dict[str, str]], filters: Dict[str, str]) -> List[Dict[str, str]]:
        start_date = filters.get("startDate", "").strip()
        end_date = filters.get("endDate", "").strip()
        if not start_date and not end_date:
            return records
        matched: List[Dict[str, str]] = []
        for question in records:
            payload = self._extract_analytics_payload(question)
            submitted_at = payload.get("submittedAt", "")
            submitted_date = submitted_at[:10] if submitted_at else ""
            if start_date and submitted_date and submitted_date < start_date:
                continue
            if end_date and submitted_date and submitted_date > end_date:
                continue
            matched.append(question)
        return matched

    def _build_ai_analytics_report(
        self,
        chapter_rankings: List[Dict[str, object]],
        mastery_rows: List[Dict[str, object]],
        weak_knowledge_tags: List[Dict[str, object]],
        low_activity_students: List[Dict[str, object]],
    ) -> str:
        weakest_chapter = chapter_rankings[0]["chapter"] if chapter_rankings else "暂无"
        weakest_tag = weak_knowledge_tags[0]["knowledgeTag"] if weak_knowledge_tags else "暂无"
        lowest_mastery = min((item["mastery"] for item in mastery_rows), default=0.0)
        low_activity = low_activity_students[0]["studentUserId"] if low_activity_students else "暂无"
        return (
            f"当前最需要优先干预的章节是 {weakest_chapter}，"
            f"高频薄弱知识点集中在 {weakest_tag}，"
            f"最低掌握度约为 {lowest_mastery}。"
            f"建议优先提醒 {low_activity} 完成刷题与错题复盘。"
        )

    def _parse_optional_iso_datetime(self, value: object) -> Optional[datetime]:
        candidate = str(value or "").strip()
        if not candidate:
            return None
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _build_wrong_book_review_status(self, wrong_book: Dict[str, object], chapter_practice: Dict[str, object]) -> Dict[str, object]:
        post_wrong_attempt_count = max(0, int(wrong_book.get("postWrongAttemptCount", 0)))
        post_wrong_correct_count = max(0, int(wrong_book.get("postWrongCorrectCount", 0)))
        submit_count = max(0, int(chapter_practice.get("submitCount", 0)))
        review_count = max(0, int(wrong_book.get("reviewCount", 0)))
        if post_wrong_attempt_count <= 0 and submit_count > 1:
            post_wrong_attempt_count = submit_count - 1
        if post_wrong_correct_count <= 0 and bool(chapter_practice.get("isCorrect")) and post_wrong_attempt_count > 0:
            post_wrong_correct_count = 1
        review_accuracy_rate = round(
            (post_wrong_correct_count / post_wrong_attempt_count) if post_wrong_attempt_count > 0 else 0.0,
            4,
        )
        status_key = "fragile"
        status_label = "生疏"
        if post_wrong_attempt_count >= 2 and post_wrong_correct_count >= 2 and review_accuracy_rate >= 0.8:
            status_key = "mastered"
            status_label = "已斩获"
        elif post_wrong_correct_count >= 1 or review_accuracy_rate >= 0.5:
            status_key = "familiar"
            status_label = "熟悉"
        return {
            "reviewStatusKey": status_key,
            "reviewStatusLabel": status_label,
            "reviewAccuracyRate": review_accuracy_rate,
            "postWrongAttemptCount": post_wrong_attempt_count,
            "postWrongCorrectCount": post_wrong_correct_count,
            "reviewCount": review_count,
            "isHarvested": status_key == "mastered",
        }

    def _build_joint_group_benchmark_payload(self, mastery: float, joint_group_average_accuracy: float) -> Dict[str, object]:
        accuracy_gap = round(joint_group_average_accuracy - mastery, 4)
        if accuracy_gap >= 0.3:
            return {
                "jointGroupAccuracyGap": accuracy_gap,
                "benchmarkStatusText": "明显落后同组，需立刻补齐",
                "benchmarkTagType": "danger",
                "benchmarkRiskBadgeText": "同组高风险",
                "showBenchmarkRiskBadge": True,
            }
        if accuracy_gap >= 0.1:
            return {
                "jointGroupAccuracyGap": accuracy_gap,
                "benchmarkStatusText": "略落后同组，建议优先回看",
                "benchmarkTagType": "warning",
                "benchmarkRiskBadgeText": "",
                "showBenchmarkRiskBadge": False,
            }
        if accuracy_gap <= -0.1:
            return {
                "jointGroupAccuracyGap": accuracy_gap,
                "benchmarkStatusText": "已超越同组",
                "benchmarkTagType": "success",
                "benchmarkRiskBadgeText": "",
                "showBenchmarkRiskBadge": False,
            }
        return {
            "jointGroupAccuracyGap": accuracy_gap,
            "benchmarkStatusText": "接近同组均值",
            "benchmarkTagType": "info",
            "benchmarkRiskBadgeText": "",
            "showBenchmarkRiskBadge": False,
        }

    def _infer_wrong_question_inducer(self, question: Dict[str, str]) -> Dict[str, str]:
        ext_json = self._load_json_object(question.get("extJson", "{}"))
        content = " ".join(
            [
                str(question.get("stem", "")).strip(),
                str(ext_json.get("analysis", "")).strip(),
                str(question.get("answer", "")).strip(),
            ]
        )
        normalized_content = content.lower()
        calculation_markers = (
            "计算", "公式", "求", "解", "化简", "导数", "积分", "方程", "函数", "运算", "概率", "数值", "公式记忆"
        )
        concept_markers = (
            "概念", "理论", "定义", "理解", "性质", "特点", "原则", "内涵", "原因", "作用", "体现", "说明", "辨析"
        )
        has_calculation_signal = any(marker in content for marker in calculation_markers) or bool(re.search(r"[0-9][0-9\.\+\-\*/=%]*", normalized_content))
        has_concept_signal = any(marker in content for marker in concept_markers)
        if has_calculation_signal and not has_concept_signal:
            return {"errorInducerType": "CALCULATION", "errorInducerLabel": "计算题", "chapterSuggestion": "加强公式记忆"}
        return {"errorInducerType": "CONCEPT", "errorInducerLabel": "概念题", "chapterSuggestion": "加强理论理解"}

    def _build_student_error_book_summary_payload(
        self,
        actor: Actor,
        filters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, object]:
        scope_filters = self._build_student_error_book_scope_filters(actor, filters)
        selected_subject_code = str(scope_filters.get("subjectCode", "")).strip()
        joint_exam_group_code = str(scope_filters.get("jointExamGroupCode", "")).strip()

        profile = self._get_student_profile(actor.user_id)
        joint_exam_group = get_joint_exam_group(joint_exam_group_code)
        core_subjects = self._build_student_core_subjects(joint_exam_group, actor.user_id)
        subject_name_map = {
            str(item.get("subjectCode", "")).strip(): str(item.get("subjectName", "")).strip() or str(item.get("subjectCode", "")).strip()
            for item in core_subjects
            if str(item.get("subjectCode", "")).strip()
        }
        subject_id_map = {
            str(item.get("subjectCode", "")).strip(): str(item.get("subjectId", "")).strip()
            for item in core_subjects
            if str(item.get("subjectCode", "")).strip()
        }

        all_wrong_questions, _ = self.list_wrong_book_questions(1, 500, actor, scope_filters)
        question_map = {
            str(item.get("id", "")).strip(): item
            for item in all_wrong_questions
            if str(item.get("id", "")).strip()
        }
        wrong_book_question_ids = set(question_map.keys())

        knowledge_rows = self.repository.list_knowledge(
            "ENABLED",
            {
                "examCategoryCode": str(scope_filters.get("examCategoryCode", "")).strip() or str(profile.get("examCategoryCode", "")).strip(),
                "jointExamGroupCode": joint_exam_group_code,
                "subjectCode": "",
            },
        )
        knowledge_map = {
            str(item.get("id", "")).strip(): item
            for item in knowledge_rows
            if str(item.get("id", "")).strip()
        }
        point_knowledge_ids = {
            knowledge_id
            for knowledge_id, item in knowledge_map.items()
            if int(self._load_json_object(str(item.get("extJson", "{}"))).get("level", 0) or 0) >= 5
        }
        question_count_by_knowledge = self._knowledge_question_count_map(point_knowledge_ids)
        mastery_by_knowledge = self._knowledge_mastery_map(
            point_knowledge_ids,
            question_count_by_knowledge,
            viewer_student_user_id=actor.user_id,
            joint_exam_group_code=joint_exam_group_code,
        )

        knowledge_subject_map: Dict[str, str] = {}
        knowledge_point_name_map: Dict[str, str] = {}
        total_point_count_by_subject: Dict[str, int] = {}
        for knowledge_id in point_knowledge_ids:
            knowledge = knowledge_map.get(knowledge_id, {})
            ext_json = self._load_json_object(str(knowledge.get("extJson", "{}")))
            subject_code = str(ext_json.get("subjectCode", "")).strip()
            if not subject_code:
                continue
            knowledge_subject_map[knowledge_id] = subject_code
            knowledge_point_name_map[knowledge_id] = str(knowledge.get("name", "")).strip() or knowledge_id
            total_point_count_by_subject[subject_code] = total_point_count_by_subject.get(subject_code, 0) + 1

        history_rows = self._collect_graph_history_rows(
            actor.user_id,
            joint_exam_group_code=joint_exam_group_code,
        )
        joint_group_history_rows = self._collect_graph_history_rows(
            viewer_student_user_id="",
            joint_exam_group_code=joint_exam_group_code,
        )
        practiced_points_by_subject: Dict[str, set[str]] = {}
        for row in history_rows:
            knowledge_id = str(row.get("knowledgeId", "")).strip()
            subject_code = knowledge_subject_map.get(knowledge_id, "")
            if not subject_code:
                continue
            practiced_points_by_subject.setdefault(subject_code, set()).add(knowledge_id)

        joint_group_accuracy_map: Dict[str, Dict[str, int]] = {}
        for row in joint_group_history_rows:
            knowledge_id = str(row.get("knowledgeId", "")).strip()
            if not knowledge_id:
                continue
            stats = joint_group_accuracy_map.setdefault(knowledge_id, {"correct": 0, "total": 0})
            stats["total"] += 1
            if bool(row.get("isCorrect", False)):
                stats["correct"] += 1

        question_insights: List[Dict[str, object]] = []
        insights_by_subject: Dict[str, List[Dict[str, object]]] = {}
        chapter_counter_by_subject: Dict[str, Dict[str, Dict[str, object]]] = {}
        point_counter_by_subject: Dict[str, Dict[str, Dict[str, object]]] = {}
        chapter_inducer_counter_by_subject: Dict[str, Dict[str, Dict[str, int]]] = {}
        now = datetime.now(timezone.utc)

        for question in all_wrong_questions:
            question_id = str(question.get("id", "")).strip()
            knowledge_id = str(question.get("knowledgeId", "")).strip()
            ext_json = self._load_json_object(question.get("extJson", "{}"))
            student_state = ext_json.get("studentState", {}) if isinstance(ext_json.get("studentState", {}), dict) else {}
            wrong_book = student_state.get("wrongBook", {}) if isinstance(student_state.get("wrongBook", {}), dict) else {}
            chapter_practice = student_state.get("chapterPractice", {}) if isinstance(student_state.get("chapterPractice", {}), dict) else {}

            subject_code = str(ext_json.get("subjectCode", "")).strip() or knowledge_subject_map.get(knowledge_id, "")
            subject_name = subject_name_map.get(subject_code, subject_code)
            chapter_name = str(ext_json.get("chapter", "")).strip()
            chapter_code = str(ext_json.get("chapterCode", "")).strip()
            point_code = str(ext_json.get("pointCode", "")).strip()
            point_name = knowledge_point_name_map.get(knowledge_id, "") or point_code or knowledge_id
            mastery = float(mastery_by_knowledge.get(knowledge_id, 0.0))
            wrong_count = max(0, int(wrong_book.get("wrongCount", 0)))
            review_status = self._build_wrong_book_review_status(wrong_book, chapter_practice)
            inducer_payload = self._infer_wrong_question_inducer(question)
            joint_group_accuracy = joint_group_accuracy_map.get(knowledge_id, {})
            joint_group_average_accuracy = round(
                (int(joint_group_accuracy.get("correct", 0)) / int(joint_group_accuracy.get("total", 0)))
                if int(joint_group_accuracy.get("total", 0)) > 0
                else 0.0,
                4,
            )
            benchmark_payload = self._build_joint_group_benchmark_payload(mastery, joint_group_average_accuracy)
            submitted_at = (
                str(chapter_practice.get("submittedAt", "")).strip()
                or str(wrong_book.get("lastWrongAt", "")).strip()
                or str(wrong_book.get("collectedAt", "")).strip()
            )
            reviewed_at = str(wrong_book.get("reviewedAt", "")).strip()
            submitted_dt = self._parse_optional_iso_datetime(submitted_at)
            reviewed_dt = self._parse_optional_iso_datetime(reviewed_at)
            overdue_hours = int((now - submitted_dt).total_seconds() // 3600) if submitted_dt else 0
            is_overdue = bool(
                wrong_count >= 2
                and submitted_dt
                and overdue_hours >= 72
                and (not reviewed_dt or reviewed_dt < submitted_dt)
            )

            insight = {
                "questionId": question_id,
                "knowledgeId": knowledge_id,
                "subjectCode": subject_code,
                "subjectName": subject_name,
                "chapterCode": chapter_code,
                "chapterName": chapter_name,
                "pointCode": point_code,
                "pointName": point_name,
                "mastery": round(mastery, 4),
                "masteryScore": int(round(mastery * 100)),
                "wrongCount": wrong_count,
                "submittedAt": submitted_at,
                "reviewedAt": reviewed_at,
                "overdueHours": overdue_hours,
                "isOverdue72h": is_overdue,
                "isPendingRepair": bool(wrong_count > 3 and mastery < 0.4),
                **review_status,
                **inducer_payload,
                "jointGroupAverageAccuracy": joint_group_average_accuracy,
                **benchmark_payload,
            }
            question_insights.append(insight)
            if subject_code:
                insights_by_subject.setdefault(subject_code, []).append(insight)

                chapter_key = chapter_code or chapter_name or "-"
                chapter_counter = chapter_counter_by_subject.setdefault(subject_code, {})
                chapter_row = chapter_counter.setdefault(
                    chapter_key,
                    {
                        "chapterCode": chapter_code,
                        "chapterName": chapter_name or chapter_code or "未标注章节",
                        "wrongCount": 0,
                    },
                )
                chapter_row["wrongCount"] += 1

                chapter_inducer_counter = chapter_inducer_counter_by_subject.setdefault(subject_code, {})
                chapter_inducer_row = chapter_inducer_counter.setdefault(
                    chapter_key,
                    {"CALCULATION": 0, "CONCEPT": 0},
                )
                chapter_inducer_row[str(inducer_payload.get("errorInducerType", "CONCEPT"))] = int(
                    chapter_inducer_row.get(str(inducer_payload.get("errorInducerType", "CONCEPT")), 0)
                ) + 1

                point_key = knowledge_id or point_code or question_id
                point_counter = point_counter_by_subject.setdefault(subject_code, {})
                point_row = point_counter.setdefault(
                    point_key,
                    {
                        "knowledgeId": knowledge_id,
                        "pointCode": point_code,
                        "pointName": point_name,
                        "wrongCount": 0,
                        "mastery": round(mastery, 4),
                    },
                )
                point_row["wrongCount"] += wrong_count or 1
                point_row["mastery"] = min(float(point_row.get("mastery", mastery)), mastery)

        ordered_subject_codes: List[str] = []
        for item in core_subjects:
            subject_code = str(item.get("subjectCode", "")).strip()
            if subject_code and subject_code not in ordered_subject_codes:
                ordered_subject_codes.append(subject_code)
        for subject_code in sorted(insights_by_subject.keys()):
            if subject_code not in ordered_subject_codes:
                ordered_subject_codes.append(subject_code)

        subject_rows: List[Dict[str, object]] = []
        for subject_code in ordered_subject_codes:
            subject_insights = sorted(
                insights_by_subject.get(subject_code, []),
                key=lambda item: (float(item.get("mastery", 0.0)), -int(item.get("wrongCount", 0)), str(item.get("questionId", ""))),
            )
            practiced_point_count = len(practiced_points_by_subject.get(subject_code, set()))
            wrong_point_count = len(point_counter_by_subject.get(subject_code, {}))
            total_point_count = int(total_point_count_by_subject.get(subject_code, 0))
            top_chapters = sorted(
                chapter_counter_by_subject.get(subject_code, {}).values(),
                key=lambda item: (-int(item.get("wrongCount", 0)), str(item.get("chapterCode", "")), str(item.get("chapterName", ""))),
            )[:3]
            review_warnings = sorted(
                [item for item in subject_insights if item.get("isOverdue72h")],
                key=lambda item: (-int(item.get("wrongCount", 0)), -int(item.get("overdueHours", 0)), float(item.get("mastery", 0.0))),
            )
            weakest_question_ids = [str(item.get("questionId", "")) for item in subject_insights[:10] if str(item.get("questionId", "")).strip()]
            weakest_mastery = float(subject_insights[0]["mastery"]) if subject_insights else 0.0
            repair_suggestions = []
            for point_row in sorted(
                point_counter_by_subject.get(subject_code, {}).values(),
                key=lambda item: (-int(item.get("wrongCount", 0)), float(item.get("mastery", 0.0)), str(item.get("pointCode", ""))),
            ):
                wrong_count = int(point_row.get("wrongCount", 0))
                mastery = float(point_row.get("mastery", 0.0))
                if wrong_count <= 3 or mastery >= 0.4:
                    continue
                point_name = str(point_row.get("pointName", "")).strip() or str(point_row.get("pointCode", "")).strip() or str(point_row.get("knowledgeId", "")).strip()
                repair_suggestions.append(
                    {
                        "knowledgeId": str(point_row.get("knowledgeId", "")).strip(),
                        "pointCode": str(point_row.get("pointCode", "")).strip(),
                        "pointName": point_name,
                        "wrongCount": wrong_count,
                        "mastery": round(mastery, 4),
                        "message": f"该考点属于【底层逻辑错误】，建议回看大纲定义：{point_name}",
                    }
                )
            subject_rows.append(
                {
                    "subjectCode": subject_code,
                    "subjectId": subject_id_map.get(subject_code, subject_id_from_subject_code(subject_code)),
                    "subjectName": subject_name_map.get(subject_code, subject_code),
                    "wrongCount": len(subject_insights),
                    "redDotCount": len(subject_insights),
                    "totalPointCount": total_point_count,
                    "practicedPointCount": practiced_point_count,
                    "wrongPointCount": wrong_point_count,
                    "knowledgeCoverageRate": round(practiced_point_count / total_point_count, 4) if total_point_count else 0.0,
                    "errorCoverageRate": round(wrong_point_count / total_point_count, 4) if total_point_count else 0.0,
                    "topChapters": top_chapters,
                    "overdueQuestionCount": len(review_warnings),
                    "lowestMastery": round(weakest_mastery, 4),
                    "weakestQuestionIds": weakest_question_ids,
                    "chapterInducerSuggestions": [
                        {
                            "chapterCode": str(item.get("chapterCode", "")).strip(),
                            "chapterName": str(item.get("chapterName", "")).strip(),
                            "dominantType": (
                                "CALCULATION"
                                if int((chapter_inducer_counter_by_subject.get(subject_code, {}).get(str(item.get("chapterCode", "")).strip() or str(item.get("chapterName", "")).strip(), {}) or {}).get("CALCULATION", 0))
                                >= int((chapter_inducer_counter_by_subject.get(subject_code, {}).get(str(item.get("chapterCode", "")).strip() or str(item.get("chapterName", "")).strip(), {}) or {}).get("CONCEPT", 0))
                                else "CONCEPT"
                            ),
                            "suggestion": (
                                "加强公式记忆"
                                if int((chapter_inducer_counter_by_subject.get(subject_code, {}).get(str(item.get("chapterCode", "")).strip() or str(item.get("chapterName", "")).strip(), {}) or {}).get("CALCULATION", 0))
                                >= int((chapter_inducer_counter_by_subject.get(subject_code, {}).get(str(item.get("chapterCode", "")).strip() or str(item.get("chapterName", "")).strip(), {}) or {}).get("CONCEPT", 0))
                                else "加强理论理解"
                            ),
                        }
                        for item in top_chapters
                    ],
                    "aiSuggestions": {
                        "repairSuggestions": repair_suggestions[:3],
                        "practiceSuggestion": {
                            "questionIds": weakest_question_ids[:10],
                            "questionCount": len(weakest_question_ids[:10]),
                            "lowestMastery": round(weakest_mastery, 4),
                        },
                        "reviewWarnings": review_warnings[:5],
                    },
                }
            )

        selected_row = {}
        if selected_subject_code:
            selected_row = next((item for item in subject_rows if str(item.get("subjectCode", "")) == selected_subject_code), {})
        if not selected_row:
            selected_row = next((item for item in subject_rows if int(item.get("wrongCount", 0)) > 0), subject_rows[0] if subject_rows else {})
        selected_subject_code = str(selected_row.get("subjectCode", "")).strip()
        current_question_insights = sorted(
            insights_by_subject.get(selected_subject_code, []),
            key=lambda item: (float(item.get("mastery", 0.0)), -int(item.get("wrongCount", 0)), str(item.get("questionId", ""))),
        )
        ordered_question_insights = sorted(
            question_insights,
            key=lambda item: (
                str(item.get("subjectCode", "")),
                float(item.get("mastery", 0.0)),
                -int(item.get("wrongCount", 0)),
                str(item.get("questionId", "")),
            ),
        )

        return {
            "policyVersionCode": POLICY_VERSION_CODE,
            "examCategoryCode": str(scope_filters.get("examCategoryCode", "")).strip(),
            "jointExamGroupCode": joint_exam_group_code,
            "selectedSubjectCode": selected_subject_code,
            "subjectRows": subject_rows,
            "questionInsights": ordered_question_insights,
            "currentQuestionInsights": current_question_insights,
            "currentSubject": selected_row,
            "_questionMap": question_map,
            "_wrongBookQuestionIds": wrong_book_question_ids,
        }
