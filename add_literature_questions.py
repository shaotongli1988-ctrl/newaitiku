import sqlite3
import json
import random

# 连接到数据库
conn = sqlite3.connect('data/question_bank.db')
cursor = conn.cursor()

# 定义文学类题目
literature_questions = [
    # 单选题
    {
        "id": "question-literature-001",
        "type": "single_choice",
        "stem": "下列哪个文化是中国新石器时代的重要文化？",
        "options": ["仰韶文化", "龙山文化", "河姆渡文化", "大汶口文化"],
        "answer": "A",
        "analysis": "仰韶文化是中国新石器时代的重要文化，分布在黄河中游地区，以彩陶为特色。",
        "knowledgeId": "LITERATURE-n00006",
        "difficulty": 3,
        "subjectId": "subject-literature"
    },
    {
        "id": "question-literature-002",
        "type": "single_choice",
        "stem": "河姆渡文化主要分布在哪个地区？",
        "options": ["黄河流域", "长江流域", "珠江流域", "辽河流域"],
        "answer": "B",
        "analysis": "河姆渡文化主要分布在长江流域的浙江省余姚市河姆渡镇。",
        "knowledgeId": "LITERATURE-n00007",
        "difficulty": 3,
        "subjectId": "subject-literature"
    },
    {
        "id": "question-literature-003",
        "type": "single_choice",
        "stem": "大汶口文化的主要特征是什么？",
        "options": ["彩陶", "黑陶", "白陶", "红陶"],
        "answer": "B",
        "analysis": "大汶口文化以黑陶为主要特征，分布在黄河下游地区。",
        "knowledgeId": "LITERATURE-n00008",
        "difficulty": 3,
        "subjectId": "subject-literature"
    },
    # 多选题
    {
        "id": "question-literature-004",
        "type": "multiple_choice",
        "stem": "下列哪些属于中国史前文化？",
        "options": ["仰韶文化", "河姆渡文化", "大汶口文化", "龙山文化"],
        "answer": "ABCD",
        "analysis": "仰韶文化、河姆渡文化、大汶口文化和龙山文化都属于中国史前文化。",
        "knowledgeId": "LITERATURE-n00005",
        "difficulty": 3,
        "subjectId": "subject-literature"
    },
    # 判断题
    {
        "id": "question-literature-005",
        "type": "judge",
        "stem": "仰韶文化以黑陶为特色。",
        "answer": "B",
        "analysis": "仰韶文化以彩陶为特色，黑陶是大汶口文化的特征。",
        "knowledgeId": "LITERATURE-n00006",
        "difficulty": 3,
        "subjectId": "subject-literature"
    },
    # 主观题
    {
        "id": "question-literature-006",
        "type": "subjective",
        "stem": "简述中华文明起源的主要特征。",
        "answer": "中华文明起源的主要特征包括：1. 多元一体的发展格局；2. 农业文明的形成；3. 城市和国家的出现；4. 文字的发明和使用；5. 礼仪制度的建立。",
        "analysis": "中华文明起源是一个复杂的过程，涉及多个方面的发展。",
        "knowledgeId": "LITERATURE-n00009",
        "difficulty": 4,
        "subjectId": "subject-literature"
    }
]

# 插入题目数据
for question in literature_questions:
    # 检查题目是否已存在
    cursor.execute("SELECT id FROM question WHERE id = ?", (question["id"],))
    if cursor.fetchone() is None:
        # 构建选项JSON
        options_json = json.dumps([
            {"label": "A", "content": question["options"][0]},
            {"label": "B", "content": question["options"][1]},
            {"label": "C", "content": question["options"][2]},
            {"label": "D", "content": question["options"][3]}
        ]) if question["type"] in ["single_choice", "multiple_choice"] else json.dumps([])
        
        # 构建扩展JSON
        ext_json = json.dumps({
            "source": "manual",
            "subjectId": question["subjectId"],
            "chapter": "文史基础",
            "chapterCode": "CH_001",
            "point": question["knowledgeId"],
            "difficulty": question["difficulty"]
        })
        
        # 插入新题目
        cursor.execute(
            "INSERT INTO question (id, userId, type, stem, optionsJson, answer, knowledgeId, status, extJson, createTime, updateTime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (
                question["id"],
                "teacher001",  # 添加userId
                question["type"],
                question["stem"],
                options_json,
                question["answer"],
                question["knowledgeId"],
                "PUBLISHED",
                ext_json
            )
        )
        print(f"添加题目: {question['stem']} (ID: {question['id']})")
    else:
        print(f"题目已存在: {question['stem']} (ID: {question['id']})")

# 提交事务
conn.commit()

# 关闭数据库连接
conn.close()

print("\n文学类题目添加完成！")
