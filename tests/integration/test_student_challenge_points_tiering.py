from __future__ import annotations

from datetime import datetime, timezone

import pytest
from app.db import get_connection
from app.shared.codecs import dump_json


pytestmark = [pytest.mark.integration]


def test_student_challenge_points_summary_uses_10000_score_tiers(
    app,
) -> None:
    service = app.state.service
    student_user_id = "student-001"
    awarded_at = datetime.now(timezone.utc).isoformat()

    with get_connection(service.repository.db_path) as connection:
        connection.execute(
            """
            INSERT INTO challenge_point_subject (
              id, studentUserId, subjectCode, totalPoints, lastAwardedAt, extJson, createTime, updateTime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{student_user_id}::POLITICS",
                student_user_id,
                "POLITICS",
                9300,
                awarded_at,
                dump_json(
                    {
                        "studentUserId": student_user_id,
                        "subjectCode": "POLITICS",
                        "totalPoints": 9300,
                        "lastAwardedAt": awarded_at,
                    }
                ),
                awarded_at,
                awarded_at,
            ),
        )
        connection.commit()

    payload = service._build_challenge_point_summary(student_user_id, "POLITICS")
    assert payload["total"] == 9300
    assert payload["scoreCap"] == 10000
    assert payload["cappedTotal"] == 9300
    assert payload["scorePercent"] == 93
    assert payload["levelName"] == "荣耀王者"
    assert payload["nextLevelName"] == "传奇王者"
    assert payload["nextLevelThreshold"] == 9800
    assert payload["pointsToNextLevel"] == 500
    assert payload["awardThreshold"] == 10000
    assert payload["awardUnlocked"] is False


def test_student_challenge_points_summary_caps_progress_at_10000(
    app,
) -> None:
    service = app.state.service
    student_user_id = "student-001"
    awarded_at = datetime.now(timezone.utc).isoformat()

    with get_connection(service.repository.db_path) as connection:
        connection.execute(
            """
            INSERT INTO challenge_point_subject (
              id, studentUserId, subjectCode, totalPoints, lastAwardedAt, extJson, createTime, updateTime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{student_user_id}::ENGLISH",
                student_user_id,
                "ENGLISH",
                12000,
                awarded_at,
                dump_json(
                    {
                        "studentUserId": student_user_id,
                        "subjectCode": "ENGLISH",
                        "totalPoints": 12000,
                        "lastAwardedAt": awarded_at,
                    }
                ),
                awarded_at,
                awarded_at,
            ),
        )
        connection.commit()

    payload = service._build_challenge_point_summary(student_user_id, "ENGLISH")
    assert payload["total"] == 12000
    assert payload["cappedTotal"] == 10000
    assert payload["scoreCap"] == 10000
    assert payload["scorePercent"] == 100
    assert payload["levelName"] == "传奇王者"
    assert payload["nextLevelName"] == ""
    assert payload["pointsToNextLevel"] == 0
    assert payload["isTopLevel"] is True
    assert payload["awardUnlocked"] is True
