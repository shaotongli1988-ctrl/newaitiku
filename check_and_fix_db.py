#!/usr/bin/env python3
import sys
import json
import uuid
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.db import get_connection, DEFAULT_DB_PATH

SYSTEM_RECORD_USER_ID = "__system__"

def check_and_fix():
    print("=" * 60)
    print("Check database status...")
    print("=" * 60)
    
    with get_connection(DEFAULT_DB_PATH) as conn:
        # Check if there are questions
        print("\n1. Check questions:")
        question = conn.execute(
            '''
            SELECT id 
            FROM question 
            WHERE status = 'PUBLISHED' 
            LIMIT 1
            '''
        ).fetchone()
        
        if not question:
            # Find any question
            question = conn.execute(
                '''
                SELECT id 
                FROM question 
                LIMIT 1
                '''
            ).fetchone()
        
        if question:
            print(f"   OK Found question: {question['id']}")
        else:
            print("   ERROR No questions found!")
            return
        
        # Check system record
        print("\n2. Find system record:")
        sys_record = conn.execute(
            '''
            SELECT id, extJson, questionId
            FROM student_question_record 
            WHERE studentUserId = ?
            LIMIT 1
            ''',
            (SYSTEM_RECORD_USER_ID,)
        ).fetchone()
        
        if not sys_record:
            print("   System record not found, creating...")
            now = "2026-03-17T08:00:00Z"
            # Generate default managed users
            default_managed_users = [
                {
                    "userId": "admin-001",
                    "role": "super_admin",
                    "name": "super_admin",
                    "mobile": "13800000001",
                    "enabled": True,
                    "permissions": [],
                    "examCategoryCode": "",
                    "jointExamGroupCode": "",
                    "vocationalMajor": "",
                    "prepStage": "",
                    "postTags": [],
                    "managedStudentIds": [],
                    "managedJointExamGroupCodes": [],
                    "createTime": now,
                    "updateTime": now,
                },
                {
                    "userId": "teacher-001",
                    "role": "teacher",
                    "name": "Teacher A",
                    "mobile": "13800000002",
                    "enabled": True,
                    "permissions": ["question:manage", "paper:manage", "analytics:view", "message:send"],
                    "examCategoryCode": "",
                    "jointExamGroupCode": "",
                    "vocationalMajor": "",
                    "prepStage": "",
                    "postTags": ["teach"],
                    "managedStudentIds": ["student-001", "student-002"],
                    "managedJointExamGroupCodes": ["LITERATURE_11", "SCIENCE_ENGINEERING_3"],
                    "createTime": now,
                    "updateTime": now,
                },
                {
                    "userId": "student-001",
                    "role": "student",
                    "name": "Science Student",
                    "mobile": "13800000005",
                    "enabled": True,
                    "permissions": [],
                    "examCategoryCode": "SCIENCE_ENGINEERING",
                    "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
                    "vocationalMajor": "计算机类",
                    "prepStage": "强化阶段",
                    "postTags": [],
                    "createTime": now,
                    "updateTime": now,
                },
                {
                    "userId": "student-002",
                    "role": "student",
                    "name": "Literature Student",
                    "mobile": "13800000006",
                    "enabled": True,
                    "permissions": [],
                    "examCategoryCode": "LITERATURE",
                    "jointExamGroupCode": "LITERATURE_11",
                    "vocationalMajor": "语言类",
                    "prepStage": "冲刺阶段",
                    "postTags": [],
                    "createTime": now,
                    "updateTime": now,
                }
            ]
            
            # Create system record
            ext_json = {
                "stateVersion": 0,
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
                "managedUsers": default_managed_users,
                "messages": [],
                "messageSettingsByUser": {},
                "messageSchedules": [],
                "teacherQaThreads": [],
                "paperTemplates": [],
            }
            
            conn.execute(
                '''
                INSERT INTO student_question_record (
                    id, studentUserId, questionId, status, lastSubmittedAt, 
                    lastAnswer, lastIsCorrect, answerCount, correctCount, 
                    wrongCount, totalAnswerDurationSec, latestSourceType, 
                    latestPaperId, wrongBookFlag, personalBankFlag, 
                    extJson, createTime, updateTime
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ''',
                (
                    f"student-bank-{uuid.uuid4().hex[:8]}",
                    SYSTEM_RECORD_USER_ID,
                    question['id'],
                    "ACTIVE",
                    "",
                    "",
                    0,
                    0,
                    0,
                    0,
                    0,
                    "",
                    "",
                    0,
                    0,
                    json.dumps(ext_json, ensure_ascii=False),
                    now,
                    now
                )
            )
            conn.commit()
            print("   OK System record created successfully!")
            
            # Re-read
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
            print(f"   OK System record found: {sys_record['id']}")
            try:
                ext_json = json.loads(sys_record['extJson'])
                managed_users = ext_json.get('managedUsers', [])
                print(f"   - Managed users count: {len(managed_users)}")
                
                print("\n3. Check managed user details:")
                for user in managed_users:
                    print(f"   - {user.get('userId')}: {user.get('role')}, {user.get('name')}")
                    if user.get('role') == 'teacher':
                        print(f"     managedStudentIds: {user.get('managedStudentIds')}")
                        print(f"     managedJointExamGroupCodes: {user.get('managedJointExamGroupCodes')}")
                
                # Check if need fix
                need_fix = False
                if not managed_users:
                    need_fix = True
                    print("\n4. Found issue: No managed users!")
                else:
                    for user in managed_users:
                        if user.get('role') == 'teacher':
                            if not user.get('managedJointExamGroupCodes'):
                                need_fix = True
                                break
                
                if need_fix:
                    print("\n4. Fixing...")
                    
                    # Generate default managed users
                    now = "2026-03-17T08:00:00Z"
                    default_managed_users = [
                        {
                            "userId": "admin-001",
                            "role": "super_admin",
                            "name": "super_admin",
                            "mobile": "13800000001",
                            "enabled": True,
                            "permissions": [],
                            "examCategoryCode": "",
                            "jointExamGroupCode": "",
                            "vocationalMajor": "",
                            "prepStage": "",
                            "postTags": [],
                            "managedStudentIds": [],
                            "managedJointExamGroupCodes": [],
                            "createTime": now,
                            "updateTime": now,
                        },
                        {
                            "userId": "teacher-001",
                            "role": "teacher",
                            "name": "Teacher A",
                            "mobile": "13800000002",
                            "enabled": True,
                            "permissions": ["question:manage", "paper:manage", "analytics:view", "message:send"],
                            "examCategoryCode": "",
                            "jointExamGroupCode": "",
                            "vocationalMajor": "",
                            "prepStage": "",
                            "postTags": ["teach"],
                            "managedStudentIds": ["student-001", "student-002"],
                            "managedJointExamGroupCodes": ["LITERATURE_11", "SCIENCE_ENGINEERING_3"],
                            "createTime": now,
                            "updateTime": now,
                        },
                        {
                            "userId": "student-001",
                            "role": "student",
                            "name": "Science Student",
                            "mobile": "13800000005",
                            "enabled": True,
                            "permissions": [],
                            "examCategoryCode": "SCIENCE_ENGINEERING",
                            "jointExamGroupCode": "SCIENCE_ENGINEERING_3",
                            "vocationalMajor": "计算机类",
                            "prepStage": "强化阶段",
                            "postTags": [],
                            "createTime": now,
                            "updateTime": now,
                        },
                        {
                            "userId": "student-002",
                            "role": "student",
                            "name": "Literature Student",
                            "mobile": "13800000006",
                            "enabled": True,
                            "permissions": [],
                            "examCategoryCode": "LITERATURE",
                            "jointExamGroupCode": "LITERATURE_11",
                            "vocationalMajor": "语言类",
                            "prepStage": "冲刺阶段",
                            "postTags": [],
                            "createTime": now,
                            "updateTime": now,
                        }
                    ]
                    
                    # Update ext_json
                    ext_json['managedUsers'] = default_managed_users
                    
                    # Save fixed data
                    conn.execute(
                        '''
                        UPDATE student_question_record 
                        SET extJson = ? 
                        WHERE studentUserId = ?
                        ''',
                        (json.dumps(ext_json, ensure_ascii=False), SYSTEM_RECORD_USER_ID)
                    )
                    conn.commit()
                    print("   OK Fix complete!")
                else:
                    print("\n4. Data looks okay, no fix needed")
            
            except Exception as e:
                print(f"   ERROR Parsing system record: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    check_and_fix()
