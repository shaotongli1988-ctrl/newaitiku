#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db import get_connection, DEFAULT_DB_PATH

def test_list():
    print("=" * 80)
    print("Testing list exam tasks")
    print("=" * 80)
    
    with get_connection(DEFAULT_DB_PATH) as conn:
        # Test without any filter
        print("\n1. All tasks:")
        all_rows = conn.execute(
            """
            SELECT id, taskName, taskType, status, teacherUserId
            FROM exam_task
            """)
        
        print(f"  Found: {all_rows.rowcount}")
        for row in all_rows:
            print(f"  - {row['id']}: {row['taskName']} by {row['teacherUserId']}, {row['taskType']}, {row['status']}")
        
        # Test with teacherUserId = teacher-001
        print("\n2. Tasks by teacher-001:")
        filtered_rows = conn.execute(
            """
            SELECT id, taskName, taskType, status
            FROM exam_task
            WHERE teacherUserId = :teacherUserId
            """, {"teacherUserId": "teacher-001"}
        )
        print(f"  Found: {filtered_rows.rowcount}")
        for row in filtered_rows:
            print(f"  - {row['id']}: {row['taskName']}, {row['taskType']}, {row['status']}")
        
        # Test with teacherUserId and status and taskType
        print("\n3. Tasks by teacher-001, status=PUBLISHED, taskType=CHAPTER:")
        full_filter = conn.execute(
            """
            SELECT *
            FROM exam_task
            WHERE teacherUserId = :teacherUserId AND status = :status AND taskType = :taskType
            """, {"teacherUserId": "teacher-001", "status": "PUBLISHED", "taskType": "CHAPTER"}
        )
        print(f"  Found: {full_filter.rowcount}")
        for row in full_filter:
            print(f"  - {row['id']}: {row['taskName']}")

if __name__ == "__main__":
    test_list()
