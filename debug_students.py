#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db import get_connection, DEFAULT_DB_PATH

SYSTEM_RECORD_USER_ID = "__system__"

def debug_students():
    print("=" * 80)
    print("DEBUG: 检查系统状态")
    print("=" * 80)
    
    with get_connection(DEFAULT_DB_PATH) as conn:
        print("\n[1] 查找系统记录")
        sys_record = conn.execute(
            '''
            SELECT id, extJson, questionId
            FROM student_question_record 
            WHERE studentUserId = ?
            LIMIT 1
            ''',
            (SYSTEM_RECORD_USER_ID,)
        ).fetchone()
        
        if sys_record:
            print("  OK 系统记录找到: " + sys_record['id'])
            ext_json = json.loads(sys_record['extJson'])
            managed_users = ext_json.get('managedUsers', [])
            print("  管理用户数: " + str(len(managed_users)))
            
            print("\n[2] 管理用户详情:")
            for user in managed_users:
                print("\n  - " + str(user.get('userId')) + " (" + str(user.get('role')) + "): " + str(user.get('name')))
                if user.get('role') == 'teacher':
                    print("    managedStudentIds: " + str(user.get('managedStudentIds')))
                    print("    managedJointExamGroupCodes: " + str(user.get('managedJointExamGroupCodes')))
                if user.get('role') == 'student':
                    print("    examCategoryCode: " + str(user.get('examCategoryCode')))
                    print("    jointExamGroupCode: " + str(user.get('jointExamGroupCode')))
        else:
            print("  ERROR 未找到系统记录")

if __name__ == "__main__":
    debug_students()
