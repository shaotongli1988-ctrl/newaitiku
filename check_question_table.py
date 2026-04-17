import sqlite3

# 连接到数据库
conn = sqlite3.connect('data/question_bank.db')
cursor = conn.cursor()

# 查询题目表的结构
cursor.execute("PRAGMA table_info(question)")
columns = cursor.fetchall()
print("题目表结构:")
for column in columns:
    print(f"  {column[1]} ({column[2]})")

# 关闭数据库连接
conn.close()
