import sqlite3

# 连接到数据库
conn = sqlite3.connect('data/question_bank.db')
cursor = conn.cursor()

# 查询知识点表的结构
cursor.execute("PRAGMA table_info(knowledge)")
columns = cursor.fetchall()
print("知识点表结构:")
for column in columns:
    print(f"  {column[1]} ({column[2]})")

# 查询知识点表中的所有知识点
cursor.execute("SELECT id, name, parentId FROM knowledge ORDER BY id")
knowledge_points = cursor.fetchall()

print("\n所有知识点:")
for id, name, parentId in knowledge_points:
    print(f"  ID: {id}, 名称: {name}, 父ID: {parentId}")

# 关闭数据库连接
conn.close()
