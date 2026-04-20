#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db import get_connection, DEFAULT_DB_PATH

def debug_simple():
    print("=" * 80)
    print("DEBUG: 简单系统检查")
    print("=" * 80)
    
    with get_connection(DEFAULT_DB_PATH) as conn:
        print("\n[1] 查找系统记录和managedUsers")
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
            print("  ✓ 系统记录找到")
            ext_json = json.loads(sys_record['extJson'])
            managed_users = ext_json.get('managedUsers', [])
            print(f"  管理用户数: {len(managed_users)}")
            
            print("\n[2] 查找所有考试任务")
            tasks = conn.execute(
                '''
                SELECT *
                FROM exam_task 
                ORDER BY createTime DESC
                '''
            ).fetchall()
            
            print(f"  找到 {len(tasks)} 个考试任务")
            for idx, task in enumerate(tasks):
                print(f"\n  [{idx+1}] 考试任务:")
                for key in task.keys():
                    print(f"    {key}: {task[key]}")

if __name__ == "__main__":
    debug_simple()
