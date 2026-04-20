#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db import get_connection, DEFAULT_DB_PATH

def debug_exam_tasks():
    print("=" * 80)
    print("DEBUG: 检查数据库中的考试任务")
    print("=" * 80)
    
    with get_connection(DEFAULT_DB_PATH) as conn:
        print("\n[1] 查看 exam_task 表结构")
        schema = conn.execute('PRAGMA table_info(exam_task)').fetchall()
        print("  表字段:")
        for col in schema:
            print(f"    - {col['name']}: {col['type']}")
        
        print("\n[2] 查找所有考试任务")
        tasks = conn.execute(
            '''
            SELECT *
            FROM exam_task 
            ORDER BY createTime DESC
            '''
        ).fetchall()
        
        print(f"  找到 {len(tasks)} 个考试任务:")
        for idx, task in enumerate(tasks):
            print(f"\n  [{idx+1}] 考试任务:")
            for key in task.keys():
                print(f"    {key}: {task[key]}")

if __name__ == "__main__":
    debug_exam_tasks()
