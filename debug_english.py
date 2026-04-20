#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db import get_connection, DEFAULT_DB_PATH

def debug_english():
    print("=" * 80)
    print("DEBUG: Simple System Check")
    print("=" * 80)
    
    with get_connection(DEFAULT_DB_PATH) as conn:
        print("\n[1] Find system record and managedUsers")
        sys_record = conn.execute(
            '''
            SELECT id, extJson, questionId
            FROM student_question_record 
            WHERE studentUserId = ?
            LIMIT 1
            ''',
            ("__system__",)
        ).fetchone()
        
        if sys_record:
            print("  OK System record found")
            ext_json = json.loads(sys_record['extJson'])
            managed_users = ext_json.get('managedUsers', [])
            print(f"  Number of managed users: {len(managed_users)}")
            
            print("\n[2] Find all exam tasks")
            tasks = conn.execute(
                '''
                SELECT *
                FROM exam_task 
                ORDER BY createTime DESC
                '''
            ).fetchall()
            
            print(f"  Number of exam tasks: {len(tasks)}")
            for idx, task in enumerate(tasks):
                print(f"\n  [{idx+1}] Exam Task:")
                for key in task.keys():
                    print(f"    {key}: {task[key]}")

if __name__ == "__main__":
    debug_english()
