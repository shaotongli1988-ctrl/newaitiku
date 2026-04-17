import sqlite3
import json

# 连接到数据库
conn = sqlite3.connect(r'd:\aitiku\data\question_bank.db')
cursor = conn.cursor()

# 查询所有学生的账号信息
query = """
SELECT 
    u.id, 
    u.phone, 
    u.status, 
    u.extJson, 
    sps.examCategoryCode, 
    sps.jointExamGroupCode, 
    sps.points, 
    sps.title
FROM 
    user u 
JOIN 
    student_profile_state sps ON u.id = sps.studentUserId
"""

cursor.execute(query)
students = cursor.fetchall()

# 打印结果
print("当前数据库中的学生账号信息：")
print("-" * 100)
print(f"{'用户ID':<30} {'手机号':<15} {'状态':<10} {'学科门类':<20} {'联考专业组':<20} {'积分':<10} {'称号':<10}")
print("-" * 100)

for student in students:
    user_id, phone, status, ext_json, exam_category, joint_group, points, title = student
    # 解析extJson获取更多信息
    try:
        ext_data = json.loads(ext_json)
    except:
        ext_data = {}
    
    print(f"{user_id:<30} {phone:<15} {status:<10} {exam_category:<20} {joint_group:<20} {points:<10} {title:<10}")

print("-" * 100)
print(f"总计：{len(students)} 个学生账号")

# 关闭连接
conn.close()