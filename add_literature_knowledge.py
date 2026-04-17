import sqlite3
import json

# 连接到数据库
conn = sqlite3.connect('data/question_bank.db')
cursor = conn.cursor()

# 定义文学类知识点结构
literature_knowledge = [
    # 文学类
    {
        "id": "LITERATURE-n00001",
        "name": "文学类",
        "parentId": None,
        "sort": 1,
        "status": "ENABLED"
    },
    # 文学1
    {
        "id": "LITERATURE-n00002",
        "name": "文学1",
        "parentId": "LITERATURE-n00001",
        "sort": 1,
        "status": "ENABLED"
    },
    # 文史基础
    {
        "id": "LITERATURE-n00003",
        "name": "文史基础",
        "parentId": "LITERATURE-n00002",
        "sort": 1,
        "status": "ENABLED"
    },
    # 中国古代史
    {
        "id": "LITERATURE-n00004",
        "name": "中国古代史",
        "parentId": "LITERATURE-n00003",
        "sort": 1,
        "status": "ENABLED"
    },
    # 史前文化
    {
        "id": "LITERATURE-n00005",
        "name": "史前文化",
        "parentId": "LITERATURE-n00004",
        "sort": 1,
        "status": "ENABLED"
    },
    # 仰韶文化
    {
        "id": "LITERATURE-n00006",
        "name": "仰韶文化",
        "parentId": "LITERATURE-n00005",
        "sort": 1,
        "status": "ENABLED"
    },
    # 河姆渡文化
    {
        "id": "LITERATURE-n00007",
        "name": "河姆渡文化",
        "parentId": "LITERATURE-n00005",
        "sort": 2,
        "status": "ENABLED"
    },
    # 大汶口文化
    {
        "id": "LITERATURE-n00008",
        "name": "大汶口文化",
        "parentId": "LITERATURE-n00005",
        "sort": 3,
        "status": "ENABLED"
    },
    # 中华文明起源
    {
        "id": "LITERATURE-n00009",
        "name": "中华文明起源",
        "parentId": "LITERATURE-n00004",
        "sort": 2,
        "status": "ENABLED"
    },
    # 古代史其他内容
    {
        "id": "LITERATURE-n00010",
        "name": "古代史其他内容",
        "parentId": "LITERATURE-n00004",
        "sort": 3,
        "status": "ENABLED"
    }
]

# 插入知识点数据
for knowledge in literature_knowledge:
    # 检查知识点是否已存在
    cursor.execute("SELECT id FROM knowledge WHERE id = ?", (knowledge["id"],))
    if cursor.fetchone() is None:
        # 插入新知识点
        cursor.execute(
            "INSERT INTO knowledge (id, parentId, name, sort, status, extJson, createTime, updateTime) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (
                knowledge["id"],
                knowledge["parentId"],
                knowledge["name"],
                knowledge["sort"],
                knowledge["status"],
                json.dumps({})
            )
        )
        print(f"添加知识点: {knowledge['name']} (ID: {knowledge['id']})")
    else:
        print(f"知识点已存在: {knowledge['name']} (ID: {knowledge['id']})")

# 提交事务
conn.commit()

# 关闭数据库连接
conn.close()

print("\n文学类知识点添加完成！")
