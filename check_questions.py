import sqlite3

# 连接到数据库
conn = sqlite3.connect('data/question_bank.db')
cursor = conn.cursor()

# 查询已发布的题目数量
cursor.execute("SELECT COUNT(*) FROM question WHERE status = 'PUBLISHED'")
published_count = cursor.fetchone()[0]
print(f"已发布题目数量: {published_count}")

# 查询所有题目的状态分布
cursor.execute("SELECT status, COUNT(*) FROM question GROUP BY status")
status_counts = cursor.fetchall()
print("题目状态分布:")
for status, count in status_counts:
    print(f"  {status}: {count}")

# 查询已发布题目的详细信息（前5条）
cursor.execute("SELECT id, type, knowledgeId, extJson FROM question WHERE status = 'PUBLISHED' LIMIT 5")
published_questions = cursor.fetchall()
print("\n已发布题目详情:")
for i, (id, type, knowledgeId, extJson) in enumerate(published_questions, 1):
    print(f"\n题目 {i}:")
    print(f"  ID: {id}")
    print(f"  类型: {type}")
    print(f"  知识点ID: {knowledgeId}")
    print(f"  扩展信息: {extJson[:100]}..." if len(extJson) > 100 else f"  扩展信息: {extJson}")

# 关闭数据库连接
conn.close()
