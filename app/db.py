from __future__ import annotations

# Observability note: persistence changes should preserve log/trace/metric hooks referenced in release readiness docs.
import json
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Union

from app.content_baseline import (
    POLICY_VERSION_CODE,
    all_joint_exam_group_codes,
    level_code_from_level,
    level_path_from_level,
    subject_applicable_group_codes,
    subject_id_from_subject_code,
)
from app.contracts import KNOWLEDGE_FIELDS, QUESTION_FIELDS, TASK_FIELDS
from app.shared.codecs import dump_json, hash_password, load_json_object

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "question_bank.db"
SCHEMA_PATH = BASE_DIR / "data" / "schema.sql"
KNOWLEDGE_TREE_PATH = BASE_DIR / "data" / "knowledge_tree.json"
LEARNING_METHOD_SEED_PATH = BASE_DIR / "data" / "learning_method_seed_v1.json"

SEED_TIME = "2026-03-17T00:00:00Z"
DIAGNOSTIC_STANDARD_SOURCE = "diagnostic-standard"
DIAGNOSTIC_STANDARD_L5_SUFFIX = "-diag-l5"
DIAGNOSTIC_STANDARD_MIN_PUBLISHED_QUESTIONS = 4
DIAGNOSTIC_STANDARD_OWNER_ID = "teacher-001"
GLOBAL_SUPER_ADMIN_ID = "admin-15373326608"
GLOBAL_SUPER_ADMIN_PHONE = "15373326608"
GLOBAL_SUPER_ADMIN_PASSWORD = os.environ.get(
    "QUESTION_BANK_SUPER_ADMIN_PASSWORD",
    "123456.",
)
GLOBAL_SUPER_ADMIN_PERMISSIONS = [
    "question:manage",
    "paper:manage",
    "analytics:view",
    "student:manage",
    "settings:manage",
    "message:send",
]

DEFAULT_SUBSCRIPTION_PLANS = (
    {
        "id": "subscription-plan-ai-score-boost-30d",
        "planCode": "AI_SCORE_BOOST_30D",
        "planName": "AI提分30天",
        "durationDays": 30,
        "listPriceFen": 19900,
        "salePriceFen": 19900,
        "status": "ACTIVE",
        "sort": 100,
    },
)

SEED_KNOWLEDGE_IDS = {
    "POLITICS_ROOT": "POLITICS-n00001",
    "POLITICS_SECTION": "POLITICS-n00004",
    "POLITICS_CHAPTER": "POLITICS-n00005",
    "POLITICS_POINT": "POLITICS-n00006",
    "POLITICS_POINT_ALT": "POLITICS-n00007",
    "POLITICS_SECOND_CHAPTER_POINT": "POLITICS-n00011",
    "ENGLISH_POINT": "ENGLISH-n00007",
    "INFO_TECH_ROOT": "INFO_TECH_INTRO-n00001",
    "INFO_TECH_SECTION": "INFO_TECH_INTRO-n00004",
    "INFO_TECH_CHAPTER": "INFO_TECH_INTRO-n00009",
    "INFO_TECH_POINT": "INFO_TECH_INTRO-n00010",
    "ADVANCED_MATH_POINT": "ADVANCED_MATH_1-n00006",
}

USER_FIELDS = (
    "id",
    "phone",
    "password",
    "status",
    "extJson",
    "createTime",
    "updateTime",
)

USER_AUTH_FIELDS = (
    "id",
    "userId",
    "type",
    "openid",
    "unionid",
    "extJson",
    "createTime",
    "updateTime",
)

USER_SELECT_SQL = ", ".join(USER_FIELDS)
USER_AUTH_SELECT_SQL = ", ".join(USER_AUTH_FIELDS)
LEGACY_STUDENT_PROFILE_HOT_FIELDS = {
    "checkInDates",
    "points",
    "title",
    "unlockedTitles",
    "dailyProgress",
    "pointsLedger",
    "aiQuota",
    "examSession",
}

def get_connection(db_path: Union[Path, str] = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA synchronous=NORMAL;")
    connection.execute("PRAGMA cache_size = -10000;")
    return connection


def init_db(db_path: Union[Path, str] = DEFAULT_DB_PATH) -> None:
    db_path = Path(db_path)
    with get_connection(db_path) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        ensure_challenge_point_event_attempt_schema(connection)
        ensure_student_question_record_hot_state_columns(connection)
        ensure_student_profile_state_columns(connection)
        ensure_student_review_plan_schema(connection)
        ensure_subscription_redeem_schema(connection)
        ensure_policy_version_indexes(connection)
        migrate_legacy_challenge_award_names(connection)
        migrate_legacy_passwords(connection)
        seed_users(connection)
        ensure_global_super_admin_account(connection)
        seed_subscription_plan_defaults(connection)
        seed_user_auth(connection)
        seed_knowledge(connection)
        seed_learning_methods(connection)
        migrate_legacy_outline_seed_data(connection)
        ensure_subject_diagnostic_knowledge_standard(connection)
        seed_questions(connection)
        ensure_subject_diagnostic_question_standard(connection)
        seed_student_question_records(connection)
        backfill_student_question_record_hot_state_columns(connection)
        backfill_student_profile_hot_state_tables(connection)
        ensure_student_profile_state_defaults(connection)
        connection.commit()


def ensure_challenge_point_event_attempt_schema(connection: sqlite3.Connection) -> None:
    table_row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = 'challenge_point_event'
        """
    ).fetchone()
    if not table_row:
        return
    table_sql = str(table_row["sql"] if isinstance(table_row, sqlite3.Row) else table_row[0] or "")
    existing_columns = {
        str(row["name"]).strip()
        for row in connection.execute("PRAGMA table_info(challenge_point_event)").fetchall()
    }
    has_attempt_column = "attemptKey" in existing_columns
    has_legacy_unique = "UNIQUE (studentUserId, questionId)" in table_sql
    has_target_unique = "UNIQUE (studentUserId, questionId, attemptKey)" in table_sql
    if has_attempt_column and has_target_unique and not has_legacy_unique:
        return

    connection.execute("PRAGMA foreign_keys = OFF;")
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS challenge_point_event_v2 (
              id TEXT PRIMARY KEY,
              studentUserId TEXT NOT NULL,
              questionId TEXT NOT NULL,
              subjectCode TEXT NOT NULL,
              attemptKey TEXT NOT NULL DEFAULT '',
              sourceType TEXT NOT NULL DEFAULT '',
              points INTEGER NOT NULL DEFAULT 1,
              awardedAt TEXT NOT NULL,
              extJson TEXT NOT NULL DEFAULT '{}',
              createTime TEXT NOT NULL,
              updateTime TEXT NOT NULL,
              FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
              FOREIGN KEY (questionId) REFERENCES question(id) ON DELETE CASCADE,
              UNIQUE (studentUserId, questionId, attemptKey)
            )
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO challenge_point_event_v2 (
              id, studentUserId, questionId, subjectCode, attemptKey, sourceType, points,
              awardedAt, extJson, createTime, updateTime
            )
            SELECT
              id,
              studentUserId,
              questionId,
              subjectCode,
              COALESCE(NULLIF(json_extract(extJson, '$.attemptKey'), ''), id) AS attemptKey,
              sourceType,
              points,
              awardedAt,
              extJson,
              createTime,
              updateTime
            FROM challenge_point_event
            """
        )
        connection.execute("DROP TABLE challenge_point_event")
        connection.execute("ALTER TABLE challenge_point_event_v2 RENAME TO challenge_point_event")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_challenge_point_event_subject_awarded "
            "ON challenge_point_event(subjectCode, awardedAt DESC)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_challenge_point_event_student_subject_awarded "
            "ON challenge_point_event(studentUserId, subjectCode, awardedAt DESC)"
        )
    finally:
        connection.execute("PRAGMA foreign_keys = ON;")


def migrate_legacy_challenge_award_names(connection: sqlite3.Connection) -> None:
    legacy_award_name = "学科闯关之星"
    normalized_award_name = "学科练习之星"
    connection.execute(
        """
        UPDATE challenge_point_award
        SET awardName = ?, updateTime = COALESCE(updateTime, createTime, ?)
        WHERE awardName = ?
        """,
        (normalized_award_name, SEED_TIME, legacy_award_name),
    )
    rows = connection.execute(
        """
        SELECT id, extJson
        FROM challenge_point_award
        WHERE extJson LIKE ?
        """,
        (f'%{legacy_award_name}%',),
    ).fetchall()
    for row in rows:
        ext_json = load_json_object(str(row["extJson"]))
        if not isinstance(ext_json, dict):
            continue
        if str(ext_json.get("awardName", "")).strip() != legacy_award_name:
            continue
        ext_json["awardName"] = normalized_award_name
        connection.execute(
            """
            UPDATE challenge_point_award
            SET extJson = ?, updateTime = COALESCE(updateTime, createTime, ?)
            WHERE id = ?
            """,
            (dump_json(ext_json), SEED_TIME, str(row["id"])),
        )


def ensure_student_question_record_hot_state_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        str(row["name"]).strip()
        for row in connection.execute("PRAGMA table_info(student_question_record)").fetchall()
    }
    statements = [
        ("wrongBookArchivedFlag", "ALTER TABLE student_question_record ADD COLUMN wrongBookArchivedFlag INTEGER NOT NULL DEFAULT 0"),
        ("wrongBookCollectedAt", "ALTER TABLE student_question_record ADD COLUMN wrongBookCollectedAt TEXT NOT NULL DEFAULT ''"),
        ("wrongBookLastWrongAt", "ALTER TABLE student_question_record ADD COLUMN wrongBookLastWrongAt TEXT NOT NULL DEFAULT ''"),
        ("wrongBookReviewedAt", "ALTER TABLE student_question_record ADD COLUMN wrongBookReviewedAt TEXT NOT NULL DEFAULT ''"),
        ("wrongBookArchivedAt", "ALTER TABLE student_question_record ADD COLUMN wrongBookArchivedAt TEXT NOT NULL DEFAULT ''"),
        ("wrongBookRestoredAt", "ALTER TABLE student_question_record ADD COLUMN wrongBookRestoredAt TEXT NOT NULL DEFAULT ''"),
        ("wrongBookReviewCount", "ALTER TABLE student_question_record ADD COLUMN wrongBookReviewCount INTEGER NOT NULL DEFAULT 0"),
        ("wrongBookPostWrongAttemptCount", "ALTER TABLE student_question_record ADD COLUMN wrongBookPostWrongAttemptCount INTEGER NOT NULL DEFAULT 0"),
        ("wrongBookPostWrongCorrectCount", "ALTER TABLE student_question_record ADD COLUMN wrongBookPostWrongCorrectCount INTEGER NOT NULL DEFAULT 0"),
        ("wrongBookLastReasonCode", "ALTER TABLE student_question_record ADD COLUMN wrongBookLastReasonCode TEXT NOT NULL DEFAULT ''"),
        ("wrongBookLastReasonLabel", "ALTER TABLE student_question_record ADD COLUMN wrongBookLastReasonLabel TEXT NOT NULL DEFAULT ''"),
        ("personalBankCollectedAt", "ALTER TABLE student_question_record ADD COLUMN personalBankCollectedAt TEXT NOT NULL DEFAULT ''"),
        ("personalBankSourceType", "ALTER TABLE student_question_record ADD COLUMN personalBankSourceType TEXT NOT NULL DEFAULT ''"),
        ("personalBankSourceLabel", "ALTER TABLE student_question_record ADD COLUMN personalBankSourceLabel TEXT NOT NULL DEFAULT ''"),
        ("profileAnchorFlag", "ALTER TABLE student_question_record ADD COLUMN profileAnchorFlag INTEGER NOT NULL DEFAULT 0"),
    ]
    for column_name, statement in statements:
        if column_name in existing_columns:
            continue
        connection.execute(statement)
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_student_question_record_user_wrong_book_archived "
        "ON student_question_record(studentUserId, wrongBookArchivedFlag, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_student_question_record_user_personal_bank_source "
        "ON student_question_record(studentUserId, personalBankFlag, personalBankSourceType, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_student_question_record_user_profile_anchor "
        "ON student_question_record(studentUserId, profileAnchorFlag, updateTime)"
    )


def ensure_student_profile_state_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        str(row["name"]).strip()
        for row in connection.execute("PRAGMA table_info(student_profile_state)").fetchall()
    }
    statements = [
        ("examCategoryCode", "ALTER TABLE student_profile_state ADD COLUMN examCategoryCode TEXT NOT NULL DEFAULT 'SCIENCE_ENGINEERING'"),
        ("jointExamGroupCode", "ALTER TABLE student_profile_state ADD COLUMN jointExamGroupCode TEXT NOT NULL DEFAULT 'SCIENCE_ENGINEERING_3'"),
    ]
    for column_name, statement in statements:
        if column_name in existing_columns:
            continue
        connection.execute(statement)


def load_student_profile_identity_payload(
    connection: sqlite3.Connection,
    student_user_id: str,
) -> Dict[str, str]:
    row = connection.execute(
        'SELECT extJson FROM "user" WHERE id = ?',
        (student_user_id,),
    ).fetchone()
    ext_json = load_json_object(str(row["extJson"] if isinstance(row, sqlite3.Row) else row[0] if row else "{}"))
    return {
        "vocationalMajor": str(ext_json.get("vocationalMajor", "")).strip(),
        "prepStage": str(ext_json.get("prepStage", "")).strip(),
    }


def ensure_student_review_plan_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS student_review_plan (
          id TEXT PRIMARY KEY,
          studentUserId TEXT NOT NULL,
          planType TEXT NOT NULL,
          planName TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'PENDING',
          generatedAt TEXT NOT NULL DEFAULT '',
          startedAt TEXT NOT NULL DEFAULT '',
          completedAt TEXT NOT NULL DEFAULT '',
          lastExecutedAt TEXT NOT NULL DEFAULT '',
          extJson TEXT NOT NULL DEFAULT '{}',
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL,
          FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
          UNIQUE (studentUserId, planType)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS student_review_plan_item (
          id TEXT PRIMARY KEY,
          planId TEXT NOT NULL,
          studentUserId TEXT NOT NULL,
          questionId TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'PENDING',
          sort INTEGER NOT NULL DEFAULT 0,
          completedAt TEXT NOT NULL DEFAULT '',
          extJson TEXT NOT NULL DEFAULT '{}',
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL,
          FOREIGN KEY (planId) REFERENCES student_review_plan(id) ON DELETE CASCADE,
          FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
          FOREIGN KEY (questionId) REFERENCES question(id) ON DELETE CASCADE,
          UNIQUE (planId, questionId)
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_student_review_plan_user_status_update "
        "ON student_review_plan(studentUserId, status, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_student_review_plan_item_plan_status_sort "
        "ON student_review_plan_item(planId, status, sort, updateTime)"
    )


def ensure_subscription_redeem_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS subscription_plan (
          id TEXT PRIMARY KEY,
          planCode TEXT NOT NULL UNIQUE,
          planName TEXT NOT NULL,
          durationDays INTEGER NOT NULL DEFAULT 30,
          listPriceFen INTEGER NOT NULL DEFAULT 0,
          salePriceFen INTEGER NOT NULL DEFAULT 0,
          status TEXT NOT NULL DEFAULT 'ACTIVE',
          sort INTEGER NOT NULL DEFAULT 0,
          extJson TEXT NOT NULL DEFAULT '{}',
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS student_subscription (
          id TEXT PRIMARY KEY,
          studentUserId TEXT NOT NULL,
          currentPlanCode TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'INACTIVE',
          startTime TEXT NOT NULL DEFAULT '',
          endTime TEXT NOT NULL DEFAULT '',
          lastActivatedAt TEXT NOT NULL DEFAULT '',
          lastExpiredAt TEXT NOT NULL DEFAULT '',
          sourceType TEXT NOT NULL DEFAULT '',
          sourceOrderId TEXT NOT NULL DEFAULT '',
          sourceRedeemCode TEXT NOT NULL DEFAULT '',
          totalActivatedDays INTEGER NOT NULL DEFAULT 0,
          extJson TEXT NOT NULL DEFAULT '{}',
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL,
          FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE,
          UNIQUE (studentUserId)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS redeem_code_batch (
          id TEXT PRIMARY KEY,
          batchCode TEXT NOT NULL UNIQUE,
          batchName TEXT NOT NULL,
          channelCode TEXT NOT NULL DEFAULT '',
          planCode TEXT NOT NULL DEFAULT '',
          totalCount INTEGER NOT NULL DEFAULT 0,
          usedCount INTEGER NOT NULL DEFAULT 0,
          expiresAt TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'ACTIVE',
          createdByUserId TEXT NOT NULL DEFAULT '',
          extJson TEXT NOT NULL DEFAULT '{}',
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS redeem_code (
          id TEXT PRIMARY KEY,
          batchId TEXT NOT NULL,
          code TEXT NOT NULL UNIQUE,
          planCode TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'UNUSED',
          expiresAt TEXT NOT NULL DEFAULT '',
          usedByUserId TEXT NOT NULL DEFAULT '',
          usedAt TEXT NOT NULL DEFAULT '',
          sourceOrderId TEXT NOT NULL DEFAULT '',
          extJson TEXT NOT NULL DEFAULT '{}',
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL,
          FOREIGN KEY (batchId) REFERENCES redeem_code_batch(id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS subscription_order (
          id TEXT PRIMARY KEY,
          orderNo TEXT NOT NULL UNIQUE,
          studentUserId TEXT NOT NULL,
          planCode TEXT NOT NULL DEFAULT '',
          amountFen INTEGER NOT NULL DEFAULT 0,
          channel TEXT NOT NULL DEFAULT 'MOCK',
          status TEXT NOT NULL DEFAULT 'CREATED',
          paidAt TEXT NOT NULL DEFAULT '',
          closedAt TEXT NOT NULL DEFAULT '',
          extJson TEXT NOT NULL DEFAULT '{}',
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL,
          FOREIGN KEY (studentUserId) REFERENCES "user"(id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_transaction_mock (
          id TEXT PRIMARY KEY,
          orderId TEXT NOT NULL,
          transactionNo TEXT NOT NULL UNIQUE,
          requestId TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'SUCCESS',
          payloadJson TEXT NOT NULL DEFAULT '{}',
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL,
          FOREIGN KEY (orderId) REFERENCES subscription_order(id) ON DELETE CASCADE
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversion_event_log (
          id TEXT PRIMARY KEY,
          studentUserId TEXT NOT NULL DEFAULT '',
          eventType TEXT NOT NULL,
          eventTime TEXT NOT NULL,
          eventDate TEXT NOT NULL DEFAULT '',
          sessionId TEXT NOT NULL DEFAULT '',
          planCode TEXT NOT NULL DEFAULT '',
          orderId TEXT NOT NULL DEFAULT '',
          redeemCode TEXT NOT NULL DEFAULT '',
          channelCode TEXT NOT NULL DEFAULT '',
          extJson TEXT NOT NULL DEFAULT '{}',
          createTime TEXT NOT NULL,
          updateTime TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_subscription_plan_status_sort "
        "ON subscription_plan(status, sort, planCode)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_student_subscription_status_end "
        "ON student_subscription(status, endTime, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_redeem_code_batch_status_expire "
        "ON redeem_code_batch(status, expiresAt, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_redeem_code_batch_used "
        "ON redeem_code(batchId, status, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_redeem_code_status_expire "
        "ON redeem_code(status, expiresAt, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_redeem_code_used_by_user "
        "ON redeem_code(usedByUserId, usedAt, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_subscription_order_student_status_update "
        "ON subscription_order(studentUserId, status, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_subscription_order_status_paid "
        "ON subscription_order(status, paidAt, updateTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_payment_transaction_mock_order "
        "ON payment_transaction_mock(orderId, createTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_conversion_event_type_time "
        "ON conversion_event_log(eventType, eventTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_conversion_event_student_time "
        "ON conversion_event_log(studentUserId, eventTime)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_conversion_event_date_type "
        "ON conversion_event_log(eventDate, eventType)"
    )


def seed_subscription_plan_defaults(connection: sqlite3.Connection) -> None:
    for item in DEFAULT_SUBSCRIPTION_PLANS:
        now_iso = SEED_TIME
        connection.execute(
            """
            INSERT OR IGNORE INTO subscription_plan (
              id, planCode, planName, durationDays, listPriceFen, salePriceFen,
              status, sort, extJson, createTime, updateTime
            ) VALUES (
              :id, :planCode, :planName, :durationDays, :listPriceFen, :salePriceFen,
              :status, :sort, :extJson, :createTime, :updateTime
            )
            """,
            {
                "id": str(item.get("id", "")).strip(),
                "planCode": str(item.get("planCode", "")).strip(),
                "planName": str(item.get("planName", "")).strip(),
                "durationDays": int(item.get("durationDays", 30) or 30),
                "listPriceFen": int(item.get("listPriceFen", 0) or 0),
                "salePriceFen": int(item.get("salePriceFen", 0) or 0),
                "status": str(item.get("status", "ACTIVE")).strip() or "ACTIVE",
                "sort": int(item.get("sort", 0) or 0),
                "extJson": dump_json({}),
                "createTime": now_iso,
                "updateTime": now_iso,
            },
        )

def backfill_student_question_record_hot_state_columns(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        UPDATE student_question_record
        SET wrongBookFlag = CASE
                WHEN COALESCE(json_extract(extJson, '$.wrongBook.isCollected'), 0) IN (1, '1', 'true', 'TRUE')
                THEN 1
                ELSE wrongBookFlag
            END,
            wrongBookArchivedFlag = CASE
                WHEN COALESCE(json_extract(extJson, '$.wrongBook.isArchived'), 0) IN (1, '1', 'true', 'TRUE')
                THEN 1
                ELSE wrongBookArchivedFlag
            END,
            wrongBookCollectedAt = COALESCE(NULLIF(json_extract(extJson, '$.wrongBook.collectedAt'), ''), wrongBookCollectedAt),
            wrongBookLastWrongAt = COALESCE(NULLIF(json_extract(extJson, '$.wrongBook.lastWrongAt'), ''), wrongBookLastWrongAt),
            wrongBookReviewedAt = COALESCE(NULLIF(json_extract(extJson, '$.wrongBook.reviewedAt'), ''), wrongBookReviewedAt),
            wrongBookArchivedAt = COALESCE(NULLIF(json_extract(extJson, '$.wrongBook.archivedAt'), ''), wrongBookArchivedAt),
            wrongBookRestoredAt = COALESCE(NULLIF(json_extract(extJson, '$.wrongBook.restoredAt'), ''), wrongBookRestoredAt),
            wrongBookReviewCount = CASE
                WHEN CAST(COALESCE(json_extract(extJson, '$.wrongBook.reviewCount'), 0) AS INTEGER) > wrongBookReviewCount
                THEN CAST(COALESCE(json_extract(extJson, '$.wrongBook.reviewCount'), 0) AS INTEGER)
                ELSE wrongBookReviewCount
            END,
            wrongBookPostWrongAttemptCount = CASE
                WHEN CAST(COALESCE(json_extract(extJson, '$.wrongBook.postWrongAttemptCount'), 0) AS INTEGER) > wrongBookPostWrongAttemptCount
                THEN CAST(COALESCE(json_extract(extJson, '$.wrongBook.postWrongAttemptCount'), 0) AS INTEGER)
                ELSE wrongBookPostWrongAttemptCount
            END,
            wrongBookPostWrongCorrectCount = CASE
                WHEN CAST(COALESCE(json_extract(extJson, '$.wrongBook.postWrongCorrectCount'), 0) AS INTEGER) > wrongBookPostWrongCorrectCount
                THEN CAST(COALESCE(json_extract(extJson, '$.wrongBook.postWrongCorrectCount'), 0) AS INTEGER)
                ELSE wrongBookPostWrongCorrectCount
            END,
            wrongBookLastReasonCode = COALESCE(NULLIF(json_extract(extJson, '$.wrongBook.lastReasonCode'), ''), wrongBookLastReasonCode),
            wrongBookLastReasonLabel = COALESCE(NULLIF(json_extract(extJson, '$.wrongBook.lastReasonLabel'), ''), wrongBookLastReasonLabel),
            personalBankFlag = CASE
                WHEN COALESCE(json_extract(extJson, '$.personalBank.isCollected'), 0) IN (1, '1', 'true', 'TRUE')
                THEN 1
                ELSE personalBankFlag
            END,
            personalBankCollectedAt = COALESCE(NULLIF(json_extract(extJson, '$.personalBank.collectedAt'), ''), personalBankCollectedAt),
            personalBankSourceType = COALESCE(NULLIF(json_extract(extJson, '$.personalBank.sourceType'), ''), personalBankSourceType),
            personalBankSourceLabel = COALESCE(NULLIF(json_extract(extJson, '$.personalBank.sourceLabel'), ''), personalBankSourceLabel),
            profileAnchorFlag = CASE
                WHEN json_type(extJson, '$.studentProfile') = 'object'
                THEN 1
                ELSE 0
            END
        """
    )


def backfill_student_profile_hot_state_tables(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        """
        SELECT studentUserId, questionId, extJson, updateTime
        FROM student_question_record
        WHERE profileAnchorFlag = 1
        """
    ).fetchall()
    for row in rows:
        student_user_id = str(row["studentUserId"] if isinstance(row, sqlite3.Row) else row[0] or "").strip()
        question_id = str(row["questionId"] if isinstance(row, sqlite3.Row) else row[1] or "").strip()
        if not student_user_id:
            continue
        record_ext = load_json_object(str(row["extJson"] if isinstance(row, sqlite3.Row) else row[2] or "{}"))
        student_profile = record_ext.get("studentProfile", {})
        if not isinstance(student_profile, dict):
            continue
        cold_profile = legacy_student_profile_cold_snapshot(student_profile)
        has_hot_state = legacy_student_profile_has_hot_state(student_profile)

        if not has_hot_state:
            if student_profile != cold_profile and question_id:
                preserved_update_time = str(row["updateTime"] if isinstance(row, sqlite3.Row) else row[3] or "").strip() or SEED_TIME
                record_ext["studentProfile"] = cold_profile
                connection.execute(
                    """
                    UPDATE student_question_record
                    SET extJson = ?, updateTime = ?
                    WHERE studentUserId = ? AND questionId = ?
                    """,
                    (
                        dump_json(record_ext),
                        preserved_update_time,
                        student_user_id,
                        question_id,
                    ),
                )
            continue

        legacy_profile_state = normalize_legacy_student_profile_state_payload(student_profile)
        daily_progress = student_profile.get("dailyProgress", {})
        if isinstance(daily_progress, dict):
            for progress_date, progress_row in daily_progress.items():
                normalized_progress = normalize_legacy_student_daily_progress_payload(
                    student_user_id,
                    progress_date,
                    progress_row,
                )
                if not normalized_progress:
                    continue
                existing_progress = load_student_daily_progress_for_backfill(
                    connection,
                    student_user_id,
                    normalized_progress["progressDate"],
                )
                upsert_student_daily_progress_for_backfill(
                    connection,
                    merge_student_daily_progress_for_backfill(existing_progress, normalized_progress),
                )
        for progress_date in legacy_profile_state["checkInDates"]:
            existing_progress = load_student_daily_progress_for_backfill(connection, student_user_id, progress_date)
            upsert_student_daily_progress_for_backfill(
                connection,
                merge_student_daily_progress_for_backfill(
                    existing_progress,
                    {
                        "id": f"{student_user_id}::{progress_date}",
                        "studentUserId": student_user_id,
                        "progressDate": progress_date,
                        "checkInCount": 1,
                        "practiceAnswers": 0,
                        "papersCompleted": 0,
                        "wrongBookReviewed": 0,
                        "rewardedKeys": [],
                        "createTime": progress_date,
                        "updateTime": progress_date,
                    },
                ),
            )

        points_ledger = student_profile.get("pointsLedger", [])
        if isinstance(points_ledger, list):
            for item in points_ledger:
                if not isinstance(item, dict):
                    continue
                event_key = str(item.get("eventKey", "")).strip()
                create_time = str(item.get("createTime", "")).strip() or SEED_TIME
                if not event_key:
                    continue
                connection.execute(
                    """
                    INSERT OR IGNORE INTO student_points_ledger (
                      id, studentUserId, eventKey, reason, points, extJson, createTime, updateTime
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"{student_user_id}::{event_key}",
                        student_user_id,
                        event_key,
                        str(item.get("reason", "")).strip(),
                        int(item.get("points", 0) or 0),
                        dump_json(item),
                        create_time,
                        create_time,
                    ),
                )

        upsert_student_profile_state_for_backfill(
            connection,
            merge_student_profile_state_for_backfill(
                load_student_profile_state_for_backfill(connection, student_user_id),
                legacy_profile_state,
                student_user_id,
            ),
        )
        if student_profile != cold_profile and question_id:
            record_ext["studentProfile"] = cold_profile
            preserved_update_time = str(row["updateTime"] if isinstance(row, sqlite3.Row) else row[3] or "").strip() or SEED_TIME
            connection.execute(
                """
                UPDATE student_question_record
                SET extJson = ?, updateTime = ?
                WHERE studentUserId = ? AND questionId = ?
                """,
                (
                    dump_json(record_ext),
                    preserved_update_time,
                    student_user_id,
                    question_id,
                ),
            )


def legacy_student_profile_cold_snapshot(student_profile: object) -> Dict[str, object]:
    if not isinstance(student_profile, dict):
        return {}
    return {
        "examCategoryCode": str(student_profile.get("examCategoryCode", "")).strip() or "SCIENCE_ENGINEERING",
        "jointExamGroupCode": str(student_profile.get("jointExamGroupCode", "")).strip() or "SCIENCE_ENGINEERING_3",
    }


def legacy_student_profile_has_hot_state(student_profile: object) -> bool:
    if not isinstance(student_profile, dict):
        return False
    return any(key in student_profile for key in LEGACY_STUDENT_PROFILE_HOT_FIELDS)


def normalize_string_list(values: object) -> List[str]:
    if not isinstance(values, list):
        return []
    normalized: List[str] = []
    seen: set[str] = set()
    for item in values:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def default_student_profile_state_payload() -> Dict[str, object]:
    return {
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
    }


def normalize_ai_quota_payload(payload: object) -> Dict[str, object]:
    if not isinstance(payload, dict):
        payload = {}
    return {
        "dailyLimit": int(payload.get("dailyLimit", 20) or 20),
        "usedCount": int(payload.get("usedCount", 0) or 0),
        "quotaDate": str(payload.get("quotaDate", "")).strip(),
    }


def normalize_exam_session_payload(payload: object) -> Dict[str, object]:
    if not isinstance(payload, dict):
        payload = {}
    return {
        "answeredCount": int(payload.get("answeredCount", 0) or 0),
        "elapsedSec": int(payload.get("elapsedSec", 0) or 0),
        "updateTime": str(payload.get("updateTime", "")).strip(),
    }


def normalize_legacy_student_profile_state_payload(student_profile: object) -> Dict[str, object]:
    defaults = default_student_profile_state_payload()
    if not isinstance(student_profile, dict):
        return dict(defaults)
    unlocked_titles = normalize_string_list(student_profile.get("unlockedTitles", defaults["unlockedTitles"]))
    if not unlocked_titles:
        unlocked_titles = list(defaults["unlockedTitles"])
    check_in_dates = sorted(normalize_string_list(student_profile.get("checkInDates", defaults["checkInDates"])))
    return {
        "examCategoryCode": str(student_profile.get("examCategoryCode", defaults["examCategoryCode"])).strip() or str(defaults["examCategoryCode"]),
        "jointExamGroupCode": str(student_profile.get("jointExamGroupCode", defaults["jointExamGroupCode"])).strip() or str(defaults["jointExamGroupCode"]),
        "vocationalMajor": str(student_profile.get("vocationalMajor", defaults["vocationalMajor"])).strip(),
        "prepStage": str(student_profile.get("prepStage", defaults["prepStage"])).strip(),
        "points": int(student_profile.get("points", defaults["points"]) or 0),
        "title": str(student_profile.get("title", defaults["title"])).strip() or str(defaults["title"]),
        "unlockedTitles": unlocked_titles,
        "checkInDates": check_in_dates,
        "aiQuota": normalize_ai_quota_payload(student_profile.get("aiQuota", defaults["aiQuota"])),
        "examSession": normalize_exam_session_payload(student_profile.get("examSession", defaults["examSession"])),
    }


def ai_quota_has_runtime_values(ai_quota: object) -> bool:
    normalized = normalize_ai_quota_payload(ai_quota)
    return (
        int(normalized["dailyLimit"]) != 20
        or int(normalized["usedCount"]) > 0
        or bool(str(normalized["quotaDate"]).strip())
    )


def merge_ai_quota_for_backfill(current_ai_quota: object, legacy_ai_quota: object) -> Dict[str, object]:
    current = normalize_ai_quota_payload(current_ai_quota)
    legacy = normalize_ai_quota_payload(legacy_ai_quota)
    current_date = str(current.get("quotaDate", "")).strip()
    legacy_date = str(legacy.get("quotaDate", "")).strip()
    if current_date and legacy_date:
        if legacy_date > current_date:
            return legacy
        if current_date > legacy_date:
            return current
        return {
            "dailyLimit": max(int(current["dailyLimit"]), int(legacy["dailyLimit"])),
            "usedCount": max(int(current["usedCount"]), int(legacy["usedCount"])),
            "quotaDate": current_date,
        }
    if ai_quota_has_runtime_values(current):
        return current
    if ai_quota_has_runtime_values(legacy):
        return legacy
    return normalize_ai_quota_payload(default_student_profile_state_payload()["aiQuota"])


def exam_session_has_runtime_values(exam_session: object) -> bool:
    normalized = normalize_exam_session_payload(exam_session)
    return (
        int(normalized["answeredCount"]) > 0
        or int(normalized["elapsedSec"]) > 0
        or bool(str(normalized["updateTime"]).strip())
    )


def merge_exam_session_for_backfill(current_exam_session: object, legacy_exam_session: object) -> Dict[str, object]:
    current = normalize_exam_session_payload(current_exam_session)
    legacy = normalize_exam_session_payload(legacy_exam_session)
    current_time = str(current.get("updateTime", "")).strip()
    legacy_time = str(legacy.get("updateTime", "")).strip()
    if current_time and legacy_time:
        return legacy if legacy_time > current_time else current
    if exam_session_has_runtime_values(current):
        return current
    if exam_session_has_runtime_values(legacy):
        return legacy
    return normalize_exam_session_payload(default_student_profile_state_payload()["examSession"])


def load_student_profile_state_for_backfill(
    connection: sqlite3.Connection,
    student_user_id: str,
) -> Optional[Dict[str, object]]:
    row = connection.execute(
        """
        SELECT studentUserId, points, title, unlockedTitlesJson, checkInDatesJson,
               examCategoryCode, jointExamGroupCode,
               aiDailyLimit, aiUsedCount, aiQuotaDate, examAnsweredCount, examElapsedSec, examUpdateTime,
               extJson, createTime, updateTime
        FROM student_profile_state
        WHERE studentUserId = ?
        """,
        (student_user_id,),
    ).fetchone()
    if not row:
        return None
    try:
        unlocked_titles = json.loads(str(row["unlockedTitlesJson"] or "[]"))
    except (TypeError, ValueError, json.JSONDecodeError):
        unlocked_titles = []
    try:
        check_in_dates = json.loads(str(row["checkInDatesJson"] or "[]"))
    except (TypeError, ValueError, json.JSONDecodeError):
        check_in_dates = []
    ext_json = load_json_object(str(row["extJson"] or "{}"))
    identity_payload = load_student_profile_identity_payload(connection, student_user_id)
    return {
        "studentUserId": student_user_id,
        "examCategoryCode": str(row["examCategoryCode"] or "").strip() or str(default_student_profile_state_payload()["examCategoryCode"]),
        "jointExamGroupCode": str(row["jointExamGroupCode"] or "").strip() or str(default_student_profile_state_payload()["jointExamGroupCode"]),
        "vocationalMajor": str(ext_json.get("vocationalMajor", "")).strip() or str(identity_payload["vocationalMajor"]),
        "prepStage": str(ext_json.get("prepStage", "")).strip() or str(identity_payload["prepStage"]),
        "points": int(row["points"] or 0),
        "title": str(row["title"] or "").strip() or "备考新星",
        "unlockedTitles": normalize_string_list(unlocked_titles),
        "checkInDates": sorted(normalize_string_list(check_in_dates)),
        "aiQuota": normalize_ai_quota_payload(
            {
                "dailyLimit": row["aiDailyLimit"],
                "usedCount": row["aiUsedCount"],
                "quotaDate": row["aiQuotaDate"],
            }
        ),
        "examSession": normalize_exam_session_payload(
            {
                "answeredCount": row["examAnsweredCount"],
                "elapsedSec": row["examElapsedSec"],
                "updateTime": row["examUpdateTime"],
            }
        ),
        "createTime": str(row["createTime"] or SEED_TIME).strip() or SEED_TIME,
        "updateTime": str(row["updateTime"] or SEED_TIME).strip() or SEED_TIME,
    }


def merge_student_profile_state_for_backfill(
    current_state: Optional[Dict[str, object]],
    legacy_state: Dict[str, object],
    student_user_id: str,
) -> Dict[str, object]:
    defaults = default_student_profile_state_payload()
    current = current_state or {
        "studentUserId": student_user_id,
        "createTime": SEED_TIME,
        "updateTime": SEED_TIME,
        **defaults,
    }
    current_points = int(current.get("points", 0) or 0)
    legacy_points = int(legacy_state.get("points", 0) or 0)
    default_exam_category_code = str(defaults["examCategoryCode"])
    default_joint_exam_group_code = str(defaults["jointExamGroupCode"])
    current_exam_category_code = str(current.get("examCategoryCode", default_exam_category_code)).strip() or default_exam_category_code
    current_joint_exam_group_code = str(current.get("jointExamGroupCode", default_joint_exam_group_code)).strip() or default_joint_exam_group_code
    legacy_exam_category_code = str(legacy_state.get("examCategoryCode", default_exam_category_code)).strip() or default_exam_category_code
    legacy_joint_exam_group_code = str(legacy_state.get("jointExamGroupCode", default_joint_exam_group_code)).strip() or default_joint_exam_group_code
    current_vocational_major = str(current.get("vocationalMajor", defaults["vocationalMajor"])).strip()
    legacy_vocational_major = str(legacy_state.get("vocationalMajor", defaults["vocationalMajor"])).strip()
    current_prep_stage = str(current.get("prepStage", defaults["prepStage"])).strip()
    legacy_prep_stage = str(legacy_state.get("prepStage", defaults["prepStage"])).strip()
    current_title = str(current.get("title", defaults["title"])).strip() or str(defaults["title"])
    legacy_title = str(legacy_state.get("title", defaults["title"])).strip() or str(defaults["title"])
    merged_title = current_title
    if legacy_points > current_points or (current_title == defaults["title"] and legacy_title != defaults["title"]):
        merged_title = legacy_title
    merged_exam_category_code = current_exam_category_code
    merged_joint_exam_group_code = current_joint_exam_group_code
    if (
        (current_exam_category_code == default_exam_category_code and legacy_exam_category_code != default_exam_category_code)
        or (current_joint_exam_group_code == default_joint_exam_group_code and legacy_joint_exam_group_code != default_joint_exam_group_code)
    ):
        merged_exam_category_code = legacy_exam_category_code
        merged_joint_exam_group_code = legacy_joint_exam_group_code
    merged_unlocked_titles = normalize_string_list(
        list(current.get("unlockedTitles", [])) + list(legacy_state.get("unlockedTitles", []))
    )
    if not merged_unlocked_titles:
        merged_unlocked_titles = list(defaults["unlockedTitles"])
    merged_check_in_dates = sorted(
        normalize_string_list(list(current.get("checkInDates", [])) + list(legacy_state.get("checkInDates", [])))
    )
    return {
        "studentUserId": student_user_id,
        "examCategoryCode": merged_exam_category_code,
        "jointExamGroupCode": merged_joint_exam_group_code,
        "vocationalMajor": current_vocational_major or legacy_vocational_major,
        "prepStage": current_prep_stage or legacy_prep_stage,
        "points": max(current_points, legacy_points),
        "title": merged_title,
        "unlockedTitles": merged_unlocked_titles,
        "checkInDates": merged_check_in_dates,
        "aiQuota": merge_ai_quota_for_backfill(current.get("aiQuota", {}), legacy_state.get("aiQuota", {})),
        "examSession": merge_exam_session_for_backfill(current.get("examSession", {}), legacy_state.get("examSession", {})),
        "createTime": str(current.get("createTime", SEED_TIME)).strip() or SEED_TIME,
        "updateTime": str(current.get("updateTime", SEED_TIME)).strip() or SEED_TIME,
    }


def upsert_student_profile_state_for_backfill(connection: sqlite3.Connection, payload: Dict[str, object]) -> None:
    ai_quota = normalize_ai_quota_payload(payload.get("aiQuota", {}))
    exam_session = normalize_exam_session_payload(payload.get("examSession", {}))
    unlocked_titles = normalize_string_list(payload.get("unlockedTitles", []))
    if not unlocked_titles:
        unlocked_titles = list(default_student_profile_state_payload()["unlockedTitles"])
    ext_json = {
        "vocationalMajor": str(payload.get("vocationalMajor", default_student_profile_state_payload()["vocationalMajor"])).strip(),
        "prepStage": str(payload.get("prepStage", default_student_profile_state_payload()["prepStage"])).strip(),
    }
    connection.execute(
        """
        INSERT INTO student_profile_state (
          id, studentUserId, examCategoryCode, jointExamGroupCode, points, title, unlockedTitlesJson, checkInDatesJson,
          aiDailyLimit, aiUsedCount, aiQuotaDate, examAnsweredCount, examElapsedSec, examUpdateTime,
          extJson, createTime, updateTime
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        (
            str(payload.get("studentUserId", "")).strip() or str(payload.get("id", "")).strip(),
            str(payload.get("studentUserId", "")).strip(),
            str(payload.get("examCategoryCode", default_student_profile_state_payload()["examCategoryCode"])).strip()
            or str(default_student_profile_state_payload()["examCategoryCode"]),
            str(payload.get("jointExamGroupCode", default_student_profile_state_payload()["jointExamGroupCode"])).strip()
            or str(default_student_profile_state_payload()["jointExamGroupCode"]),
            int(payload.get("points", 0) or 0),
            str(payload.get("title", "备考新星")).strip() or "备考新星",
            dump_json(unlocked_titles),
            dump_json(sorted(normalize_string_list(payload.get("checkInDates", [])))),
            int(ai_quota["dailyLimit"]),
            int(ai_quota["usedCount"]),
            str(ai_quota["quotaDate"]).strip(),
            int(exam_session["answeredCount"]),
            int(exam_session["elapsedSec"]),
            str(exam_session["updateTime"]).strip(),
            dump_json(ext_json),
            str(payload.get("createTime", SEED_TIME)).strip() or SEED_TIME,
            str(payload.get("updateTime", SEED_TIME)).strip() or SEED_TIME,
        ),
    )


def normalize_legacy_student_daily_progress_payload(
    student_user_id: str,
    progress_date: object,
    progress_row: object,
) -> Optional[Dict[str, object]]:
    normalized_date = str(progress_date or "").strip()
    if not normalized_date or not isinstance(progress_row, dict):
        return None
    return {
        "id": f"{student_user_id}::{normalized_date}",
        "studentUserId": student_user_id,
        "progressDate": normalized_date,
        "checkInCount": int(progress_row.get("checkInCount", 0) or 0),
        "practiceAnswers": int(progress_row.get("practiceAnswers", 0) or 0),
        "papersCompleted": int(progress_row.get("papersCompleted", 0) or 0),
        "wrongBookReviewed": int(progress_row.get("wrongBookReviewed", 0) or 0),
        "rewardedKeys": normalize_string_list(progress_row.get("rewardedKeys", [])),
        "createTime": normalized_date,
        "updateTime": normalized_date,
    }


def load_student_daily_progress_for_backfill(
    connection: sqlite3.Connection,
    student_user_id: str,
    progress_date: str,
) -> Optional[Dict[str, object]]:
    row = connection.execute(
        """
        SELECT id, studentUserId, progressDate, checkInCount, practiceAnswers, papersCompleted,
               wrongBookReviewed, rewardedKeysJson, createTime, updateTime
        FROM student_daily_progress
        WHERE studentUserId = ? AND progressDate = ?
        """,
        (student_user_id, progress_date),
    ).fetchone()
    if not row:
        return None
    try:
        rewarded_keys = json.loads(str(row["rewardedKeysJson"] or "[]"))
    except (TypeError, ValueError, json.JSONDecodeError):
        rewarded_keys = []
    return {
        "id": str(row["id"] or f"{student_user_id}::{progress_date}").strip() or f"{student_user_id}::{progress_date}",
        "studentUserId": student_user_id,
        "progressDate": progress_date,
        "checkInCount": int(row["checkInCount"] or 0),
        "practiceAnswers": int(row["practiceAnswers"] or 0),
        "papersCompleted": int(row["papersCompleted"] or 0),
        "wrongBookReviewed": int(row["wrongBookReviewed"] or 0),
        "rewardedKeys": normalize_string_list(rewarded_keys),
        "createTime": str(row["createTime"] or progress_date).strip() or progress_date,
        "updateTime": str(row["updateTime"] or progress_date).strip() or progress_date,
    }


def merge_student_daily_progress_for_backfill(
    current_progress: Optional[Dict[str, object]],
    incoming_progress: Dict[str, object],
) -> Dict[str, object]:
    if not current_progress:
        return incoming_progress
    progress_date = str(incoming_progress.get("progressDate", current_progress.get("progressDate", ""))).strip()
    student_user_id = str(
        incoming_progress.get("studentUserId", current_progress.get("studentUserId", ""))
    ).strip()
    current_update_time = str(current_progress.get("updateTime", progress_date)).strip() or progress_date
    incoming_update_time = str(incoming_progress.get("updateTime", progress_date)).strip() or progress_date
    return {
        "id": str(current_progress.get("id", incoming_progress.get("id", f"{student_user_id}::{progress_date}"))).strip()
        or f"{student_user_id}::{progress_date}",
        "studentUserId": student_user_id,
        "progressDate": progress_date,
        "checkInCount": max(
            int(current_progress.get("checkInCount", 0) or 0),
            int(incoming_progress.get("checkInCount", 0) or 0),
        ),
        "practiceAnswers": max(
            int(current_progress.get("practiceAnswers", 0) or 0),
            int(incoming_progress.get("practiceAnswers", 0) or 0),
        ),
        "papersCompleted": max(
            int(current_progress.get("papersCompleted", 0) or 0),
            int(incoming_progress.get("papersCompleted", 0) or 0),
        ),
        "wrongBookReviewed": max(
            int(current_progress.get("wrongBookReviewed", 0) or 0),
            int(incoming_progress.get("wrongBookReviewed", 0) or 0),
        ),
        "rewardedKeys": normalize_string_list(
            list(current_progress.get("rewardedKeys", [])) + list(incoming_progress.get("rewardedKeys", []))
        ),
        "createTime": str(current_progress.get("createTime", incoming_progress.get("createTime", progress_date))).strip()
        or progress_date,
        "updateTime": incoming_update_time if incoming_update_time > current_update_time else current_update_time,
    }


def upsert_student_daily_progress_for_backfill(connection: sqlite3.Connection, payload: Dict[str, object]) -> None:
    progress_date = str(payload.get("progressDate", "")).strip()
    student_user_id = str(payload.get("studentUserId", "")).strip()
    if not student_user_id or not progress_date:
        return
    connection.execute(
        """
        INSERT INTO student_daily_progress (
          id, studentUserId, progressDate, checkInCount, practiceAnswers, papersCompleted,
          wrongBookReviewed, rewardedKeysJson, extJson, createTime, updateTime
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        (
            str(payload.get("id", f"{student_user_id}::{progress_date}")).strip() or f"{student_user_id}::{progress_date}",
            student_user_id,
            progress_date,
            int(payload.get("checkInCount", 0) or 0),
            int(payload.get("practiceAnswers", 0) or 0),
            int(payload.get("papersCompleted", 0) or 0),
            int(payload.get("wrongBookReviewed", 0) or 0),
            dump_json(normalize_string_list(payload.get("rewardedKeys", []))),
            dump_json({}),
            str(payload.get("createTime", progress_date)).strip() or progress_date,
            str(payload.get("updateTime", progress_date)).strip() or progress_date,
        ),
    )


def ensure_student_profile_state_defaults(connection: sqlite3.Connection) -> None:
    default_state = default_student_profile_state_payload()
    rows = connection.execute(
        """
        SELECT studentUserId, extJson
        FROM student_question_record
        WHERE profileAnchorFlag = 1
        """
    ).fetchall()
    seen_student_ids: set[str] = set()
    for row in rows:
        student_user_id = str(row["studentUserId"] if isinstance(row, sqlite3.Row) else row[0] or "").strip()
        if not student_user_id or student_user_id in seen_student_ids:
            continue
        record_ext = load_json_object(str(row["extJson"] if isinstance(row, sqlite3.Row) else row[1] or "{}"))
        student_profile = record_ext.get("studentProfile", {})
        if not isinstance(student_profile, dict):
            continue
        seen_student_ids.add(student_user_id)
        identity_payload = load_student_profile_identity_payload(connection, student_user_id)
        connection.execute(
            """
            INSERT OR IGNORE INTO student_profile_state (
              id, studentUserId, examCategoryCode, jointExamGroupCode, points, title, unlockedTitlesJson, checkInDatesJson,
              aiDailyLimit, aiUsedCount, aiQuotaDate, examAnsweredCount, examElapsedSec, examUpdateTime,
              extJson, createTime, updateTime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_user_id,
                student_user_id,
                str(student_profile.get("examCategoryCode", default_state["examCategoryCode"])).strip() or str(default_state["examCategoryCode"]),
                str(student_profile.get("jointExamGroupCode", default_state["jointExamGroupCode"])).strip() or str(default_state["jointExamGroupCode"]),
                int(default_state["points"]),
                str(default_state["title"]),
                dump_json(default_state["unlockedTitles"]),
                dump_json(default_state["checkInDates"]),
                int(default_state["aiQuota"]["dailyLimit"]),
                int(default_state["aiQuota"]["usedCount"]),
                str(default_state["aiQuota"]["quotaDate"]),
                int(default_state["examSession"]["answeredCount"]),
                int(default_state["examSession"]["elapsedSec"]),
                str(default_state["examSession"]["updateTime"]),
                dump_json(identity_payload),
                SEED_TIME,
                SEED_TIME,
            ),
        )
        current = load_student_profile_state_for_backfill(connection, student_user_id) or {}
        current_identity_payload = {
            "vocationalMajor": str(current.get("vocationalMajor", "")).strip(),
            "prepStage": str(current.get("prepStage", "")).strip(),
        }
        if current_identity_payload == identity_payload:
            continue
        merged_payload = {
            **current,
            "studentUserId": student_user_id,
            "vocationalMajor": current_identity_payload["vocationalMajor"] or identity_payload["vocationalMajor"],
            "prepStage": current_identity_payload["prepStage"] or identity_payload["prepStage"],
        }
        upsert_student_profile_state_for_backfill(connection, merged_payload)


def ensure_policy_version_indexes(connection: sqlite3.Connection) -> None:
    statements = [
        (
            "CREATE INDEX IF NOT EXISTS idx_question_policy_version_expr "
            "ON question(COALESCE(json_extract(extJson, '$.policyVersionCode'), ''))"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_question_status_policy_version_expr "
            "ON question(status, COALESCE(json_extract(extJson, '$.policyVersionCode'), ''))"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_knowledge_policy_version_expr "
            "ON knowledge(COALESCE(json_extract(extJson, '$.policyVersionCode'), ''))"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_knowledge_status_policy_version_expr "
            "ON knowledge(status, COALESCE(json_extract(extJson, '$.policyVersionCode'), ''))"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_question_policy "
            "ON question(COALESCE(json_extract(extJson, '$.policyVersionCode'), ''))"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_question_joint_group "
            "ON question(COALESCE(json_extract(extJson, '$.jointExamGroupCode'), ''))"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_question_subject "
            "ON question(COALESCE(json_extract(extJson, '$.subjectCode'), ''))"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_question_chapter_code "
            "ON question(COALESCE(json_extract(extJson, '$.chapterCode'), ''))"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_question_point_code "
            "ON question(COALESCE(json_extract(extJson, '$.pointCode'), ''))"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_question_policy_chapter_code "
            "ON question("
            "COALESCE(json_extract(extJson, '$.policyVersionCode'), ''), "
            "COALESCE(json_extract(extJson, '$.chapterCode'), '')"
            ")"
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_question_policy_point_code "
            "ON question("
            "COALESCE(json_extract(extJson, '$.policyVersionCode'), ''), "
            "COALESCE(json_extract(extJson, '$.pointCode'), '')"
            ")"
        ),
    ]
    for statement in statements:
        connection.execute(statement)


def migrate_legacy_passwords(connection: sqlite3.Connection) -> None:
    rows = connection.execute('SELECT id, password FROM "user"').fetchall()
    for row in rows:
        if isinstance(row, sqlite3.Row):
            user_id = row["id"]
            stored = str(row["password"] or "")
        else:
            user_id = row[0]
            stored = str(row[1] or "")
        if stored.startswith("sha256$"):
            continue
        connection.execute(
            'UPDATE "user" SET password = ? WHERE id = ?',
            (hash_password(stored), user_id),
        )


def seed_users(connection: sqlite3.Connection) -> None:
    total = connection.execute('SELECT COUNT(*) AS total FROM "user"').fetchone()["total"]
    if total:
        return
    users = [
        _user_row(
            "admin-001",
            "13800000001",
            True,
            {
                "role": "super_admin",
                "name": "总管理员",
                "permissions": [
                    "student:manage",
                    "settings:manage",
                ],
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "",
                "prepStage": "",
            },
        ),
        _user_row(
            "teacher-001",
            "13800000002",
            True,
            {
                "role": "teacher",
                "name": "教师A",
                "permissions": ["question:manage", "paper:manage", "analytics:view", "message:send"],
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "",
                "prepStage": "",
            },
        ),
        _user_row(
            "teacher-002",
            "13800000003",
            True,
            {
                "role": "teacher",
                "name": "教师B",
                "permissions": ["question:manage", "paper:manage", "analytics:view", "message:send"],
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "",
                "prepStage": "",
            },
        ),
        _user_row(
            "academic-001",
            "13800000004",
            True,
            {
                "role": "teacher",
                "name": "教师学情专员",
                "permissions": ["question:manage", "paper:manage", "analytics:view", "message:send"],
                "examCategoryCode": "",
                "jointExamGroupCode": "",
                "vocationalMajor": "",
                "prepStage": "",
            },
        ),
        _user_row(
            "student-001",
            "13800000005",
            True,
            {
                "role": "student",
                "name": "理工考生",
                "permissions": [],
                "examCategoryCode": "SCIENCE_ENGINEERING",
                "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
                "vocationalMajor": "计算机类",
                "prepStage": "强化阶段",
            },
        ),
        _user_row(
            "student-002",
            "13800000006",
            True,
            {
                "role": "student",
                "name": "文学考生",
                "permissions": [],
                "examCategoryCode": "LITERATURE",
                "jointExamGroupCode": "LITERATURE_11",
                "vocationalMajor": "语言类",
                "prepStage": "冲刺阶段",
            },
        ),
        _user_row(
            "__system__",
            "00000000000",
            True,
            {
                "role": "system",
                "name": "system",
                "permissions": [],
                "systemSettings": {
                    "platformName": "专升本 ALL AI",
                    "defaultExamMinutes": 120,
                    "dailyCheckInPoints": 2,
                    "practiceRewardThreshold": 10,
                    "practiceRewardPoints": 2,
                    "paperRewardPoints": 2,
                    "wrongBookRewardThreshold": 5,
                    "wrongBookRewardPoints": 2,
                    "aiDailyLimit": 20,
                },
                "messages": [],
                "messageSettingsByUser": {},
                "paperTemplates": [],
            },
        ),
    ]
    connection.executemany(
        '''
        INSERT INTO "user" (id, phone, password, status, extJson, createTime, updateTime)
        VALUES (:id, :phone, :password, :status, :extJson, :createTime, :updateTime)
        ''',
        users,
    )


def _user_row(user_id: str, phone: str, enabled: bool, ext_json: Dict[str, object]) -> Dict[str, str]:
    payload = dict(ext_json)
    payload.setdefault("createTime", SEED_TIME)
    payload.setdefault("updateTime", SEED_TIME)
    return {
        "id": user_id,
        "phone": phone,
        "password": hash_password(f"seed-password-{user_id}"),
        "status": "ENABLED" if enabled else "DISABLED",
        "extJson": dump_json(payload),
        "createTime": SEED_TIME,
        "updateTime": SEED_TIME,
    }


def seed_student_question_records(connection: sqlite3.Connection) -> None:
    total = connection.execute("SELECT COUNT(*) AS total FROM student_question_record").fetchone()["total"]
    if total:
        return
    rows = [
        {
            "id": "student-bank-seed-001",
            "studentUserId": "student-001",
            "questionId": "question-seed-001",
            "status": "ACTIVE",
            "lastSubmittedAt": "",
            "lastAnswer": "B",
            "lastIsCorrect": 1,
            "answerCount": 1,
            "correctCount": 1,
            "wrongCount": 0,
            "totalAnswerDurationSec": 42,
            "latestSourceType": "SIMULATION_PAPER",
            "latestPaperId": "paper-demo-001",
            "wrongBookFlag": 0,
            "personalBankFlag": 0,
            "extJson": dump_json(
                {
                    "studentProfile": {
                        "examCategoryCode": "SCIENCE_ENGINEERING",
                        "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
                    },
                    "chapterPractice": {
                        "lastAnswer": "B",
                        "isCorrect": True,
                        "answerDurationSec": 42,
                        "submitCount": 1,
                    },
                    "simulationAttempts": {
                        "paper-demo-001": {
                            "lastAnswer": "B",
                            "isCorrect": True,
                            "answerDurationSec": 38,
                            "marked": False,
                        }
                    },
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "student-bank-seed-002",
            "studentUserId": "student-001",
            "questionId": "question-seed-002",
            "status": "ACTIVE",
            "lastSubmittedAt": "",
            "lastAnswer": "AC",
            "lastIsCorrect": 0,
            "answerCount": 1,
            "correctCount": 0,
            "wrongCount": 1,
            "totalAnswerDurationSec": 58,
            "latestSourceType": "SIMULATION_PAPER",
            "latestPaperId": "paper-demo-001",
            "wrongBookFlag": 0,
            "personalBankFlag": 0,
            "extJson": dump_json(
                {
                    "chapterPractice": {
                        "lastAnswer": "AC",
                        "isCorrect": False,
                        "answerDurationSec": 58,
                        "submitCount": 1,
                    },
                    "simulationAttempts": {
                        "paper-demo-001": {
                            "lastAnswer": "ABC",
                            "isCorrect": True,
                            "answerDurationSec": 55,
                            "marked": True,
                        }
                    },
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "student-bank-seed-004",
            "studentUserId": "student-001",
            "questionId": "question-seed-004",
            "status": "ACTIVE",
            "lastSubmittedAt": "",
            "lastAnswer": "B",
            "lastIsCorrect": 1,
            "answerCount": 2,
            "correctCount": 1,
            "wrongCount": 1,
            "totalAnswerDurationSec": 27,
            "latestSourceType": "",
            "latestPaperId": "",
            "wrongBookFlag": 0,
            "personalBankFlag": 0,
            "extJson": dump_json(
                {
                    "chapterPractice": {
                        "lastAnswer": "B",
                        "isCorrect": True,
                        "answerDurationSec": 27,
                        "submitCount": 2,
                    }
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "student-bank-seed-007",
            "studentUserId": "student-001",
            "questionId": "question-seed-007",
            "status": "ACTIVE",
            "lastSubmittedAt": "",
            "lastAnswer": "B",
            "lastIsCorrect": 1,
            "answerCount": 1,
            "correctCount": 1,
            "wrongCount": 0,
            "totalAnswerDurationSec": 50,
            "latestSourceType": "",
            "latestPaperId": "",
            "wrongBookFlag": 0,
            "personalBankFlag": 0,
            "extJson": dump_json(
                {
                    "chapterPractice": {
                        "lastAnswer": "B",
                        "isCorrect": True,
                        "answerDurationSec": 50,
                        "submitCount": 1,
                    }
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "student-bank-seed-008",
            "studentUserId": "student-001",
            "questionId": "question-seed-008",
            "status": "ACTIVE",
            "lastSubmittedAt": "",
            "lastAnswer": "B",
            "lastIsCorrect": 0,
            "answerCount": 1,
            "correctCount": 0,
            "wrongCount": 1,
            "totalAnswerDurationSec": 20,
            "latestSourceType": "",
            "latestPaperId": "",
            "wrongBookFlag": 1,
            "personalBankFlag": 0,
            "extJson": dump_json(
                {
                    "chapterPractice": {
                        "lastAnswer": "B",
                        "isCorrect": False,
                        "answerDurationSec": 20,
                        "submitCount": 1,
                    },
                    "wrongBook": {"isCollected": True, "collectedAt": "2026-03-17T08:00:00Z"},
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "student-bank-seed-005",
            "studentUserId": "student-002",
            "questionId": "question-seed-005",
            "status": "ACTIVE",
            "lastSubmittedAt": "",
            "lastAnswer": "终身学习能帮助人持续成长。",
            "lastIsCorrect": 0,
            "answerCount": 1,
            "correctCount": 0,
            "wrongCount": 1,
            "totalAnswerDurationSec": 166,
            "latestSourceType": "",
            "latestPaperId": "",
            "wrongBookFlag": 0,
            "personalBankFlag": 0,
            "extJson": dump_json(
                {
                    "studentProfile": {
                        "examCategoryCode": "LITERATURE",
                        "jointExamGroupCode": "LITERATURE_11",
                    },
                    "chapterPractice": {
                        "lastAnswer": "终身学习能帮助人持续成长。",
                        "isCorrect": False,
                        "answerDurationSec": 166,
                        "submitCount": 1,
                    },
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
    ]
    connection.executemany(
        """
        INSERT INTO student_question_record (
          id, studentUserId, questionId, status, lastSubmittedAt, lastAnswer, lastIsCorrect,
          answerCount, correctCount, wrongCount, totalAnswerDurationSec,
          latestSourceType, latestPaperId, wrongBookFlag, personalBankFlag,
          extJson, createTime, updateTime
        ) VALUES (
          :id, :studentUserId, :questionId, :status, :lastSubmittedAt, :lastAnswer, :lastIsCorrect,
          :answerCount, :correctCount, :wrongCount, :totalAnswerDurationSec,
          :latestSourceType, :latestPaperId, :wrongBookFlag, :personalBankFlag,
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
          personalBankFlag = excluded.personalBankFlag,
          extJson = excluded.extJson,
          createTime = excluded.createTime,
          updateTime = excluded.updateTime
        """,
        rows,
    )


def _global_super_admin_ext_json() -> Dict[str, object]:
    return {
        "role": "super_admin",
        "name": "全局超管",
        "permissions": list(GLOBAL_SUPER_ADMIN_PERMISSIONS),
        "examCategoryCode": "",
        "jointExamGroupCode": "",
        "vocationalMajor": "",
        "prepStage": "",
    }


def ensure_global_super_admin_account(connection: sqlite3.Connection) -> None:
    existing_user = connection.execute(
        f'SELECT {USER_SELECT_SQL} FROM "user" WHERE phone = ? LIMIT 1',
        (GLOBAL_SUPER_ADMIN_PHONE,),
    ).fetchone()
    if not existing_user:
        existing_user = connection.execute(
            f'SELECT {USER_SELECT_SQL} FROM "user" WHERE id = ? LIMIT 1',
            (GLOBAL_SUPER_ADMIN_ID,),
        ).fetchone()

    ext_json = _global_super_admin_ext_json()
    password = hash_password(GLOBAL_SUPER_ADMIN_PASSWORD)
    now = SEED_TIME

    if existing_user:
        merged_ext_json = load_json_object(existing_user["extJson"])
        merged_ext_json.update(ext_json)
        connection.execute(
            '''
            UPDATE "user"
            SET phone = ?,
                password = ?,
                status = ?,
                extJson = ?,
                updateTime = ?
            WHERE id = ?
            ''',
            (
                GLOBAL_SUPER_ADMIN_PHONE,
                password,
                "ENABLED",
                dump_json(merged_ext_json),
                now,
                existing_user["id"],
            ),
        )
        target_user_id = str(existing_user["id"])
    else:
        payload = {
            "id": GLOBAL_SUPER_ADMIN_ID,
            "phone": GLOBAL_SUPER_ADMIN_PHONE,
            "password": password,
            "status": "ENABLED",
            "extJson": dump_json(ext_json),
            "createTime": now,
            "updateTime": now,
        }
        connection.execute(
            '''
            INSERT INTO "user" (id, phone, password, status, extJson, createTime, updateTime)
            VALUES (:id, :phone, :password, :status, :extJson, :createTime, :updateTime)
            ''',
            payload,
        )
        target_user_id = GLOBAL_SUPER_ADMIN_ID

    existing_sms_auth = connection.execute(
        f"SELECT {USER_AUTH_SELECT_SQL} FROM userAuth WHERE type = ? AND openid = ? LIMIT 1",
        ("SMS", GLOBAL_SUPER_ADMIN_PHONE),
    ).fetchone()
    if existing_sms_auth:
        connection.execute(
            """
            UPDATE userAuth
            SET userId = ?,
                extJson = ?,
                updateTime = ?
            WHERE id = ?
            """,
            (
                target_user_id,
                dump_json({"source": "seed", "kind": "global-super-admin"}),
                now,
                existing_sms_auth["id"],
            ),
        )
    else:
        connection.execute(
            """
            INSERT INTO userAuth (id, userId, type, openid, unionid, extJson, createTime, updateTime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"user-auth-sms-{target_user_id}",
                target_user_id,
                "SMS",
                GLOBAL_SUPER_ADMIN_PHONE,
                "",
                dump_json({"source": "seed", "kind": "global-super-admin"}),
                now,
                now,
            ),
        )


def seed_user_auth(connection: sqlite3.Connection) -> None:
    total = connection.execute("SELECT COUNT(*) AS total FROM userAuth").fetchone()["total"]
    if total:
        return
    rows = [
        {
            "id": "user-auth-sms-student-001",
            "userId": "student-001",
            "type": "SMS",
            "openid": "student-001",
            "unionid": "",
            "extJson": dump_json({"source": "seed"}),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "user-auth-wechat-student-001",
            "userId": "student-001",
            "type": "WECHAT",
            "openid": "wx-student-001",
            "unionid": "union-student-001",
            "extJson": dump_json({"source": "seed"}),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
    ]
    connection.executemany(
        """
        INSERT INTO userAuth (id, userId, type, openid, unionid, extJson, createTime, updateTime)
        VALUES (:id, :userId, :type, :openid, :unionid, :extJson, :createTime, :updateTime)
        """,
        rows,
    )


def seed_knowledge(connection: sqlite3.Connection) -> None:
    total = connection.execute("SELECT COUNT(*) AS total FROM knowledge").fetchone()["total"]
    if total:
        return
    rows = _load_outline_knowledge_rows()
    if not rows:
        raise RuntimeError(f"未找到可用的 2026 大纲知识树种子文件: {KNOWLEDGE_TREE_PATH}")
    connection.executemany(
        """
        INSERT INTO knowledge (id, parentId, name, sort, status, extJson, createTime, updateTime)
        VALUES (:id, :parentId, :name, :sort, :status, :extJson, :createTime, :updateTime)
        """,
        rows,
    )


def seed_learning_methods(connection: sqlite3.Connection) -> None:
    if not LEARNING_METHOD_SEED_PATH.exists():
        return
    try:
        payload = json.loads(LEARNING_METHOD_SEED_PATH.read_text(encoding="utf-8"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return
    if not isinstance(payload, dict):
        return
    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        return

    seed_version = str(payload.get("version", "")).strip()
    seed_module = str(payload.get("module", "")).strip() or "learning-method"
    rows: List[Dict[str, object]] = []
    for index, raw_item in enumerate(items):
        if not isinstance(raw_item, dict):
            continue
        method_code = str(raw_item.get("methodCode", "")).strip()
        method_name = str(raw_item.get("methodName", "")).strip()
        if not method_code or not method_name:
            continue
        normalized_code = _sanitize_seed_identifier(method_code).upper() or method_code
        one_line_intro = str(raw_item.get("oneLineIntro", "")).strip()
        starter_task = str(raw_item.get("starterTask", "")).strip()
        difficulty_level = str(raw_item.get("difficultyLevel", "L1")).strip() or "L1"
        try:
            estimated_minutes = int(raw_item.get("estimatedMinutes", 15) or 15)
        except (TypeError, ValueError):
            estimated_minutes = 15
        ext_json = {
            "source": "seed",
            "seedVersion": seed_version,
            "module": seed_module,
        }
        rows.append(
            {
                "id": f"learning-method-{normalized_code.lower()}",
                "methodCode": normalized_code,
                "methodName": method_name,
                "oneLineIntro": one_line_intro,
                "useWhenJson": dump_json(normalize_string_list(raw_item.get("useWhen", []))),
                "stepsJson": dump_json(normalize_string_list(raw_item.get("steps", []))),
                "commonMistakesJson": dump_json(normalize_string_list(raw_item.get("commonMistakes", []))),
                "questionBankActionsJson": dump_json(normalize_string_list(raw_item.get("questionBankActions", []))),
                "starterTask": starter_task,
                "difficultyLevel": difficulty_level,
                "estimatedMinutes": max(1, estimated_minutes),
                "sort": index + 1,
                "status": "ACTIVE",
                "extJson": dump_json(ext_json),
                "createTime": SEED_TIME,
                "updateTime": SEED_TIME,
            }
        )
    if not rows:
        return
    connection.executemany(
        """
        INSERT OR IGNORE INTO learning_method (
          id, methodCode, methodName, oneLineIntro, useWhenJson, stepsJson, commonMistakesJson,
          questionBankActionsJson, starterTask, difficultyLevel, estimatedMinutes, sort,
          status, extJson, createTime, updateTime
        )
        VALUES (
          :id, :methodCode, :methodName, :oneLineIntro, :useWhenJson, :stepsJson, :commonMistakesJson,
          :questionBankActionsJson, :starterTask, :difficultyLevel, :estimatedMinutes, :sort,
          :status, :extJson, :createTime, :updateTime
        )
        """,
        rows,
    )


def _load_outline_knowledge_rows() -> list[dict[str, object]]:
    if not KNOWLEDGE_TREE_PATH.exists():
        return []
    payload = json.loads(KNOWLEDGE_TREE_PATH.read_text(encoding="utf-8"))
    raw_nodes = payload.get("nodes", []) if isinstance(payload, dict) else []
    if not isinstance(raw_nodes, list):
        return []

    rows: list[dict[str, object]] = []
    for raw_node in raw_nodes:
        if not isinstance(raw_node, dict):
            continue
        subject_code = str(raw_node.get("subject_code", "")).strip()
        subject_type = str(raw_node.get("subject_type", "")).strip() or "PROFESSIONAL"
        level = int(raw_node.get("level", 1) or 1)
        applicable_groups = subject_applicable_group_codes(subject_code)
        joint_exam_group_code = str(raw_node.get("joint_exam_group_code", "")).strip()
        if not applicable_groups and joint_exam_group_code:
            applicable_groups = [joint_exam_group_code]
        ext_json = {
            "level": level,
            "levelCode": level_code_from_level(level),
            "levelPath": level_path_from_level(level),
            "policyVersionCode": POLICY_VERSION_CODE,
            "subjectId": subject_id_from_subject_code(subject_code),
            "subjectCode": subject_code,
            "subjectType": subject_type,
            "examCategoryCode": "" if subject_type == "PUBLIC" else str(raw_node.get("exam_category_code", "")).strip(),
            "jointExamGroupCode": "" if subject_type == "PUBLIC" else joint_exam_group_code,
            "applicableGroups": applicable_groups or (all_joint_exam_group_codes() if subject_type == "PUBLIC" else []),
        }
        rows.append(
            {
                "id": str(raw_node.get("id", "")).strip(),
                "parentId": (
                    str(raw_node.get("parent_id", "")).strip()
                    if raw_node.get("parent_id") not in {None, ""}
                    else None
                ),
                "name": str(raw_node.get("name", "")).strip(),
                "sort": int(raw_node.get("sort", 0) or 0),
                "status": "ENABLED",
                "extJson": dump_json(ext_json),
                "createTime": SEED_TIME,
                "updateTime": SEED_TIME,
            }
        )
    return rows


def migrate_legacy_outline_seed_data(connection: sqlite3.Connection) -> None:
    legacy_knowledge_targets = {
        "knowledge-point-practice": (
            SEED_KNOWLEDGE_IDS["POLITICS_POINT"],
            "POLITICS",
            "理解哲学是系统化、理论化的世界观",
        ),
        "knowledge-point-truth": (
            SEED_KNOWLEDGE_IDS["POLITICS_POINT_ALT"],
            "POLITICS",
            "理解哲学基本问题和基本派别",
        ),
        "knowledge-point-stack": (
            SEED_KNOWLEDGE_IDS["INFO_TECH_POINT"],
            "INFO_TECH_INTRO",
            "掌握计算机硬件系统组成，掌握冯·诺依曼计算机体系结构。掌握微型计算机五大部件（运算器、控制器、存储器、输入/输出设备）的功能，理解微型计算机的工作原理和工作过程",
        ),
        "knowledge-point-subject-verb": (
            SEED_KNOWLEDGE_IDS["ENGLISH_POINT"],
            "ENGLISH",
            "掌握单词拼写和音节结构知识，准确认读单词中的字母或字母组合等",
        ),
        "knowledge-point-reading-summary": (
            SEED_KNOWLEDGE_IDS["ENGLISH_POINT"],
            "ENGLISH",
            "掌握单词拼写和音节结构知识，准确认读单词中的字母或字母组合等",
        ),
        "knowledge-point-limit-basic": (
            SEED_KNOWLEDGE_IDS["ADVANCED_MATH_POINT"],
            "ADVANCED_MATH_1",
            "理解函数的概念，掌握求函数的定义域、值域、表达式及在某一点的函数值的方法",
        ),
        "knowledge-point-party-leadership": (
            SEED_KNOWLEDGE_IDS["POLITICS_POINT_ALT"],
            "POLITICS",
            "理解哲学基本问题和基本派别",
        ),
    }
    delete_order = [
        "knowledge-point-practice",
        "knowledge-point-truth",
        "knowledge-point-party-leadership",
        "knowledge-point-subject-verb",
        "knowledge-point-reading-summary",
        "knowledge-point-limit-basic",
        "knowledge-point-stack",
        "knowledge-core-philosophy",
        "knowledge-core-theory",
        "knowledge-core-grammar",
        "knowledge-core-reading",
        "knowledge-core-limit",
        "knowledge-core-structure",
        "knowledge-root-politics",
        "knowledge-root-english",
        "knowledge-root-math",
        "knowledge-root-computer",
    ]
    legacy_ids = tuple(delete_order)

    placeholders = ",".join("?" for _ in legacy_ids)
    legacy_question_total = connection.execute(
        f"SELECT COUNT(*) AS total FROM question WHERE knowledgeId IN ({placeholders})",
        legacy_ids,
    ).fetchone()["total"]
    legacy_knowledge_total = connection.execute(
        f"SELECT COUNT(*) AS total FROM knowledge WHERE id IN ({placeholders})",
        legacy_ids,
    ).fetchone()["total"]
    if not legacy_question_total and not legacy_knowledge_total:
        return

    for legacy_id, target in legacy_knowledge_targets.items():
        current_id = _resolve_outline_target_knowledge_id(connection, *target)
        if not current_id:
            continue
        connection.execute(
            "UPDATE question SET knowledgeId = ? WHERE knowledgeId = ?",
            (current_id, legacy_id),
        )

    for legacy_id in delete_order:
        connection.execute("DELETE FROM knowledge WHERE id = ?", (legacy_id,))


def _resolve_outline_target_knowledge_id(
    connection: sqlite3.Connection,
    preferred_id: str,
    subject_code: str,
    name: str,
) -> str:
    normalized_preferred_id = str(preferred_id or "").strip()
    if normalized_preferred_id:
        row = connection.execute(
            "SELECT id FROM knowledge WHERE id = ?",
            (normalized_preferred_id,),
        ).fetchone()
        if row:
            return str(row["id"])
    row = connection.execute(
        """
        SELECT id
        FROM knowledge
        WHERE name = ?
          AND COALESCE(json_extract(extJson, '$.subjectCode'), '') = ?
          AND COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = ?
        ORDER BY createTime, id
        LIMIT 1
        """,
        (str(name or "").strip(), str(subject_code or "").strip(), POLICY_VERSION_CODE),
    ).fetchone()
    return str(row["id"]) if row else ""


def _seed_sort_key(item: Dict[str, object]) -> tuple[object, ...]:
    return (
        int(item.get("sort", 0) or 0),
        str(item.get("createTime", "") or ""),
        str(item.get("id", "") or ""),
        str(item.get("name", "") or ""),
    )


def _sanitize_seed_identifier(value: str) -> str:
    return "".join(
        character.lower() if character.isalnum() else "-"
        for character in str(value or "").strip()
    ).strip("-")


def _policy_knowledge_rows(connection: sqlite3.Connection) -> List[Dict[str, object]]:
    rows = connection.execute(
        """
        SELECT id, parentId, name, sort, status, extJson, createTime, updateTime
        FROM knowledge
        WHERE COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = ?
        ORDER BY sort, createTime, id
        """,
        (POLICY_VERSION_CODE,),
    ).fetchall()
    normalized_rows: List[Dict[str, object]] = []
    for row in rows:
        ext_json = load_json_object(row["extJson"])
        normalized_rows.append(
            {
                "id": str(row["id"] or "").strip(),
                "parentId": str(row["parentId"] or "").strip(),
                "name": str(row["name"] or "").strip(),
                "sort": int(row["sort"] or 0),
                "status": str(row["status"] or "").strip(),
                "extJson": ext_json,
                "createTime": str(row["createTime"] or "").strip(),
                "updateTime": str(row["updateTime"] or "").strip(),
                "level": int(ext_json.get("level", 0) or 0),
            }
        )
    return normalized_rows


def _subject_diagnostic_context(connection: sqlite3.Connection) -> Dict[str, Dict[str, object]]:
    knowledge_rows = _policy_knowledge_rows(connection)
    subjects: Dict[str, Dict[str, object]] = {}
    for row in knowledge_rows:
        ext_json = row["extJson"]
        subject_code = str(ext_json.get("subjectCode", "")).strip()
        if not subject_code:
            continue
        subject_bucket = subjects.setdefault(
            subject_code,
            {
                "subjectCode": subject_code,
                "subjectId": str(ext_json.get("subjectId", "")).strip() or subject_id_from_subject_code(subject_code),
                "subjectType": str(ext_json.get("subjectType", "")).strip() or "PROFESSIONAL",
                "examCategoryCode": str(ext_json.get("examCategoryCode", "")).strip(),
                "jointExamGroupCode": str(ext_json.get("jointExamGroupCode", "")).strip(),
                "applicableGroups": list(ext_json.get("applicableGroups", []) or []),
                "rows": [],
                "nodeById": {},
                "childrenByParent": {},
                "rootName": "",
            },
        )
        subject_bucket["rows"].append(row)
        subject_bucket["nodeById"][row["id"]] = row
        subject_bucket["childrenByParent"].setdefault(row["parentId"], []).append(row)
        if row["level"] == 1 and not subject_bucket["rootName"]:
            subject_bucket["rootName"] = row["name"]

    for subject_bucket in subjects.values():
        for child_rows in subject_bucket["childrenByParent"].values():
            child_rows.sort(key=_seed_sort_key)
        if not subject_bucket["applicableGroups"]:
            applicable_groups = subject_applicable_group_codes(subject_bucket["subjectCode"])
            subject_bucket["applicableGroups"] = (
                applicable_groups
                or (
                    all_joint_exam_group_codes()
                    if subject_bucket["subjectType"] == "PUBLIC"
                    else []
                )
            )
    return subjects


def ensure_subject_diagnostic_knowledge_standard(connection: sqlite3.Connection) -> None:
    subjects = _subject_diagnostic_context(connection)
    rows_to_insert: List[Dict[str, object]] = []
    for subject_bucket in subjects.values():
        chapter_rows = [
            row
            for row in subject_bucket["rows"]
            if int(row.get("level", 0) or 0) == 4
        ]
        chapter_rows.sort(key=_seed_sort_key)
        for chapter_row in chapter_rows:
            child_rows = subject_bucket["childrenByParent"].get(chapter_row["id"], [])
            if any(int(item.get("level", 0) or 0) >= 5 for item in child_rows):
                continue
            synthetic_id = f"{chapter_row['id']}{DIAGNOSTIC_STANDARD_L5_SUFFIX}"
            if synthetic_id in subject_bucket["nodeById"]:
                continue
            ext_json = {
                "level": 5,
                "levelCode": level_code_from_level(5),
                "levelPath": level_path_from_level(5),
                "policyVersionCode": POLICY_VERSION_CODE,
                "subjectId": subject_bucket["subjectId"],
                "subjectCode": subject_bucket["subjectCode"],
                "subjectType": subject_bucket["subjectType"],
                "examCategoryCode": "" if subject_bucket["subjectType"] == "PUBLIC" else subject_bucket["examCategoryCode"],
                "jointExamGroupCode": "" if subject_bucket["subjectType"] == "PUBLIC" else subject_bucket["jointExamGroupCode"],
                "applicableGroups": subject_bucket["applicableGroups"],
                "seedSource": DIAGNOSTIC_STANDARD_SOURCE,
                "synthetic": True,
            }
            next_sort = max((int(item.get("sort", 0) or 0) for item in child_rows), default=0) + 1
            rows_to_insert.append(
                {
                    "id": synthetic_id,
                    "parentId": chapter_row["id"],
                    "name": f"{chapter_row['name']}核心诊断点",
                    "sort": next_sort,
                    "status": "ENABLED",
                    "extJson": dump_json(ext_json),
                    "createTime": SEED_TIME,
                    "updateTime": SEED_TIME,
                }
            )
    if rows_to_insert:
        connection.executemany(
            """
            INSERT INTO knowledge (id, parentId, name, sort, status, extJson, createTime, updateTime)
            VALUES (:id, :parentId, :name, :sort, :status, :extJson, :createTime, :updateTime)
            """,
            rows_to_insert,
        )


def _diagnostic_question_templates(point_name: str) -> List[Dict[str, object]]:
    return [
        {
            "type": "single_choice",
            "stem": f"围绕「{point_name}」，下面哪项最符合该考点的核心要求？",
            "optionsJson": dump_json(
                [
                    {"key": "A", "content": f"先明确「{point_name}」的定义、条件与适用范围"},
                    {"key": "B", "content": f"只背「{point_name}」的结论，不分析前提"},
                    {"key": "C", "content": "忽略题目中的边界条件和限制"},
                    {"key": "D", "content": "把相近概念直接视为等价"},
                ]
            ),
            "answer": "A",
            "analysis": f"这道示例题用于稳定诊断层次。处理「{point_name}」时，应先回到定义、条件和典型用法。",
        },
        {
            "type": "judge",
            "stem": f"判断：学习「{point_name}」时，只记住结果、不看成立条件也能稳定解题。",
            "optionsJson": dump_json(
                [
                    {"key": "A", "content": "正确"},
                    {"key": "B", "content": "错误"},
                ]
            ),
            "answer": "B",
            "analysis": f"「{point_name}」的应用离不开条件判断，忽略成立前提通常会导致误判。",
        },
        {
            "type": "multiple_choice",
            "stem": f"围绕「{point_name}」，下列哪些做法有助于稳定得分？",
            "optionsJson": dump_json(
                [
                    {"key": "A", "content": "先识别题目对应的核心概念"},
                    {"key": "B", "content": "核对已知条件是否满足使用前提"},
                    {"key": "C", "content": "用典型题型回练巩固思路"},
                    {"key": "D", "content": "跳过过程，直接套用相似结论"},
                ]
            ),
            "answer": "ABC",
            "analysis": f"处理「{point_name}」时，要先识别概念、校验前提，再用典型题型巩固，不能直接跳步套结论。",
        },
        {
            "type": "single_choice",
            "stem": f"复盘「{point_name}」时，最适合作为第一步的动作是什么？",
            "optionsJson": dump_json(
                [
                    {"key": "A", "content": "回到定义和章节结构，先定位错因"},
                    {"key": "B", "content": "直接刷陌生难题"},
                    {"key": "C", "content": "跳过基础题，只做压轴题"},
                    {"key": "D", "content": "先记答案，再补过程"},
                ]
            ),
            "answer": "A",
            "analysis": f"标准化示例题优先强调诊断闭环，因此先定位「{point_name}」的定义与错因最有效。",
        },
    ]


def ensure_subject_diagnostic_question_standard(connection: sqlite3.Connection) -> None:
    subjects = _subject_diagnostic_context(connection)
    published_counts = {
        str(row["subject"] or "").strip(): int(row["count"] or 0)
        for row in connection.execute(
            """
            SELECT COALESCE(json_extract(extJson, '$.subjectCode'), '') AS subject,
                   COUNT(*) AS count
            FROM question
            WHERE status = 'PUBLISHED'
              AND COALESCE(json_extract(extJson, '$.policyVersionCode'), '') = ?
            GROUP BY subject
            """,
            (POLICY_VERSION_CODE,),
        ).fetchall()
    }
    existing_question_ids = {
        str(row["id"] or "").strip()
        for row in connection.execute("SELECT id FROM question").fetchall()
    }
    rows_to_insert: List[Dict[str, object]] = []

    for subject_code, subject_bucket in subjects.items():
        chapter_rows = [
            row
            for row in subject_bucket["rows"]
            if int(row.get("level", 0) or 0) == 4
        ]
        chapter_rows.sort(key=_seed_sort_key)
        point_targets: List[Dict[str, object]] = []
        for chapter_index, chapter_row in enumerate(chapter_rows, start=1):
            point_rows = [
                item
                for item in subject_bucket["childrenByParent"].get(chapter_row["id"], [])
                if int(item.get("level", 0) or 0) >= 5
            ]
            point_rows.sort(key=_seed_sort_key)
            for point_index, point_row in enumerate(point_rows, start=1):
                point_targets.append(
                    {
                        "chapterRow": chapter_row,
                        "pointRow": point_row,
                        "chapterCode": f"CH_{chapter_index:03d}",
                        "pointCode": f"PT_{chapter_index:03d}_{point_index:03d}",
                    }
                )
        if not point_targets:
            continue

        published_count = int(published_counts.get(subject_code, 0))
        inserted_count = 0
        template_count = len(_diagnostic_question_templates(point_targets[0]["pointRow"]["name"]))
        subject_slug = _sanitize_seed_identifier(subject_code)
        slot_index = 0
        while published_count + inserted_count < DIAGNOSTIC_STANDARD_MIN_PUBLISHED_QUESTIONS:
            point_target = point_targets[slot_index % len(point_targets)]
            question_id = f"question-seed-std-{subject_slug}-{slot_index + 1:03d}"
            slot_index += 1
            if question_id in existing_question_ids:
                continue
            point_name = point_target["pointRow"]["name"]
            chapter_name = point_target["chapterRow"]["name"]
            point_template = _diagnostic_question_templates(point_name)[(slot_index - 1) % template_count]
            question_ext_json = {
                "source": DIAGNOSTIC_STANDARD_SOURCE,
                "subjectId": subject_bucket["subjectId"],
                "chapter": chapter_name,
                "chapterCode": point_target["chapterCode"],
                "pointCode": point_target["pointCode"],
                "difficulty": "medium",
                "analysis": point_template["analysis"],
                "knowledgeTags": [chapter_name, point_name],
                "chapterNode": point_target["chapterRow"]["id"],
                "reviewRemark": "diagnostic standard seed",
                "policyVersionCode": POLICY_VERSION_CODE,
                "examCategoryCode": "" if subject_bucket["subjectType"] == "PUBLIC" else subject_bucket["examCategoryCode"],
                "jointExamGroupCode": "" if subject_bucket["subjectType"] == "PUBLIC" else subject_bucket["jointExamGroupCode"],
                "subjectCode": subject_code,
                "subjectType": subject_bucket["subjectType"],
                "moduleCode": f"{subject_code}_DIAG_STD_{slot_index:03d}",
                "sourceType": "demo",
                "applicableGroups": subject_bucket["applicableGroups"],
                "practiceConfig": {"timeLimitSec": 60},
                "paperBindings": [],
                "reviewRecords": [],
            }
            rows_to_insert.append(
                {
                    "id": question_id,
                    "knowledgeId": point_target["pointRow"]["id"],
                    "userId": DIAGNOSTIC_STANDARD_OWNER_ID,
                    "type": point_template["type"],
                    "stem": point_template["stem"],
                    "optionsJson": point_template["optionsJson"],
                    "answer": point_template["answer"],
                    "status": "PUBLISHED",
                    "extJson": dump_json(question_ext_json),
                    "createTime": SEED_TIME,
                    "updateTime": SEED_TIME,
                }
            )
            existing_question_ids.add(question_id)
            inserted_count += 1

    if rows_to_insert:
        connection.executemany(
            """
            INSERT INTO question (
              id, knowledgeId, userId, type, stem, optionsJson,
              answer, status, extJson, createTime, updateTime
            )
            VALUES (
              :id, :knowledgeId, :userId, :type, :stem, :optionsJson,
              :answer, :status, :extJson, :createTime, :updateTime
            )
            """,
            rows_to_insert,
        )


def seed_questions(connection: sqlite3.Connection) -> None:
    total = connection.execute("SELECT COUNT(*) AS total FROM question").fetchone()["total"]
    if total:
        return
    questions = [
        {
            "id": "question-seed-001",
            "knowledgeId": SEED_KNOWLEDGE_IDS["POLITICS_POINT"],
            "userId": "teacher-001",
            "type": "single_choice",
            "stem": "实践是检验真理的唯一标准，这句话强调了什么？",
            "optionsJson": dump_json(
                [
                    {"key": "A", "content": "真理来自权威"},
                    {"key": "B", "content": "真理必须接受实践检验"},
                    {"key": "C", "content": "真理不需要条件"},
                    {"key": "D", "content": "真理完全主观"},
                ]
            ),
            "answer": "B",
            "status": "PUBLISHED",
            "extJson": dump_json(
                {
                    "source": "seed",
                    "subjectId": "subject-politics",
                    "chapter": "导论",
                    "chapterCode": "CH_001",
                    "pointCode": "PT_001_001",
                    "difficulty": "medium",
                    "analysis": "题干强调通过实践判断认识是否正确，符合马克思主义认识论。",
                    "knowledgeTags": ["导论", "理解哲学是系统化、理论化的世界观"],
                    "chapterNode": "POLITICS-n00005",
                    "reviewRemark": "demo published",
                    "policyVersionCode": POLICY_VERSION_CODE,
                    "examCategoryCode": "",
                    "jointExamGroupCode": "",
                    "subjectCode": "POLITICS",
                    "subjectType": "PUBLIC",
                    "moduleCode": "POLITICS_PRACTICE_STANDARD",
                    "sourceType": "official",
                    "applicableGroups": all_joint_exam_group_codes(),
                    "practiceConfig": {"timeLimitSec": 60},
                    "paperBindings": [
                        {
                            "paperId": "paper-demo-001",
                            "paperName": "政治哲学章节卷",
                            "paperType": "chapter",
                            "paperStatus": "PUBLISHED",
                            "durationMinutes": 20,
                            "totalScore": 20,
                            "questionScore": 10,
                            "orderNo": 1,
                            "ownerUserId": "teacher-001",
                            "visibleToStudents": True,
                            "ruleMode": "manual",
                        }
                    ],
                    "reviewRecords": [
                        {
                            "id": "review-seed-001",
                            "questionId": "question-seed-001",
                            "reviewerUserId": "teacher-002",
                            "status": "REVIEW_PENDING",
                            "extJson": dump_json({"fromStatus": "QA_IN_PROGRESS", "toStatus": "REVIEW_PENDING"}),
                        },
                        {
                            "id": "review-seed-002",
                            "questionId": "question-seed-001",
                            "reviewerUserId": "admin-001",
                            "status": "PUBLISHED",
                            "extJson": dump_json({"fromStatus": "REVIEW_PENDING", "toStatus": "PUBLISHED"}),
                        },
                    ],
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "question-seed-002",
            "knowledgeId": SEED_KNOWLEDGE_IDS["POLITICS_POINT"],
            "userId": "teacher-001",
            "type": "multiple_choice",
            "stem": "下列哪些选项体现了实践的基本特征？",
            "optionsJson": dump_json(
                [
                    {"key": "A", "content": "客观物质性"},
                    {"key": "B", "content": "自觉能动性"},
                    {"key": "C", "content": "社会历史性"},
                    {"key": "D", "content": "完全脱离社会"},
                ]
            ),
            "answer": "ABC",
            "status": "PUBLISHED",
            "extJson": dump_json(
                {
                    "source": "seed",
                    "subjectId": "subject-politics",
                    "chapter": "导论",
                    "chapterCode": "CH_001",
                    "pointCode": "PT_001_001",
                    "difficulty": "hard",
                    "analysis": "实践具有客观物质性、自觉能动性和社会历史性。",
                    "knowledgeTags": ["导论", "理解哲学是系统化、理论化的世界观"],
                    "chapterNode": "POLITICS-n00005",
                    "reviewRemark": "demo published",
                    "policyVersionCode": POLICY_VERSION_CODE,
                    "examCategoryCode": "",
                    "jointExamGroupCode": "",
                    "subjectCode": "POLITICS",
                    "subjectType": "PUBLIC",
                    "moduleCode": "POLITICS_PRACTICE_FEATURES",
                    "sourceType": "official",
                    "applicableGroups": all_joint_exam_group_codes(),
                    "practiceConfig": {"timeLimitSec": 60},
                    "paperBindings": [
                        {
                            "paperId": "paper-demo-001",
                            "paperName": "政治哲学章节卷",
                            "paperType": "chapter",
                            "paperStatus": "PUBLISHED",
                            "durationMinutes": 20,
                            "totalScore": 20,
                            "questionScore": 10,
                            "orderNo": 2,
                            "ownerUserId": "teacher-001",
                            "visibleToStudents": True,
                            "ruleMode": "manual",
                        }
                    ],
                    "reviewRecords": [],
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "question-seed-003",
            "knowledgeId": SEED_KNOWLEDGE_IDS["POLITICS_SECOND_CHAPTER_POINT"],
            "userId": "teacher-002",
            "type": "judge",
            "stem": "中国特色社会主义最本质的特征是中国共产党领导。",
            "optionsJson": dump_json([{"key": "A", "content": "正确"}, {"key": "B", "content": "错误"}]),
            "answer": "A",
            "status": "PUBLISHED",
            "extJson": dump_json(
                {
                    "source": "seed",
                    "subjectId": "subject-politics",
                    "chapter": "世界的物质性及其发展规律",
                    "chapterCode": "CH_004",
                    "pointCode": "PT_004_001",
                    "difficulty": "easy",
                    "analysis": "这是党的理论体系中的重要判断。",
                    "knowledgeTags": ["世界的物质性及其发展规律", "理解马克思主义的物质观及其理论意义"],
                    "chapterNode": "POLITICS-n00010",
                    "reviewRemark": "demo published",
                    "policyVersionCode": POLICY_VERSION_CODE,
                    "examCategoryCode": "",
                    "jointExamGroupCode": "",
                    "subjectCode": "POLITICS",
                    "subjectType": "PUBLIC",
                    "moduleCode": "POLITICS_HISTORY_OUTLINE",
                    "sourceType": "official",
                    "applicableGroups": all_joint_exam_group_codes(),
                    "practiceConfig": {"timeLimitSec": 60},
                    "paperBindings": [
                        {
                            "paperId": "paper-auto-001",
                            "paperName": "政治模拟卷",
                            "paperType": "simulation",
                            "paperStatus": "REVIEW_PENDING",
                            "durationMinutes": 45,
                            "totalScore": 30,
                            "questionScore": 10,
                            "orderNo": 1,
                            "ownerUserId": "teacher-002",
                            "visibleToStudents": False,
                            "ruleMode": "auto",
                        }
                    ],
                    "reviewRecords": [],
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "question-seed-004",
            "knowledgeId": SEED_KNOWLEDGE_IDS["ENGLISH_POINT"],
            "userId": "teacher-001",
            "type": "single_choice",
            "stem": "He ____ to school every day.",
            "optionsJson": dump_json(
                [
                    {"key": "A", "content": "go"},
                    {"key": "B", "content": "goes"},
                    {"key": "C", "content": "gone"},
                    {"key": "D", "content": "going"},
                ]
            ),
            "answer": "B",
            "status": "PUBLISHED",
            "extJson": dump_json(
                {
                    "source": "seed",
                    "subjectId": "subject-english",
                    "chapter": "词汇知识",
                    "chapterCode": "CH_001",
                    "pointCode": "PT_001_002",
                    "difficulty": "medium",
                    "analysis": "主语为第三人称单数，谓语动词用 goes。",
                    "knowledgeTags": ["词汇知识", "掌握单词拼写和音节结构知识，准确认读单词中的字母或字母组合等"],
                    "chapterNode": "ENGLISH-n00005",
                    "reviewRemark": "demo published",
                    "policyVersionCode": POLICY_VERSION_CODE,
                    "examCategoryCode": "",
                    "jointExamGroupCode": "",
                    "subjectCode": "ENGLISH",
                    "subjectType": "PUBLIC",
                    "moduleCode": "ENGLISH_GRAMMAR_001",
                    "sourceType": "official",
                    "applicableGroups": all_joint_exam_group_codes(),
                    "practiceConfig": {"timeLimitSec": 60},
                    "paperBindings": [
                        {
                            "paperId": "paper-english-001",
                            "paperName": "英语语法专项卷",
                            "paperType": "special",
                            "paperStatus": "PUBLISHED",
                            "durationMinutes": 25,
                            "totalScore": 20,
                            "questionScore": 10,
                            "orderNo": 1,
                            "ownerUserId": "teacher-001",
                            "visibleToStudents": True,
                            "ruleMode": "manual",
                        }
                    ],
                    "reviewRecords": [],
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "question-seed-005",
            "knowledgeId": SEED_KNOWLEDGE_IDS["ENGLISH_POINT"],
            "userId": "teacher-002",
            "type": "subjective",
            "stem": "请根据短文内容概括作者对终身学习的看法。",
            "optionsJson": dump_json([]),
            "answer": "围绕终身学习提升适应能力、持续成长作答即可。",
            "status": "PUBLISHED",
            "extJson": dump_json(
                {
                    "source": "seed",
                    "subjectId": "subject-english",
                    "chapter": "词汇知识",
                    "chapterCode": "CH_001",
                    "pointCode": "PT_001_002",
                    "difficulty": "hard",
                    "analysis": "答案需覆盖持续学习、适应变化、个人成长三个点。",
                    "knowledgeTags": ["词汇知识", "掌握单词拼写和音节结构知识，准确认读单词中的字母或字母组合等"],
                    "chapterNode": "ENGLISH-n00005",
                    "reviewRemark": "demo published",
                    "policyVersionCode": POLICY_VERSION_CODE,
                    "examCategoryCode": "",
                    "jointExamGroupCode": "",
                    "subjectCode": "ENGLISH",
                    "subjectType": "PUBLIC",
                    "moduleCode": "ENGLISH_READING_001",
                    "sourceType": "mock",
                    "applicableGroups": all_joint_exam_group_codes(),
                    "practiceConfig": {"timeLimitSec": 180},
                    "paperBindings": [
                        {
                            "paperId": "paper-english-001",
                            "paperName": "英语语法专项卷",
                            "paperType": "special",
                            "paperStatus": "PUBLISHED",
                            "durationMinutes": 25,
                            "totalScore": 20,
                            "questionScore": 10,
                            "orderNo": 2,
                            "ownerUserId": "teacher-001",
                            "visibleToStudents": True,
                            "ruleMode": "manual",
                        }
                    ],
                    "aiMarking": {"enabled": True, "criteria": {"correctness": 0.6, "steps": 0.3, "format": 0.1}},
                    "reviewRecords": [],
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "question-seed-006",
            "knowledgeId": SEED_KNOWLEDGE_IDS["POLITICS_SECOND_CHAPTER_POINT"],
            "userId": "teacher-001",
            "type": "single_choice",
            "stem": "新时代坚持和发展中国特色社会主义的总任务是什么？",
            "optionsJson": dump_json(
                [
                    {"key": "A", "content": "实现社会主义现代化和中华民族伟大复兴"},
                    {"key": "B", "content": "只发展经济"},
                    {"key": "C", "content": "只强调公平"},
                    {"key": "D", "content": "只发展科技"},
                ]
            ),
            "answer": "A",
            "status": "DRAFT",
            "extJson": dump_json(
                {
                    "source": "seed",
                    "subjectId": "subject-politics",
                    "chapter": "世界的物质性及其发展规律",
                    "chapterCode": "CH_004",
                    "pointCode": "PT_004_001",
                    "difficulty": "medium",
                    "analysis": "总任务是实现社会主义现代化和中华民族伟大复兴。",
                    "knowledgeTags": ["世界的物质性及其发展规律", "理解马克思主义的物质观及其理论意义"],
                    "chapterNode": "POLITICS-n00010",
                    "reviewRemark": "",
                    "policyVersionCode": POLICY_VERSION_CODE,
                    "examCategoryCode": "",
                    "jointExamGroupCode": "",
                    "subjectCode": "POLITICS",
                    "subjectType": "PUBLIC",
                    "moduleCode": "POLITICS_NEW_ERA_001",
                    "sourceType": "mock",
                    "applicableGroups": all_joint_exam_group_codes(),
                    "practiceConfig": {"timeLimitSec": 60},
                    "paperBindings": [],
                    "reviewRecords": [],
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "question-seed-007",
            "knowledgeId": SEED_KNOWLEDGE_IDS["ADVANCED_MATH_POINT"],
            "userId": "teacher-001",
            "type": "single_choice",
            "stem": "当 x 趋近于 0 时，sinx/x 的极限是？",
            "optionsJson": dump_json(
                [
                    {"key": "A", "content": "0"},
                    {"key": "B", "content": "1"},
                    {"key": "C", "content": "不存在"},
                    {"key": "D", "content": "无穷大"},
                ]
            ),
            "answer": "B",
            "status": "PUBLISHED",
            "extJson": dump_json(
                {
                    "source": "seed",
                    "subjectId": "subject-advanced-math-1",
                    "chapter": "函数",
                    "chapterCode": "CH_001",
                    "pointCode": "PT_001_001",
                    "difficulty": "medium",
                    "analysis": "这是常见极限，结果为 1。",
                    "knowledgeTags": ["函数", "理解函数的概念，掌握求函数的定义域、值域、表达式及在某一点的函数值的方法"],
                    "chapterNode": "subject-advanced-math-1-chapter-1",
                    "reviewRemark": "demo published",
                    "policyVersionCode": POLICY_VERSION_CODE,
                    "examCategoryCode": "SCIENCE_ENGINEERING",
                    "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
                    "subjectCode": "ADVANCED_MATH_1",
                    "subjectType": "PROFESSIONAL_2",
                    "moduleCode": "ADVANCED_MATH_1_LIMIT_001",
                    "sourceType": "official",
                    "applicableGroups": [
                        "SCIENCE_ENGINEERING_1",
                        "SCIENCE_ENGINEERING_2",
                        "SCIENCE_ENGINEERING_3",
                        "SCIENCE_ENGINEERING_4",
                        "SCIENCE_ENGINEERING_5",
                    ],
                    "practiceConfig": {"timeLimitSec": 60},
                    "paperBindings": [],
                    "reviewRecords": [],
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
        {
            "id": "question-seed-008",
            "knowledgeId": SEED_KNOWLEDGE_IDS["INFO_TECH_POINT"],
            "userId": "teacher-002",
            "type": "judge",
            "stem": "栈结构遵循先进后出原则。",
            "optionsJson": dump_json([{"key": "A", "content": "正确"}, {"key": "B", "content": "错误"}]),
            "answer": "A",
            "status": "PUBLISHED",
            "extJson": dump_json(
                {
                    "source": "seed",
                    "subjectId": "subject-computer",
                    "chapter": "计算机系统组成",
                    "chapterCode": "CH_018",
                    "pointCode": "PT_018_001",
                    "difficulty": "easy",
                    "analysis": "栈是 LIFO 结构。",
                    "knowledgeTags": ["计算机系统组成", "掌握计算机硬件系统组成，掌握冯·诺依曼计算机体系结构。掌握微型计算机五大部件（运算器、控制器、存储器、输入/输出设备）的功能，理解微型计算机的工作原理和工作过程"],
                    "chapterNode": "INFO_TECH_INTRO-n00009",
                    "reviewRemark": "demo published",
                    "policyVersionCode": POLICY_VERSION_CODE,
                    "examCategoryCode": "SCIENCE_ENGINEERING",
                    "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
                    "subjectCode": "INFO_TECH_INTRO",
                    "subjectType": "PROFESSIONAL_1",
                    "moduleCode": "INFO_TECH_INTRO_001",
                    "sourceType": "official",
                    "applicableGroups": ["SCIENCE_ENGINEERING_3", "SCIENCE_ENGINEERING_4"],
                    "practiceConfig": {"timeLimitSec": 60},
                    "paperBindings": [],
                    "reviewRecords": [],
                }
            ),
            "createTime": SEED_TIME,
            "updateTime": SEED_TIME,
        },
    ]
    connection.executemany(
        """
        INSERT INTO question (
          id, knowledgeId, userId, type, stem, optionsJson,
          answer, status, extJson, createTime, updateTime
        ) VALUES (
          :id, :knowledgeId, :userId, :type, :stem, :optionsJson,
          :answer, :status, :extJson, :createTime, :updateTime
        )
        """,
        questions,
    )


def row_to_question(row: sqlite3.Row) -> Dict[str, str]:
    return {field: row[field] for field in QUESTION_FIELDS}


def row_to_knowledge(row: sqlite3.Row) -> Dict[str, object]:
    return {field: row[field] for field in KNOWLEDGE_FIELDS}


def row_to_task(row: sqlite3.Row) -> Dict[str, object]:
    return {field: row[field] for field in TASK_FIELDS}
