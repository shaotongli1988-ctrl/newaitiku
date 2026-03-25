from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

from app.content_baseline import POLICY_VERSION_CODE, list_joint_exam_groups
from app.db import DEFAULT_DB_PATH, get_connection, row_to_knowledge, row_to_question, row_to_task
from app.shared.codecs import dump_json, hash_password, load_json_object

SYSTEM_USER_ID = "__system__"
STUDENT_RECORD_TEMP_TABLE_THRESHOLD = 500

USER_FIELDS = ("id", "phone", "password", "status", "extJson", "createTime", "updateTime")
USER_AUTH_FIELDS = ("id", "userId", "type", "openid", "unionid", "extJson", "createTime", "updateTime")
STUDENT_QUESTION_RECORD_FIELDS = (
    "id",
    "studentUserId",
    "questionId",
    "status",
    "lastSubmittedAt",
    "lastAnswer",
    "lastIsCorrect",
    "answerCount",
    "correctCount",
    "wrongCount",
    "totalAnswerDurationSec",
    "latestSourceType",
    "latestPaperId",
    "wrongBookFlag",
    "wrongBookArchivedFlag",
    "wrongBookCollectedAt",
    "wrongBookLastWrongAt",
    "wrongBookReviewedAt",
    "wrongBookArchivedAt",
    "wrongBookRestoredAt",
    "wrongBookReviewCount",
    "wrongBookPostWrongAttemptCount",
    "wrongBookPostWrongCorrectCount",
    "wrongBookLastReasonCode",
    "wrongBookLastReasonLabel",
    "personalBankFlag",
    "personalBankCollectedAt",
    "personalBankSourceType",
    "personalBankSourceLabel",
    "profileAnchorFlag",
    "extJson",
    "createTime",
    "updateTime",
)
STUDENT_DAILY_PROGRESS_FIELDS = (
    "id",
    "studentUserId",
    "progressDate",
    "checkInCount",
    "practiceAnswers",
    "papersCompleted",
    "wrongBookReviewed",
    "rewardedKeysJson",
    "extJson",
    "createTime",
    "updateTime",
)
STUDENT_POINTS_LEDGER_FIELDS = (
    "id",
    "studentUserId",
    "eventKey",
    "reason",
    "points",
    "extJson",
    "createTime",
    "updateTime",
)
STUDENT_PROFILE_STATE_FIELDS = (
    "id",
    "studentUserId",
    "examCategoryCode",
    "jointExamGroupCode",
    "points",
    "title",
    "unlockedTitlesJson",
    "checkInDatesJson",
    "aiDailyLimit",
    "aiUsedCount",
    "aiQuotaDate",
    "examAnsweredCount",
    "examElapsedSec",
    "examUpdateTime",
    "extJson",
    "createTime",
    "updateTime",
)
STUDENT_REVIEW_PLAN_FIELDS = (
    "id",
    "studentUserId",
    "planType",
    "planName",
    "status",
    "generatedAt",
    "startedAt",
    "completedAt",
    "lastExecutedAt",
    "extJson",
    "createTime",
    "updateTime",
)
STUDENT_REVIEW_PLAN_ITEM_FIELDS = (
    "id",
    "planId",
    "studentUserId",
    "questionId",
    "status",
    "sort",
    "completedAt",
    "extJson",
    "createTime",
    "updateTime",
)
PAPER_REPORT_FIELDS = (
    "id",
    "reportId",
    "studentUserId",
    "paperId",
    "subjectId",
    "subjectIdsJson",
    "score",
    "totalScore",
    "scoreRate",
    "totalElapsedSec",
    "submittedAt",
    "pendingSubjectiveCount",
    "status",
    "extJson",
    "createTime",
    "updateTime",
)
EXAM_TASK_FIELDS = (
    "id",
    "taskName",
    "taskType",
    "subjectId",
    "examCategoryCode",
    "jointExamGroupCode",
    "subjectCode",
    "sourceType",
    "sourceId",
    "sourceLabel",
    "teacherUserId",
    "teacherName",
    "description",
    "allowRedo",
    "dueAt",
    "status",
    "extJson",
    "createTime",
    "updateTime",
)
EXAM_TASK_TARGET_FIELDS = (
    "id",
    "taskId",
    "targetType",
    "targetId",
    "targetName",
    "createTime",
)
EXAM_TASK_ASSIGNMENT_FIELDS = (
    "id",
    "taskId",
    "studentUserId",
    "status",
    "score",
    "totalScore",
    "startedAt",
    "submittedAt",
    "completedAt",
    "expiredAt",
    "lastPaperId",
    "redoCount",
    "maxRedoCount",
    "extJson",
    "createTime",
    "updateTime",
)
MOCK_EXAM_SESSION_FIELDS = (
    "id",
    "studentUserId",
    "subjectCode",
    "examCategoryCode",
    "jointExamGroupCode",
    "paperId",
    "paperName",
    "questionCount",
    "totalScore",
    "durationMinutes",
    "syllabusVersion",
    "status",
    "ruleSnapshotJson",
    "degradeSummaryJson",
    "startedAt",
    "submittedAt",
    "createTime",
    "updateTime",
)
CHALLENGE_POINT_SUBJECT_FIELDS = (
    "id",
    "studentUserId",
    "subjectCode",
    "totalPoints",
    "lastAwardedAt",
    "extJson",
    "createTime",
    "updateTime",
)
CHALLENGE_POINT_AWARD_FIELDS = (
    "id",
    "studentUserId",
    "subjectCode",
    "awardCode",
    "awardName",
    "unlockedAt",
    "extJson",
    "createTime",
    "updateTime",
)
MESSAGE_SEND_HISTORY_FIELDS = (
    "id",
    "traceId",
    "scheduleId",
    "senderUserId",
    "targetMode",
    "targetCount",
    "sentCount",
    "category",
    "title",
    "content",
    "sendAt",
    "status",
    "recalledAt",
    "createTime",
    "updateTime",
    "extJson",
)
LEARNING_METHOD_FIELDS = (
    "id",
    "methodCode",
    "methodName",
    "oneLineIntro",
    "useWhenJson",
    "stepsJson",
    "commonMistakesJson",
    "questionBankActionsJson",
    "starterTask",
    "difficultyLevel",
    "estimatedMinutes",
    "sort",
    "status",
    "extJson",
    "createTime",
    "updateTime",
)
STUDENT_LEARNING_METHOD_PROGRESS_FIELDS = (
    "id",
    "studentUserId",
    "methodCode",
    "startCount",
    "completeCount",
    "lastPracticedAt",
    "lastAccuracy",
    "lastReviewSummary",
    "status",
    "extJson",
    "createTime",
    "updateTime",
)
SUBSCRIPTION_PLAN_FIELDS = (
    "id",
    "planCode",
    "planName",
    "durationDays",
    "listPriceFen",
    "salePriceFen",
    "status",
    "sort",
    "extJson",
    "createTime",
    "updateTime",
)
STUDENT_SUBSCRIPTION_FIELDS = (
    "id",
    "studentUserId",
    "currentPlanCode",
    "status",
    "startTime",
    "endTime",
    "lastActivatedAt",
    "lastExpiredAt",
    "sourceType",
    "sourceOrderId",
    "sourceRedeemCode",
    "totalActivatedDays",
    "extJson",
    "createTime",
    "updateTime",
)
REDEEM_CODE_BATCH_FIELDS = (
    "id",
    "batchCode",
    "batchName",
    "channelCode",
    "planCode",
    "totalCount",
    "usedCount",
    "expiresAt",
    "status",
    "createdByUserId",
    "extJson",
    "createTime",
    "updateTime",
)
REDEEM_CODE_FIELDS = (
    "id",
    "batchId",
    "code",
    "planCode",
    "status",
    "expiresAt",
    "usedByUserId",
    "usedAt",
    "sourceOrderId",
    "extJson",
    "createTime",
    "updateTime",
)
SUBSCRIPTION_ORDER_FIELDS = (
    "id",
    "orderNo",
    "studentUserId",
    "planCode",
    "amountFen",
    "channel",
    "status",
    "paidAt",
    "closedAt",
    "extJson",
    "createTime",
    "updateTime",
)
PAYMENT_TRANSACTION_MOCK_FIELDS = (
    "id",
    "orderId",
    "transactionNo",
    "requestId",
    "status",
    "payloadJson",
    "createTime",
    "updateTime",
)
CONVERSION_EVENT_LOG_FIELDS = (
    "id",
    "studentUserId",
    "eventType",
    "eventTime",
    "eventDate",
    "sessionId",
    "planCode",
    "orderId",
    "redeemCode",
    "channelCode",
    "extJson",
    "createTime",
    "updateTime",
)
QUESTION_SELECT_SQL = ", ".join(
    (
        "id",
        "knowledgeId",
        "userId",
        "type",
        "stem",
        "optionsJson",
        "answer",
        "status",
        "extJson",
        "createTime",
        "updateTime",
    )
)
QUESTION_SELECT_SQL_Q = ", ".join(f"q.{field}" for field in (
    "id",
    "knowledgeId",
    "userId",
    "type",
    "stem",
    "optionsJson",
    "answer",
    "status",
    "extJson",
    "createTime",
    "updateTime",
))
USER_SELECT_SQL = ", ".join(USER_FIELDS)
USER_AUTH_SELECT_SQL = ", ".join(USER_AUTH_FIELDS)
STUDENT_QUESTION_RECORD_SELECT_SQL = ", ".join(STUDENT_QUESTION_RECORD_FIELDS)
STUDENT_DAILY_PROGRESS_SELECT_SQL = ", ".join(STUDENT_DAILY_PROGRESS_FIELDS)
STUDENT_POINTS_LEDGER_SELECT_SQL = ", ".join(STUDENT_POINTS_LEDGER_FIELDS)
STUDENT_PROFILE_STATE_SELECT_SQL = ", ".join(STUDENT_PROFILE_STATE_FIELDS)
STUDENT_REVIEW_PLAN_SELECT_SQL = ", ".join(STUDENT_REVIEW_PLAN_FIELDS)
STUDENT_REVIEW_PLAN_ITEM_SELECT_SQL = ", ".join(STUDENT_REVIEW_PLAN_ITEM_FIELDS)
PAPER_REPORT_SELECT_SQL = ", ".join(PAPER_REPORT_FIELDS)
EXAM_TASK_SELECT_SQL = ", ".join(EXAM_TASK_FIELDS)
EXAM_TASK_TARGET_SELECT_SQL = ", ".join(EXAM_TASK_TARGET_FIELDS)
EXAM_TASK_ASSIGNMENT_SELECT_SQL = ", ".join(EXAM_TASK_ASSIGNMENT_FIELDS)
MOCK_EXAM_SESSION_SELECT_SQL = ", ".join(MOCK_EXAM_SESSION_FIELDS)
CHALLENGE_POINT_SUBJECT_SELECT_SQL = ", ".join(CHALLENGE_POINT_SUBJECT_FIELDS)
CHALLENGE_POINT_AWARD_SELECT_SQL = ", ".join(CHALLENGE_POINT_AWARD_FIELDS)
MESSAGE_SEND_HISTORY_SELECT_SQL = ", ".join(MESSAGE_SEND_HISTORY_FIELDS)
LEARNING_METHOD_SELECT_SQL = ", ".join(LEARNING_METHOD_FIELDS)
STUDENT_LEARNING_METHOD_PROGRESS_SELECT_SQL = ", ".join(STUDENT_LEARNING_METHOD_PROGRESS_FIELDS)
SUBSCRIPTION_PLAN_SELECT_SQL = ", ".join(SUBSCRIPTION_PLAN_FIELDS)
STUDENT_SUBSCRIPTION_SELECT_SQL = ", ".join(STUDENT_SUBSCRIPTION_FIELDS)
REDEEM_CODE_BATCH_SELECT_SQL = ", ".join(REDEEM_CODE_BATCH_FIELDS)
REDEEM_CODE_SELECT_SQL = ", ".join(REDEEM_CODE_FIELDS)
SUBSCRIPTION_ORDER_SELECT_SQL = ", ".join(SUBSCRIPTION_ORDER_FIELDS)
PAYMENT_TRANSACTION_MOCK_SELECT_SQL = ", ".join(PAYMENT_TRANSACTION_MOCK_FIELDS)
CONVERSION_EVENT_LOG_SELECT_SQL = ", ".join(CONVERSION_EVENT_LOG_FIELDS)


class QuestionRepository:
    def __init__(self, db_path: Union[Path, str] = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._knowledge_change_listener: Optional[Callable[[], None]] = None
        self._refresh_query_planner_stats()

    def set_knowledge_change_listener(self, listener: Optional[Callable[[], None]]) -> None:
        self._knowledge_change_listener = listener

    def _notify_knowledge_changed(self) -> None:
        if not callable(self._knowledge_change_listener):
            return
        self._knowledge_change_listener()

    def _normalize_legacy_student_profile_snapshot(self, payload: object) -> Dict[str, object]:
        if not isinstance(payload, dict):
            return {}
        return {
            "examCategoryCode": str(payload.get("examCategoryCode", "")).strip() or "SCIENCE_ENGINEERING",
            "jointExamGroupCode": str(payload.get("jointExamGroupCode", "")).strip() or "SCIENCE_ENGINEERING_3",
        }

    def _refresh_query_planner_stats(self) -> None:
        try:
            with get_connection(self.db_path) as connection:
                connection.execute("ANALYZE")
                connection.commit()
        except Exception:
            # Keep repository startup resilient even when ANALYZE is unavailable.
            return

    def _question_metadata(self, question: Dict[str, str]) -> Dict[str, object]:
        return load_json_object(question.get("extJson", "{}"))

    def _safe_int(self, value: object, default: int = 0) -> int:
        try:
            return int(value)
        except Exception:
            return default

    def _safe_float(self, value: object, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default

    def _is_truthy(self, value: object) -> bool:
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _question_matches_content_filters(
        self,
        question: Dict[str, str],
        filters: Dict[str, str],
        enforce_policy_version: bool = True,
    ) -> bool:
        metadata = self._question_metadata(question)
        if enforce_policy_version:
            policy_version = (
                str(
                    filters.get("policyVersion")
                    or filters.get("policyVersionCode")
                    or ""
                ).strip()
                or POLICY_VERSION_CODE
            )
            if str(metadata.get("policyVersionCode", "")).strip() != policy_version:
                return False
        exam_category_code = str(filters.get("examCategoryCode", "")).strip()
        if exam_category_code:
            if metadata.get("subjectType") == "PUBLIC":
                allowed_group_codes = {
                    item["jointExamGroupCode"]
                    for item in list_joint_exam_groups(exam_category_code)
                }
                applicable_groups = set(metadata.get("applicableGroups", []))
                if not allowed_group_codes.intersection(applicable_groups):
                    return False
            elif str(metadata.get("examCategoryCode", "")) != exam_category_code:
                return False
        joint_exam_group_code = str(filters.get("jointExamGroupCode", "")).strip()
        if joint_exam_group_code:
            applicable_groups = metadata.get("applicableGroups", [])
            if joint_exam_group_code not in applicable_groups and str(metadata.get("jointExamGroupCode", "")).strip() != joint_exam_group_code:
                return False
        subject_code = str(filters.get("subjectCode", "")).strip()
        if subject_code and str(metadata.get("subjectCode", "")) != subject_code:
            return False
        return True

    def _question_matches_date_filters(self, record_ext_json: str, filters: Dict[str, str]) -> bool:
        start_date = str(filters.get("startDate", "")).strip()
        end_date = str(filters.get("endDate", "")).strip()
        if not start_date and not end_date:
            return True
        record_ext = load_json_object(record_ext_json)
        chapter_practice = load_json_object(record_ext.get("chapterPractice", {}))
        submitted_at = str(chapter_practice.get("submittedAt", ""))
        submitted_date = submitted_at[:10] if submitted_at else ""
        if start_date and submitted_date and submitted_date < start_date:
            return False
        if end_date and submitted_date and submitted_date > end_date:
            return False
        return True

    def _normalized_policy_version(self, filters: Dict[str, str]) -> str:
        return (
            str(
                filters.get("policyVersion")
                or filters.get("policyVersionCode")
                or ""
            ).strip()
            or POLICY_VERSION_CODE
        )

    def _load_question_rows_for_student_records(
        self,
        connection: sqlite3.Connection,
        question_ids: List[str],
        policy_version: str,
    ) -> List[sqlite3.Row]:
        if not question_ids:
            return []
        if len(question_ids) > STUDENT_RECORD_TEMP_TABLE_THRESHOLD:
            return self._load_question_rows_for_student_records_with_temp_table(
                connection,
                question_ids,
                policy_version,
            )
        placeholders = ",".join("?" for _ in question_ids)
        return connection.execute(
            (
                f"SELECT {QUESTION_SELECT_SQL} "
                "FROM question "
                "WHERE COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = ? "
                f"AND id IN ({placeholders})"
            ),
            (policy_version, *question_ids),
        ).fetchall()

    def _load_question_rows_for_student_records_with_temp_table(
        self,
        connection: sqlite3.Connection,
        question_ids: List[str],
        policy_version: str,
    ) -> List[sqlite3.Row]:
        connection.execute("CREATE TEMP TABLE IF NOT EXISTS temp_student_record_question_ids (questionId TEXT PRIMARY KEY)")
        connection.execute("DELETE FROM temp_student_record_question_ids")
        try:
            connection.executemany(
                "INSERT INTO temp_student_record_question_ids (questionId) VALUES (?)",
                [(question_id,) for question_id in question_ids],
            )
            return connection.execute(
                f"""
                SELECT {QUESTION_SELECT_SQL}
                FROM question
                INNER JOIN temp_student_record_question_ids AS temp_ids ON temp_ids.questionId = question.id
                WHERE COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = ?
                """,
                (policy_version,),
            ).fetchall()
        finally:
            connection.execute("DELETE FROM temp_student_record_question_ids")

    def _append_question_content_filter_clauses(
        self,
        clauses: List[str],
        params: Dict[str, object],
        filters: Dict[str, str],
        ext_json_expr: str,
    ) -> None:
        exam_category_code = str(filters.get("examCategoryCode") or "").strip()
        if exam_category_code:
            allowed_group_codes = [
                str(item.get("jointExamGroupCode", "")).strip()
                for item in list_joint_exam_groups(exam_category_code)
                if str(item.get("jointExamGroupCode", "")).strip()
            ]
            params["exam_category_code"] = exam_category_code
            if allowed_group_codes:
                allowed_group_placeholders: List[str] = []
                for index, group_code in enumerate(allowed_group_codes):
                    placeholder = f"allowed_group_code_{index}"
                    allowed_group_placeholders.append(f":{placeholder}")
                    params[placeholder] = group_code
                clauses.append(
                    "("
                    f"(COALESCE(json_extract({ext_json_expr}, '$.subjectType'), '') != 'PUBLIC' "
                    "AND "
                    f"COALESCE(json_extract({ext_json_expr}, '$.examCategoryCode'), '') = :exam_category_code)"
                    " OR "
                    f"(COALESCE(json_extract({ext_json_expr}, '$.subjectType'), '') = 'PUBLIC' "
                    "AND EXISTS ("
                    f"SELECT 1 FROM json_each({ext_json_expr}, '$.applicableGroups') AS applicable_group "
                    f"WHERE applicable_group.value IN ({','.join(allowed_group_placeholders)})"
                    "))"
                    ")"
                )
            else:
                clauses.append(f"COALESCE(json_extract({ext_json_expr}, '$.examCategoryCode'), '') = :exam_category_code")

        joint_exam_group_code = str(filters.get("jointExamGroupCode") or "").strip()
        if joint_exam_group_code:
            clauses.append(
                "("
                "EXISTS ("
                f"SELECT 1 FROM json_each({ext_json_expr}, '$.applicableGroups') AS applicable_group "
                "WHERE applicable_group.value = :joint_exam_group_code"
                ") "
                f"OR COALESCE(json_extract({ext_json_expr}, '$.jointExamGroupCode'), '') = :joint_exam_group_code "
                ")"
            )
            params["joint_exam_group_code"] = joint_exam_group_code

        subject_code = str(filters.get("subjectCode") or "").strip()
        if subject_code:
            clauses.append(f"COALESCE(json_extract({ext_json_expr}, '$.subjectCode'), '') = :subject_code")
            params["subject_code"] = subject_code

    def aggregate_student_analytics_rollups(
        self,
        filters: Dict[str, str],
    ) -> List[Dict[str, object]]:
        params: Dict[str, object] = {
            "student_user_id": str(filters.get("studentUserId", "")).strip(),
            "paper_id": str(filters.get("paperId", "")).strip(),
            "start_date": str(filters.get("startDate", "")).strip(),
            "end_date": str(filters.get("endDate", "")).strip(),
            "policy_version": self._normalized_policy_version(filters),
        }
        keyword = str(filters.get("keyword", "")).strip().lower()
        params["keyword"] = f"%{keyword}%" if keyword else ""

        joined_record_clauses = [
            "COALESCE(json_extract(q.extJson, '$.policyVersionCode'), '') = :policy_version",
        ]
        if keyword:
            joined_record_clauses.append(
                "("
                "LOWER("
                "COALESCE(q.id, '') || ' ' || "
                "COALESCE(q.stem, '') || ' ' || "
                "COALESCE(q.extJson, '') || ' ' || "
                "COALESCE(filtered_records.recordExtJsonText, '') || ' ' || "
                "COALESCE(filtered_records.studentUserId, '')"
                ") LIKE :keyword"
                ")"
            )
        subject_id = str(filters.get("subjectId", "")).strip()
        if subject_id:
            joined_record_clauses.append("COALESCE(json_extract(q.extJson, '$.subjectId'), '') = :subject_id")
            params["subject_id"] = subject_id
        chapter = str(filters.get("chapter", "")).strip()
        if chapter:
            joined_record_clauses.append("COALESCE(json_extract(q.extJson, '$.chapter'), '') = :chapter")
            params["chapter"] = chapter
        self._append_question_content_filter_clauses(joined_record_clauses, params, filters, "q.extJson")

        sql = f"""
        WITH record_refs AS (
            SELECT
                sqr.studentUserId AS studentUserId,
                sqr.questionId AS questionId,
                COALESCE(sqr.extJson, '{{}}') AS recordExtJsonText,
                COALESCE(sqr.lastSubmittedAt, '') AS submittedAt,
                CAST(COALESCE(sqr.totalAnswerDurationSec, 0) AS INTEGER) AS answerDurationSec,
                CASE
                    WHEN COALESCE(sqr.lastIsCorrect, 0) IN (1, '1', 'true', 'TRUE')
                    THEN 1
                    ELSE 0
                END AS isCorrect
            FROM student_question_record AS sqr
            WHERE (:student_user_id = '' OR sqr.studentUserId = :student_user_id)
              AND (:paper_id = '' OR INSTR(COALESCE(sqr.extJson, ''), :paper_id) > 0)
        ),
        filtered_records AS (
            SELECT
                studentUserId,
                questionId,
                recordExtJsonText,
                submittedAt,
                answerDurationSec,
                isCorrect
            FROM record_refs
            WHERE (:start_date = '' OR submittedAt = '' OR substr(submittedAt, 1, 10) >= :start_date)
              AND (:end_date = '' OR submittedAt = '' OR substr(submittedAt, 1, 10) <= :end_date)
        ),
        joined_records AS (
            SELECT
                filtered_records.studentUserId AS studentUserId,
                q.id AS questionId,
                COALESCE(json_extract(q.extJson, '$.subjectId'), '') AS subjectId,
                COALESCE(json_extract(q.extJson, '$.subjectCode'), '') AS subjectCode,
                COALESCE(json_extract(q.extJson, '$.chapter'), '') AS chapter,
                COALESCE(json_extract(q.extJson, '$.chapterCode'), '') AS chapterCode,
                COALESCE(json_extract(q.extJson, '$.pointCode'), '') AS pointCode,
                COALESCE(json_extract(q.extJson, '$.knowledgeTags'), '[]') AS knowledgeTagsJson,
                filtered_records.answerDurationSec AS answerDurationSec,
                filtered_records.isCorrect AS isCorrect,
                filtered_records.submittedAt AS submittedAt
            FROM filtered_records
            JOIN question AS q ON q.id = filtered_records.questionId
            WHERE {" AND ".join(joined_record_clauses)}
        ),
        point_rollups AS (
            SELECT
                studentUserId,
                subjectId,
                subjectCode,
                chapter,
                chapterCode,
                pointCode,
                COUNT(*) AS answerCount,
                SUM(isCorrect) AS correctCount,
                SUM(CASE WHEN isCorrect = 0 THEN 1 ELSE 0 END) AS wrongCount,
                SUM(answerDurationSec) AS totalAnswerDurationSec,
                MAX(submittedAt) AS latestSubmittedAt
            FROM joined_records
            GROUP BY studentUserId, subjectId, subjectCode, chapter, chapterCode, pointCode
        ),
        chapter_rollups AS (
            SELECT
                subjectId,
                chapter,
                COUNT(*) AS answerCount,
                SUM(CASE WHEN isCorrect = 0 THEN 1 ELSE 0 END) AS wrongCount
            FROM joined_records
            GROUP BY subjectId, chapter
        ),
        student_subject_rollups AS (
            SELECT
                studentUserId,
                subjectId,
                MAX(subjectCode) AS subjectCode,
                COUNT(*) AS answerCount,
                SUM(isCorrect) AS correctCount,
                SUM(answerDurationSec) AS totalAnswerDurationSec,
                MAX(submittedAt) AS latestSubmittedAt
            FROM joined_records
            GROUP BY studentUserId, subjectId
        ),
        student_activity_rollups AS (
            SELECT
                studentUserId,
                COUNT(*) AS activityCount,
                MAX(submittedAt) AS latestSubmittedAt
            FROM joined_records
            GROUP BY studentUserId
        ),
        tag_rollups AS (
            SELECT
                COALESCE(tag.value, '') AS knowledgeTag,
                SUM(CASE WHEN joined_records.isCorrect = 0 THEN 1 ELSE 0 END) AS wrongCount
            FROM joined_records
            JOIN json_each(joined_records.knowledgeTagsJson) AS tag
            GROUP BY COALESCE(tag.value, '')
        )
        SELECT
            'point' AS rowType,
            studentUserId,
            subjectId,
            subjectCode,
            chapter,
            chapterCode,
            pointCode,
            '' AS knowledgeTag,
            answerCount,
            correctCount,
            wrongCount,
            totalAnswerDurationSec,
            latestSubmittedAt,
            0 AS activityCount
        FROM point_rollups
        UNION ALL
        SELECT
            'chapter' AS rowType,
            '' AS studentUserId,
            subjectId,
            '' AS subjectCode,
            chapter,
            '' AS chapterCode,
            '' AS pointCode,
            '' AS knowledgeTag,
            answerCount,
            0 AS correctCount,
            wrongCount,
            0 AS totalAnswerDurationSec,
            '' AS latestSubmittedAt,
            0 AS activityCount
        FROM chapter_rollups
        UNION ALL
        SELECT
            'student_subject' AS rowType,
            studentUserId,
            subjectId,
            subjectCode,
            '' AS chapter,
            '' AS chapterCode,
            '' AS pointCode,
            '' AS knowledgeTag,
            answerCount,
            correctCount,
            0 AS wrongCount,
            totalAnswerDurationSec,
            latestSubmittedAt,
            0 AS activityCount
        FROM student_subject_rollups
        UNION ALL
        SELECT
            'student_activity' AS rowType,
            studentUserId,
            '' AS subjectId,
            '' AS subjectCode,
            '' AS chapter,
            '' AS chapterCode,
            '' AS pointCode,
            '' AS knowledgeTag,
            0 AS answerCount,
            0 AS correctCount,
            0 AS wrongCount,
            0 AS totalAnswerDurationSec,
            latestSubmittedAt,
            activityCount
        FROM student_activity_rollups
        UNION ALL
        SELECT
            'tag' AS rowType,
            '' AS studentUserId,
            '' AS subjectId,
            '' AS subjectCode,
            '' AS chapter,
            '' AS chapterCode,
            '' AS pointCode,
            knowledgeTag,
            0 AS answerCount,
            0 AS correctCount,
            wrongCount,
            0 AS totalAnswerDurationSec,
            '' AS latestSubmittedAt,
            0 AS activityCount
        FROM tag_rollups
        """
        with get_connection(self.db_path) as connection:
            rows = connection.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def count_visible_published_questions_by_subject(
        self,
        filters: Dict[str, str],
        actor_role: str,
        actor_user_id: str,
    ) -> List[Dict[str, object]]:
        clauses = [
            "COALESCE(json_extract(q.extJson, '$.policyVersionCode'), '') = :policy_version",
            "q.status = 'PUBLISHED'",
        ]
        params: Dict[str, object] = {"policy_version": self._normalized_policy_version(filters)}

        subject_id = str(filters.get("subjectId") or "").strip()
        if subject_id:
            clauses.append("COALESCE(json_extract(q.extJson, '$.subjectId'), '') = :subject_id")
            params["subject_id"] = subject_id
        self._append_question_content_filter_clauses(clauses, params, filters, "q.extJson")

        if actor_role == "teacher":
            clauses.append("q.userId = :user_id")
            params["user_id"] = actor_user_id

        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT
                    COALESCE(json_extract(q.extJson, '$.subjectId'), '') AS subjectId,
                    COALESCE(json_extract(q.extJson, '$.subjectCode'), '') AS subjectCode,
                    COUNT(*) AS questionCount
                FROM question AS q
                WHERE {" AND ".join(clauses)}
                GROUP BY subjectId, subjectCode
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def count_l5_knowledge_points_by_subject(self, filters: Dict[str, str]) -> List[Dict[str, object]]:
        clauses = [
            "COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = :policy_version",
            "status = 'ENABLED'",
            "CAST(COALESCE(json_extract(extJson, '$.level'), 0) AS INTEGER) = 5",
        ]
        params: Dict[str, object] = {"policy_version": self._normalized_policy_version(filters)}
        self._append_question_content_filter_clauses(clauses, params, filters, "extJson")
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT
                    COALESCE(json_extract(extJson, '$.subjectId'), '') AS subjectId,
                    COALESCE(json_extract(extJson, '$.subjectCode'), '') AS subjectCode,
                    COUNT(*) AS totalPointCount
                FROM knowledge
                WHERE {" AND ".join(clauses)}
                GROUP BY subjectId, subjectCode
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, str]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(f'SELECT {USER_SELECT_SQL} FROM "user" WHERE id = ?', (user_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "phone": row["phone"],
            "password": row["password"],
            "status": row["status"],
            "extJson": row["extJson"],
            "createTime": row["createTime"],
            "updateTime": row["updateTime"],
        }

    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, str]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(f'SELECT {USER_SELECT_SQL} FROM "user" WHERE phone = ? LIMIT 1', (phone,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "phone": row["phone"],
            "password": row["password"],
            "status": row["status"],
            "extJson": row["extJson"],
            "createTime": row["createTime"],
            "updateTime": row["updateTime"],
        }

    def create_user(self, payload: Dict[str, str]) -> Dict[str, str]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                '''
                INSERT INTO "user" (id, phone, password, status, extJson, createTime, updateTime)
                VALUES (:id, :phone, :password, :status, :extJson, :createTime, :updateTime)
                ''',
                payload,
            )
            connection.commit()
        return payload

    def update_user(self, payload: Dict[str, str]) -> Dict[str, str]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                '''
                UPDATE "user"
                SET phone = :phone,
                    password = :password,
                    status = :status,
                    extJson = :extJson,
                    createTime = :createTime,
                    updateTime = :updateTime
                WHERE id = :id
                ''',
                payload,
            )
            connection.commit()
        return payload

    def get_user_auth(self, user_id: str, auth_type: str) -> Optional[Dict[str, str]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"SELECT {USER_AUTH_SELECT_SQL} FROM userAuth WHERE userId = ? AND type = ? LIMIT 1",
                (user_id, auth_type),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "userId": row["userId"],
            "type": row["type"],
            "openid": row["openid"],
            "unionid": row["unionid"],
            "extJson": row["extJson"],
            "createTime": row["createTime"],
            "updateTime": row["updateTime"],
        }

    def get_user_auth_by_type_openid(self, auth_type: str, openid: str) -> Optional[Dict[str, str]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"SELECT {USER_AUTH_SELECT_SQL} FROM userAuth WHERE type = ? AND openid = ? LIMIT 1",
                (auth_type, openid),
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "userId": row["userId"],
            "type": row["type"],
            "openid": row["openid"],
            "unionid": row["unionid"],
            "extJson": row["extJson"],
            "createTime": row["createTime"],
            "updateTime": row["updateTime"],
        }

    def create_user_auth(self, payload: Dict[str, str]) -> Dict[str, str]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO userAuth (id, userId, type, openid, unionid, extJson, createTime, updateTime)
                VALUES (:id, :userId, :type, :openid, :unionid, :extJson, :createTime, :updateTime)
                """,
                payload,
            )
            connection.commit()
        return payload

    def update_user_auth(self, payload: Dict[str, str]) -> Dict[str, str]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                UPDATE userAuth
                SET userId = :userId,
                    type = :type,
                    openid = :openid,
                    unionid = :unionid,
                    extJson = :extJson,
                    createTime = :createTime,
                    updateTime = :updateTime
                WHERE id = :id
                """,
                payload,
            )
            connection.commit()
        return payload

    def _get_user_row(self, connection, user_id: str):
        return connection.execute(f'SELECT {USER_SELECT_SQL} FROM "user" WHERE id = ?', (user_id,)).fetchone()

    def _directory_scope_from_row(
        self,
        connection,
        row,
        ext_json: Dict[str, object],
    ) -> Tuple[str, str]:
        ext_exam_category_code = str(ext_json.get("examCategoryCode", "")).strip()
        ext_joint_exam_group_code = str(ext_json.get("jointExamGroupCode", "")).strip()
        if str(ext_json.get("role", "")).strip().lower() != "student":
            return ext_exam_category_code, ext_joint_exam_group_code
        profile_row = connection.execute(
            """
            SELECT examCategoryCode, jointExamGroupCode
            FROM student_profile_state
            WHERE studentUserId = ?
            """,
            (str(row["id"]),),
        ).fetchone()
        if not profile_row:
            return ext_exam_category_code, ext_joint_exam_group_code
        return (
            str(profile_row["examCategoryCode"] or "").strip() or ext_exam_category_code,
            str(profile_row["jointExamGroupCode"] or "").strip() or ext_joint_exam_group_code,
        )

    def _directory_item_from_row(self, connection, row) -> Dict[str, object]:
        ext_json = load_json_object(row["extJson"])
        exam_category_code, joint_exam_group_code = self._directory_scope_from_row(connection, row, ext_json)
        return {
            "userId": row["id"],
            "role": str(ext_json.get("role", "")),
            "name": str(ext_json.get("name", "")),
            "mobile": row["phone"],
            "enabled": row["status"] == "ENABLED",
            "permissions": list(ext_json.get("permissions", [])) if isinstance(ext_json.get("permissions"), list) else [],
            "examCategoryCode": exam_category_code,
            "jointExamGroupCode": joint_exam_group_code,
            "vocationalMajor": str(ext_json.get("vocationalMajor", "")),
            "prepStage": str(ext_json.get("prepStage", "")),
            "createTime": str(ext_json.get("createTime", row["createTime"])),
            "updateTime": str(ext_json.get("updateTime", row["updateTime"])),
        }

    def _list_directory_items(self, connection) -> List[Dict[str, object]]:
        rows = connection.execute(f'SELECT {USER_SELECT_SQL} FROM "user" WHERE id != ? ORDER BY id', (SYSTEM_USER_ID,)).fetchall()
        items: List[Dict[str, object]] = []
        for row in rows:
            item = self._directory_item_from_row(connection, row)
            if item.get("role"):
                items.append(item)
        return items

    def _upsert_directory_item(self, connection, user: Dict[str, object]) -> None:
        existing = self._get_user_row(connection, str(user["userId"]))
        existing_ext = load_json_object(existing["extJson"]) if existing else {}
        payload = dict(existing_ext)
        payload.update(
            {
                "role": user["role"],
                "name": user["name"],
                "permissions": list(user.get("permissions", [])),
                "vocationalMajor": user.get("vocationalMajor", ""),
                "prepStage": user.get("prepStage", ""),
                "createTime": user.get("createTime") or existing_ext.get("createTime") or (existing["createTime"] if existing else ""),
                "updateTime": user.get("updateTime") or existing_ext.get("updateTime") or (existing["updateTime"] if existing else ""),
            }
        )
        if str(user.get("role", "")).strip().lower() == "student":
            payload.pop("examCategoryCode", None)
            payload.pop("jointExamGroupCode", None)
        else:
            payload["examCategoryCode"] = user.get("examCategoryCode", "")
            payload["jointExamGroupCode"] = user.get("jointExamGroupCode", "")
        status = "ENABLED" if user.get("enabled", True) else "DISABLED"
        if existing:
            connection.execute(
                '''
                UPDATE "user"
                SET phone = ?,
                    status = ?,
                    extJson = ?,
                    updateTime = ?
                WHERE id = ?
                ''',
                (
                    str(user.get("mobile", existing["phone"])),
                    status,
                    dump_json(payload),
                    payload["updateTime"] or existing["updateTime"],
                    str(user["userId"]),
                ),
            )
            return
        connection.execute(
            '''
            INSERT INTO "user" (id, phone, password, status, extJson, createTime, updateTime)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                str(user["userId"]),
                str(user.get("mobile", "")),
                hash_password(f"seed-password-{user['userId']}"),
                status,
                dump_json(payload),
                payload["createTime"] or payload["updateTime"],
                payload["updateTime"] or payload["createTime"],
            ),
        )

    def _ensure_system_user(self, connection) -> None:
        if self._get_user_row(connection, SYSTEM_USER_ID):
            return
        connection.execute(
            '''
            INSERT INTO "user" (id, phone, password, status, extJson, createTime, updateTime)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                SYSTEM_USER_ID,
                "00000000000",
                hash_password("seed-password-system"),
                "ENABLED",
                dump_json(
                    {
                        "role": "system",
                        "name": "system",
                        "permissions": [],
                        "systemSettings": {},
                        "messages": [],
                        "messageSettingsByUser": {},
                        "paperTemplates": [],
                    }
                ),
                "",
                "",
            ),
        )

    def _load_system_state(self, connection) -> Dict[str, object]:
        self._ensure_system_user(connection)
        row = self._get_user_row(connection, SYSTEM_USER_ID)
        state = load_json_object(row["extJson"]) if row else {}
        state["managedUsers"] = self._list_directory_items(connection)
        return state

    def _save_system_state(self, connection, state: Dict[str, object]) -> None:
        self._ensure_system_user(connection)
        directory = state.get("managedUsers", [])
        if isinstance(directory, list):
            for item in directory:
                if isinstance(item, dict) and item.get("userId"):
                    self._upsert_directory_item(connection, item)
        payload = dict(state)
        payload.pop("managedUsers", None)
        payload.pop("paperReports", None)
        payload.pop("messageSendHistory", None)
        row = self._get_user_row(connection, SYSTEM_USER_ID)
        ext_json = load_json_object(row["extJson"]) if row else {}
        ext_json.pop("paperReports", None)
        ext_json.pop("messageSendHistory", None)
        ext_json.update(payload)
        ext_json.setdefault("role", "system")
        ext_json.setdefault("name", "system")
        ext_json.setdefault("permissions", [])
        connection.execute(
            'UPDATE "user" SET extJson = ? WHERE id = ?',
            (dump_json(ext_json), SYSTEM_USER_ID),
        )

    def _ensure_student_row(self, connection, user_id: str) -> None:
        if self._get_user_row(connection, user_id):
            return
        connection.execute(
            '''
            INSERT INTO "user" (id, phone, password, status, extJson, createTime, updateTime)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                user_id,
                "",
                hash_password(f"seed-password-{user_id}"),
                "ENABLED",
                dump_json(
                    {
                        "role": "student",
                        "name": user_id,
                        "permissions": [],
                        "examCategoryCode": "",
                        "jointExamGroupCode": "",
                        "vocationalMajor": "",
                        "prepStage": "",
                    }
                ),
                "",
                "",
            ),
        )

    def _stored_record_to_payload(self, question_id: str, student_user_id: str, stored: object) -> Optional[Dict[str, str]]:
        if not isinstance(stored, dict):
            return None
        ext_json = stored.get("extJson", {})
        if isinstance(ext_json, dict):
            ext_json = dump_json(ext_json)
        return {
            "id": str(stored.get("id", "")),
            "questionId": question_id,
            "studentUserId": student_user_id,
            "status": str(stored.get("status", "ACTIVE")),
            "extJson": str(ext_json or "{}"),
        }

    def _normalize_student_question_record_row(
        self,
        student_user_id: str,
        question_id: str,
        stored: object,
    ) -> Optional[Dict[str, object]]:
        payload = self._stored_record_to_payload(question_id, student_user_id, stored)
        if not payload:
            return None
        record_ext = load_json_object(payload["extJson"])
        student_profile = record_ext.get("studentProfile")
        if isinstance(student_profile, dict):
            record_ext["studentProfile"] = self._normalize_legacy_student_profile_snapshot(student_profile)
            payload["extJson"] = dump_json(record_ext)
        profile_anchor_flag = 1 if isinstance(record_ext.get("studentProfile"), dict) else 0
        chapter_practice = record_ext.get("chapterPractice", {})
        if not isinstance(chapter_practice, dict):
            chapter_practice = {}
        wrong_book = record_ext.get("wrongBook", {})
        if not isinstance(wrong_book, dict):
            wrong_book = {}
        personal_bank = record_ext.get("personalBank", {})
        if not isinstance(personal_bank, dict):
            personal_bank = {}
        simulation_attempts = record_ext.get("simulationAttempts", {})
        if not isinstance(simulation_attempts, dict):
            simulation_attempts = {}

        latest_submitted_at = str(chapter_practice.get("submittedAt", "")).strip()
        latest_answer = str(chapter_practice.get("lastAnswer", "")).strip()
        latest_is_correct = 1 if self._is_truthy(chapter_practice.get("isCorrect", 0)) else 0
        latest_paper_id = ""
        latest_source_type = str(personal_bank.get("sourceType", "")).strip()

        for paper_id, attempt in simulation_attempts.items():
            if not isinstance(attempt, dict):
                continue
            attempt_submitted_at = str(attempt.get("submittedAt", "")).strip()
            if attempt_submitted_at < latest_submitted_at:
                continue
            latest_submitted_at = attempt_submitted_at or latest_submitted_at
            latest_answer = str(attempt.get("lastAnswer", "")).strip() or latest_answer
            latest_is_correct = 1 if self._is_truthy(attempt.get("isCorrect", 0)) else 0
            latest_paper_id = str(paper_id).strip()

        if not latest_source_type:
            if latest_paper_id:
                latest_source_type = "paper"
            elif chapter_practice:
                latest_source_type = "chapterPractice"

        answer_history = chapter_practice.get("answerHistory", [])
        total_answer_duration_sec = 0
        if isinstance(answer_history, list) and answer_history:
            total_answer_duration_sec = sum(
                self._safe_int(item.get("answerDurationSec", 0))
                for item in answer_history
                if isinstance(item, dict)
            )
        if total_answer_duration_sec <= 0:
            total_answer_duration_sec = self._safe_int(chapter_practice.get("answerDurationSec", 0))

        answer_count = self._safe_int(chapter_practice.get("submitCount", 0))
        if answer_count <= 0 and chapter_practice:
            answer_count = len(answer_history) if isinstance(answer_history, list) and answer_history else 1
        correct_count = self._safe_int(chapter_practice.get("correctCount", 0))
        wrong_count = self._safe_int(wrong_book.get("wrongCount", 0))
        if wrong_count <= 0 and answer_count > 0:
            wrong_count = max(answer_count - correct_count, 0)
        wrong_book_collected_at = str(wrong_book.get("collectedAt", "")).strip()
        wrong_book_last_wrong_at = str(wrong_book.get("lastWrongAt", "")).strip()
        wrong_book_reviewed_at = str(wrong_book.get("reviewedAt", "")).strip()
        wrong_book_archived_at = str(wrong_book.get("archivedAt", "")).strip()
        wrong_book_restored_at = str(wrong_book.get("restoredAt", "")).strip()
        wrong_book_review_count = self._safe_int(wrong_book.get("reviewCount", 0))
        wrong_book_post_wrong_attempt_count = self._safe_int(wrong_book.get("postWrongAttemptCount", 0))
        wrong_book_post_wrong_correct_count = self._safe_int(wrong_book.get("postWrongCorrectCount", 0))
        wrong_book_last_reason_code = str(wrong_book.get("lastReasonCode", "")).strip()
        wrong_book_last_reason_label = str(wrong_book.get("lastReasonLabel", "")).strip()
        personal_bank_collected_at = str(personal_bank.get("collectedAt", "")).strip()
        personal_bank_source_type = str(personal_bank.get("sourceType", "")).strip()
        personal_bank_source_label = str(personal_bank.get("sourceLabel", "")).strip()

        create_time = str(stored.get("createTime", "")).strip() or latest_submitted_at
        update_time = str(stored.get("updateTime", "")).strip() or latest_submitted_at or create_time
        return {
            "id": payload["id"] or f"student-record::{student_user_id}::{question_id}",
            "studentUserId": student_user_id,
            "questionId": question_id,
            "status": payload["status"] or "ACTIVE",
            "lastSubmittedAt": latest_submitted_at,
            "lastAnswer": latest_answer,
            "lastIsCorrect": latest_is_correct,
            "answerCount": answer_count,
            "correctCount": correct_count,
            "wrongCount": wrong_count,
            "totalAnswerDurationSec": total_answer_duration_sec,
            "latestSourceType": latest_source_type,
            "latestPaperId": latest_paper_id,
            "wrongBookFlag": 1 if self._is_truthy(wrong_book.get("isCollected", 0)) else 0,
            "wrongBookArchivedFlag": 1 if self._is_truthy(wrong_book.get("isArchived", 0)) else 0,
            "wrongBookCollectedAt": wrong_book_collected_at,
            "wrongBookLastWrongAt": wrong_book_last_wrong_at,
            "wrongBookReviewedAt": wrong_book_reviewed_at,
            "wrongBookArchivedAt": wrong_book_archived_at,
            "wrongBookRestoredAt": wrong_book_restored_at,
            "wrongBookReviewCount": wrong_book_review_count,
            "wrongBookPostWrongAttemptCount": wrong_book_post_wrong_attempt_count,
            "wrongBookPostWrongCorrectCount": wrong_book_post_wrong_correct_count,
            "wrongBookLastReasonCode": wrong_book_last_reason_code,
            "wrongBookLastReasonLabel": wrong_book_last_reason_label,
            "personalBankFlag": 1 if self._is_truthy(personal_bank.get("isCollected", 0)) else 0,
            "personalBankCollectedAt": personal_bank_collected_at,
            "personalBankSourceType": personal_bank_source_type,
            "personalBankSourceLabel": personal_bank_source_label,
            "profileAnchorFlag": profile_anchor_flag,
            "extJson": payload["extJson"],
            "createTime": create_time,
            "updateTime": update_time,
        }

    def _upsert_student_question_record_row(self, connection, row: Dict[str, object]) -> None:
        connection.execute(
            """
            INSERT INTO student_question_record (
              id, studentUserId, questionId, status, lastSubmittedAt, lastAnswer, lastIsCorrect,
              answerCount, correctCount, wrongCount, totalAnswerDurationSec,
              latestSourceType, latestPaperId, wrongBookFlag, wrongBookArchivedFlag,
              wrongBookCollectedAt, wrongBookLastWrongAt, wrongBookReviewedAt, wrongBookArchivedAt, wrongBookRestoredAt,
              wrongBookReviewCount, wrongBookPostWrongAttemptCount, wrongBookPostWrongCorrectCount,
              wrongBookLastReasonCode, wrongBookLastReasonLabel,
              personalBankFlag,
              personalBankCollectedAt, personalBankSourceType, personalBankSourceLabel, profileAnchorFlag,
              extJson, createTime, updateTime
            ) VALUES (
              :id, :studentUserId, :questionId, :status, :lastSubmittedAt, :lastAnswer, :lastIsCorrect,
              :answerCount, :correctCount, :wrongCount, :totalAnswerDurationSec,
              :latestSourceType, :latestPaperId, :wrongBookFlag, :wrongBookArchivedFlag,
              :wrongBookCollectedAt, :wrongBookLastWrongAt, :wrongBookReviewedAt, :wrongBookArchivedAt, :wrongBookRestoredAt,
              :wrongBookReviewCount, :wrongBookPostWrongAttemptCount, :wrongBookPostWrongCorrectCount,
              :wrongBookLastReasonCode, :wrongBookLastReasonLabel,
              :personalBankFlag,
              :personalBankCollectedAt, :personalBankSourceType, :personalBankSourceLabel, :profileAnchorFlag,
              :extJson, :createTime, :updateTime
            )
            ON CONFLICT(studentUserId, questionId) DO UPDATE SET
              id = excluded.id,
              status = excluded.status,
              lastSubmittedAt = excluded.lastSubmittedAt,
              lastAnswer = excluded.lastAnswer,
              lastIsCorrect = excluded.lastIsCorrect,
              answerCount = excluded.answerCount,
              correctCount = excluded.correctCount,
              wrongCount = excluded.wrongCount,
              totalAnswerDurationSec = excluded.totalAnswerDurationSec,
              latestSourceType = excluded.latestSourceType,
              latestPaperId = excluded.latestPaperId,
              wrongBookFlag = excluded.wrongBookFlag,
              wrongBookArchivedFlag = excluded.wrongBookArchivedFlag,
              wrongBookCollectedAt = excluded.wrongBookCollectedAt,
              wrongBookLastWrongAt = excluded.wrongBookLastWrongAt,
              wrongBookReviewedAt = excluded.wrongBookReviewedAt,
              wrongBookArchivedAt = excluded.wrongBookArchivedAt,
              wrongBookRestoredAt = excluded.wrongBookRestoredAt,
              wrongBookReviewCount = excluded.wrongBookReviewCount,
              wrongBookPostWrongAttemptCount = excluded.wrongBookPostWrongAttemptCount,
              wrongBookPostWrongCorrectCount = excluded.wrongBookPostWrongCorrectCount,
              wrongBookLastReasonCode = excluded.wrongBookLastReasonCode,
              wrongBookLastReasonLabel = excluded.wrongBookLastReasonLabel,
              personalBankFlag = excluded.personalBankFlag,
              personalBankCollectedAt = excluded.personalBankCollectedAt,
              personalBankSourceType = excluded.personalBankSourceType,
              personalBankSourceLabel = excluded.personalBankSourceLabel,
              profileAnchorFlag = excluded.profileAnchorFlag,
              extJson = excluded.extJson,
              createTime = excluded.createTime,
              updateTime = excluded.updateTime
            """,
            row,
        )

    def _sync_student_question_record_table(self, connection, student_user_id: str, records: object) -> None:
        normalized = dict(records) if isinstance(records, dict) else {}
        seen_question_ids: List[str] = []
        for question_id, stored in normalized.items():
            normalized_row = self._normalize_student_question_record_row(student_user_id, str(question_id), stored)
            if not normalized_row:
                continue
            seen_question_ids.append(str(question_id))
            self._upsert_student_question_record_row(connection, normalized_row)
        if seen_question_ids:
            placeholders = ",".join("?" for _ in seen_question_ids)
            connection.execute(
                f"""
                DELETE FROM student_question_record
                WHERE studentUserId = ?
                  AND questionId NOT IN ({placeholders})
                """,
                (student_user_id, *seen_question_ids),
            )
            return
        connection.execute(
            "DELETE FROM student_question_record WHERE studentUserId = ?",
            (student_user_id,),
        )

    def _normalize_paper_report_row(self, report: object) -> Optional[Dict[str, object]]:
        if not isinstance(report, dict):
            return None
        report_id = str(report.get("reportId", "")).strip()
        paper_id = str(report.get("paperId", "")).strip()
        submitted_at = str(report.get("submittedAt", "")).strip()
        if not report_id:
            report_id = f"legacy::{paper_id}::{submitted_at}"
        subject_ids_raw = report.get("subjectIds", [])
        if isinstance(subject_ids_raw, list):
            subject_ids = [str(item).strip() for item in subject_ids_raw if str(item).strip()]
        else:
            subject_id_single = str(report.get("subjectId", "")).strip()
            subject_ids = [subject_id_single] if subject_id_single else []
        pending_task_ids = report.get("pendingSubjectiveTaskIds", [])
        pending_subjective_count = self._safe_int(report.get("pendingSubjectiveCount", 0))
        if isinstance(pending_task_ids, list):
            pending_subjective_count = max(pending_subjective_count, len(pending_task_ids))
        create_time = str(report.get("createTime", "")).strip() or submitted_at
        update_time = str(report.get("updateTime", "")).strip() or submitted_at or create_time
        score = self._safe_int(report.get("score", 0))
        total_score = self._safe_int(report.get("totalScore", 0))
        score_rate = self._safe_float(report.get("scoreRate", 0.0))
        if score_rate <= 0 and total_score > 0:
            score_rate = round(float(score) / float(total_score), 4)
        return {
            "id": report_id,
            "reportId": report_id,
            "studentUserId": str(report.get("studentUserId", "")).strip(),
            "paperId": paper_id,
            "subjectId": str(report.get("subjectId", "")).strip(),
            "subjectIdsJson": dump_json(subject_ids),
            "score": score,
            "totalScore": total_score,
            "scoreRate": score_rate,
            "totalElapsedSec": self._safe_int(report.get("totalElapsedSec", 0)),
            "submittedAt": submitted_at,
            "pendingSubjectiveCount": pending_subjective_count,
            "status": str(report.get("status", "ACTIVE")).strip() or "ACTIVE",
            "extJson": dump_json(report),
            "createTime": create_time,
            "updateTime": update_time,
        }

    def _sync_paper_report_table(self, connection, reports: object) -> None:
        rows = reports if isinstance(reports, list) else []
        seen_report_ids: List[str] = []
        for report in rows:
            normalized = self._normalize_paper_report_row(report)
            if not normalized:
                continue
            seen_report_ids.append(str(normalized["reportId"]))
            connection.execute(
                """
                INSERT INTO paper_report (
                  id, reportId, studentUserId, paperId, subjectId, subjectIdsJson,
                  score, totalScore, scoreRate, totalElapsedSec, submittedAt,
                  pendingSubjectiveCount, status, extJson, createTime, updateTime
                ) VALUES (
                  :id, :reportId, :studentUserId, :paperId, :subjectId, :subjectIdsJson,
                  :score, :totalScore, :scoreRate, :totalElapsedSec, :submittedAt,
                  :pendingSubjectiveCount, :status, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(reportId) DO UPDATE SET
                  id = excluded.id,
                  studentUserId = excluded.studentUserId,
                  paperId = excluded.paperId,
                  subjectId = excluded.subjectId,
                  subjectIdsJson = excluded.subjectIdsJson,
                  score = excluded.score,
                  totalScore = excluded.totalScore,
                  scoreRate = excluded.scoreRate,
                  totalElapsedSec = excluded.totalElapsedSec,
                  submittedAt = excluded.submittedAt,
                  pendingSubjectiveCount = excluded.pendingSubjectiveCount,
                  status = excluded.status,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
        if seen_report_ids:
            placeholders = ",".join("?" for _ in seen_report_ids)
            connection.execute(
                f"DELETE FROM paper_report WHERE reportId NOT IN ({placeholders})",
                tuple(seen_report_ids),
            )
            return
        connection.execute("DELETE FROM paper_report")

    def _normalize_message_send_history_row(self, item: object) -> Optional[Dict[str, object]]:
        if not isinstance(item, dict):
            return None
        trace_id = str(item.get("traceId", "")).strip()
        if not trace_id:
            return None
        create_time = str(item.get("createTime", "")).strip()
        send_at = str(item.get("sendAt", "")).strip()
        update_time = str(item.get("updateTime", "")).strip() or str(item.get("recalledAt", "")).strip() or send_at or create_time
        return {
            "id": trace_id,
            "traceId": trace_id,
            "scheduleId": str(item.get("scheduleId", "")).strip(),
            "senderUserId": str(item.get("senderUserId", "")).strip(),
            "targetMode": str(item.get("targetMode", "")).strip(),
            "targetCount": self._safe_int(item.get("targetCount", 0)),
            "sentCount": self._safe_int(item.get("sentCount", 0)),
            "category": str(item.get("category", "")).strip(),
            "title": str(item.get("title", "")).strip(),
            "content": str(item.get("content", "")).strip(),
            "sendAt": send_at,
            "status": str(item.get("status", "")).strip() or "SENT",
            "recalledAt": str(item.get("recalledAt", "")).strip(),
            "createTime": create_time,
            "updateTime": update_time,
            "extJson": dump_json(item),
        }

    def _sync_message_send_history_table(self, connection, items: object) -> None:
        rows = items if isinstance(items, list) else []
        seen_trace_ids: List[str] = []
        for item in rows:
            normalized = self._normalize_message_send_history_row(item)
            if not normalized:
                continue
            seen_trace_ids.append(str(normalized["traceId"]))
            connection.execute(
                """
                INSERT INTO message_send_history (
                  id, traceId, scheduleId, senderUserId, targetMode, targetCount, sentCount,
                  category, title, content, sendAt, status, recalledAt, createTime, updateTime, extJson
                ) VALUES (
                  :id, :traceId, :scheduleId, :senderUserId, :targetMode, :targetCount, :sentCount,
                  :category, :title, :content, :sendAt, :status, :recalledAt, :createTime, :updateTime, :extJson
                )
                ON CONFLICT(traceId) DO UPDATE SET
                  id = excluded.id,
                  scheduleId = excluded.scheduleId,
                  senderUserId = excluded.senderUserId,
                  targetMode = excluded.targetMode,
                  targetCount = excluded.targetCount,
                  sentCount = excluded.sentCount,
                  category = excluded.category,
                  title = excluded.title,
                  content = excluded.content,
                  sendAt = excluded.sendAt,
                  status = excluded.status,
                  recalledAt = excluded.recalledAt,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime,
                  extJson = excluded.extJson
                """,
                normalized,
            )
        if seen_trace_ids:
            placeholders = ",".join("?" for _ in seen_trace_ids)
            connection.execute(
                f"DELETE FROM message_send_history WHERE traceId NOT IN ({placeholders})",
                tuple(seen_trace_ids),
            )
            return
        connection.execute("DELETE FROM message_send_history")

    def get_student_question_record_row(self, student_user_id: str, question_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + STUDENT_QUESTION_RECORD_SELECT_SQL + """
                FROM student_question_record
                WHERE studentUserId = ? AND questionId = ?
                """,
                (student_user_id, question_id),
            ).fetchone()
        return dict(row) if row else None

    def get_student_profile_record_row(self, student_user_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + STUDENT_QUESTION_RECORD_SELECT_SQL + """
                FROM student_question_record
                WHERE studentUserId = ?
                  AND profileAnchorFlag = 1
                ORDER BY updateTime DESC, questionId ASC
                LIMIT 1
                """,
                (student_user_id,),
            ).fetchone()
        return dict(row) if row else None

    def _decode_student_question_record_row(self, row: sqlite3.Row) -> Dict[str, object]:
        return dict(row)

    def _list_student_question_record_payloads(
        self,
        connection,
        student_user_id: Optional[str],
    ) -> List[Dict[str, object]]:
        if student_user_id:
            rows = connection.execute(
                """
                SELECT """ + STUDENT_QUESTION_RECORD_SELECT_SQL + """
                FROM student_question_record
                WHERE studentUserId = ?
                ORDER BY updateTime DESC, questionId ASC
                """,
                (student_user_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT """ + STUDENT_QUESTION_RECORD_SELECT_SQL + """
                FROM student_question_record
                ORDER BY updateTime DESC, questionId ASC
                """
            ).fetchall()
        return [self._decode_student_question_record_row(row) for row in rows]

    def list_student_question_record_rows(self, student_user_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            return self._list_student_question_record_payloads(connection, student_user_id)

    def _decode_student_review_plan_row(self, row: sqlite3.Row) -> Dict[str, object]:
        return dict(row)

    def _decode_student_review_plan_item_row(self, row: sqlite3.Row) -> Dict[str, object]:
        return dict(row)

    def get_student_review_plan(self, student_user_id: str, plan_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + STUDENT_REVIEW_PLAN_SELECT_SQL + """
                FROM student_review_plan
                WHERE studentUserId = ? AND id = ?
                """,
                (student_user_id, plan_id),
            ).fetchone()
        return self._decode_student_review_plan_row(row) if row else None

    def list_student_review_plans(self, student_user_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT """ + STUDENT_REVIEW_PLAN_SELECT_SQL + """
                FROM student_review_plan
                WHERE studentUserId = ?
                ORDER BY updateTime DESC, id ASC
                """,
                (student_user_id,),
            ).fetchall()
        return [self._decode_student_review_plan_row(row) for row in rows]

    def list_student_review_plan_items(self, plan_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT """ + STUDENT_REVIEW_PLAN_ITEM_SELECT_SQL + """
                FROM student_review_plan_item
                WHERE planId = ?
                ORDER BY sort ASC, updateTime DESC, questionId ASC
                """,
                (plan_id,),
            ).fetchall()
        return [self._decode_student_review_plan_item_row(row) for row in rows]

    def replace_student_review_plan(
        self,
        plan_payload: Dict[str, object],
        item_payloads: List[Dict[str, object]],
    ) -> Dict[str, object]:
        plan_id = str(plan_payload.get("id", "")).strip()
        student_user_id = str(plan_payload.get("studentUserId", "")).strip()
        if not plan_id or not student_user_id:
            raise ValueError("student review plan payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO student_review_plan (
                  id, studentUserId, planType, planName, status, generatedAt, startedAt,
                  completedAt, lastExecutedAt, extJson, createTime, updateTime
                ) VALUES (
                  :id, :studentUserId, :planType, :planName, :status, :generatedAt, :startedAt,
                  :completedAt, :lastExecutedAt, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(studentUserId, planType) DO UPDATE SET
                  id = excluded.id,
                  planName = excluded.planName,
                  status = excluded.status,
                  generatedAt = excluded.generatedAt,
                  startedAt = excluded.startedAt,
                  completedAt = excluded.completedAt,
                  lastExecutedAt = excluded.lastExecutedAt,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                plan_payload,
            )
            seen_item_ids: List[str] = []
            for item_payload in item_payloads:
                connection.execute(
                    """
                    INSERT INTO student_review_plan_item (
                      id, planId, studentUserId, questionId, status, sort,
                      completedAt, extJson, createTime, updateTime
                    ) VALUES (
                      :id, :planId, :studentUserId, :questionId, :status, :sort,
                      :completedAt, :extJson, :createTime, :updateTime
                    )
                    ON CONFLICT(planId, questionId) DO UPDATE SET
                      id = excluded.id,
                      studentUserId = excluded.studentUserId,
                      status = excluded.status,
                      sort = excluded.sort,
                      completedAt = excluded.completedAt,
                      extJson = excluded.extJson,
                      createTime = excluded.createTime,
                      updateTime = excluded.updateTime
                    """,
                    item_payload,
                )
                seen_item_ids.append(str(item_payload.get("id", "")).strip())
            if seen_item_ids:
                placeholders = ",".join("?" for _ in seen_item_ids)
                connection.execute(
                    f"DELETE FROM student_review_plan_item WHERE planId = ? AND id NOT IN ({placeholders})",
                    (plan_id, *seen_item_ids),
                )
            else:
                connection.execute(
                    "DELETE FROM student_review_plan_item WHERE planId = ?",
                    (plan_id,),
                )
            connection.commit()
        saved = self.get_student_review_plan(student_user_id, plan_id)
        return saved or dict(plan_payload)

    def _decode_paper_report_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        payload.setdefault("reportId", str(row["reportId"]))
        payload.setdefault("studentUserId", str(row["studentUserId"]))
        payload.setdefault("paperId", str(row["paperId"]))
        payload.setdefault("subjectId", str(row["subjectId"]))
        payload.setdefault("score", self._safe_int(row["score"]))
        payload.setdefault("totalScore", self._safe_int(row["totalScore"]))
        payload.setdefault("scoreRate", self._safe_float(row["scoreRate"]))
        payload.setdefault("totalElapsedSec", self._safe_int(row["totalElapsedSec"]))
        payload.setdefault("submittedAt", str(row["submittedAt"]))
        payload.setdefault("status", str(row["status"]))
        payload.setdefault("pendingSubjectiveCount", self._safe_int(row["pendingSubjectiveCount"]))
        subject_ids = load_json_object(str(row["subjectIdsJson"]))
        if isinstance(subject_ids, list):
            payload.setdefault("subjectIds", [str(item) for item in subject_ids if str(item).strip()])
        return payload

    def list_paper_reports_by_student(self, student_user_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            if student_user_id:
                rows = connection.execute(
                    """
                    SELECT """ + PAPER_REPORT_SELECT_SQL + """
                    FROM paper_report
                    WHERE studentUserId = ?
                    ORDER BY submittedAt DESC, reportId DESC
                    """,
                    (student_user_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT """ + PAPER_REPORT_SELECT_SQL + """
                    FROM paper_report
                    ORDER BY submittedAt DESC, reportId DESC
                    """
                ).fetchall()
        return [self._decode_paper_report_row(row) for row in rows]

    def get_paper_report_payload(self, report_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + PAPER_REPORT_SELECT_SQL + """
                FROM paper_report
                WHERE reportId = ?
                """,
                (report_id,),
            ).fetchone()
        return self._decode_paper_report_row(row) if row else None

    def find_student_paper_report_by_paper_and_day(
        self,
        student_user_id: str,
        paper_id: str,
        day: str,
    ) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + PAPER_REPORT_SELECT_SQL + """
                FROM paper_report
                WHERE studentUserId = ?
                  AND paperId = ?
                  AND substr(submittedAt, 1, 10) = ?
                ORDER BY submittedAt DESC, reportId DESC
                LIMIT 1
                """,
                (student_user_id, paper_id, day),
            ).fetchone()
        return self._decode_paper_report_row(row) if row else None

    def get_paper_report_row(self, report_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + PAPER_REPORT_SELECT_SQL + """
                FROM paper_report
                WHERE reportId = ?
                """,
                (report_id,),
            ).fetchone()
        return dict(row) if row else None

    def _normalize_exam_task_row(self, task: object) -> Optional[Dict[str, object]]:
        if not isinstance(task, dict):
            return None
        task_id = str(task.get("id", "")).strip()
        if not task_id:
            return None
        create_time = str(task.get("createTime", "")).strip()
        update_time = str(task.get("updateTime", "")).strip() or create_time
        ext_json = task.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = load_json_object(ext_json)
            if not isinstance(ext_json, dict):
                ext_json = {}
        return {
            "id": task_id,
            "taskName": str(task.get("taskName", "")).strip(),
            "taskType": str(task.get("taskType", "")).strip(),
            "subjectId": str(task.get("subjectId", "")).strip(),
            "examCategoryCode": str(task.get("examCategoryCode", "")).strip(),
            "jointExamGroupCode": str(task.get("jointExamGroupCode", "")).strip(),
            "subjectCode": str(task.get("subjectCode", "")).strip(),
            "sourceType": str(task.get("sourceType", "")).strip(),
            "sourceId": str(task.get("sourceId", "")).strip(),
            "sourceLabel": str(task.get("sourceLabel", "")).strip(),
            "teacherUserId": str(task.get("teacherUserId", "")).strip(),
            "teacherName": str(task.get("teacherName", "")).strip(),
            "description": str(task.get("description", "")).strip(),
            "allowRedo": 1 if self._is_truthy(task.get("allowRedo", False)) else 0,
            "dueAt": str(task.get("dueAt", "")).strip(),
            "status": str(task.get("status", "DRAFT")).strip() or "DRAFT",
            "extJson": dump_json(ext_json),
            "createTime": create_time,
            "updateTime": update_time,
        }

    def _decode_exam_task_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        payload.setdefault("id", str(row["id"]))
        payload.setdefault("taskName", str(row["taskName"]))
        payload.setdefault("taskType", str(row["taskType"]))
        payload.setdefault("subjectId", str(row["subjectId"]))
        payload.setdefault("examCategoryCode", str(row["examCategoryCode"]))
        payload.setdefault("jointExamGroupCode", str(row["jointExamGroupCode"]))
        payload.setdefault("subjectCode", str(row["subjectCode"]))
        payload.setdefault("sourceType", str(row["sourceType"]))
        payload.setdefault("sourceId", str(row["sourceId"]))
        payload.setdefault("sourceLabel", str(row["sourceLabel"]))
        payload.setdefault("teacherUserId", str(row["teacherUserId"]))
        payload.setdefault("teacherName", str(row["teacherName"]))
        payload.setdefault("description", str(row["description"]))
        payload.setdefault("allowRedo", self._is_truthy(row["allowRedo"]))
        payload.setdefault("dueAt", str(row["dueAt"]))
        payload.setdefault("status", str(row["status"]))
        payload.setdefault("createTime", str(row["createTime"]))
        payload.setdefault("updateTime", str(row["updateTime"]))
        return payload

    def list_exam_tasks(
        self,
        filters: Dict[str, str],
        page: int,
        size: int,
        teacher_user_id: str = "",
    ) -> Tuple[List[Dict[str, object]], int]:
        clauses = ["1 = 1"]
        params: Dict[str, object] = {}
        if teacher_user_id:
            clauses.append("teacherUserId = :teacherUserId")
            params["teacherUserId"] = teacher_user_id
        keyword = str(filters.get("keyword", "")).strip()
        if keyword:
            clauses.append("(taskName LIKE :keyword OR description LIKE :keyword OR teacherName LIKE :keyword)")
            params["keyword"] = f"%{keyword}%"
        for key in ("taskType", "status", "subjectCode"):
            if filters.get(key):
                clauses.append(f"{key} = :{key}")
                params[key] = str(filters[key]).strip()
        where_clause = " AND ".join(clauses)
        offset = (page - 1) * size
        params.update({"limit": size, "offset": offset})
        with get_connection(self.db_path) as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS total FROM exam_task WHERE {where_clause}",
                params,
            ).fetchone()["total"]
            rows = connection.execute(
                f"""
                SELECT {EXAM_TASK_SELECT_SQL}
                FROM exam_task
                WHERE {where_clause}
                ORDER BY dueAt ASC, updateTime DESC, id DESC
                LIMIT :limit OFFSET :offset
                """,
                params,
            ).fetchall()
        return [self._decode_exam_task_row(row) for row in rows], total

    def get_exam_task(self, task_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {EXAM_TASK_SELECT_SQL}
                FROM exam_task
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
        return self._decode_exam_task_row(row) if row else None

    def upsert_exam_task(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = self._normalize_exam_task_row(payload)
        if not normalized:
            raise ValueError("exam task payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO exam_task (
                  id, taskName, taskType, subjectId, examCategoryCode, jointExamGroupCode, subjectCode,
                  sourceType, sourceId, sourceLabel, teacherUserId, teacherName, description,
                  allowRedo, dueAt, status, extJson, createTime, updateTime
                ) VALUES (
                  :id, :taskName, :taskType, :subjectId, :examCategoryCode, :jointExamGroupCode, :subjectCode,
                  :sourceType, :sourceId, :sourceLabel, :teacherUserId, :teacherName, :description,
                  :allowRedo, :dueAt, :status, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(id) DO UPDATE SET
                  taskName = excluded.taskName,
                  taskType = excluded.taskType,
                  subjectId = excluded.subjectId,
                  examCategoryCode = excluded.examCategoryCode,
                  jointExamGroupCode = excluded.jointExamGroupCode,
                  subjectCode = excluded.subjectCode,
                  sourceType = excluded.sourceType,
                  sourceId = excluded.sourceId,
                  sourceLabel = excluded.sourceLabel,
                  teacherUserId = excluded.teacherUserId,
                  teacherName = excluded.teacherName,
                  description = excluded.description,
                  allowRedo = excluded.allowRedo,
                  dueAt = excluded.dueAt,
                  status = excluded.status,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        return self.get_exam_task(str(normalized["id"])) or dict(payload)

    def replace_exam_task_targets(self, task_id: str, targets: List[Dict[str, object]]) -> List[Dict[str, object]]:
        normalized_rows: List[Dict[str, object]] = []
        for target in targets:
            target_id = str(target.get("id", "")).strip()
            if not target_id:
                continue
            normalized_rows.append(
                {
                    "id": target_id,
                    "taskId": task_id,
                    "targetType": str(target.get("targetType", "")).strip(),
                    "targetId": str(target.get("targetId", "")).strip(),
                    "targetName": str(target.get("targetName", "")).strip(),
                    "createTime": str(target.get("createTime", "")).strip(),
                }
            )
        with get_connection(self.db_path) as connection:
            connection.execute("DELETE FROM exam_task_target WHERE taskId = ?", (task_id,))
            for row in normalized_rows:
                connection.execute(
                    """
                    INSERT INTO exam_task_target (id, taskId, targetType, targetId, targetName, createTime)
                    VALUES (:id, :taskId, :targetType, :targetId, :targetName, :createTime)
                    """,
                    row,
                )
            connection.commit()
        return self.list_exam_task_targets(task_id)

    def list_exam_task_targets(self, task_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT {EXAM_TASK_TARGET_SELECT_SQL}
                FROM exam_task_target
                WHERE taskId = ?
                ORDER BY targetType ASC, targetId ASC, id ASC
                """,
                (task_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _normalize_exam_task_assignment_row(self, assignment: object) -> Optional[Dict[str, object]]:
        if not isinstance(assignment, dict):
            return None
        assignment_id = str(assignment.get("id", "")).strip()
        task_id = str(assignment.get("taskId", "")).strip()
        student_user_id = str(assignment.get("studentUserId", "")).strip()
        if not assignment_id or not task_id or not student_user_id:
            return None
        ext_json = assignment.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = load_json_object(ext_json)
            if not isinstance(ext_json, dict):
                ext_json = {}
        return {
            "id": assignment_id,
            "taskId": task_id,
            "studentUserId": student_user_id,
            "status": str(assignment.get("status", "NOT_STARTED")).strip() or "NOT_STARTED",
            "score": self._safe_int(assignment.get("score", 0)),
            "totalScore": self._safe_int(assignment.get("totalScore", 0)),
            "startedAt": str(assignment.get("startedAt", "")).strip(),
            "submittedAt": str(assignment.get("submittedAt", "")).strip(),
            "completedAt": str(assignment.get("completedAt", "")).strip(),
            "expiredAt": str(assignment.get("expiredAt", "")).strip(),
            "lastPaperId": str(assignment.get("lastPaperId", "")).strip(),
            "redoCount": self._safe_int(assignment.get("redoCount", 0)),
            "maxRedoCount": self._safe_int(assignment.get("maxRedoCount", 0)),
            "extJson": dump_json(ext_json),
            "createTime": str(assignment.get("createTime", "")).strip(),
            "updateTime": str(assignment.get("updateTime", "")).strip() or str(assignment.get("createTime", "")).strip(),
        }

    def _decode_exam_task_assignment_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        payload.setdefault("id", str(row["id"]))
        payload.setdefault("taskId", str(row["taskId"]))
        payload.setdefault("studentUserId", str(row["studentUserId"]))
        payload.setdefault("status", str(row["status"]))
        payload.setdefault("score", self._safe_int(row["score"]))
        payload.setdefault("totalScore", self._safe_int(row["totalScore"]))
        payload.setdefault("startedAt", str(row["startedAt"]))
        payload.setdefault("submittedAt", str(row["submittedAt"]))
        payload.setdefault("completedAt", str(row["completedAt"]))
        payload.setdefault("expiredAt", str(row["expiredAt"]))
        payload.setdefault("lastPaperId", str(row["lastPaperId"]))
        payload.setdefault("redoCount", self._safe_int(row["redoCount"]))
        payload.setdefault("maxRedoCount", self._safe_int(row["maxRedoCount"]))
        payload.setdefault("createTime", str(row["createTime"]))
        payload.setdefault("updateTime", str(row["updateTime"]))
        return payload

    def upsert_exam_task_assignment(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = self._normalize_exam_task_assignment_row(payload)
        if not normalized:
            raise ValueError("exam task assignment payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO exam_task_assignment (
                  id, taskId, studentUserId, status, score, totalScore, startedAt, submittedAt,
                  completedAt, expiredAt, lastPaperId, redoCount, maxRedoCount, extJson, createTime, updateTime
                ) VALUES (
                  :id, :taskId, :studentUserId, :status, :score, :totalScore, :startedAt, :submittedAt,
                  :completedAt, :expiredAt, :lastPaperId, :redoCount, :maxRedoCount, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(taskId, studentUserId) DO UPDATE SET
                  id = excluded.id,
                  status = excluded.status,
                  score = excluded.score,
                  totalScore = excluded.totalScore,
                  startedAt = excluded.startedAt,
                  submittedAt = excluded.submittedAt,
                  completedAt = excluded.completedAt,
                  expiredAt = excluded.expiredAt,
                  lastPaperId = excluded.lastPaperId,
                  redoCount = excluded.redoCount,
                  maxRedoCount = excluded.maxRedoCount,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        return self.get_exam_task_assignment(str(normalized["id"])) or dict(payload)

    def get_exam_task_assignment(self, assignment_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {EXAM_TASK_ASSIGNMENT_SELECT_SQL}
                FROM exam_task_assignment
                WHERE id = ?
                """,
                (assignment_id,),
            ).fetchone()
        return self._decode_exam_task_assignment_row(row) if row else None

    def find_exam_task_assignment(self, task_id: str, student_user_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {EXAM_TASK_ASSIGNMENT_SELECT_SQL}
                FROM exam_task_assignment
                WHERE taskId = ? AND studentUserId = ?
                """,
                (task_id, student_user_id),
            ).fetchone()
        return self._decode_exam_task_assignment_row(row) if row else None

    def list_exam_task_assignments_for_task(self, task_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT {EXAM_TASK_ASSIGNMENT_SELECT_SQL}
                FROM exam_task_assignment
                WHERE taskId = ?
                ORDER BY updateTime DESC, id DESC
                """,
                (task_id,),
            ).fetchall()
        return [self._decode_exam_task_assignment_row(row) for row in rows]

    def list_student_exam_task_assignments(
        self,
        student_user_id: str,
        filters: Dict[str, str],
        page: int,
        size: int,
    ) -> Tuple[List[Dict[str, object]], int]:
        clauses = ["a.studentUserId = :studentUserId", "t.status = 'PUBLISHED'"]
        params: Dict[str, object] = {"studentUserId": student_user_id}
        if filters.get("status"):
            clauses.append("a.status = :status")
            params["status"] = str(filters["status"]).strip()
        if filters.get("taskType"):
            clauses.append("t.taskType = :taskType")
            params["taskType"] = str(filters["taskType"]).strip()
        if filters.get("subjectCode"):
            clauses.append("t.subjectCode = :subjectCode")
            params["subjectCode"] = str(filters["subjectCode"]).strip()
        where_clause = " AND ".join(clauses)
        offset = (page - 1) * size
        params.update({"limit": size, "offset": offset})
        with get_connection(self.db_path) as connection:
            total = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM exam_task_assignment AS a
                JOIN exam_task AS t ON t.id = a.taskId
                WHERE {where_clause}
                """,
                params,
            ).fetchone()["total"]
            rows = connection.execute(
                f"""
                SELECT
                  {", ".join(f"a.{field}" for field in EXAM_TASK_ASSIGNMENT_FIELDS)},
                  {", ".join(f"t.{field} AS task_{field}" for field in EXAM_TASK_FIELDS)}
                FROM exam_task_assignment AS a
                JOIN exam_task AS t ON t.id = a.taskId
                WHERE {where_clause}
                ORDER BY
                  CASE WHEN t.dueAt = '' THEN 1 ELSE 0 END ASC,
                  t.dueAt ASC,
                  a.updateTime DESC,
                  a.id DESC
                LIMIT :limit OFFSET :offset
                """,
                params,
            ).fetchall()
        items: List[Dict[str, object]] = []
        for row in rows:
            row_map = dict(row)
            assignment_payload = self._decode_exam_task_assignment_row(row)
            task_row = {field: row_map.get(f"task_{field}") for field in EXAM_TASK_FIELDS}
            task_payload = {
                "id": str(task_row.get("id", "")),
                "taskName": str(task_row.get("taskName", "")),
                "taskType": str(task_row.get("taskType", "")),
                "subjectId": str(task_row.get("subjectId", "")),
                "examCategoryCode": str(task_row.get("examCategoryCode", "")),
                "jointExamGroupCode": str(task_row.get("jointExamGroupCode", "")),
                "subjectCode": str(task_row.get("subjectCode", "")),
                "sourceType": str(task_row.get("sourceType", "")),
                "sourceId": str(task_row.get("sourceId", "")),
                "sourceLabel": str(task_row.get("sourceLabel", "")),
                "teacherUserId": str(task_row.get("teacherUserId", "")),
                "teacherName": str(task_row.get("teacherName", "")),
                "description": str(task_row.get("description", "")),
                "allowRedo": self._is_truthy(task_row.get("allowRedo", 0)),
                "dueAt": str(task_row.get("dueAt", "")),
                "status": str(task_row.get("status", "")),
                "createTime": str(task_row.get("createTime", "")),
                "updateTime": str(task_row.get("updateTime", "")),
                "extJson": load_json_object(str(task_row.get("extJson", "{}"))),
            }
            assignment_payload["task"] = task_payload
            items.append(assignment_payload)
        return items, total

    def _normalize_mock_exam_session_row(self, session: object) -> Optional[Dict[str, object]]:
        if not isinstance(session, dict):
            return None
        session_id = str(session.get("id", "")).strip()
        if not session_id:
            return None
        rule_snapshot = session.get("ruleSnapshot", session.get("ruleSnapshotJson", {}))
        if not isinstance(rule_snapshot, dict):
            rule_snapshot = load_json_object(rule_snapshot)
            if not isinstance(rule_snapshot, dict):
                rule_snapshot = {}
        degrade_summary = session.get("degradeSummary", session.get("degradeSummaryJson", {}))
        if not isinstance(degrade_summary, dict):
            degrade_summary = load_json_object(degrade_summary)
            if not isinstance(degrade_summary, dict):
                degrade_summary = {}
        return {
            "id": session_id,
            "studentUserId": str(session.get("studentUserId", "")).strip(),
            "subjectCode": str(session.get("subjectCode", "")).strip(),
            "examCategoryCode": str(session.get("examCategoryCode", "")).strip(),
            "jointExamGroupCode": str(session.get("jointExamGroupCode", "")).strip(),
            "paperId": str(session.get("paperId", "")).strip(),
            "paperName": str(session.get("paperName", "")).strip(),
            "questionCount": self._safe_int(session.get("questionCount", 0)),
            "totalScore": self._safe_int(session.get("totalScore", 0)),
            "durationMinutes": self._safe_int(session.get("durationMinutes", 0)),
            "syllabusVersion": str(session.get("syllabusVersion", "")).strip(),
            "status": str(session.get("status", "ACTIVE")).strip() or "ACTIVE",
            "ruleSnapshotJson": dump_json(rule_snapshot),
            "degradeSummaryJson": dump_json(degrade_summary),
            "startedAt": str(session.get("startedAt", "")).strip(),
            "submittedAt": str(session.get("submittedAt", "")).strip(),
            "createTime": str(session.get("createTime", "")).strip(),
            "updateTime": str(session.get("updateTime", "")).strip() or str(session.get("createTime", "")).strip(),
        }

    def _decode_mock_exam_session_row(self, row: sqlite3.Row) -> Dict[str, object]:
        return {
            "id": str(row["id"]),
            "studentUserId": str(row["studentUserId"]),
            "subjectCode": str(row["subjectCode"]),
            "examCategoryCode": str(row["examCategoryCode"]),
            "jointExamGroupCode": str(row["jointExamGroupCode"]),
            "paperId": str(row["paperId"]),
            "paperName": str(row["paperName"]),
            "questionCount": self._safe_int(row["questionCount"]),
            "totalScore": self._safe_int(row["totalScore"]),
            "durationMinutes": self._safe_int(row["durationMinutes"]),
            "syllabusVersion": str(row["syllabusVersion"]),
            "status": str(row["status"]),
            "ruleSnapshot": load_json_object(str(row["ruleSnapshotJson"])),
            "degradeSummary": load_json_object(str(row["degradeSummaryJson"])),
            "startedAt": str(row["startedAt"]),
            "submittedAt": str(row["submittedAt"]),
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def upsert_mock_exam_session(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = self._normalize_mock_exam_session_row(payload)
        if not normalized:
            raise ValueError("mock exam session payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO mock_exam_session (
                  id, studentUserId, subjectCode, examCategoryCode, jointExamGroupCode, paperId,
                  paperName, questionCount, totalScore, durationMinutes, syllabusVersion, status,
                  ruleSnapshotJson, degradeSummaryJson, startedAt, submittedAt, createTime, updateTime
                ) VALUES (
                  :id, :studentUserId, :subjectCode, :examCategoryCode, :jointExamGroupCode, :paperId,
                  :paperName, :questionCount, :totalScore, :durationMinutes, :syllabusVersion, :status,
                  :ruleSnapshotJson, :degradeSummaryJson, :startedAt, :submittedAt, :createTime, :updateTime
                )
                ON CONFLICT(id) DO UPDATE SET
                  studentUserId = excluded.studentUserId,
                  subjectCode = excluded.subjectCode,
                  examCategoryCode = excluded.examCategoryCode,
                  jointExamGroupCode = excluded.jointExamGroupCode,
                  paperId = excluded.paperId,
                  paperName = excluded.paperName,
                  questionCount = excluded.questionCount,
                  totalScore = excluded.totalScore,
                  durationMinutes = excluded.durationMinutes,
                  syllabusVersion = excluded.syllabusVersion,
                  status = excluded.status,
                  ruleSnapshotJson = excluded.ruleSnapshotJson,
                  degradeSummaryJson = excluded.degradeSummaryJson,
                  startedAt = excluded.startedAt,
                  submittedAt = excluded.submittedAt,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        return self.get_mock_exam_session(str(normalized["id"])) or dict(payload)

    def get_mock_exam_session(self, session_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {MOCK_EXAM_SESSION_SELECT_SQL}
                FROM mock_exam_session
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
        return self._decode_mock_exam_session_row(row) if row else None

    def find_active_mock_exam_session(self, student_user_id: str, subject_code: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {MOCK_EXAM_SESSION_SELECT_SQL}
                FROM mock_exam_session
                WHERE studentUserId = ?
                  AND subjectCode = ?
                  AND status = 'ACTIVE'
                ORDER BY createTime DESC, id DESC
                LIMIT 1
                """,
                (student_user_id, subject_code),
            ).fetchone()
        return self._decode_mock_exam_session_row(row) if row else None

    def find_mock_exam_session_by_paper(self, student_user_id: str, paper_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {MOCK_EXAM_SESSION_SELECT_SQL}
                FROM mock_exam_session
                WHERE studentUserId = ?
                  AND paperId = ?
                ORDER BY createTime DESC, id DESC
                LIMIT 1
                """,
                (student_user_id, paper_id),
            ).fetchone()
        return self._decode_mock_exam_session_row(row) if row else None

    def _decode_challenge_point_subject_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        payload.setdefault("id", str(row["id"]))
        payload.setdefault("studentUserId", str(row["studentUserId"]))
        payload.setdefault("subjectCode", str(row["subjectCode"]))
        payload.setdefault("totalPoints", self._safe_int(row["totalPoints"]))
        payload.setdefault("lastAwardedAt", str(row["lastAwardedAt"]))
        payload.setdefault("createTime", str(row["createTime"]))
        payload.setdefault("updateTime", str(row["updateTime"]))
        return payload

    def _decode_student_daily_progress_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        try:
            rewarded_keys = json.loads(str(row["rewardedKeysJson"] or "[]"))
        except (TypeError, ValueError, json.JSONDecodeError):
            rewarded_keys = []
        if not isinstance(rewarded_keys, list):
            rewarded_keys = []
        payload.setdefault("id", str(row["id"]))
        payload.setdefault("studentUserId", str(row["studentUserId"]))
        payload.setdefault("progressDate", str(row["progressDate"]))
        payload.setdefault("checkInCount", self._safe_int(row["checkInCount"]))
        payload.setdefault("practiceAnswers", self._safe_int(row["practiceAnswers"]))
        payload.setdefault("papersCompleted", self._safe_int(row["papersCompleted"]))
        payload.setdefault("wrongBookReviewed", self._safe_int(row["wrongBookReviewed"]))
        payload.setdefault("rewardedKeys", [str(item).strip() for item in rewarded_keys if str(item).strip()])
        payload.setdefault("createTime", str(row["createTime"]))
        payload.setdefault("updateTime", str(row["updateTime"]))
        return payload

    def _normalize_student_daily_progress_payload(self, payload: Dict[str, object]) -> Dict[str, object]:
        student_user_id = str(payload.get("studentUserId", "")).strip()
        progress_date = str(payload.get("progressDate", "")).strip()
        rewarded_keys_raw = payload.get("rewardedKeys", [])
        if isinstance(rewarded_keys_raw, list):
            rewarded_keys = rewarded_keys_raw
        else:
            try:
                rewarded_keys = json.loads(str(rewarded_keys_raw or "[]"))
            except (TypeError, ValueError, json.JSONDecodeError):
                rewarded_keys = []
        if not isinstance(rewarded_keys, list):
            rewarded_keys = []
        ext_json = payload.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = load_json_object(str(ext_json or "{}"))
        if not isinstance(ext_json, dict):
            ext_json = {}
        create_time = str(payload.get("createTime", "")).strip() or progress_date
        update_time = str(payload.get("updateTime", "")).strip() or create_time
        return {
            "id": str(payload.get("id", "")).strip() or f"{student_user_id}::{progress_date}",
            "studentUserId": student_user_id,
            "progressDate": progress_date,
            "checkInCount": self._safe_int(payload.get("checkInCount", 0)),
            "practiceAnswers": self._safe_int(payload.get("practiceAnswers", 0)),
            "papersCompleted": self._safe_int(payload.get("papersCompleted", 0)),
            "wrongBookReviewed": self._safe_int(payload.get("wrongBookReviewed", 0)),
            "rewardedKeysJson": dump_json([str(item).strip() for item in rewarded_keys if str(item).strip()]),
            "extJson": dump_json(ext_json),
            "createTime": create_time,
            "updateTime": update_time,
        }

    def get_student_daily_progress(self, student_user_id: str, progress_date: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + STUDENT_DAILY_PROGRESS_SELECT_SQL + """
                FROM student_daily_progress
                WHERE studentUserId = ? AND progressDate = ?
                """,
                (student_user_id, progress_date),
            ).fetchone()
        return self._decode_student_daily_progress_row(row) if row else None

    def list_student_daily_progress(self, student_user_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT """ + STUDENT_DAILY_PROGRESS_SELECT_SQL + """
                FROM student_daily_progress
                WHERE studentUserId = ?
                ORDER BY progressDate ASC
                """,
                (student_user_id,),
            ).fetchall()
        return [self._decode_student_daily_progress_row(row) for row in rows]

    def upsert_student_daily_progress(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = self._normalize_student_daily_progress_payload(payload)
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO student_daily_progress (
                  id, studentUserId, progressDate, checkInCount, practiceAnswers, papersCompleted,
                  wrongBookReviewed, rewardedKeysJson, extJson, createTime, updateTime
                ) VALUES (
                  :id, :studentUserId, :progressDate, :checkInCount, :practiceAnswers, :papersCompleted,
                  :wrongBookReviewed, :rewardedKeysJson, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(studentUserId, progressDate) DO UPDATE SET
                  id = excluded.id,
                  checkInCount = excluded.checkInCount,
                  practiceAnswers = excluded.practiceAnswers,
                  papersCompleted = excluded.papersCompleted,
                  wrongBookReviewed = excluded.wrongBookReviewed,
                  rewardedKeysJson = excluded.rewardedKeysJson,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        saved = self.get_student_daily_progress(normalized["studentUserId"], normalized["progressDate"])
        return saved or normalized

    def increment_student_daily_progress_metric(
        self,
        student_user_id: str,
        progress_date: str,
        metric_key: str,
        delta: int,
        now_iso: str,
    ) -> Dict[str, object]:
        allowed_metrics = {"checkInCount", "practiceAnswers", "papersCompleted", "wrongBookReviewed"}
        if metric_key not in allowed_metrics:
            raise ValueError(f"unsupported student daily progress metric: {metric_key}")
        normalized_delta = self._safe_int(delta)
        if normalized_delta == 0:
            return self.get_student_daily_progress(student_user_id, progress_date) or {}
        row_id = f"{student_user_id}::{progress_date}"
        with get_connection(self.db_path) as connection:
            connection.execute(
                f"""
                INSERT INTO student_daily_progress (
                  id, studentUserId, progressDate, checkInCount, practiceAnswers, papersCompleted,
                  wrongBookReviewed, rewardedKeysJson, extJson, createTime, updateTime
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(studentUserId, progressDate) DO UPDATE SET
                  {metric_key} = student_daily_progress.{metric_key} + excluded.{metric_key},
                  updateTime = excluded.updateTime
                """,
                (
                    row_id,
                    student_user_id,
                    progress_date,
                    normalized_delta if metric_key == "checkInCount" else 0,
                    normalized_delta if metric_key == "practiceAnswers" else 0,
                    normalized_delta if metric_key == "papersCompleted" else 0,
                    normalized_delta if metric_key == "wrongBookReviewed" else 0,
                    dump_json([]),
                    dump_json({}),
                    now_iso,
                    now_iso,
                ),
            )
            connection.commit()
        return self.get_student_daily_progress(student_user_id, progress_date) or {}

    def add_student_daily_progress_rewarded_key(
        self,
        student_user_id: str,
        progress_date: str,
        rewarded_key: str,
        now_iso: str,
    ) -> Dict[str, object]:
        current = self.get_student_daily_progress(student_user_id, progress_date) or {
            "studentUserId": student_user_id,
            "progressDate": progress_date,
            "checkInCount": 0,
            "practiceAnswers": 0,
            "papersCompleted": 0,
            "wrongBookReviewed": 0,
            "rewardedKeys": [],
            "createTime": now_iso,
        }
        rewarded_keys = [str(item).strip() for item in current.get("rewardedKeys", []) if str(item).strip()]
        normalized_key = str(rewarded_key or "").strip()
        if normalized_key and normalized_key not in rewarded_keys:
            rewarded_keys.append(normalized_key)
        current["rewardedKeys"] = rewarded_keys
        current["updateTime"] = now_iso
        return self.upsert_student_daily_progress(current)

    def _decode_student_points_ledger_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        payload.setdefault("id", str(row["id"]))
        payload.setdefault("studentUserId", str(row["studentUserId"]))
        payload.setdefault("eventKey", str(row["eventKey"]))
        payload.setdefault("reason", str(row["reason"]))
        payload.setdefault("points", self._safe_int(row["points"]))
        payload.setdefault("createTime", str(row["createTime"]))
        payload.setdefault("updateTime", str(row["updateTime"]))
        return payload

    def _decode_student_profile_state_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        try:
            unlocked_titles = json.loads(str(row["unlockedTitlesJson"] or "[]"))
        except (TypeError, ValueError, json.JSONDecodeError):
            unlocked_titles = []
        if not isinstance(unlocked_titles, list):
            unlocked_titles = []
        try:
            check_in_dates = json.loads(str(row["checkInDatesJson"] or "[]"))
        except (TypeError, ValueError, json.JSONDecodeError):
            check_in_dates = []
        if not isinstance(check_in_dates, list):
            check_in_dates = []
        payload.setdefault("id", str(row["id"]))
        payload.setdefault("studentUserId", str(row["studentUserId"]))
        payload.setdefault("examCategoryCode", str(row["examCategoryCode"] or "").strip() or "SCIENCE_ENGINEERING")
        payload.setdefault("jointExamGroupCode", str(row["jointExamGroupCode"] or "").strip() or "SCIENCE_ENGINEERING_3")
        payload.setdefault("vocationalMajor", str(payload.get("vocationalMajor", "")).strip())
        payload.setdefault("prepStage", str(payload.get("prepStage", "")).strip())
        payload.setdefault("points", self._safe_int(row["points"]))
        payload.setdefault("title", str(row["title"]))
        payload.setdefault("unlockedTitles", [str(item).strip() for item in unlocked_titles if str(item).strip()])
        payload.setdefault("checkInDates", [str(item).strip() for item in check_in_dates if str(item).strip()])
        payload.setdefault(
            "aiQuota",
            {
                "dailyLimit": self._safe_int(row["aiDailyLimit"]),
                "usedCount": self._safe_int(row["aiUsedCount"]),
                "quotaDate": str(row["aiQuotaDate"]),
            },
        )
        payload.setdefault(
            "examSession",
            {
                "answeredCount": self._safe_int(row["examAnsweredCount"]),
                "elapsedSec": self._safe_int(row["examElapsedSec"]),
                "updateTime": str(row["examUpdateTime"]),
            },
        )
        payload.setdefault("createTime", str(row["createTime"]))
        payload.setdefault("updateTime", str(row["updateTime"]))
        return payload

    def _normalize_student_profile_state_payload(self, payload: Dict[str, object]) -> Dict[str, object]:
        student_user_id = str(payload.get("studentUserId", "")).strip()
        unlocked_titles_raw = payload.get("unlockedTitles", [])
        if isinstance(unlocked_titles_raw, list):
            unlocked_titles = unlocked_titles_raw
        else:
            try:
                unlocked_titles = json.loads(str(unlocked_titles_raw or "[]"))
            except (TypeError, ValueError, json.JSONDecodeError):
                unlocked_titles = []
        if not isinstance(unlocked_titles, list):
            unlocked_titles = []
        check_in_dates_raw = payload.get("checkInDates", [])
        if isinstance(check_in_dates_raw, list):
            check_in_dates = check_in_dates_raw
        else:
            try:
                check_in_dates = json.loads(str(check_in_dates_raw or "[]"))
            except (TypeError, ValueError, json.JSONDecodeError):
                check_in_dates = []
        if not isinstance(check_in_dates, list):
            check_in_dates = []
        ai_quota = payload.get("aiQuota", {})
        if not isinstance(ai_quota, dict):
            ai_quota = load_json_object(str(ai_quota or "{}"))
        if not isinstance(ai_quota, dict):
            ai_quota = {}
        exam_session = payload.get("examSession", {})
        if not isinstance(exam_session, dict):
            exam_session = load_json_object(str(exam_session or "{}"))
        if not isinstance(exam_session, dict):
            exam_session = {}
        ext_json = payload.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = load_json_object(str(ext_json or "{}"))
        if not isinstance(ext_json, dict):
            ext_json = {}
        ext_json["vocationalMajor"] = str(payload.get("vocationalMajor", ext_json.get("vocationalMajor", ""))).strip()
        ext_json["prepStage"] = str(payload.get("prepStage", ext_json.get("prepStage", ""))).strip()
        create_time = str(payload.get("createTime", "")).strip() or str(payload.get("updateTime", "")).strip()
        update_time = str(payload.get("updateTime", "")).strip() or create_time
        return {
            "id": str(payload.get("id", "")).strip() or student_user_id,
            "studentUserId": student_user_id,
            "examCategoryCode": str(payload.get("examCategoryCode", "")).strip() or "SCIENCE_ENGINEERING",
            "jointExamGroupCode": str(payload.get("jointExamGroupCode", "")).strip() or "SCIENCE_ENGINEERING_3",
            "points": self._safe_int(payload.get("points", 0)),
            "title": str(payload.get("title", "")).strip() or "备考新星",
            "unlockedTitlesJson": dump_json([str(item).strip() for item in unlocked_titles if str(item).strip()]),
            "checkInDatesJson": dump_json([str(item).strip() for item in check_in_dates if str(item).strip()]),
            "aiDailyLimit": self._safe_int(ai_quota.get("dailyLimit", 20)),
            "aiUsedCount": self._safe_int(ai_quota.get("usedCount", 0)),
            "aiQuotaDate": str(ai_quota.get("quotaDate", "")).strip(),
            "examAnsweredCount": self._safe_int(exam_session.get("answeredCount", 0)),
            "examElapsedSec": self._safe_int(exam_session.get("elapsedSec", 0)),
            "examUpdateTime": str(exam_session.get("updateTime", "")).strip(),
            "extJson": dump_json(ext_json),
            "createTime": create_time,
            "updateTime": update_time,
        }

    def _normalize_student_points_ledger_payload(self, payload: Dict[str, object]) -> Dict[str, object]:
        student_user_id = str(payload.get("studentUserId", "")).strip()
        event_key = str(payload.get("eventKey", "")).strip()
        ext_json = payload.get("extJson", payload)
        if not isinstance(ext_json, dict):
            ext_json = load_json_object(str(ext_json or "{}"))
        if not isinstance(ext_json, dict):
            ext_json = {}
        create_time = str(payload.get("createTime", "")).strip()
        update_time = str(payload.get("updateTime", "")).strip() or create_time
        return {
            "id": str(payload.get("id", "")).strip() or f"{student_user_id}::{event_key}",
            "studentUserId": student_user_id,
            "eventKey": event_key,
            "reason": str(payload.get("reason", "")).strip(),
            "points": self._safe_int(payload.get("points", 0)),
            "extJson": dump_json(ext_json),
            "createTime": create_time,
            "updateTime": update_time,
        }

    def list_student_points_ledger(self, student_user_id: str, limit: Optional[int] = None) -> List[Dict[str, object]]:
        limit_clause = ""
        params: List[object] = [student_user_id]
        if limit is not None and int(limit) > 0:
            limit_clause = " LIMIT ?"
            params.append(int(limit))
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT """ + STUDENT_POINTS_LEDGER_SELECT_SQL + """
                FROM student_points_ledger
                WHERE studentUserId = ?
                ORDER BY createTime ASC, eventKey ASC
                """ + limit_clause,
                tuple(params),
            ).fetchall()
        return [self._decode_student_points_ledger_row(row) for row in rows]

    def get_student_profile_state(self, student_user_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + STUDENT_PROFILE_STATE_SELECT_SQL + """
                FROM student_profile_state
                WHERE studentUserId = ?
                """,
                (student_user_id,),
            ).fetchone()
        return self._decode_student_profile_state_row(row) if row else None

    def upsert_student_profile_state(self, payload: Dict[str, object]) -> Dict[str, object]:
        student_user_id = str(payload.get("studentUserId", "")).strip()
        merged_payload = dict(payload)
        if student_user_id:
            existing = self.get_student_profile_state(student_user_id)
            if existing:
                merged_payload = {**existing, **merged_payload}
        normalized = self._normalize_student_profile_state_payload(merged_payload)
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO student_profile_state (
                  id, studentUserId, examCategoryCode, jointExamGroupCode, points, title, unlockedTitlesJson, checkInDatesJson,
                  aiDailyLimit, aiUsedCount, aiQuotaDate, examAnsweredCount, examElapsedSec, examUpdateTime,
                  extJson, createTime, updateTime
                ) VALUES (
                  :id, :studentUserId, :examCategoryCode, :jointExamGroupCode, :points, :title, :unlockedTitlesJson, :checkInDatesJson,
                  :aiDailyLimit, :aiUsedCount, :aiQuotaDate, :examAnsweredCount, :examElapsedSec, :examUpdateTime,
                  :extJson, :createTime, :updateTime
                )
                ON CONFLICT(studentUserId) DO UPDATE SET
                  id = excluded.id,
                  examCategoryCode = excluded.examCategoryCode,
                  jointExamGroupCode = excluded.jointExamGroupCode,
                  points = excluded.points,
                  title = excluded.title,
                  unlockedTitlesJson = excluded.unlockedTitlesJson,
                  checkInDatesJson = excluded.checkInDatesJson,
                  aiDailyLimit = excluded.aiDailyLimit,
                  aiUsedCount = excluded.aiUsedCount,
                  aiQuotaDate = excluded.aiQuotaDate,
                  examAnsweredCount = excluded.examAnsweredCount,
                  examElapsedSec = excluded.examElapsedSec,
                  examUpdateTime = excluded.examUpdateTime,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        return self.get_student_profile_state(normalized["studentUserId"]) or normalized

    def _student_profile_state_seed(self, student_user_id: str, now_iso: str) -> Dict[str, object]:
        return {
            "studentUserId": student_user_id,
            "examCategoryCode": "SCIENCE_ENGINEERING",
            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
            "vocationalMajor": "",
            "prepStage": "",
            "points": 0,
            "title": "备考新星",
            "unlockedTitles": ["备考新星"],
            "checkInDates": [],
            "aiQuota": {"dailyLimit": 20, "usedCount": 0, "quotaDate": ""},
            "examSession": {"answeredCount": 0, "elapsedSec": 0, "updateTime": ""},
            "createTime": now_iso,
            "updateTime": now_iso,
        }

    def append_student_profile_check_in_date(
        self,
        student_user_id: str,
        check_in_date: str,
        now_iso: str,
    ) -> Dict[str, object]:
        current = self.get_student_profile_state(student_user_id) or self._student_profile_state_seed(student_user_id, now_iso)
        check_in_dates = [str(item).strip() for item in current.get("checkInDates", []) if str(item).strip()]
        normalized_date = str(check_in_date or "").strip()
        if normalized_date and normalized_date not in check_in_dates:
            check_in_dates.append(normalized_date)
            check_in_dates.sort()
        current["checkInDates"] = check_in_dates
        current["updateTime"] = now_iso
        return self.upsert_student_profile_state(current)

    def increment_student_profile_points(
        self,
        student_user_id: str,
        delta: int,
        title: str,
        unlocked_titles: List[str],
        now_iso: str,
    ) -> Dict[str, object]:
        current = self.get_student_profile_state(student_user_id) or self._student_profile_state_seed(student_user_id, now_iso)
        current["points"] = self._safe_int(current.get("points", 0)) + self._safe_int(delta)
        current["title"] = str(title or "").strip() or "备考新星"
        current["unlockedTitles"] = [str(item).strip() for item in unlocked_titles if str(item).strip()]
        current["updateTime"] = now_iso
        return self.upsert_student_profile_state(current)

    def set_student_profile_selection(
        self,
        student_user_id: str,
        exam_category_code: str,
        joint_exam_group_code: str,
        now_iso: str,
    ) -> Dict[str, object]:
        current = self.get_student_profile_state(student_user_id) or self._student_profile_state_seed(student_user_id, now_iso)
        current["examCategoryCode"] = str(exam_category_code or "").strip() or "SCIENCE_ENGINEERING"
        current["jointExamGroupCode"] = str(joint_exam_group_code or "").strip() or "SCIENCE_ENGINEERING_3"
        current["updateTime"] = now_iso
        return self.upsert_student_profile_state(current)

    def set_student_profile_bio(
        self,
        student_user_id: str,
        vocational_major: str,
        prep_stage: str,
        now_iso: str,
    ) -> Dict[str, object]:
        current = self.get_student_profile_state(student_user_id) or self._student_profile_state_seed(student_user_id, now_iso)
        current["vocationalMajor"] = str(vocational_major or "").strip()
        current["prepStage"] = str(prep_stage or "").strip()
        current["updateTime"] = now_iso
        return self.upsert_student_profile_state(current)

    def set_student_profile_ai_quota(self, student_user_id: str, ai_quota: Dict[str, object], now_iso: str) -> Dict[str, object]:
        current = self.get_student_profile_state(student_user_id) or self._student_profile_state_seed(student_user_id, now_iso)
        current["aiQuota"] = {
            "dailyLimit": self._safe_int(ai_quota.get("dailyLimit", 20)),
            "usedCount": self._safe_int(ai_quota.get("usedCount", 0)),
            "quotaDate": str(ai_quota.get("quotaDate", "")).strip(),
        }
        current["updateTime"] = now_iso
        return self.upsert_student_profile_state(current)

    def set_student_profile_exam_session(
        self,
        student_user_id: str,
        exam_session: Dict[str, object],
        now_iso: str,
    ) -> Dict[str, object]:
        current = self.get_student_profile_state(student_user_id) or self._student_profile_state_seed(student_user_id, now_iso)
        current["examSession"] = {
            "answeredCount": self._safe_int(exam_session.get("answeredCount", 0)),
            "elapsedSec": self._safe_int(exam_session.get("elapsedSec", 0)),
            "updateTime": str(exam_session.get("updateTime", "")).strip() or now_iso,
        }
        current["updateTime"] = now_iso
        return self.upsert_student_profile_state(current)

    def upsert_student_points_ledger(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = self._normalize_student_points_ledger_payload(payload)
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO student_points_ledger (
                  id, studentUserId, eventKey, reason, points, extJson, createTime, updateTime
                ) VALUES (
                  :id, :studentUserId, :eventKey, :reason, :points, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(studentUserId, eventKey) DO UPDATE SET
                  id = excluded.id,
                  reason = excluded.reason,
                  points = excluded.points,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        rows = self.list_student_points_ledger(normalized["studentUserId"])
        return next((row for row in rows if str(row.get("eventKey", "")).strip() == normalized["eventKey"]), normalized)

    def insert_student_points_ledger_if_absent(
        self,
        student_user_id: str,
        event_key: str,
        reason: str,
        points: int,
        create_time: str,
        ext_json: Optional[Dict[str, object]] = None,
    ) -> bool:
        normalized = self._normalize_student_points_ledger_payload(
            {
                "studentUserId": student_user_id,
                "eventKey": event_key,
                "reason": reason,
                "points": points,
                "createTime": create_time,
                "updateTime": create_time,
                "extJson": ext_json or {},
            }
        )
        with get_connection(self.db_path) as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO student_points_ledger (
                      id, studentUserId, eventKey, reason, points, extJson, createTime, updateTime
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized["id"],
                        normalized["studentUserId"],
                        normalized["eventKey"],
                        normalized["reason"],
                        normalized["points"],
                        normalized["extJson"],
                        normalized["createTime"],
                        normalized["updateTime"],
                    ),
                )
                connection.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_challenge_point_subject(self, student_user_id: str, subject_code: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + CHALLENGE_POINT_SUBJECT_SELECT_SQL + """
                FROM challenge_point_subject
                WHERE studentUserId = ? AND subjectCode = ?
                """,
                (student_user_id, subject_code),
            ).fetchone()
        return self._decode_challenge_point_subject_row(row) if row else None

    def list_challenge_point_subjects_by_student(self, student_user_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT """ + CHALLENGE_POINT_SUBJECT_SELECT_SQL + """
                FROM challenge_point_subject
                WHERE studentUserId = ?
                ORDER BY totalPoints DESC, updateTime ASC, subjectCode ASC
                """,
                (student_user_id,),
            ).fetchall()
        return [self._decode_challenge_point_subject_row(row) for row in rows]

    def count_today_challenge_points(self, student_user_id: str, subject_code: str, day: str) -> int:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(points), 0) AS total
                FROM challenge_point_event
                WHERE studentUserId = ?
                  AND subjectCode = ?
                  AND substr(awardedAt, 1, 10) = ?
                """,
                (student_user_id, subject_code, day),
            ).fetchone()
        return self._safe_int((row or {}).get("total", 0) if isinstance(row, dict) else row["total"] if row else 0)

    def count_challenge_point_correct_submits(self, student_user_id: str, subject_code: str) -> int:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM challenge_point_event
                WHERE studentUserId = ?
                  AND subjectCode = ?
                  AND points > 0
                """,
                (student_user_id, subject_code),
            ).fetchone()
        return self._safe_int((row or {}).get("total", 0) if isinstance(row, dict) else row["total"] if row else 0)

    def count_today_challenge_point_correct_submits(self, student_user_id: str, subject_code: str, day: str) -> int:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM challenge_point_event
                WHERE studentUserId = ?
                  AND subjectCode = ?
                  AND points > 0
                  AND substr(awardedAt, 1, 10) = ?
                """,
                (student_user_id, subject_code, day),
            ).fetchone()
        return self._safe_int((row or {}).get("total", 0) if isinstance(row, dict) else row["total"] if row else 0)

    def list_challenge_point_awards(self, student_user_id: str, subject_code: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT """ + CHALLENGE_POINT_AWARD_SELECT_SQL + """
                FROM challenge_point_award
                WHERE studentUserId = ?
                  AND subjectCode = ?
                ORDER BY unlockedAt DESC, awardCode ASC
                """,
                (student_user_id, subject_code),
            ).fetchall()
        awards: List[Dict[str, object]] = []
        for row in rows:
            payload = load_json_object(str(row["extJson"]))
            if not isinstance(payload, dict):
                payload = {}
            payload.setdefault("id", str(row["id"]))
            payload.setdefault("studentUserId", str(row["studentUserId"]))
            payload.setdefault("subjectCode", str(row["subjectCode"]))
            payload.setdefault("awardCode", str(row["awardCode"]))
            payload.setdefault("awardName", str(row["awardName"]))
            payload.setdefault("unlockedAt", str(row["unlockedAt"]))
            payload.setdefault("createTime", str(row["createTime"]))
            payload.setdefault("updateTime", str(row["updateTime"]))
            awards.append(payload)
        return awards

    def get_challenge_point_rank(
        self,
        subject_code: str,
        total_points: int,
        reached_at: str,
        student_user_id: str,
    ) -> int:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM challenge_point_subject
                WHERE subjectCode = ?
                  AND (
                    totalPoints > ?
                    OR (totalPoints = ? AND updateTime < ?)
                    OR (totalPoints = ? AND updateTime = ? AND studentUserId < ?)
                  )
                """,
                (subject_code, total_points, total_points, reached_at, total_points, reached_at, student_user_id),
            ).fetchone()
        base_count = self._safe_int((row or {}).get("total", 0) if isinstance(row, dict) else row["total"] if row else 0)
        return base_count + 1

    def list_challenge_point_leaderboard(self, subject_code: str, limit: int = 10) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                  cps.studentUserId,
                  cps.subjectCode,
                  cps.totalPoints,
                  cps.lastAwardedAt,
                  cps.createTime,
                  cps.updateTime,
                  u.phone AS phone,
                  u.extJson AS userExtJson
                FROM challenge_point_subject AS cps
                JOIN "user" AS u
                  ON u.id = cps.studentUserId
                WHERE cps.subjectCode = ?
                ORDER BY cps.totalPoints DESC, cps.updateTime ASC, cps.studentUserId ASC
                LIMIT ?
                """,
                (subject_code, limit),
            ).fetchall()
        leaderboard: List[Dict[str, object]] = []
        for index, row in enumerate(rows, start=1):
            user_ext = load_json_object(str(row["userExtJson"]))
            display_name = str(user_ext.get("name", "")).strip() or str(row["studentUserId"])
            leaderboard.append(
                {
                    "rank": index,
                    "studentUserId": str(row["studentUserId"]),
                    "studentName": display_name,
                    "phone": str(row["phone"]),
                    "subjectCode": str(row["subjectCode"]),
                    "totalPoints": self._safe_int(row["totalPoints"]),
                    "lastAwardedAt": str(row["lastAwardedAt"]),
                    "updateTime": str(row["updateTime"]),
                }
            )
        return leaderboard

    def grant_challenge_point(
        self,
        student_user_id: str,
        question_id: str,
        subject_code: str,
        attempt_key: str,
        source_type: str,
        awarded_at: str,
        points: int = 1,
        award_threshold: int = 10_000,
        award_code: str = "SUBJECT_CHALLENGE_STAR",
        award_name: str = "学科练习之星",
    ) -> Dict[str, object]:
        normalized_source_type = str(source_type or "").strip().upper() or "CHAPTER_CHALLENGE"
        normalized_attempt_key = str(attempt_key or "").strip()
        event_id = f"{student_user_id}::{question_id}::{normalized_attempt_key}"
        summary_id = f"{student_user_id}::{subject_code}"
        award_id = f"{student_user_id}::{subject_code}::{award_code}"
        with get_connection(self.db_path) as connection:
            granted = False
            try:
                connection.execute(
                    """
                    INSERT INTO challenge_point_event (
                      id, studentUserId, questionId, subjectCode, attemptKey, sourceType, points,
                      awardedAt, extJson, createTime, updateTime
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        student_user_id,
                        question_id,
                        subject_code,
                        normalized_attempt_key,
                        normalized_source_type,
                        points,
                        awarded_at,
                        dump_json(
                            {
                                "studentUserId": student_user_id,
                                "questionId": question_id,
                                "subjectCode": subject_code,
                                "attemptKey": normalized_attempt_key,
                                "sourceType": normalized_source_type,
                                "points": points,
                                "awardedAt": awarded_at,
                            }
                        ),
                        awarded_at,
                        awarded_at,
                    ),
                )
                granted = True
            except sqlite3.IntegrityError:
                granted = False

            summary_row = connection.execute(
                """
                SELECT """ + CHALLENGE_POINT_SUBJECT_SELECT_SQL + """
                FROM challenge_point_subject
                WHERE studentUserId = ? AND subjectCode = ?
                """,
                (student_user_id, subject_code),
            ).fetchone()
            if granted:
                if summary_row:
                    create_time = str(summary_row["createTime"])
                    total_points = self._safe_int(summary_row["totalPoints"]) + points
                else:
                    create_time = awarded_at
                    total_points = points
                connection.execute(
                    """
                    INSERT INTO challenge_point_subject (
                      id, studentUserId, subjectCode, totalPoints, lastAwardedAt,
                      extJson, createTime, updateTime
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(studentUserId, subjectCode) DO UPDATE SET
                      totalPoints = excluded.totalPoints,
                      lastAwardedAt = excluded.lastAwardedAt,
                      extJson = excluded.extJson,
                      updateTime = excluded.updateTime
                    """,
                    (
                        summary_id,
                        student_user_id,
                        subject_code,
                        total_points,
                        awarded_at,
                        dump_json(
                            {
                                "studentUserId": student_user_id,
                                "subjectCode": subject_code,
                                "totalPoints": total_points,
                                "lastAwardedAt": awarded_at,
                            }
                        ),
                        create_time,
                        awarded_at,
                    ),
                )
            else:
                total_points = self._safe_int(summary_row["totalPoints"]) if summary_row else 0

            award_granted = False
            if granted and total_points >= award_threshold:
                try:
                    connection.execute(
                        """
                        INSERT INTO challenge_point_award (
                          id, studentUserId, subjectCode, awardCode, awardName,
                          unlockedAt, extJson, createTime, updateTime
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            award_id,
                            student_user_id,
                            subject_code,
                            award_code,
                            award_name,
                            awarded_at,
                            dump_json(
                                {
                                    "studentUserId": student_user_id,
                                    "subjectCode": subject_code,
                                    "awardCode": award_code,
                                    "awardName": award_name,
                                    "unlockedAt": awarded_at,
                                    "threshold": award_threshold,
                                }
                            ),
                            awarded_at,
                            awarded_at,
                        ),
                    )
                    award_granted = True
                except sqlite3.IntegrityError:
                    award_granted = False
            connection.commit()
        return {
            "granted": granted,
            "totalPoints": total_points,
            "awardGranted": award_granted,
        }

    def _decode_message_send_history_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        payload.setdefault("traceId", str(row["traceId"]))
        payload.setdefault("scheduleId", str(row["scheduleId"]))
        payload.setdefault("senderUserId", str(row["senderUserId"]))
        payload.setdefault("targetMode", str(row["targetMode"]))
        payload.setdefault("targetCount", self._safe_int(row["targetCount"]))
        payload.setdefault("sentCount", self._safe_int(row["sentCount"]))
        payload.setdefault("category", str(row["category"]))
        payload.setdefault("title", str(row["title"]))
        payload.setdefault("content", str(row["content"]))
        payload.setdefault("sendAt", str(row["sendAt"]))
        payload.setdefault("status", str(row["status"]))
        payload.setdefault("recalledAt", str(row["recalledAt"]))
        payload.setdefault("createTime", str(row["createTime"]))
        payload.setdefault("updateTime", str(row["updateTime"]))
        return payload

    def list_message_send_history_by_sender(self, sender_user_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            if sender_user_id:
                rows = connection.execute(
                    """
                    SELECT """ + MESSAGE_SEND_HISTORY_SELECT_SQL + """
                    FROM message_send_history
                    WHERE senderUserId = ?
                    ORDER BY createTime DESC, traceId DESC
                    """,
                    (sender_user_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT """ + MESSAGE_SEND_HISTORY_SELECT_SQL + """
                    FROM message_send_history
                    ORDER BY createTime DESC, traceId DESC
                    """
                ).fetchall()
        return [self._decode_message_send_history_row(row) for row in rows]

    def get_message_send_history_payload(self, trace_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + MESSAGE_SEND_HISTORY_SELECT_SQL + """
                FROM message_send_history
                WHERE traceId = ?
                """,
                (trace_id,),
            ).fetchone()
        return self._decode_message_send_history_row(row) if row else None

    def get_message_send_history_row(self, trace_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT """ + MESSAGE_SEND_HISTORY_SELECT_SQL + """
                FROM message_send_history
                WHERE traceId = ?
                """,
                (trace_id,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_paper_report_payload(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = self._normalize_paper_report_row(payload)
        if not normalized:
            raise ValueError("paper report payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO paper_report (
                  id, reportId, studentUserId, paperId, subjectId, subjectIdsJson,
                  score, totalScore, scoreRate, totalElapsedSec, submittedAt,
                  pendingSubjectiveCount, status, extJson, createTime, updateTime
                ) VALUES (
                  :id, :reportId, :studentUserId, :paperId, :subjectId, :subjectIdsJson,
                  :score, :totalScore, :scoreRate, :totalElapsedSec, :submittedAt,
                  :pendingSubjectiveCount, :status, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(reportId) DO UPDATE SET
                  id = excluded.id,
                  studentUserId = excluded.studentUserId,
                  paperId = excluded.paperId,
                  subjectId = excluded.subjectId,
                  subjectIdsJson = excluded.subjectIdsJson,
                  score = excluded.score,
                  totalScore = excluded.totalScore,
                  scoreRate = excluded.scoreRate,
                  totalElapsedSec = excluded.totalElapsedSec,
                  submittedAt = excluded.submittedAt,
                  pendingSubjectiveCount = excluded.pendingSubjectiveCount,
                  status = excluded.status,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        return self.get_paper_report_payload(str(normalized["reportId"])) or dict(payload)

    def upsert_message_send_history_payload(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = self._normalize_message_send_history_row(payload)
        if not normalized:
            raise ValueError("message send history payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO message_send_history (
                  id, traceId, scheduleId, senderUserId, targetMode, targetCount, sentCount,
                  category, title, content, sendAt, status, recalledAt, createTime, updateTime, extJson
                ) VALUES (
                  :id, :traceId, :scheduleId, :senderUserId, :targetMode, :targetCount, :sentCount,
                  :category, :title, :content, :sendAt, :status, :recalledAt, :createTime, :updateTime, :extJson
                )
                ON CONFLICT(traceId) DO UPDATE SET
                  id = excluded.id,
                  scheduleId = excluded.scheduleId,
                  senderUserId = excluded.senderUserId,
                  targetMode = excluded.targetMode,
                  targetCount = excluded.targetCount,
                  sentCount = excluded.sentCount,
                  category = excluded.category,
                  title = excluded.title,
                  content = excluded.content,
                  sendAt = excluded.sendAt,
                  status = excluded.status,
                  recalledAt = excluded.recalledAt,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime,
                  extJson = excluded.extJson
                """,
                normalized,
            )
            connection.commit()
        return self.get_message_send_history_payload(str(normalized["traceId"])) or dict(payload)

    def _normalize_text_list(self, value: object) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            try:
                loaded = json.loads(text)
            except (TypeError, ValueError, json.JSONDecodeError):
                return []
            if isinstance(loaded, list):
                return [str(item).strip() for item in loaded if str(item).strip()]
        return []

    def _decode_learning_method_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "id": str(row["id"]),
            "methodCode": str(row["methodCode"]),
            "methodName": str(row["methodName"]),
            "oneLineIntro": str(row["oneLineIntro"]),
            "useWhen": self._normalize_text_list(row["useWhenJson"]),
            "steps": self._normalize_text_list(row["stepsJson"]),
            "commonMistakes": self._normalize_text_list(row["commonMistakesJson"]),
            "questionBankActions": self._normalize_text_list(row["questionBankActionsJson"]),
            "starterTask": str(row["starterTask"]),
            "difficultyLevel": str(row["difficultyLevel"]),
            "estimatedMinutes": self._safe_int(row["estimatedMinutes"], 15),
            "sort": self._safe_int(row["sort"], 0),
            "status": str(row["status"]),
            "extJson": payload,
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def _normalize_learning_method_row(self, payload: object) -> Optional[Dict[str, object]]:
        if not isinstance(payload, dict):
            return None
        method_code = str(payload.get("methodCode", "")).strip().upper()
        method_name = str(payload.get("methodName", "")).strip()
        if not method_code or not method_name:
            return None
        method_id = str(payload.get("id", "")).strip()
        if not method_id:
            slug = "".join(character.lower() if character.isalnum() else "-" for character in method_code).strip("-")
            method_id = f"learning-method-{slug or method_code.lower()}"
        ext_json = payload.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = load_json_object(ext_json)
            if not isinstance(ext_json, dict):
                ext_json = {}
        create_time = str(payload.get("createTime", "")).strip()
        update_time = str(payload.get("updateTime", "")).strip() or create_time
        estimated_minutes = self._safe_int(payload.get("estimatedMinutes", 15), 15)
        sort_value = self._safe_int(payload.get("sort", 0), 0)
        return {
            "id": method_id,
            "methodCode": method_code,
            "methodName": method_name,
            "oneLineIntro": str(payload.get("oneLineIntro", "")).strip(),
            "useWhenJson": dump_json(self._normalize_text_list(payload.get("useWhen", payload.get("useWhenJson", [])))),
            "stepsJson": dump_json(self._normalize_text_list(payload.get("steps", payload.get("stepsJson", [])))),
            "commonMistakesJson": dump_json(
                self._normalize_text_list(payload.get("commonMistakes", payload.get("commonMistakesJson", [])))
            ),
            "questionBankActionsJson": dump_json(
                self._normalize_text_list(payload.get("questionBankActions", payload.get("questionBankActionsJson", [])))
            ),
            "starterTask": str(payload.get("starterTask", "")).strip(),
            "difficultyLevel": str(payload.get("difficultyLevel", "L1")).strip() or "L1",
            "estimatedMinutes": max(1, estimated_minutes),
            "sort": max(0, sort_value),
            "status": str(payload.get("status", "ACTIVE")).strip() or "ACTIVE",
            "extJson": dump_json(ext_json),
            "createTime": create_time,
            "updateTime": update_time,
        }

    def list_learning_methods(self, status: str = "") -> List[Dict[str, object]]:
        clauses = ["1 = 1"]
        params: Dict[str, object] = {}
        if status:
            clauses.append("status = :status")
            params["status"] = str(status).strip()
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT {LEARNING_METHOD_SELECT_SQL}
                FROM learning_method
                WHERE {" AND ".join(clauses)}
                ORDER BY sort ASC, createTime ASC, methodCode ASC
                """,
                params,
            ).fetchall()
        return [self._decode_learning_method_row(row) for row in rows]

    def get_learning_method(self, method_code: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {LEARNING_METHOD_SELECT_SQL}
                FROM learning_method
                WHERE UPPER(methodCode) = UPPER(?)
                LIMIT 1
                """,
                (str(method_code or "").strip(),),
            ).fetchone()
        return self._decode_learning_method_row(row) if row else None

    def upsert_learning_method(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = self._normalize_learning_method_row(payload)
        if not normalized:
            raise ValueError("learning method payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO learning_method (
                  id, methodCode, methodName, oneLineIntro, useWhenJson, stepsJson, commonMistakesJson,
                  questionBankActionsJson, starterTask, difficultyLevel, estimatedMinutes, sort,
                  status, extJson, createTime, updateTime
                ) VALUES (
                  :id, :methodCode, :methodName, :oneLineIntro, :useWhenJson, :stepsJson, :commonMistakesJson,
                  :questionBankActionsJson, :starterTask, :difficultyLevel, :estimatedMinutes, :sort,
                  :status, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(methodCode) DO UPDATE SET
                  id = excluded.id,
                  methodName = excluded.methodName,
                  oneLineIntro = excluded.oneLineIntro,
                  useWhenJson = excluded.useWhenJson,
                  stepsJson = excluded.stepsJson,
                  commonMistakesJson = excluded.commonMistakesJson,
                  questionBankActionsJson = excluded.questionBankActionsJson,
                  starterTask = excluded.starterTask,
                  difficultyLevel = excluded.difficultyLevel,
                  estimatedMinutes = excluded.estimatedMinutes,
                  sort = excluded.sort,
                  status = excluded.status,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        return self.get_learning_method(str(normalized["methodCode"])) or dict(payload)

    def _decode_student_learning_method_progress_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "id": str(row["id"]),
            "studentUserId": str(row["studentUserId"]),
            "methodCode": str(row["methodCode"]),
            "startCount": self._safe_int(row["startCount"], 0),
            "completeCount": self._safe_int(row["completeCount"], 0),
            "lastPracticedAt": str(row["lastPracticedAt"]),
            "lastAccuracy": self._safe_float(row["lastAccuracy"], 0.0),
            "lastReviewSummary": str(row["lastReviewSummary"]),
            "status": str(row["status"]),
            "extJson": payload,
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def _normalize_student_learning_method_progress_row(self, payload: object) -> Optional[Dict[str, object]]:
        if not isinstance(payload, dict):
            return None
        student_user_id = str(payload.get("studentUserId", "")).strip()
        method_code = str(payload.get("methodCode", "")).strip().upper()
        if not student_user_id or not method_code:
            return None
        progress_id = str(payload.get("id", "")).strip() or f"slmp-{student_user_id}-{method_code.lower()}"
        ext_json = payload.get("extJson", {})
        if not isinstance(ext_json, dict):
            ext_json = load_json_object(ext_json)
            if not isinstance(ext_json, dict):
                ext_json = {}
        create_time = str(payload.get("createTime", "")).strip()
        update_time = str(payload.get("updateTime", "")).strip() or create_time
        return {
            "id": progress_id,
            "studentUserId": student_user_id,
            "methodCode": method_code,
            "startCount": max(0, self._safe_int(payload.get("startCount", 0), 0)),
            "completeCount": max(0, self._safe_int(payload.get("completeCount", 0), 0)),
            "lastPracticedAt": str(payload.get("lastPracticedAt", "")).strip(),
            "lastAccuracy": max(0.0, min(1.0, self._safe_float(payload.get("lastAccuracy", 0.0), 0.0))),
            "lastReviewSummary": str(payload.get("lastReviewSummary", "")).strip(),
            "status": str(payload.get("status", "NOT_STARTED")).strip() or "NOT_STARTED",
            "extJson": dump_json(ext_json),
            "createTime": create_time,
            "updateTime": update_time,
        }

    def get_student_learning_method_progress(
        self,
        student_user_id: str,
        method_code: str,
    ) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {STUDENT_LEARNING_METHOD_PROGRESS_SELECT_SQL}
                FROM student_learning_method_progress
                WHERE studentUserId = ? AND UPPER(methodCode) = UPPER(?)
                LIMIT 1
                """,
                (student_user_id, method_code),
            ).fetchone()
        return self._decode_student_learning_method_progress_row(row) if row else None

    def list_student_learning_method_progress(self, student_user_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT {STUDENT_LEARNING_METHOD_PROGRESS_SELECT_SQL}
                FROM student_learning_method_progress
                WHERE studentUserId = ?
                ORDER BY updateTime DESC, methodCode ASC
                """,
                (student_user_id,),
            ).fetchall()
        return [self._decode_student_learning_method_progress_row(row) for row in rows]

    def upsert_student_learning_method_progress(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = self._normalize_student_learning_method_progress_row(payload)
        if not normalized:
            raise ValueError("student learning method progress payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO student_learning_method_progress (
                  id, studentUserId, methodCode, startCount, completeCount, lastPracticedAt, lastAccuracy,
                  lastReviewSummary, status, extJson, createTime, updateTime
                ) VALUES (
                  :id, :studentUserId, :methodCode, :startCount, :completeCount, :lastPracticedAt, :lastAccuracy,
                  :lastReviewSummary, :status, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(studentUserId, methodCode) DO UPDATE SET
                  id = excluded.id,
                  startCount = excluded.startCount,
                  completeCount = excluded.completeCount,
                  lastPracticedAt = excluded.lastPracticedAt,
                  lastAccuracy = excluded.lastAccuracy,
                  lastReviewSummary = excluded.lastReviewSummary,
                  status = excluded.status,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        return (
            self.get_student_learning_method_progress(
                str(normalized["studentUserId"]),
                str(normalized["methodCode"]),
            )
            or dict(payload)
        )

    def _decode_subscription_plan_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "id": str(row["id"]),
            "planCode": str(row["planCode"]),
            "planName": str(row["planName"]),
            "durationDays": self._safe_int(row["durationDays"], 30),
            "listPriceFen": self._safe_int(row["listPriceFen"], 0),
            "salePriceFen": self._safe_int(row["salePriceFen"], 0),
            "status": str(row["status"]),
            "sort": self._safe_int(row["sort"], 0),
            "extJson": payload,
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def _decode_student_subscription_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "id": str(row["id"]),
            "studentUserId": str(row["studentUserId"]),
            "currentPlanCode": str(row["currentPlanCode"]),
            "status": str(row["status"]),
            "startTime": str(row["startTime"]),
            "endTime": str(row["endTime"]),
            "lastActivatedAt": str(row["lastActivatedAt"]),
            "lastExpiredAt": str(row["lastExpiredAt"]),
            "sourceType": str(row["sourceType"]),
            "sourceOrderId": str(row["sourceOrderId"]),
            "sourceRedeemCode": str(row["sourceRedeemCode"]),
            "totalActivatedDays": self._safe_int(row["totalActivatedDays"], 0),
            "extJson": payload,
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def _decode_redeem_code_batch_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "id": str(row["id"]),
            "batchCode": str(row["batchCode"]),
            "batchName": str(row["batchName"]),
            "channelCode": str(row["channelCode"]),
            "planCode": str(row["planCode"]),
            "totalCount": self._safe_int(row["totalCount"], 0),
            "usedCount": self._safe_int(row["usedCount"], 0),
            "expiresAt": str(row["expiresAt"]),
            "status": str(row["status"]),
            "createdByUserId": str(row["createdByUserId"]),
            "extJson": payload,
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def _decode_redeem_code_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "id": str(row["id"]),
            "batchId": str(row["batchId"]),
            "code": str(row["code"]),
            "planCode": str(row["planCode"]),
            "status": str(row["status"]),
            "expiresAt": str(row["expiresAt"]),
            "usedByUserId": str(row["usedByUserId"]),
            "usedAt": str(row["usedAt"]),
            "sourceOrderId": str(row["sourceOrderId"]),
            "extJson": payload,
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def _decode_subscription_order_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "id": str(row["id"]),
            "orderNo": str(row["orderNo"]),
            "studentUserId": str(row["studentUserId"]),
            "planCode": str(row["planCode"]),
            "amountFen": self._safe_int(row["amountFen"], 0),
            "channel": str(row["channel"]),
            "status": str(row["status"]),
            "paidAt": str(row["paidAt"]),
            "closedAt": str(row["closedAt"]),
            "extJson": payload,
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def _decode_payment_transaction_mock_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["payloadJson"]))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "id": str(row["id"]),
            "orderId": str(row["orderId"]),
            "transactionNo": str(row["transactionNo"]),
            "requestId": str(row["requestId"]),
            "status": str(row["status"]),
            "payloadJson": payload,
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def _decode_conversion_event_log_row(self, row: sqlite3.Row) -> Dict[str, object]:
        payload = load_json_object(str(row["extJson"]))
        if not isinstance(payload, dict):
            payload = {}
        return {
            "id": str(row["id"]),
            "studentUserId": str(row["studentUserId"]),
            "eventType": str(row["eventType"]),
            "eventTime": str(row["eventTime"]),
            "eventDate": str(row["eventDate"]),
            "sessionId": str(row["sessionId"]),
            "planCode": str(row["planCode"]),
            "orderId": str(row["orderId"]),
            "redeemCode": str(row["redeemCode"]),
            "channelCode": str(row["channelCode"]),
            "extJson": payload,
            "createTime": str(row["createTime"]),
            "updateTime": str(row["updateTime"]),
        }

    def list_subscription_plans(self, status: str = "ACTIVE") -> List[Dict[str, object]]:
        clauses = ["1 = 1"]
        params: Dict[str, object] = {}
        normalized_status = str(status or "").strip()
        if normalized_status:
            clauses.append("status = :status")
            params["status"] = normalized_status
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT {SUBSCRIPTION_PLAN_SELECT_SQL}
                FROM subscription_plan
                WHERE {" AND ".join(clauses)}
                ORDER BY sort ASC, createTime ASC, planCode ASC
                """,
                params,
            ).fetchall()
        return [self._decode_subscription_plan_row(row) for row in rows]

    def get_subscription_plan(self, plan_code: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {SUBSCRIPTION_PLAN_SELECT_SQL}
                FROM subscription_plan
                WHERE UPPER(planCode) = UPPER(?)
                LIMIT 1
                """,
                (str(plan_code or "").strip(),),
            ).fetchone()
        return self._decode_subscription_plan_row(row) if row else None

    def upsert_subscription_plan(self, payload: Dict[str, object]) -> Dict[str, object]:
        now_iso = str(payload.get("updateTime", "")).strip() or str(payload.get("createTime", "")).strip()
        normalized = {
            "id": str(payload.get("id", "")).strip(),
            "planCode": str(payload.get("planCode", "")).strip().upper(),
            "planName": str(payload.get("planName", "")).strip(),
            "durationDays": max(1, self._safe_int(payload.get("durationDays", 30), 30)),
            "listPriceFen": max(0, self._safe_int(payload.get("listPriceFen", 0), 0)),
            "salePriceFen": max(0, self._safe_int(payload.get("salePriceFen", 0), 0)),
            "status": str(payload.get("status", "ACTIVE")).strip() or "ACTIVE",
            "sort": max(0, self._safe_int(payload.get("sort", 0), 0)),
            "extJson": dump_json(payload.get("extJson", {}) if isinstance(payload.get("extJson", {}), dict) else {}),
            "createTime": str(payload.get("createTime", "")).strip() or now_iso,
            "updateTime": now_iso or str(payload.get("createTime", "")).strip(),
        }
        if not normalized["id"] or not normalized["planCode"] or not normalized["planName"]:
            raise ValueError("subscription plan payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO subscription_plan (
                  id, planCode, planName, durationDays, listPriceFen, salePriceFen,
                  status, sort, extJson, createTime, updateTime
                ) VALUES (
                  :id, :planCode, :planName, :durationDays, :listPriceFen, :salePriceFen,
                  :status, :sort, :extJson, :createTime, :updateTime
                )
                ON CONFLICT(planCode) DO UPDATE SET
                  id = excluded.id,
                  planName = excluded.planName,
                  durationDays = excluded.durationDays,
                  listPriceFen = excluded.listPriceFen,
                  salePriceFen = excluded.salePriceFen,
                  status = excluded.status,
                  sort = excluded.sort,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        return self.get_subscription_plan(normalized["planCode"]) or dict(normalized)

    def get_student_subscription(self, student_user_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {STUDENT_SUBSCRIPTION_SELECT_SQL}
                FROM student_subscription
                WHERE studentUserId = ?
                LIMIT 1
                """,
                (str(student_user_id or "").strip(),),
            ).fetchone()
        return self._decode_student_subscription_row(row) if row else None

    def upsert_student_subscription(self, payload: Dict[str, object]) -> Dict[str, object]:
        student_user_id = str(payload.get("studentUserId", "")).strip()
        if not student_user_id:
            raise ValueError("student subscription payload is invalid")
        create_time = str(payload.get("createTime", "")).strip()
        update_time = str(payload.get("updateTime", "")).strip() or create_time
        normalized = {
            "id": str(payload.get("id", "")).strip() or f"student-subscription-{student_user_id}",
            "studentUserId": student_user_id,
            "currentPlanCode": str(payload.get("currentPlanCode", "")).strip().upper(),
            "status": str(payload.get("status", "INACTIVE")).strip() or "INACTIVE",
            "startTime": str(payload.get("startTime", "")).strip(),
            "endTime": str(payload.get("endTime", "")).strip(),
            "lastActivatedAt": str(payload.get("lastActivatedAt", "")).strip(),
            "lastExpiredAt": str(payload.get("lastExpiredAt", "")).strip(),
            "sourceType": str(payload.get("sourceType", "")).strip(),
            "sourceOrderId": str(payload.get("sourceOrderId", "")).strip(),
            "sourceRedeemCode": str(payload.get("sourceRedeemCode", "")).strip(),
            "totalActivatedDays": max(0, self._safe_int(payload.get("totalActivatedDays", 0), 0)),
            "extJson": dump_json(payload.get("extJson", {}) if isinstance(payload.get("extJson", {}), dict) else {}),
            "createTime": create_time or update_time,
            "updateTime": update_time or create_time,
        }
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO student_subscription (
                  id, studentUserId, currentPlanCode, status, startTime, endTime, lastActivatedAt,
                  lastExpiredAt, sourceType, sourceOrderId, sourceRedeemCode, totalActivatedDays,
                  extJson, createTime, updateTime
                ) VALUES (
                  :id, :studentUserId, :currentPlanCode, :status, :startTime, :endTime, :lastActivatedAt,
                  :lastExpiredAt, :sourceType, :sourceOrderId, :sourceRedeemCode, :totalActivatedDays,
                  :extJson, :createTime, :updateTime
                )
                ON CONFLICT(studentUserId) DO UPDATE SET
                  id = excluded.id,
                  currentPlanCode = excluded.currentPlanCode,
                  status = excluded.status,
                  startTime = excluded.startTime,
                  endTime = excluded.endTime,
                  lastActivatedAt = excluded.lastActivatedAt,
                  lastExpiredAt = excluded.lastExpiredAt,
                  sourceType = excluded.sourceType,
                  sourceOrderId = excluded.sourceOrderId,
                  sourceRedeemCode = excluded.sourceRedeemCode,
                  totalActivatedDays = excluded.totalActivatedDays,
                  extJson = excluded.extJson,
                  createTime = excluded.createTime,
                  updateTime = excluded.updateTime
                """,
                normalized,
            )
            connection.commit()
        return self.get_student_subscription(student_user_id) or dict(normalized)

    def create_redeem_code_batch(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = {
            "id": str(payload.get("id", "")).strip(),
            "batchCode": str(payload.get("batchCode", "")).strip().upper(),
            "batchName": str(payload.get("batchName", "")).strip(),
            "channelCode": str(payload.get("channelCode", "")).strip(),
            "planCode": str(payload.get("planCode", "")).strip().upper(),
            "totalCount": max(0, self._safe_int(payload.get("totalCount", 0), 0)),
            "usedCount": max(0, self._safe_int(payload.get("usedCount", 0), 0)),
            "expiresAt": str(payload.get("expiresAt", "")).strip(),
            "status": str(payload.get("status", "ACTIVE")).strip() or "ACTIVE",
            "createdByUserId": str(payload.get("createdByUserId", "")).strip(),
            "extJson": dump_json(payload.get("extJson", {}) if isinstance(payload.get("extJson", {}), dict) else {}),
            "createTime": str(payload.get("createTime", "")).strip(),
            "updateTime": str(payload.get("updateTime", "")).strip() or str(payload.get("createTime", "")).strip(),
        }
        if not normalized["id"] or not normalized["batchCode"] or not normalized["batchName"]:
            raise ValueError("redeem code batch payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO redeem_code_batch (
                  id, batchCode, batchName, channelCode, planCode, totalCount, usedCount,
                  expiresAt, status, createdByUserId, extJson, createTime, updateTime
                ) VALUES (
                  :id, :batchCode, :batchName, :channelCode, :planCode, :totalCount, :usedCount,
                  :expiresAt, :status, :createdByUserId, :extJson, :createTime, :updateTime
                )
                """,
                normalized,
            )
            connection.commit()
            row = connection.execute(
                f"SELECT {REDEEM_CODE_BATCH_SELECT_SQL} FROM redeem_code_batch WHERE id = ? LIMIT 1",
                (normalized["id"],),
            ).fetchone()
        return self._decode_redeem_code_batch_row(row) if row else dict(normalized)

    def get_redeem_code_batch(self, batch_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"SELECT {REDEEM_CODE_BATCH_SELECT_SQL} FROM redeem_code_batch WHERE id = ? LIMIT 1",
                (str(batch_id or "").strip(),),
            ).fetchone()
        return self._decode_redeem_code_batch_row(row) if row else None

    def list_redeem_code_batches(self, status: str = "") -> List[Dict[str, object]]:
        clauses = ["1 = 1"]
        params: Dict[str, object] = {}
        normalized_status = str(status or "").strip()
        if normalized_status:
            clauses.append("status = :status")
            params["status"] = normalized_status
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT {REDEEM_CODE_BATCH_SELECT_SQL}
                FROM redeem_code_batch
                WHERE {" AND ".join(clauses)}
                ORDER BY updateTime DESC, createTime DESC, batchCode ASC
                """,
                params,
            ).fetchall()
        return [self._decode_redeem_code_batch_row(row) for row in rows]

    def update_redeem_code_batch(self, payload: Dict[str, object]) -> Dict[str, object]:
        batch_id = str(payload.get("id", "")).strip()
        if not batch_id:
            raise ValueError("redeem code batch payload is invalid")
        existing = self.get_redeem_code_batch(batch_id)
        if not existing:
            raise ValueError("redeem code batch does not exist")
        merged = {
            **existing,
            **payload,
            "updateTime": str(payload.get("updateTime", "")).strip() or str(existing.get("updateTime", "")).strip(),
        }
        normalized = {
            "id": str(merged.get("id", "")).strip(),
            "batchCode": str(merged.get("batchCode", "")).strip().upper(),
            "batchName": str(merged.get("batchName", "")).strip(),
            "channelCode": str(merged.get("channelCode", "")).strip(),
            "planCode": str(merged.get("planCode", "")).strip().upper(),
            "totalCount": max(0, self._safe_int(merged.get("totalCount", 0), 0)),
            "usedCount": max(0, self._safe_int(merged.get("usedCount", 0), 0)),
            "expiresAt": str(merged.get("expiresAt", "")).strip(),
            "status": str(merged.get("status", "ACTIVE")).strip() or "ACTIVE",
            "createdByUserId": str(merged.get("createdByUserId", "")).strip(),
            "extJson": dump_json(merged.get("extJson", {}) if isinstance(merged.get("extJson", {}), dict) else {}),
            "createTime": str(merged.get("createTime", "")).strip(),
            "updateTime": str(merged.get("updateTime", "")).strip() or str(merged.get("createTime", "")).strip(),
        }
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                UPDATE redeem_code_batch
                SET batchCode = :batchCode,
                    batchName = :batchName,
                    channelCode = :channelCode,
                    planCode = :planCode,
                    totalCount = :totalCount,
                    usedCount = :usedCount,
                    expiresAt = :expiresAt,
                    status = :status,
                    createdByUserId = :createdByUserId,
                    extJson = :extJson,
                    createTime = :createTime,
                    updateTime = :updateTime
                WHERE id = :id
                """,
                normalized,
            )
            connection.commit()
        return self.get_redeem_code_batch(batch_id) or dict(normalized)

    def create_redeem_code(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = {
            "id": str(payload.get("id", "")).strip(),
            "batchId": str(payload.get("batchId", "")).strip(),
            "code": str(payload.get("code", "")).strip().upper(),
            "planCode": str(payload.get("planCode", "")).strip().upper(),
            "status": str(payload.get("status", "UNUSED")).strip() or "UNUSED",
            "expiresAt": str(payload.get("expiresAt", "")).strip(),
            "usedByUserId": str(payload.get("usedByUserId", "")).strip(),
            "usedAt": str(payload.get("usedAt", "")).strip(),
            "sourceOrderId": str(payload.get("sourceOrderId", "")).strip(),
            "extJson": dump_json(payload.get("extJson", {}) if isinstance(payload.get("extJson", {}), dict) else {}),
            "createTime": str(payload.get("createTime", "")).strip(),
            "updateTime": str(payload.get("updateTime", "")).strip() or str(payload.get("createTime", "")).strip(),
        }
        if not normalized["id"] or not normalized["batchId"] or not normalized["code"]:
            raise ValueError("redeem code payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO redeem_code (
                  id, batchId, code, planCode, status, expiresAt, usedByUserId, usedAt,
                  sourceOrderId, extJson, createTime, updateTime
                ) VALUES (
                  :id, :batchId, :code, :planCode, :status, :expiresAt, :usedByUserId, :usedAt,
                  :sourceOrderId, :extJson, :createTime, :updateTime
                )
                """,
                normalized,
            )
            connection.commit()
            row = connection.execute(
                f"SELECT {REDEEM_CODE_SELECT_SQL} FROM redeem_code WHERE id = ? LIMIT 1",
                (normalized["id"],),
            ).fetchone()
        return self._decode_redeem_code_row(row) if row else dict(normalized)

    def get_redeem_code(self, code: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {REDEEM_CODE_SELECT_SQL}
                FROM redeem_code
                WHERE UPPER(code) = UPPER(?)
                LIMIT 1
                """,
                (str(code or "").strip(),),
            ).fetchone()
        return self._decode_redeem_code_row(row) if row else None

    def list_redeem_codes_by_batch(self, batch_id: str, status: str = "") -> List[Dict[str, object]]:
        clauses = ["batchId = :batch_id"]
        params: Dict[str, object] = {"batch_id": str(batch_id or "").strip()}
        normalized_status = str(status or "").strip()
        if normalized_status:
            clauses.append("status = :status")
            params["status"] = normalized_status
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT {REDEEM_CODE_SELECT_SQL}
                FROM redeem_code
                WHERE {" AND ".join(clauses)}
                ORDER BY updateTime DESC, createTime DESC, code ASC
                """,
                params,
            ).fetchall()
        return [self._decode_redeem_code_row(row) for row in rows]

    def consume_redeem_code(
        self,
        code: str,
        student_user_id: str,
        used_at: str,
        update_time: str,
        source_order_id: str = "",
    ) -> bool:
        normalized_code = str(code or "").strip().upper()
        with get_connection(self.db_path) as connection:
            result = connection.execute(
                """
                UPDATE redeem_code
                SET status = 'USED',
                    usedByUserId = :student_user_id,
                    usedAt = :used_at,
                    sourceOrderId = :source_order_id,
                    updateTime = :update_time
                WHERE UPPER(code) = :code
                  AND status = 'UNUSED'
                  AND usedByUserId = ''
                """,
                {
                    "code": normalized_code,
                    "student_user_id": str(student_user_id or "").strip(),
                    "used_at": str(used_at or "").strip(),
                    "source_order_id": str(source_order_id or "").strip(),
                    "update_time": str(update_time or "").strip(),
                },
            )
            if result.rowcount <= 0:
                connection.commit()
                return False
            connection.execute(
                """
                UPDATE redeem_code_batch
                SET usedCount = usedCount + 1,
                    updateTime = :update_time
                WHERE id = (
                  SELECT batchId
                  FROM redeem_code
                  WHERE UPPER(code) = :code
                  LIMIT 1
                )
                """,
                {"code": normalized_code, "update_time": str(update_time or "").strip()},
            )
            connection.commit()
        return True

    def create_subscription_order(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = {
            "id": str(payload.get("id", "")).strip(),
            "orderNo": str(payload.get("orderNo", "")).strip(),
            "studentUserId": str(payload.get("studentUserId", "")).strip(),
            "planCode": str(payload.get("planCode", "")).strip().upper(),
            "amountFen": max(0, self._safe_int(payload.get("amountFen", 0), 0)),
            "channel": str(payload.get("channel", "MOCK")).strip() or "MOCK",
            "status": str(payload.get("status", "CREATED")).strip() or "CREATED",
            "paidAt": str(payload.get("paidAt", "")).strip(),
            "closedAt": str(payload.get("closedAt", "")).strip(),
            "extJson": dump_json(payload.get("extJson", {}) if isinstance(payload.get("extJson", {}), dict) else {}),
            "createTime": str(payload.get("createTime", "")).strip(),
            "updateTime": str(payload.get("updateTime", "")).strip() or str(payload.get("createTime", "")).strip(),
        }
        if not normalized["id"] or not normalized["orderNo"] or not normalized["studentUserId"]:
            raise ValueError("subscription order payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO subscription_order (
                  id, orderNo, studentUserId, planCode, amountFen, channel, status, paidAt, closedAt,
                  extJson, createTime, updateTime
                ) VALUES (
                  :id, :orderNo, :studentUserId, :planCode, :amountFen, :channel, :status, :paidAt, :closedAt,
                  :extJson, :createTime, :updateTime
                )
                """,
                normalized,
            )
            connection.commit()
            row = connection.execute(
                f"SELECT {SUBSCRIPTION_ORDER_SELECT_SQL} FROM subscription_order WHERE id = ? LIMIT 1",
                (normalized["id"],),
            ).fetchone()
        return self._decode_subscription_order_row(row) if row else dict(normalized)

    def get_subscription_order(self, order_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"SELECT {SUBSCRIPTION_ORDER_SELECT_SQL} FROM subscription_order WHERE id = ? LIMIT 1",
                (str(order_id or "").strip(),),
            ).fetchone()
        return self._decode_subscription_order_row(row) if row else None

    def get_subscription_order_by_order_no(self, order_no: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"SELECT {SUBSCRIPTION_ORDER_SELECT_SQL} FROM subscription_order WHERE orderNo = ? LIMIT 1",
                (str(order_no or "").strip(),),
            ).fetchone()
        return self._decode_subscription_order_row(row) if row else None

    def update_subscription_order(self, payload: Dict[str, object]) -> Dict[str, object]:
        order_id = str(payload.get("id", "")).strip()
        if not order_id:
            raise ValueError("subscription order payload is invalid")
        existing = self.get_subscription_order(order_id)
        if not existing:
            raise ValueError("subscription order does not exist")
        merged = {
            **existing,
            **payload,
            "updateTime": str(payload.get("updateTime", "")).strip() or str(existing.get("updateTime", "")).strip(),
        }
        normalized = {
            "id": str(merged.get("id", "")).strip(),
            "orderNo": str(merged.get("orderNo", "")).strip(),
            "studentUserId": str(merged.get("studentUserId", "")).strip(),
            "planCode": str(merged.get("planCode", "")).strip().upper(),
            "amountFen": max(0, self._safe_int(merged.get("amountFen", 0), 0)),
            "channel": str(merged.get("channel", "MOCK")).strip() or "MOCK",
            "status": str(merged.get("status", "CREATED")).strip() or "CREATED",
            "paidAt": str(merged.get("paidAt", "")).strip(),
            "closedAt": str(merged.get("closedAt", "")).strip(),
            "extJson": dump_json(merged.get("extJson", {}) if isinstance(merged.get("extJson", {}), dict) else {}),
            "createTime": str(merged.get("createTime", "")).strip(),
            "updateTime": str(merged.get("updateTime", "")).strip() or str(merged.get("createTime", "")).strip(),
        }
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                UPDATE subscription_order
                SET orderNo = :orderNo,
                    studentUserId = :studentUserId,
                    planCode = :planCode,
                    amountFen = :amountFen,
                    channel = :channel,
                    status = :status,
                    paidAt = :paidAt,
                    closedAt = :closedAt,
                    extJson = :extJson,
                    createTime = :createTime,
                    updateTime = :updateTime
                WHERE id = :id
                """,
                normalized,
            )
            connection.commit()
        return self.get_subscription_order(order_id) or dict(normalized)

    def create_payment_transaction_mock(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = {
            "id": str(payload.get("id", "")).strip(),
            "orderId": str(payload.get("orderId", "")).strip(),
            "transactionNo": str(payload.get("transactionNo", "")).strip(),
            "requestId": str(payload.get("requestId", "")).strip(),
            "status": str(payload.get("status", "SUCCESS")).strip() or "SUCCESS",
            "payloadJson": dump_json(payload.get("payloadJson", {}) if isinstance(payload.get("payloadJson", {}), dict) else {}),
            "createTime": str(payload.get("createTime", "")).strip(),
            "updateTime": str(payload.get("updateTime", "")).strip() or str(payload.get("createTime", "")).strip(),
        }
        if not normalized["id"] or not normalized["orderId"] or not normalized["transactionNo"]:
            raise ValueError("mock payment transaction payload is invalid")
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO payment_transaction_mock (
                  id, orderId, transactionNo, requestId, status, payloadJson, createTime, updateTime
                ) VALUES (
                  :id, :orderId, :transactionNo, :requestId, :status, :payloadJson, :createTime, :updateTime
                )
                """,
                normalized,
            )
            connection.commit()
            row = connection.execute(
                f"SELECT {PAYMENT_TRANSACTION_MOCK_SELECT_SQL} FROM payment_transaction_mock WHERE id = ? LIMIT 1",
                (normalized["id"],),
            ).fetchone()
        return self._decode_payment_transaction_mock_row(row) if row else dict(normalized)

    def get_payment_transaction_mock_by_transaction_no(self, transaction_no: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {PAYMENT_TRANSACTION_MOCK_SELECT_SQL}
                FROM payment_transaction_mock
                WHERE transactionNo = ?
                LIMIT 1
                """,
                (str(transaction_no or "").strip(),),
            ).fetchone()
        return self._decode_payment_transaction_mock_row(row) if row else None

    def list_payment_transactions_by_order(self, order_id: str) -> List[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT {PAYMENT_TRANSACTION_MOCK_SELECT_SQL}
                FROM payment_transaction_mock
                WHERE orderId = ?
                ORDER BY createTime DESC, transactionNo DESC
                """,
                (str(order_id or "").strip(),),
            ).fetchall()
        return [self._decode_payment_transaction_mock_row(row) for row in rows]

    def create_conversion_event_log(self, payload: Dict[str, object]) -> Dict[str, object]:
        normalized = {
            "id": str(payload.get("id", "")).strip(),
            "studentUserId": str(payload.get("studentUserId", "")).strip(),
            "eventType": str(payload.get("eventType", "")).strip(),
            "eventTime": str(payload.get("eventTime", "")).strip(),
            "eventDate": str(payload.get("eventDate", "")).strip(),
            "sessionId": str(payload.get("sessionId", "")).strip(),
            "planCode": str(payload.get("planCode", "")).strip().upper(),
            "orderId": str(payload.get("orderId", "")).strip(),
            "redeemCode": str(payload.get("redeemCode", "")).strip().upper(),
            "channelCode": str(payload.get("channelCode", "")).strip(),
            "extJson": dump_json(payload.get("extJson", {}) if isinstance(payload.get("extJson", {}), dict) else {}),
            "createTime": str(payload.get("createTime", "")).strip(),
            "updateTime": str(payload.get("updateTime", "")).strip() or str(payload.get("createTime", "")).strip(),
        }
        if not normalized["id"] or not normalized["eventType"] or not normalized["eventTime"]:
            raise ValueError("conversion event payload is invalid")
        if not normalized["eventDate"]:
            normalized["eventDate"] = normalized["eventTime"][:10]
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO conversion_event_log (
                  id, studentUserId, eventType, eventTime, eventDate, sessionId, planCode, orderId,
                  redeemCode, channelCode, extJson, createTime, updateTime
                ) VALUES (
                  :id, :studentUserId, :eventType, :eventTime, :eventDate, :sessionId, :planCode, :orderId,
                  :redeemCode, :channelCode, :extJson, :createTime, :updateTime
                )
                """,
                normalized,
            )
            connection.commit()
            row = connection.execute(
                f"SELECT {CONVERSION_EVENT_LOG_SELECT_SQL} FROM conversion_event_log WHERE id = ? LIMIT 1",
                (normalized["id"],),
            ).fetchone()
        return self._decode_conversion_event_log_row(row) if row else dict(normalized)

    def list_conversion_event_logs(
        self,
        filters: Dict[str, str],
        page: int,
        size: int,
    ) -> Tuple[List[Dict[str, object]], int]:
        clauses = ["1 = 1"]
        params: Dict[str, object] = {}
        event_type = str(filters.get("eventType", "")).strip()
        student_user_id = str(filters.get("studentUserId", "")).strip()
        start_date = str(filters.get("startDate", "")).strip()
        end_date = str(filters.get("endDate", "")).strip()
        if event_type:
            clauses.append("eventType = :event_type")
            params["event_type"] = event_type
        if student_user_id:
            clauses.append("studentUserId = :student_user_id")
            params["student_user_id"] = student_user_id
        if start_date:
            clauses.append("eventDate >= :start_date")
            params["start_date"] = start_date
        if end_date:
            clauses.append("eventDate <= :end_date")
            params["end_date"] = end_date
        where_clause = " AND ".join(clauses)
        offset = (page - 1) * size
        params.update({"limit": size, "offset": offset})
        with get_connection(self.db_path) as connection:
            total = self._safe_int(
                connection.execute(
                    f"SELECT COUNT(*) AS total FROM conversion_event_log WHERE {where_clause}",
                    params,
                ).fetchone()["total"],
                0,
            )
            rows = connection.execute(
                f"""
                SELECT {CONVERSION_EVENT_LOG_SELECT_SQL}
                FROM conversion_event_log
                WHERE {where_clause}
                ORDER BY eventTime DESC, createTime DESC, id DESC
                LIMIT :limit OFFSET :offset
                """,
                params,
            ).fetchall()
        return [self._decode_conversion_event_log_row(row) for row in rows], total

    def list_tasks(
        self,
        filters: Dict[str, str],
        page: int,
        size: int,
        user_id: str = "",
    ) -> Tuple[List[Dict[str, object]], int]:
        clauses = ["1 = 1"]
        params: Dict[str, object] = {}
        if user_id:
            clauses.append("userId = :userId")
            params["userId"] = user_id
        for key in ("type", "status"):
            if filters.get(key):
                clauses.append(f"{key} = :{key}")
                params[key] = filters[key]
        if filters.get("questionId"):
            clauses.append("extJson LIKE :questionId")
            params["questionId"] = f'%\"questionId\": \"{filters["questionId"]}\"%'
        where_clause = " AND ".join(clauses)
        offset = (page - 1) * size
        params.update({"limit": size, "offset": offset})
        with get_connection(self.db_path) as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS total FROM task WHERE {where_clause}",
                params,
            ).fetchone()["total"]
            rows = connection.execute(
                f"""
                SELECT id, userId, type, status, progress, extJson, createTime, updateTime
                FROM task
                WHERE {where_clause}
                ORDER BY updateTime DESC, createTime DESC, id DESC
                LIMIT :limit OFFSET :offset
                """,
                params,
            ).fetchall()
        return [row_to_task(row) for row in rows], total

    def get_task(self, task_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT id, userId, type, status, progress, extJson, createTime, updateTime
                FROM task
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
        return row_to_task(row) if row else None

    def create_task(self, payload: Dict[str, object]) -> Dict[str, object]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO task (id, userId, type, status, progress, extJson, createTime, updateTime)
                VALUES (:id, :userId, :type, :status, :progress, :extJson, :createTime, :updateTime)
                """,
                payload,
            )
            connection.commit()
        return payload

    def update_task(self, payload: Dict[str, object]) -> Dict[str, object]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                UPDATE task
                SET userId = :userId,
                    type = :type,
                    status = :status,
                    progress = :progress,
                    extJson = :extJson,
                    createTime = :createTime,
                    updateTime = :updateTime
                WHERE id = :id
                """,
                payload,
            )
            connection.commit()
        return payload

    def list_subjects(self) -> List[Dict[str, Optional[str]]]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT id, parentId, name, extJson
                FROM knowledge
                ORDER BY sort, createTime, id
                """
            ).fetchall()
        knowledge_map = {row["id"]: row for row in rows}
        items: List[Dict[str, Optional[str]]] = []
        seen_subject_ids = set()
        for row in rows:
            ext_json = load_json_object(row["extJson"])
            level = int(ext_json.get("level", 0) or 0)
            subject_id = str(ext_json.get("subjectId", ""))
            if level == 1 and subject_id and subject_id not in seen_subject_ids:
                items.append({"id": subject_id, "name": row["name"], "parentId": None, "extJson": row["extJson"]})
                seen_subject_ids.add(subject_id)
            elif level == 2 and row["parentId"] in knowledge_map:
                parent_ext = load_json_object(knowledge_map[row["parentId"]]["extJson"])
                parent_subject_id = str(parent_ext.get("subjectId", ""))
                if parent_subject_id:
                    items.append({"id": row["id"], "name": row["name"], "parentId": parent_subject_id, "extJson": row["extJson"]})
        return items

    def list_knowledge(self, status: str = "", filters: Optional[Dict[str, str]] = None) -> List[Dict[str, object]]:
        normalized_filters = dict(filters or {})
        clauses = ["1 = 1"]
        params: Dict[str, object] = {"policy_version": POLICY_VERSION_CODE}
        clauses.append("COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = :policy_version")
        if status:
            clauses.append("status = :status")
            params["status"] = status
        subject_code = str(normalized_filters.get("subjectCode") or "").strip()
        if subject_code:
            clauses.append("COALESCE(json_extract(extJson, '$.subjectCode'), '') = :subject_code")
            params["subject_code"] = subject_code

        exam_category_code = str(normalized_filters.get("examCategoryCode") or "").strip()
        if exam_category_code:
            clauses.append(
                "("
                "COALESCE(json_extract(extJson, '$.examCategoryCode'), '') = :exam_category_code "
                "OR COALESCE(json_extract(extJson, '$.subjectType'), '') = 'PUBLIC'"
                ")"
            )
            params["exam_category_code"] = exam_category_code

        joint_exam_group_code = str(normalized_filters.get("jointExamGroupCode") or "").strip()
        if joint_exam_group_code:
            clauses.append(
                "("
                "COALESCE(json_extract(extJson, '$.jointExamGroupCode'), '') = :joint_exam_group_code "
                "OR COALESCE(json_extract(extJson, '$.subjectType'), '') = 'PUBLIC'"
                ")"
            )
            params["joint_exam_group_code"] = joint_exam_group_code
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT id, parentId, name, sort, status, extJson, createTime, updateTime
                FROM knowledge
                WHERE {" AND ".join(clauses)}
                ORDER BY COALESCE(parentId, id), sort, createTime
                """,
                params,
            ).fetchall()
        return [row_to_knowledge(row) for row in rows]

    def list_knowledge_children(self, parent_id: str | None, status: str = "") -> List[Dict[str, object]]:
        clauses = ["parentId IS NULL" if not parent_id else "parentId = :parentId"]
        params: Dict[str, object] = {}
        if parent_id:
            params["parentId"] = parent_id
        if status:
            clauses.append("status = :status")
            params["status"] = status
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT id, parentId, name, sort, status, extJson, createTime, updateTime
                FROM knowledge
                WHERE {" AND ".join(clauses)}
                ORDER BY sort, createTime
                """,
                params,
            ).fetchall()
        return [row_to_knowledge(row) for row in rows]

    def get_knowledge(self, knowledge_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT id, parentId, name, sort, status, extJson, createTime, updateTime
                FROM knowledge
                WHERE id = ?
                """,
                (knowledge_id,),
            ).fetchone()
        return row_to_knowledge(row) if row else None

    def count_knowledge_children(self, parent_id: str) -> int:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM knowledge WHERE parentId = ?",
                (parent_id,),
            ).fetchone()
        return int(row["total"])

    def get_knowledge_sibling_by_name(self, parent_id: str | None, name: str, exclude_id: str = "") -> Optional[Dict[str, object]]:
        clause = "parentId IS NULL" if not parent_id else "parentId = :parentId"
        params: Dict[str, object] = {"name": name}
        if parent_id:
            params["parentId"] = parent_id
        exclude_clause = ""
        if exclude_id:
            params["excludeId"] = exclude_id
            exclude_clause = "AND id != :excludeId"
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT id, parentId, name, sort, status, extJson, createTime, updateTime
                FROM knowledge
                WHERE {clause}
                  AND name = :name
                  {exclude_clause}
                LIMIT 1
                """,
                params,
            ).fetchone()
        return row_to_knowledge(row) if row else None

    def get_max_knowledge_sort(self, parent_id: str | None) -> int:
        clause = "parentId IS NULL" if not parent_id else "parentId = :parentId"
        params: Dict[str, object] = {}
        if parent_id:
            params["parentId"] = parent_id
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"SELECT COALESCE(MAX(sort), 0) AS maxSort FROM knowledge WHERE {clause}",
                params,
            ).fetchone()
        return int(row["maxSort"])

    def create_knowledge(self, payload: Dict[str, object]) -> Dict[str, object]:
        record = dict(payload)
        record["extJson"] = dump_json(load_json_object(record.get("extJson", {})))
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO knowledge (id, parentId, name, sort, status, extJson, createTime, updateTime)
                VALUES (:id, :parentId, :name, :sort, :status, :extJson, :createTime, :updateTime)
                """,
                record,
            )
            connection.commit()
        self._notify_knowledge_changed()
        return record

    def update_knowledge(self, payload: Dict[str, object]) -> Dict[str, object]:
        record = dict(payload)
        record["extJson"] = dump_json(load_json_object(record.get("extJson", {})))
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                UPDATE knowledge
                SET parentId = :parentId,
                    name = :name,
                    sort = :sort,
                    status = :status,
                    extJson = :extJson,
                    createTime = :createTime,
                    updateTime = :updateTime
                WHERE id = :id
                """,
                record,
            )
            connection.commit()
        self._notify_knowledge_changed()
        return record

    def delete_knowledge(self, knowledge_id: str) -> None:
        with get_connection(self.db_path) as connection:
            connection.execute("DELETE FROM knowledge WHERE id = ?", (knowledge_id,))
            connection.commit()
        self._notify_knowledge_changed()

    def list_questions(
        self,
        filters: dict[str, str],
        page: int,
        size: int,
        actor_role: str,
        actor_user_id: str,
    ) -> Tuple[List[Dict[str, str]], int]:
        clauses = ["1 = 1"]
        params: dict[str, object] = {}
        policy_version = (
            str(
                filters.get("policyVersion")
                or filters.get("policyVersionCode")
                or ""
            ).strip()
            or POLICY_VERSION_CODE
        )
        clauses.append("COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = :policy_version")
        params["policy_version"] = policy_version
        for key in ("knowledgeId", "userId", "type", "status"):
            if filters.get(key):
                clauses.append(f"{key} = :{key}")
                params[key] = filters[key]
        raw_question_ids = str(filters.get("questionIds") or "").strip()
        if raw_question_ids:
            normalized_question_ids: List[str] = []
            seen_question_ids: set[str] = set()
            for raw_question_id in raw_question_ids.split(","):
                question_id = str(raw_question_id or "").strip()
                if not question_id or question_id in seen_question_ids:
                    continue
                seen_question_ids.add(question_id)
                normalized_question_ids.append(question_id)
            if normalized_question_ids:
                placeholders: List[str] = []
                for index, question_id in enumerate(normalized_question_ids):
                    placeholder = f"question_id_{index}"
                    placeholders.append(f":{placeholder}")
                    params[placeholder] = question_id
                clauses.append(f"id IN ({','.join(placeholders)})")
        if filters.get("keyword"):
            clauses.append("(stem LIKE :keyword OR extJson LIKE :keyword)")
            params["keyword"] = f'%{filters["keyword"]}%'
        exam_category_code = str(filters.get("examCategoryCode") or "").strip()
        if exam_category_code:
            allowed_group_codes = [
                str(item.get("jointExamGroupCode", "")).strip()
                for item in list_joint_exam_groups(exam_category_code)
                if str(item.get("jointExamGroupCode", "")).strip()
            ]
            params["exam_category_code"] = exam_category_code
            if allowed_group_codes:
                allowed_group_placeholders: List[str] = []
                for index, group_code in enumerate(allowed_group_codes):
                    placeholder = f"allowed_group_code_{index}"
                    allowed_group_placeholders.append(f":{placeholder}")
                    params[placeholder] = group_code
                clauses.append(
                    "("
                    "(COALESCE(json_extract(extJson, '$.subjectType'), '') != 'PUBLIC' "
                    "AND COALESCE(json_extract(extJson, '$.examCategoryCode'), '') = :exam_category_code)"
                    " OR "
                    "(COALESCE(json_extract(extJson, '$.subjectType'), '') = 'PUBLIC' "
                    "AND EXISTS ("
                    "SELECT 1 FROM json_each(extJson, '$.applicableGroups') AS applicable_group "
                    f"WHERE applicable_group.value IN ({','.join(allowed_group_placeholders)})"
                    "))"
                    ")"
                )
            else:
                clauses.append("COALESCE(json_extract(extJson, '$.examCategoryCode'), '') = :exam_category_code")
        joint_exam_group_code = str(filters.get("jointExamGroupCode") or "").strip()
        if joint_exam_group_code:
            clauses.append(
                "("
                "EXISTS ("
                "SELECT 1 FROM json_each(extJson, '$.applicableGroups') AS applicable_group "
                "WHERE applicable_group.value = :joint_exam_group_code"
                ") "
                "OR COALESCE(json_extract(extJson, '$.jointExamGroupCode'), '') = :joint_exam_group_code "
                ")"
            )
            params["joint_exam_group_code"] = joint_exam_group_code
        subject_code = str(filters.get("subjectCode") or "").strip()
        if subject_code:
            clauses.append("COALESCE(json_extract(extJson, '$.subjectCode'), '') = :subject_code")
            params["subject_code"] = subject_code
        chapter_code = str(filters.get("chapterCode") or "").strip()
        if chapter_code:
            clauses.append("COALESCE(json_extract(extJson, '$.chapterCode'), '') = :chapter_code")
            params["chapter_code"] = chapter_code
        point_code = str(filters.get("pointCode") or "").strip()
        if point_code:
            clauses.append("COALESCE(json_extract(extJson, '$.pointCode'), '') = :point_code")
            params["point_code"] = point_code
        if actor_role == "teacher":
            clauses.append("(userId = :actorUserId OR status IN ('QA_IN_PROGRESS', 'REVIEW_PENDING'))")
            params["actorUserId"] = actor_user_id
        where_clause = " AND ".join(clauses)
        offset = (page - 1) * size
        params.update({"limit": size, "offset": offset})
        with get_connection(self.db_path) as connection:
            total = connection.execute(
                f'SELECT COUNT(*) AS total FROM question WHERE {where_clause}',
                params,
            ).fetchone()["total"]
            rows = connection.execute(
                f"""
                SELECT {QUESTION_SELECT_SQL}
                FROM question
                WHERE {where_clause}
                ORDER BY updateTime DESC, createTime DESC, id DESC
                LIMIT :limit OFFSET :offset
                """,
                params,
            ).fetchall()
        return [row_to_question(row) for row in rows], total

    def get_question(self, question_id: str) -> Optional[Dict[str, str]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {QUESTION_SELECT_SQL}
                FROM question
                WHERE id = :question_id
                  AND COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = :policy_version
                """,
                {"question_id": question_id, "policy_version": POLICY_VERSION_CODE},
            ).fetchone()
        return row_to_question(row) if row else None

    def list_questions_by_ids(self, question_ids: List[str]) -> List[Dict[str, str]]:
        if not question_ids:
            return []
        placeholders = ",".join("?" for _ in question_ids)
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                (
                    f"SELECT {QUESTION_SELECT_SQL} "
                    "FROM question "
                    f"WHERE id IN ({placeholders}) "
                    "AND COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = ?"
                ),
                tuple(question_ids) + (POLICY_VERSION_CODE,),
            ).fetchall()
        return [row_to_question(row) for row in rows]

    def get_first_published_question(self) -> Optional[Dict[str, str]]:
        with get_connection(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT {QUESTION_SELECT_SQL}
                FROM question
                WHERE status = 'PUBLISHED'
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()
        return row_to_question(row) if row else None

    def list_visible_published_questions(
        self,
        filters: Dict[str, str],
        actor_role: str,
        actor_user_id: str,
    ) -> List[Dict[str, str]]:
        clauses = ["q.status = 'PUBLISHED'"]
        params: Dict[str, object] = {}
        knowledge_id = str(filters.get("knowledgeId") or "").strip()
        if knowledge_id:
            clauses.append("q.knowledgeId = :knowledge_id")
            params["knowledge_id"] = knowledge_id
        question_type = str(filters.get("type", "")).strip()
        if question_type:
            clauses.append("q.type = :question_type")
            params["question_type"] = question_type
        keyword = str(filters.get("keyword", "")).strip()
        if keyword:
            clauses.append("(q.stem LIKE :keyword OR q.extJson LIKE :keyword)")
            params["keyword"] = f"%{keyword}%"

        subject_id = str(filters.get("subjectId") or "").strip()
        if subject_id:
            clauses.append("COALESCE(json_extract(q.extJson, '$.subjectId'), '') = :subject_id")
            params["subject_id"] = subject_id
        chapter = str(filters.get("chapter", "")).strip()
        if chapter:
            clauses.append("COALESCE(json_extract(q.extJson, '$.chapter'), '') = :chapter")
            params["chapter"] = chapter
        difficulty = str(filters.get("difficulty", "")).strip()
        if difficulty:
            clauses.append("COALESCE(json_extract(q.extJson, '$.difficulty'), '') = :difficulty")
            params["difficulty"] = difficulty

        policy_version = (
            str(
                filters.get("policyVersion")
                or filters.get("policyVersionCode")
                or ""
            ).strip()
            or POLICY_VERSION_CODE
        )
        clauses.append("COALESCE(json_extract(q.extJson, '$.policyVersionCode'), '') = :policy_version")
        params["policy_version"] = policy_version

        exam_category_code = str(filters.get("examCategoryCode") or "").strip()
        if exam_category_code:
            allowed_group_codes = [
                str(item.get("jointExamGroupCode", "")).strip()
                for item in list_joint_exam_groups(exam_category_code)
                if str(item.get("jointExamGroupCode", "")).strip()
            ]
            params["exam_category_code"] = exam_category_code
            if allowed_group_codes:
                allowed_group_placeholders: List[str] = []
                for index, group_code in enumerate(allowed_group_codes):
                    placeholder = f"allowed_group_code_{index}"
                    allowed_group_placeholders.append(f":{placeholder}")
                    params[placeholder] = group_code
                clauses.append(
                    "("
                    "(COALESCE(json_extract(q.extJson, '$.subjectType'), '') != 'PUBLIC' "
                    "AND COALESCE(json_extract(q.extJson, '$.examCategoryCode'), '') = :exam_category_code)"
                    " OR "
                    "(COALESCE(json_extract(q.extJson, '$.subjectType'), '') = 'PUBLIC' "
                    "AND EXISTS ("
                    "SELECT 1 FROM json_each(q.extJson, '$.applicableGroups') AS applicable_group "
                    f"WHERE applicable_group.value IN ({','.join(allowed_group_placeholders)})"
                    "))"
                    ")"
                )
            else:
                clauses.append("COALESCE(json_extract(q.extJson, '$.examCategoryCode'), '') = :exam_category_code")

        joint_exam_group_code = str(filters.get("jointExamGroupCode") or "").strip()
        if joint_exam_group_code:
            clauses.append(
                "("
                "EXISTS ("
                "SELECT 1 FROM json_each(q.extJson, '$.applicableGroups') AS applicable_group "
                "WHERE applicable_group.value = :joint_exam_group_code"
                ") "
                "OR COALESCE(json_extract(q.extJson, '$.jointExamGroupCode'), '') = :joint_exam_group_code "
                ")"
            )
            params["joint_exam_group_code"] = joint_exam_group_code

        subject_code = str(filters.get("subjectCode") or "").strip()
        if subject_code:
            clauses.append("COALESCE(json_extract(q.extJson, '$.subjectCode'), '') = :subject_code")
            params["subject_code"] = subject_code
        chapter_code = str(filters.get("chapterCode") or "").strip()
        if chapter_code:
            clauses.append("COALESCE(json_extract(q.extJson, '$.chapterCode'), '') = :chapter_code")
            params["chapter_code"] = chapter_code
        point_code = str(filters.get("pointCode") or "").strip()
        if point_code:
            clauses.append("COALESCE(json_extract(q.extJson, '$.pointCode'), '') = :point_code")
            params["point_code"] = point_code

        if actor_role == "teacher":
            clauses.append("q.userId = :user_id")
            params["user_id"] = actor_user_id
        where_clause = " AND ".join(clauses)
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT {QUESTION_SELECT_SQL_Q}
                FROM question AS q
                WHERE {where_clause}
                ORDER BY q.knowledgeId, q.id
                """,
                params,
            ).fetchall()
        return [row_to_question(row) for row in rows]

    def create_question(self, payload: dict[str, str]) -> dict[str, str]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO question (
                  id, knowledgeId, userId, type, stem, optionsJson,
                  answer, status, extJson, createTime, updateTime
                ) VALUES (
                  :id, :knowledgeId, :userId, :type, :stem, :optionsJson,
                  :answer, :status, :extJson, :createTime, :updateTime
                )
                """,
                payload,
            )
            connection.commit()
        return payload

    def update_question(self, payload: dict[str, str]) -> dict[str, str]:
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                UPDATE question
                SET knowledgeId = :knowledgeId,
                    userId = :userId,
                    type = :type,
                    stem = :stem,
                    optionsJson = :optionsJson,
                    answer = :answer,
                    status = :status,
                    extJson = :extJson,
                    createTime = :createTime,
                    updateTime = :updateTime
                WHERE id = :id
                """,
                payload,
            )
            connection.commit()
        return payload

    def delete_question(self, question_id: str) -> None:
        with get_connection(self.db_path) as connection:
            connection.execute("DELETE FROM question WHERE id = ?", (question_id,))
            connection.commit()

    def create_review(self, payload: dict[str, str]) -> None:
        question = self.get_question(payload["questionId"])
        if not question:
            return
        ext_json = load_json_object(question["extJson"])
        reviews = list(ext_json.get("reviewRecords", []))
        review = dict(payload)
        review.setdefault("reviewerId", str(review.get("reviewerUserId", "")))
        review.setdefault("timestamp", str(review.get("createTime", "")))
        reviews.append(review)
        if len(reviews) > 500:
            reviews = reviews[-500:]
        ext_json["reviewSummary"] = {
            "reviewCount": len(reviews),
            "latestReviewId": str(review.get("id", "")),
            "latestStatus": str(review.get("status", "")),
            "latestReviewerUserId": str(review.get("reviewerUserId", "")),
            "latestReviewedAt": str(review.get("createTime", "")),
        }
        ext_json["reviewRecords"] = reviews
        with get_connection(self.db_path) as connection:
            connection.execute(
                "UPDATE question SET extJson = ? WHERE id = ?",
                (dump_json(ext_json), payload["questionId"]),
            )
            connection.commit()

    def list_reviews(self, question_id: str) -> list[dict[str, str]]:
        question = self.get_question(question_id)
        if not question:
            return []
        ext_json = load_json_object(question["extJson"])
        reviews = ext_json.get("reviewRecords", [])
        if not isinstance(reviews, list):
            return []
        normalized = [item for item in reviews if isinstance(item, dict)]
        normalized.sort(
            key=lambda item: (
                str(item.get("createTime", "")),
                str(item.get("id", "")),
            ),
            reverse=True,
        )
        return [
            {
                "id": str(item.get("id", "")),
                "questionId": str(item.get("questionId", question_id)),
                "reviewerUserId": str(item.get("reviewerUserId", "")),
                "reviewerId": str(item.get("reviewerId", item.get("reviewerUserId", ""))),
                "status": str(item.get("status", "")),
                "createTime": str(item.get("createTime", "")),
                "timestamp": str(item.get("timestamp", item.get("createTime", ""))),
                "extJson": str(item.get("extJson", "{}")),
            }
            for item in normalized
        ]

    def get_student_question_bank(self, question_id: str, student_user_id: str) -> Optional[Dict[str, object]]:
        with get_connection(self.db_path) as connection:
            if student_user_id == SYSTEM_USER_ID:
                state = self._load_system_state(connection)
                return {
                    "id": "system-record",
                    "questionId": question_id,
                    "studentUserId": student_user_id,
                    "status": "ACTIVE",
                    "extJson": dump_json(state),
                }
            row = connection.execute(
                """
                SELECT """ + STUDENT_QUESTION_RECORD_SELECT_SQL + """
                FROM student_question_record
                WHERE studentUserId = ? AND questionId = ?
                """,
                (student_user_id, question_id),
            ).fetchone()
            return self._decode_student_question_record_row(row) if row else None

    def upsert_student_question_bank(self, payload: Dict[str, str]) -> Dict[str, object]:
        with get_connection(self.db_path) as connection:
            if payload["studentUserId"] == SYSTEM_USER_ID:
                state = load_json_object(payload.get("extJson", "{}"))
                self._save_system_state(connection, state)
                connection.commit()
                return dict(payload)
            self._ensure_student_row(connection, payload["studentUserId"])
            existing = self.get_student_question_record_row(payload["studentUserId"], payload["questionId"])
            stored = {
                "id": payload.get("id") or str((existing or {}).get("id", "")),
                "status": payload.get("status", "ACTIVE"),
                "extJson": payload.get("extJson", "{}"),
                "createTime": str((existing or {}).get("createTime", "")),
                "updateTime": str((existing or {}).get("updateTime", "")),
            }
            normalized_row = self._normalize_student_question_record_row(
                payload["studentUserId"],
                payload["questionId"],
                stored,
            )
            if not normalized_row:
                raise ValueError("student question payload is invalid")
            self._upsert_student_question_record_row(connection, normalized_row)
            connection.commit()
        saved = self.get_student_question_bank(payload["questionId"], payload["studentUserId"])
        return saved or dict(payload)

    def list_student_records(
        self,
        student_user_id: Optional[str],
        filters: Dict[str, str],
        page: int,
        size: int,
    ) -> Tuple[List[Dict[str, str]], int]:
        with get_connection(self.db_path) as connection:
            items = self._list_student_record_items(connection, student_user_id, filters)
            total = len(items)
            offset = (page - 1) * size
            return items[offset : offset + size], total

    def _student_record_student_ids(self, connection, student_user_id: Optional[str]) -> List[str]:
        if student_user_id:
            return [student_user_id]
        return [item["userId"] for item in self._list_directory_items(connection) if item.get("role") == "student"]

    def _collect_student_record_matches(
        self,
        connection,
        student_user_id: Optional[str],
        filters: Dict[str, str],
    ) -> Tuple[List[Dict[str, object]], Dict[str, Dict[str, str]]]:
        student_ids = self._student_record_student_ids(connection, student_user_id)
        matched_refs: List[Dict[str, object]] = []
        question_ref_pool: List[Dict[str, object]] = []
        allowed_student_ids = set(student_ids)
        for record in self._list_student_question_record_payloads(connection, student_user_id):
            if allowed_student_ids and record["studentUserId"] not in allowed_student_ids:
                continue
            if filters.get("paperId") and filters["paperId"] not in record["extJson"]:
                continue
            if not self._question_matches_date_filters(record["extJson"], filters):
                continue
            question_ref_pool.append(
                {
                    "questionId": record["questionId"],
                    "studentUserId": record["studentUserId"],
                    "recordId": record["id"],
                    "recordStatus": record["status"],
                    "recordExtJson": record["extJson"],
                    "recordFormalState": {
                        "profileAnchorFlag": self._safe_int(record.get("profileAnchorFlag", 0)),
                        "wrongBookFlag": self._safe_int(record.get("wrongBookFlag", 0)),
                        "wrongBookArchivedFlag": self._safe_int(record.get("wrongBookArchivedFlag", 0)),
                        "wrongBookCollectedAt": str(record.get("wrongBookCollectedAt", "")).strip(),
                        "wrongBookLastWrongAt": str(record.get("wrongBookLastWrongAt", "")).strip(),
                        "wrongBookReviewedAt": str(record.get("wrongBookReviewedAt", "")).strip(),
                        "wrongBookArchivedAt": str(record.get("wrongBookArchivedAt", "")).strip(),
                        "wrongBookRestoredAt": str(record.get("wrongBookRestoredAt", "")).strip(),
                        "wrongBookReviewCount": self._safe_int(record.get("wrongBookReviewCount", 0)),
                        "wrongBookPostWrongAttemptCount": self._safe_int(record.get("wrongBookPostWrongAttemptCount", 0)),
                        "wrongBookPostWrongCorrectCount": self._safe_int(record.get("wrongBookPostWrongCorrectCount", 0)),
                        "wrongBookLastReasonCode": str(record.get("wrongBookLastReasonCode", "")).strip(),
                        "wrongBookLastReasonLabel": str(record.get("wrongBookLastReasonLabel", "")).strip(),
                        "wrongCount": self._safe_int(record.get("wrongCount", 0)),
                    },
                }
            )

        question_ids = sorted({str(item["questionId"]) for item in question_ref_pool if str(item.get("questionId", "")).strip()})
        question_cache: Dict[str, Dict[str, str]] = {}
        if question_ids:
            rows = self._load_question_rows_for_student_records(
                connection,
                question_ids,
                self._normalized_policy_version(filters),
            )
            question_cache = {str(row["id"]): row_to_question(row) for row in rows}

        keyword = str(filters.get("keyword", "")).strip().lower()
        for ref in question_ref_pool:
            question_id = str(ref["questionId"])
            question = question_cache.get(question_id)
            if not question:
                continue
            if keyword:
                haystack = " ".join(
                    [
                        str(question.get("id", "")),
                        str(question.get("stem", "")),
                        str(question.get("extJson", "")),
                        str(ref.get("recordExtJson", "")),
                        str(ref.get("studentUserId", "")),
                    ]
                ).lower()
                if keyword not in haystack:
                    continue
            metadata = self._question_metadata(question)
            if filters.get("subjectId") and str(metadata.get("subjectId", "")) != filters["subjectId"]:
                continue
            if filters.get("chapter") and str(metadata.get("chapter", "")) != filters["chapter"]:
                continue
            if not self._question_matches_content_filters(question, filters, enforce_policy_version=False):
                continue
            matched_refs.append(
                {
                    "questionId": question_id,
                    "studentUserId": ref["studentUserId"],
                    "recordId": ref["recordId"],
                    "recordStatus": ref["recordStatus"],
                    "recordExtJson": ref["recordExtJson"],
                    "recordFormalState": dict(ref.get("recordFormalState", {})),
                    "knowledgeId": question["knowledgeId"],
                    "orderId": question["id"],
                }
            )

        matched_refs.sort(key=lambda item: (str(item["knowledgeId"]), str(item["orderId"])))
        return matched_refs, question_cache

    def _materialize_student_record_items(
        self,
        matched_refs: List[Dict[str, object]],
        question_cache: Dict[str, Dict[str, str]],
    ) -> List[Dict[str, str]]:
        items: List[Dict[str, str]] = []
        for ref in matched_refs:
            question_id = str(ref["questionId"])
            question = question_cache.get(question_id)
            if not question:
                continue
            ext_json = load_json_object(question["extJson"])
            ext_json["studentRecord"] = {
                "id": str(ref["recordId"]),
                "studentUserId": str(ref["studentUserId"]),
                "status": str(ref["recordStatus"]),
                "extJson": str(ref["recordExtJson"]),
                "formalState": dict(ref.get("recordFormalState", {})),
            }
            question_copy = dict(question)
            question_copy["extJson"] = dump_json(ext_json)
            items.append(question_copy)
        return items

    def _list_student_record_items(
        self,
        connection,
        student_user_id: Optional[str],
        filters: Dict[str, str],
    ) -> List[Dict[str, str]]:
        matched_refs, question_cache = self._collect_student_record_matches(connection, student_user_id, filters)
        return self._materialize_student_record_items(matched_refs, question_cache)

    def list_all_student_records(
        self,
        student_user_id: Optional[str],
        filters: Dict[str, str],
    ) -> List[Dict[str, str]]:
        with get_connection(self.db_path) as connection:
            return self._list_student_record_items(connection, student_user_id, filters)

    def list_student_records_by_user(self, student_user_id: str) -> List[Dict[str, str]]:
        return self.list_all_student_records(student_user_id, {"subjectId": "", "chapter": "", "paperId": ""})
