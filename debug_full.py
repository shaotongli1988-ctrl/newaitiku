#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db import get_connection, DEFAULT_DB_PATH
from app.service_modules.exam_task import ExamTaskService
from app.service_modules.system import SystemService
from app.service_modules.question_bank import QuestionBankService

def debug_full():
    print("=" * 80)
    print("DEBUG: 完整系统检查")
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
            print(f"  ✓ 系统记录找到: {sys_record['id']}")
            ext_json = json.loads(sys_record['extJson'])
            managed_users = ext_json.get('managedUsers', [])
            print(f"  管理用户数: {len(managed_users)}")
            
            print("\n[2] 管理用户详情:")
            for user in managed_users:
                print(f"\n  - {user.get('userId')} ({user.get('role')}): {user.get('name')}")
                if user.get('role') == 'teacher':
                    print(f"    managedStudentIds: {user.get('managedStudentIds')}")
                    print(f"    managedJointExamGroupCodes: {user.get('managedJointExamGroupCodes')}")
        
        print("\n[3] 查找所有考试任务")
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
            print(f"    id: {task['id']}")
            print(f"    taskName: {task['taskName']}")
            print(f"    taskType: {task['taskType']}")
            print(f"    subjectCode: {task['subjectCode']}")
            print(f"    status: {task['status']}")
            print(f"    teacherUserId: {task['teacherUserId']}")

if __name__ == "__main__":
    debug_full()
