from __future__ import annotations

from app.content_baseline import subject_code_from_subject_id
from app.service_shared import *

EXAM_TASK_TYPES = {"CHAPTER", "SPECIAL", "PAPER", "SUBJECTIVE_MARKING"}
EXAM_TASK_STATUSES = {"DRAFT", "PUBLISHED", "CLOSED"}
EXAM_TASK_ASSIGNMENT_STATUSES = {
    "NOT_STARTED",
    "IN_PROGRESS",
    "SUBMITTED",
    "PENDING_REVIEW",
    "COMPLETED",
    "EXPIRED",
}


class ExamTaskServiceMixin:
    def _resolve_exam_task_teacher_name(self, actor: Actor) -> str:
        managed_user = self._get_managed_user(actor.user_id) or {}
        name = str(managed_user.get("name", "")).strip()
        if name:
            return name
        user = self.repository.get_user_by_id(actor.user_id) or {}
        user_ext = self._load_json_object(user.get("extJson", "{}"))
        return str(user_ext.get("name", "")).strip() or actor.user_id

    def _resolve_exam_task_scope(
        self,
        payload: Dict[str, object],
        actor: Actor,
    ) -> tuple[str, str, str, str]:
        subject_id = str(payload.get("subjectId") or "").strip()
        exam_category_code = str(payload.get("examCategoryCode") or "").strip()
        joint_exam_group_code = str(payload.get("jointExamGroupCode") or "").strip()
        subject_code = str(payload.get("subjectCode") or "").strip()
        if not subject_id and subject_code:
            subject_id = subject_id_from_subject_code(subject_code)
        self._assert_actor_scope_write_access(actor, exam_category_code, joint_exam_group_code)
        return subject_id, exam_category_code, joint_exam_group_code, subject_code

    def _resolve_exam_task_students(
        self,
        class_ids: List[str],
        student_ids: List[str],
        actor: Actor,
    ) -> List[Dict[str, object]]:
        students_by_id: Dict[str, Dict[str, object]] = {}
        for class_id in class_ids:
            for student in self._list_teacher_students_for_class(class_id, actor):
                student_user_id = str(student.get("userId", "")).strip()
                if not student_user_id:
                    continue
                students_by_id[student_user_id] = {
                    "studentUserId": student_user_id,
                    "studentName": str(student.get("name", "")).strip() or str(student.get("studentName", "")).strip() or student_user_id,
                    "classId": str(student.get("classId", "")).strip(),
                    "className": str(student.get("className", "")).strip(),
                }
        for student_user_id in student_ids:
            user = self.repository.get_user_by_id(student_user_id) or {}
            user_ext = self._load_json_object(user.get("extJson", "{}"))
            student_profile = self._get_student_profile(student_user_id)
            joint_exam_group_code = str(student_profile.get("jointExamGroupCode", "")).strip()
            students_by_id[student_user_id] = {
                "studentUserId": student_user_id,
                "studentName": str(user_ext.get("name", "")).strip() or student_user_id,
                "classId": joint_exam_group_code,
                "className": str((get_joint_exam_group(joint_exam_group_code) or {}).get("jointExamGroupName", "")).strip(),
            }
        return list(students_by_id.values())

    def _build_exam_task_targets(
        self,
        task_id: str,
        class_ids: List[str],
        students: List[Dict[str, object]],
        now_iso: str,
    ) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for class_id in class_ids:
            class_meta = get_joint_exam_group(class_id) or {}
            rows.append(
                {
                    "id": f"exam-task-target-{uuid.uuid4().hex[:8]}",
                    "taskId": task_id,
                    "targetType": "CLASS",
                    "targetId": class_id,
                    "targetName": str(class_meta.get("jointExamGroupName", "")).strip() or class_id,
                    "createTime": now_iso,
                }
            )
        for student in students:
            student_user_id = str(student.get("studentUserId", "")).strip()
            if not student_user_id:
                continue
            rows.append(
                {
                    "id": f"exam-task-target-{uuid.uuid4().hex[:8]}",
                    "taskId": task_id,
                    "targetType": "STUDENT",
                    "targetId": student_user_id,
                    "targetName": str(student.get("studentName", "")).strip() or student_user_id,
                    "createTime": now_iso,
                }
            )
        return rows

    def _build_exam_task_assignments(
        self,
        task_id: str,
        students: List[Dict[str, object]],
        allow_redo: bool,
        due_at: str,
        target_question_count: int,
        now_iso: str,
    ) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for student in students:
            student_user_id = str(student.get("studentUserId", "")).strip()
            if not student_user_id:
                continue
            rows.append(
                {
                    "id": f"exam-assignment-{uuid.uuid4().hex[:8]}",
                    "taskId": task_id,
                    "studentUserId": student_user_id,
                    "status": "NOT_STARTED",
                    "score": 0,
                    "totalScore": 0,
                    "startedAt": "",
                    "submittedAt": "",
                    "completedAt": "",
                    "expiredAt": "",
                    "lastPaperId": "",
                    "redoCount": 0,
                    "maxRedoCount": 1 if allow_redo else 0,
                    "extJson": {
                        "studentName": str(student.get("studentName", "")).strip(),
                        "classId": str(student.get("classId", "")).strip(),
                        "className": str(student.get("className", "")).strip(),
                        "dueAt": due_at,
                        "progressCount": 0,
                        "targetQuestionCount": target_question_count,
                        "completedQuestionIds": [],
                        "pendingReviewQuestionIds": [],
                    },
                    "createTime": now_iso,
                    "updateTime": now_iso,
                }
            )
        return rows

    def _build_exam_task_summary(self, task: Dict[str, object]) -> Dict[str, object]:
        targets = self.repository.list_exam_task_targets(str(task.get("id", "")).strip())
        assignments = self.repository.list_exam_task_assignments_for_task(str(task.get("id", "")).strip())
        summary = {
            "total": len(assignments),
            "notStarted": 0,
            "inProgress": 0,
            "submitted": 0,
            "pendingReview": 0,
            "completed": 0,
            "expired": 0,
        }
        for assignment in assignments:
            status = str(assignment.get("status", "")).strip()
            if status == "NOT_STARTED":
                summary["notStarted"] += 1
            elif status == "IN_PROGRESS":
                summary["inProgress"] += 1
            elif status == "SUBMITTED":
                summary["submitted"] += 1
            elif status == "PENDING_REVIEW":
                summary["pendingReview"] += 1
            elif status == "COMPLETED":
                summary["completed"] += 1
            elif status == "EXPIRED":
                summary["expired"] += 1
        return {
            **task,
            "targets": targets,
            "assignmentSummary": summary,
        }

    def list_exam_tasks(self, filters: Dict[str, str], page: int, size: int, actor: Actor) -> Tuple[List[Dict[str, object]], int]:
        rows, total = self.repository.list_exam_tasks(filters, page, size, teacher_user_id=actor.user_id if actor.role == ROLE_TEACHER else "")
        return [self._build_exam_task_summary(row) for row in rows], total

    def create_exam_task(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        task_name = str(payload.get("taskName") or "").strip()
        task_type = str(payload.get("taskType") or "").strip().upper()
        if not task_name:
            raise validation_failed("taskName 不能为空。")
        if task_type not in EXAM_TASK_TYPES:
            raise validation_failed("taskType 仅支持 CHAPTER、SPECIAL、PAPER、SUBJECTIVE_MARKING。")
        status = str(payload.get("status", "PUBLISHED")).strip().upper() or "PUBLISHED"
        if status not in EXAM_TASK_STATUSES:
            raise validation_failed("status 仅支持 DRAFT、PUBLISHED、CLOSED。")
        class_ids = self._deduplicate_ids(payload.get("classIds") or [], "classIds")
        student_ids = self._deduplicate_ids(payload.get("studentIds") or [], "studentIds")
        if not class_ids and not student_ids:
            raise validation_failed("classIds 和 studentIds 至少提供一项。")
        due_at = str(payload.get("dueAt") or "").strip()
        subject_id, exam_category_code, joint_exam_group_code, subject_code = self._resolve_exam_task_scope(payload, actor)
        students = self._resolve_exam_task_students(class_ids, student_ids, actor)
        if not students:
            raise validation_failed("当前筛选范围下没有可布置的学生。")
        now_iso = self._now_iso()
        task_id = str(payload.get("id") or payload.get("taskId") or "").strip() or f"exam-task-{uuid.uuid4().hex[:8]}"
        allow_redo = bool(payload.get("allowRedo", False))
        target_question_count = int(payload.get("targetQuestionCount") or 1)
        source_type = str(payload.get("sourceType") or "").strip().upper()
        source_id = str(payload.get("sourceId") or "").strip()
        source_label = str(payload.get("sourceLabel") or "").strip()
        task_row = {
            "id": task_id,
            "taskName": task_name,
            "taskType": task_type,
            "subjectId": subject_id,
            "examCategoryCode": exam_category_code,
            "jointExamGroupCode": joint_exam_group_code,
            "subjectCode": subject_code,
            "sourceType": source_type,
            "sourceId": source_id,
            "sourceLabel": source_label,
            "teacherUserId": actor.user_id,
            "teacherName": self._resolve_exam_task_teacher_name(actor),
            "description": str(payload.get("description", "")).strip(),
            "allowRedo": allow_redo,
            "dueAt": due_at,
            "status": status,
            "extJson": {
                "classIds": class_ids,
                "studentIds": [str(item.get("studentUserId", "")).strip() for item in students],
                "targetQuestionCount": target_question_count,
            },
            "createTime": now_iso,
            "updateTime": now_iso,
        }
        saved_task = self.repository.upsert_exam_task(task_row)
        self.repository.replace_exam_task_targets(task_id, self._build_exam_task_targets(task_id, class_ids, students, now_iso))
        for assignment in self._build_exam_task_assignments(task_id, students, allow_redo, due_at, target_question_count, now_iso):
            self.repository.upsert_exam_task_assignment(assignment)
        return self._build_exam_task_summary(saved_task)

    def get_exam_task_detail(self, task_id: str, actor: Actor) -> Dict[str, object]:
        task = self.repository.get_exam_task(task_id)
        if not task:
            raise not_found("考试任务不存在。")
        if actor.role == ROLE_TEACHER and str(task.get("teacherUserId", "")).strip() != actor.user_id:
            raise forbidden("仅可查看本人创建的考试任务。")
        detail = self._build_exam_task_summary(task)
        detail["assignments"] = self.repository.list_exam_task_assignments_for_task(task_id)
        return detail

    def _parse_iso_datetime_or_none(self, value: str) -> Optional[datetime]:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        try:
            return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _is_exam_task_assignment_expired(self, task: Dict[str, object], assignment: Dict[str, object]) -> bool:
        status = str(assignment.get("status", "")).strip()
        if status in {"COMPLETED", "PENDING_REVIEW", "SUBMITTED", "EXPIRED"}:
            return status == "EXPIRED"
        due_at = self._parse_iso_datetime_or_none(str(task.get("dueAt", "")).strip())
        if due_at is None:
            return False
        return due_at <= datetime.now(timezone.utc)

    def _ensure_exam_task_assignment_fresh(self, task: Dict[str, object], assignment: Dict[str, object]) -> Dict[str, object]:
        if not self._is_exam_task_assignment_expired(task, assignment):
            return assignment
        if str(assignment.get("status", "")).strip() == "EXPIRED":
            return assignment
        next_assignment = dict(assignment)
        now_iso = self._now_iso()
        next_assignment["status"] = "EXPIRED"
        next_assignment["expiredAt"] = now_iso
        next_assignment["updateTime"] = now_iso
        return self.repository.upsert_exam_task_assignment(next_assignment)

    def _build_exam_task_assignment_action(self, task: Dict[str, object], assignment: Dict[str, object]) -> Dict[str, object]:
        subject_code = str(task.get("subjectCode", "")).strip()
        source_id = str(task.get("sourceId", "")).strip()
        source_label = str(task.get("sourceLabel", "")).strip()
        common_query = {
            "subjectCode": subject_code,
            "practiceSource": "TASK",
            "practiceSourceLabel": "考试任务进入",
            "assignmentId": str(assignment.get("id", "")).strip(),
        }
        task_type = str(task.get("taskType", "")).strip()
        if task_type == "CHAPTER":
            return {"actionPath": "/student/practice/chapter", "actionQuery": {**common_query, "knowledgeId": source_id}}
        if task_type == "SPECIAL":
            return {"actionPath": "/student/practice/free", "actionQuery": {**common_query, "knowledgeId": source_id}}
        return {"actionPath": "/student/practice/mock", "actionQuery": {**common_query, "paperId": source_id, "paperName": source_label}}

    def list_student_exam_tasks(self, filters: Dict[str, str], page: int, size: int, actor: Actor) -> Tuple[List[Dict[str, object]], int]:
        rows, total = self.repository.list_student_exam_task_assignments(actor.user_id, filters, page, size)
        normalized_rows: List[Dict[str, object]] = []
        for row in rows:
            task = row.get("task", {}) if isinstance(row.get("task"), dict) else {}
            assignment = self._ensure_exam_task_assignment_fresh(task, row)
            merged = {**assignment, "task": task}
            merged["effectiveStatus"] = str(assignment.get("status", "")).strip()
            merged.update(self._build_exam_task_assignment_action(task, assignment))
            normalized_rows.append(merged)
        return normalized_rows, total

    def get_student_exam_task_detail(self, assignment_id: str, actor: Actor) -> Dict[str, object]:
        assignment = self.repository.get_exam_task_assignment(assignment_id)
        if not assignment or str(assignment.get("studentUserId", "")).strip() != actor.user_id:
            raise not_found("考试任务不存在。")
        task = self.repository.get_exam_task(str(assignment.get("taskId", "")).strip())
        if not task or str(task.get("status", "")).strip() != "PUBLISHED":
            raise not_found("考试任务不存在。")
        assignment = self._ensure_exam_task_assignment_fresh(task, assignment)
        return {
            **assignment,
            "task": task,
            "effectiveStatus": str(assignment.get("status", "")).strip(),
            **self._build_exam_task_assignment_action(task, assignment),
        }

    def start_student_exam_task(self, assignment_id: str, actor: Actor) -> Dict[str, object]:
        detail = self.get_student_exam_task_detail(assignment_id, actor)
        assignment = {key: value for key, value in detail.items() if key not in {"task", "actionPath", "actionQuery", "effectiveStatus"}}
        task = detail["task"]
        current_status = str(assignment.get("status", "")).strip()
        if current_status == "EXPIRED":
            raise validation_failed("当前考试任务已过期。")
        if current_status == "COMPLETED":
            allow_redo = bool(task.get("allowRedo", False))
            redo_count = int(assignment.get("redoCount", 0))
            max_redo_count = int(assignment.get("maxRedoCount", 0))
            if not allow_redo or redo_count >= max_redo_count:
                raise validation_failed("当前考试任务不允许重做。")
            assignment["redoCount"] = redo_count + 1
        now_iso = self._now_iso()
        assignment["status"] = "IN_PROGRESS"
        assignment["startedAt"] = str(assignment.get("startedAt", "")).strip() or now_iso
        assignment["updateTime"] = now_iso
        saved_assignment = self.repository.upsert_exam_task_assignment(assignment)
        return {
            **saved_assignment,
            "task": task,
            **self._build_exam_task_assignment_action(task, saved_assignment),
        }

    def submit_student_exam_task(self, assignment_id: str, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        detail = self.get_student_exam_task_detail(assignment_id, actor)
        assignment = {key: value for key, value in detail.items() if key not in {"task", "actionPath", "actionQuery", "effectiveStatus"}}
        task = detail["task"]
        now_iso = self._now_iso()
        pending_subjective_count = int(payload.get("pendingSubjectiveCount", 0) or 0)
        ext_json = assignment.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = {}
        normalized_question_id = str(payload.get("questionId", "")).strip()
        completed_question_ids = [
            str(item).strip()
            for item in (ext_json.get("completedQuestionIds", []) if isinstance(ext_json.get("completedQuestionIds", []), list) else [])
            if str(item).strip()
        ]
        pending_review_ids = [
            str(item).strip()
            for item in (ext_json.get("pendingReviewQuestionIds", []) if isinstance(ext_json.get("pendingReviewQuestionIds", []), list) else [])
            if str(item).strip()
        ]
        if normalized_question_id and normalized_question_id not in completed_question_ids:
            completed_question_ids.append(normalized_question_id)
        if normalized_question_id:
            if pending_subjective_count > 0 and normalized_question_id not in pending_review_ids:
                pending_review_ids.append(normalized_question_id)
            if pending_subjective_count <= 0:
                pending_review_ids = [item for item in pending_review_ids if item != normalized_question_id]
        target_question_count = int(
            ext_json.get("targetQuestionCount")
            or (task.get("extJson", {}) if isinstance(task.get("extJson", {}), dict) else {}).get("targetQuestionCount")
            or 1
        )
        ext_json["completedQuestionIds"] = completed_question_ids
        ext_json["pendingReviewQuestionIds"] = pending_review_ids
        ext_json["progressCount"] = len(completed_question_ids)
        ext_json["targetQuestionCount"] = target_question_count
        next_status = "PENDING_REVIEW" if pending_review_ids or str(task.get("taskType", "")).strip() == "SUBJECTIVE_MARKING" and pending_subjective_count > 0 else "COMPLETED"
        if next_status != "PENDING_REVIEW" and len(completed_question_ids) < target_question_count:
            next_status = "IN_PROGRESS"
        assignment["status"] = next_status
        assignment["score"] = int(payload.get("score", assignment.get("score", 0)) or 0)
        assignment["totalScore"] = int(payload.get("totalScore", assignment.get("totalScore", 0)) or 0)
        assignment["lastPaperId"] = str(payload.get("paperId", assignment.get("lastPaperId", "")) or "").strip()
        assignment["submittedAt"] = str(payload.get("submittedAt", now_iso) or now_iso).strip()
        assignment["completedAt"] = assignment["submittedAt"] if next_status == "COMPLETED" else ""
        assignment["extJson"] = ext_json
        assignment["updateTime"] = now_iso
        saved_assignment = self.repository.upsert_exam_task_assignment(assignment)
        return {
            **saved_assignment,
            "task": task,
            **self._build_exam_task_assignment_action(task, saved_assignment),
        }

    def record_exam_task_practice_progress(
        self,
        assignment_id: str,
        question_id: str,
        actor: Actor,
        *,
        pending_review: bool,
    ) -> Optional[Dict[str, object]]:
        if not assignment_id:
            return None
        detail = self.get_student_exam_task_detail(assignment_id, actor)
        assignment = {key: value for key, value in detail.items() if key not in {"task", "actionPath", "actionQuery", "effectiveStatus"}}
        task = detail["task"]
        task_type = str(task.get("taskType", "")).strip()
        if task_type not in {"CHAPTER", "SPECIAL", "SUBJECTIVE_MARKING"}:
            return None
        ext_json = assignment.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = {}
        completed_question_ids = [
            str(item).strip()
            for item in (ext_json.get("completedQuestionIds", []) if isinstance(ext_json.get("completedQuestionIds", []), list) else [])
            if str(item).strip()
        ]
        pending_review_ids = [
            str(item).strip()
            for item in (ext_json.get("pendingReviewQuestionIds", []) if isinstance(ext_json.get("pendingReviewQuestionIds", []), list) else [])
            if str(item).strip()
        ]
        normalized_question_id = str(question_id or "").strip()
        if normalized_question_id and normalized_question_id not in completed_question_ids:
            completed_question_ids.append(normalized_question_id)
        if normalized_question_id:
            if pending_review and normalized_question_id not in pending_review_ids:
                pending_review_ids.append(normalized_question_id)
            if not pending_review:
                pending_review_ids = [item for item in pending_review_ids if item != normalized_question_id]
        target_question_count = int(
            ext_json.get("targetQuestionCount")
            or (task.get("extJson", {}) if isinstance(task.get("extJson", {}), dict) else {}).get("targetQuestionCount")
            or 1
        )
        progress_count = len(completed_question_ids)
        ext_json["completedQuestionIds"] = completed_question_ids
        ext_json["pendingReviewQuestionIds"] = pending_review_ids
        ext_json["progressCount"] = progress_count
        ext_json["targetQuestionCount"] = target_question_count
        assignment["extJson"] = ext_json
        assignment["updateTime"] = self._now_iso()
        if pending_review_ids:
            assignment["status"] = "PENDING_REVIEW"
        elif progress_count >= target_question_count:
            assignment["status"] = "COMPLETED"
            assignment["completedAt"] = assignment["updateTime"]
        else:
            assignment["status"] = "IN_PROGRESS"
        return self.repository.upsert_exam_task_assignment(assignment)

    def _resolve_subject_meta(self, subject_code: str, joint_exam_group_code: str = "") -> Dict[str, object]:
        for item in PUBLIC_SUBJECTS:
            if str(item.get("subjectCode", "")).strip() == subject_code:
                return dict(item)
        group = get_joint_exam_group(joint_exam_group_code) if joint_exam_group_code else None
        professional_subjects = group.get("professionalSubjects", []) if isinstance(group, dict) else []
        for item in professional_subjects:
            if str(item.get("subjectCode", "")).strip() == subject_code:
                return dict(item)
        return {"subjectCode": subject_code, "subjectName": subject_code, "score": 100}

    def _build_mock_exam_rule_profile(self, total_score: int) -> tuple[List[Dict[str, int]], Dict[str, float], int]:
        default_key = "__DEFAULT_150__" if total_score >= 150 else "__DEFAULT_100__"
        settings = self._load_system_state()["systemSettings"]
        profiles = settings.get("mockExamRuleProfiles", {}) if isinstance(settings, dict) else {}
        profile = profiles.get(default_key, {}) if isinstance(profiles, dict) else {}
        type_rules = profile.get("typeRules", []) if isinstance(profile, dict) else []
        difficulty_ratio = profile.get("difficultyRatio", {}) if isinstance(profile, dict) else {}
        duration_minutes = int(profile.get("durationMinutes", 120 if total_score >= 150 else 90) or (120 if total_score >= 150 else 90))
        if not isinstance(type_rules, list) or not type_rules:
            type_rules = [
                {"type": "single_choice", "count": 20, "questionScore": 2},
                {"type": "multiple_choice", "count": 10 if total_score >= 150 else 5, "questionScore": 4},
                {"type": "judge", "count": 10, "questionScore": 2},
                {"type": "subjective", "count": 5 if total_score >= 150 else 2, "questionScore": 10},
            ]
        if not isinstance(difficulty_ratio, dict) or not difficulty_ratio:
            difficulty_ratio = {"easy": 0.25, "medium": 0.5, "hard": 0.25} if total_score >= 150 else {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        return (type_rules, difficulty_ratio, duration_minutes)

    def _resolve_mock_exam_rule_profile(self, subject_code: str, total_score: int) -> tuple[List[Dict[str, int]], Dict[str, float], int]:
        settings = self._load_system_state()["systemSettings"]
        profiles = settings.get("mockExamRuleProfiles", {}) if isinstance(settings, dict) else {}
        profile = profiles.get(subject_code, {}) if isinstance(profiles, dict) else {}
        if isinstance(profile, dict) and profile:
            type_rules = profile.get("typeRules", [])
            difficulty_ratio = profile.get("difficultyRatio", {})
            duration_minutes = int(profile.get("durationMinutes", 120 if total_score >= 150 else 90) or (120 if total_score >= 150 else 90))
            if isinstance(type_rules, list) and type_rules and isinstance(difficulty_ratio, dict) and difficulty_ratio:
                return type_rules, difficulty_ratio, duration_minutes
        return self._build_mock_exam_rule_profile(total_score)

    def _select_mock_questions_for_rule(
        self,
        questions: List[Dict[str, str]],
        count: int,
        difficulty_ratio: Dict[str, float],
    ) -> List[str]:
        if count <= 0 or not questions:
            return []
        selected_ids: List[str] = []
        remaining_questions = list(questions)
        target_distribution = {
            difficulty: int(round(count * max(0.0, float(ratio))))
            for difficulty, ratio in difficulty_ratio.items()
        }
        while sum(target_distribution.values()) < count:
            target_distribution["medium"] = target_distribution.get("medium", 0) + 1
        while sum(target_distribution.values()) > count:
            for difficulty in ("hard", "easy", "medium"):
                if target_distribution.get(difficulty, 0) > 0 and sum(target_distribution.values()) > count:
                    target_distribution[difficulty] -= 1
        for difficulty in ("easy", "medium", "hard"):
            if not remaining_questions:
                break
            need = int(target_distribution.get(difficulty, 0))
            if need <= 0:
                continue
            bucket = [
                question for question in remaining_questions
                if str(self._question_difficulty(question) or "").strip().lower() == difficulty
            ]
            picked_ids = self._pick_ai_questions_by_weight(bucket, [], min(need, len(bucket))) if bucket else []
            selected_ids.extend(picked_ids)
            picked_set = set(picked_ids)
            remaining_questions = [
                question for question in remaining_questions
                if str(question.get("id", "")).strip() not in picked_set
            ]
        if len(selected_ids) < count and remaining_questions:
            remaining_need = count - len(selected_ids)
            selected_ids.extend(self._pick_ai_questions_by_weight(remaining_questions, [], min(remaining_need, len(remaining_questions))))
        return selected_ids[:count]

    def _select_mock_exam_questions(
        self,
        available_questions: List[Dict[str, str]],
        total_score: int,
        subject_code: str,
    ) -> tuple[List[str], Dict[str, int], Dict[str, object]]:
        type_rules, difficulty_ratio, duration_minutes = self._resolve_mock_exam_rule_profile(subject_code, total_score)
        selected_ids: List[str] = []
        question_score_map: Dict[str, int] = {}
        degrade_summary = {
            "difficultyRatio": difficulty_ratio,
            "typeRuleSummary": list(type_rules),
            "degradeReasons": [],
        }
        remaining_questions = list(available_questions)
        for rule in type_rules:
            question_type = str(rule.get("type", "")).strip()
            count = int(rule.get("count", 0))
            question_score = int(rule.get("questionScore", 0))
            type_candidates = [
                question for question in remaining_questions
                if str(question.get("type", "")).strip() == question_type
            ]
            picked_ids = self._select_mock_questions_for_rule(type_candidates, count, difficulty_ratio)
            if len(picked_ids) < count:
                degrade_summary["degradeReasons"].append(f"{question_type} 题量不足，已用其他题型补位。")
                fallback_candidates = [
                    question for question in remaining_questions
                    if str(question.get("id", "")).strip() not in set(picked_ids)
                ]
                fallback_ids = self._pick_ai_questions_by_weight(
                    fallback_candidates,
                    [],
                    min(count - len(picked_ids), len(fallback_candidates)),
                )
                picked_ids.extend(fallback_ids)
            selected_ids.extend(picked_ids)
            for question_id in picked_ids:
                question_score_map[question_id] = question_score
            picked_set = set(picked_ids)
            remaining_questions = [
                question for question in remaining_questions
                if str(question.get("id", "")).strip() not in picked_set
            ]
        degrade_summary["selectedQuestionCount"] = len(selected_ids)
        degrade_summary["targetQuestionCount"] = sum(int(item.get("count", 0)) for item in type_rules)
        degrade_summary["durationMinutes"] = duration_minutes
        return selected_ids, question_score_map, degrade_summary

    def start_student_mock_exam(self, payload: Dict[str, object], actor: Actor) -> Dict[str, object]:
        subject_id, exam_category_code, joint_exam_group_code, subject_code = self._resolve_exam_task_scope(payload, actor)
        if not subject_code and subject_id:
            subject_code = subject_code_from_subject_id(subject_id)
        if not subject_code:
            raise validation_failed("subjectCode 不能为空。")
        existing_session = self.repository.find_active_mock_exam_session(actor.user_id, subject_code)
        if existing_session:
            existing_paper_id = str(existing_session.get("paperId", "")).strip()
            existing_questions: List[Dict[str, str]] = []
            if existing_paper_id:
                try:
                    existing_questions = self._list_questions_for_paper(existing_paper_id, actor, visible_to_students=True)
                except Exception:
                    existing_questions = []
            if existing_questions:
                return existing_session
            now_iso = self._now_iso()
            self.repository.upsert_mock_exam_session(
                {
                    **existing_session,
                    "status": "SUBMITTED",
                    "submittedAt": str(existing_session.get("submittedAt", "")).strip() or now_iso,
                    "updateTime": now_iso,
                }
            )
        subject_meta = self._resolve_subject_meta(subject_code, joint_exam_group_code)
        total_score = max(50, int(subject_meta.get("score", 100) or 100))
        available_questions = self._list_published_questions_with_content_filters(
            {
                "subjectId": subject_id,
                "chapter": "",
                "type": "",
                "difficulty": "",
                "keyword": "",
            },
            {
                "examCategoryCode": exam_category_code,
                "jointExamGroupCode": joint_exam_group_code,
                "subjectCode": subject_code,
            },
            actor.role,
            actor.user_id,
            injected_joint_group_code=actor.assigned_joint_group_code,
        )
        if not available_questions:
            raise validation_failed("当前科目下暂无可用于模拟考试的题目。")
        selected_ids, question_score_map, degrade_summary = self._select_mock_exam_questions(available_questions, total_score, subject_code)
        if not selected_ids:
            raise validation_failed("当前科目题量不足，无法生成模拟考试。")
        question_count = len(selected_ids)
        duration_minutes = int(degrade_summary.get("durationMinutes", 90) or 90)
        actual_total_score = sum(int(score) for score in question_score_map.values())
        paper_id = f"paper-mock-{uuid.uuid4().hex[:8]}"
        paper_name = f"{str(subject_meta.get('subjectName', subject_code)).strip() or subject_code}全真模拟卷"
        self._save_paper_bindings(
            paper_id=paper_id,
            paper_name=paper_name,
            subject_id=subject_id or subject_id_from_subject_code(subject_code),
            exam_category_code=exam_category_code,
            joint_exam_group_code=joint_exam_group_code,
            subject_code=subject_code,
            paper_type="simulation",
            paper_status="PUBLISHED",
            duration_minutes=duration_minutes,
            total_score=actual_total_score,
            visible_to_students=True,
            target_class_ids=[],
            question_ids=selected_ids,
            question_score_map=question_score_map,
            rule_mode="student_mock_start",
            actor=actor,
            owner_student_user_id=actor.user_id,
        )
        now_iso = self._now_iso()
        session = self.repository.upsert_mock_exam_session(
            {
                "id": f"mock-session-{uuid.uuid4().hex[:8]}",
                "studentUserId": actor.user_id,
                "subjectCode": subject_code,
                "examCategoryCode": exam_category_code,
                "jointExamGroupCode": joint_exam_group_code,
                "paperId": paper_id,
                "paperName": paper_name,
                "questionCount": question_count,
                "totalScore": actual_total_score,
                "durationMinutes": duration_minutes,
                "syllabusVersion": POLICY_VERSION_CODE,
                "status": "ACTIVE",
                "ruleSnapshot": {
                    "questionScoreMap": question_score_map,
                    "selectedQuestionIds": selected_ids,
                    "selectionMethod": "syllabus_weighted_type_difficulty_matrix",
                },
                "degradeSummary": {
                    **degrade_summary,
                    "availableQuestionCount": len(available_questions),
                    "selectedQuestionCount": question_count,
                },
                "startedAt": now_iso,
                "submittedAt": "",
                "createTime": now_iso,
                "updateTime": now_iso,
            }
        )
        return session

    def get_student_mock_exam_session(self, session_id: str, actor: Actor) -> Dict[str, object]:
        session = self.repository.get_mock_exam_session(session_id)
        if not session or str(session.get("studentUserId", "")).strip() != actor.user_id:
            raise not_found("模拟考试会话不存在。")
        return session
