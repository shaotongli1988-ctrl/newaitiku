#!/usr/bin/env python3
"""
添加中国古代史知识点分支到文史基础科目
"""
import json
import uuid
import sqlite3
from datetime import datetime

DB_PATH = "data/question_bank.db"

def now_iso():
    return datetime.now().isoformat()

def create_knowledge_record(name, parent_id, subject_code, exam_category_code, joint_exam_group_code, level, sort):
    """创建知识点记录"""
    knowledge_id = f"knowledge-{uuid.uuid4().hex[:8]}"
    ext_json = {
        "level": level,
        "levelCode": f"L{level}",
        "levelPath": "/".join(["L1", "L2", "L3", "L4", "L5"][:level]),
        "policyVersionCode": "HB_ZSB_2026",
        "subjectId": f"subject-{subject_code.lower()}",
        "subjectCode": subject_code,
        "subjectType": "PROFESSIONAL",
        "examCategoryCode": exam_category_code,
        "jointExamGroupCode": joint_exam_group_code,
        "applicableGroups": [joint_exam_group_code],
    }
    
    return {
        "id": knowledge_id,
        "name": name,
        "parentId": parent_id,
        "status": "ENABLED",
        "sort": sort,
        "createTime": now_iso(),
        "updateTime": now_iso(),
        "extJson": json.dumps(ext_json, ensure_ascii=False),
    }

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查找"文史基础"科目的根节点（L1）
    cursor.execute(
        "SELECT id, name FROM knowledge WHERE name = '文史基础' AND parentId IS NULL"
    )
    root = cursor.fetchone()
    if not root:
        print("错误：未找到'文史基础'根节点")
        return
    
    root_id = root["id"]
    print(f"找到文史基础根节点: {root_id}")
    
    # 查找"具体内容与要求"节点（L2）
    cursor.execute(
        "SELECT id, name FROM knowledge WHERE name = '具体内容与要求' AND parentId = ?",
        (root_id,)
    )
    content_node = cursor.fetchone()
    if not content_node:
        print("错误：未找到'具体内容与要求'节点")
        return
    
    content_id = content_node["id"]
    print(f"找到具体内容与要求节点: {content_id}")
    
    # 检查是否已存在"中国古代史"节点
    cursor.execute(
        "SELECT id FROM knowledge WHERE name = '中国古代史' AND parentId = ?",
        (content_id,)
    )
    if cursor.fetchone():
        print("警告：'中国古代史'节点已存在，跳过创建")
        return
    
    # 创建"中国古代史"节点（L3）
    ancient_history = create_knowledge_record(
        name="中国古代史",
        parent_id=content_id,
        subject_code="ARTS_HISTORY_FOUNDATION",
        exam_category_code="EDUCATION",
        joint_exam_group_code="EDUCATION_3",
        level=3,
        sort=40  # 在中国文学、现代汉语、中国近现代史之后
    )
    
    cursor.execute(
        """INSERT INTO knowledge (id, name, parentId, status, sort, createTime, updateTime, extJson)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (ancient_history["id"], ancient_history["name"], ancient_history["parentId"],
         ancient_history["status"], ancient_history["sort"], ancient_history["createTime"],
         ancient_history["updateTime"], ancient_history["extJson"])
    )
    ancient_history_id = ancient_history["id"]
    print(f"创建中国古代史节点: {ancient_history_id}")
    
    # 创建"史前文化"节点（L4）
    prehistoric = create_knowledge_record(
        name="史前文化",
        parent_id=ancient_history_id,
        subject_code="ARTS_HISTORY_FOUNDATION",
        exam_category_code="EDUCATION",
        joint_exam_group_code="EDUCATION_3",
        level=4,
        sort=10
    )
    cursor.execute(
        """INSERT INTO knowledge (id, name, parentId, status, sort, createTime, updateTime, extJson)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (prehistoric["id"], prehistoric["name"], prehistoric["parentId"],
         prehistoric["status"], prehistoric["sort"], prehistoric["createTime"],
         prehistoric["updateTime"], prehistoric["extJson"])
    )
    prehistoric_id = prehistoric["id"]
    print(f"创建史前文化节点: {prehistoric_id}")
    
    # 创建史前文化下的L5节点
    prehistoric_cultures = [
        ("了解仰韶文化的分布区域、典型特征和主要遗址，认识其在黄河中游地区新石器时代文化中的重要地位", 10),
        ("了解河姆渡文化的分布区域、典型特征和主要遗址，认识其在长江下游地区新石器时代文化中的重要地位", 20),
        ("了解大汶口文化的分布区域、典型特征和主要遗址，认识其在黄河下游地区新石器时代文化中的重要地位", 30),
        ("了解北京人、山顶洞人等旧石器时代人类的生活状况和文化特征", 40),
        ("理解新石器时代与旧石器时代的区别，掌握农耕文明的起源和发展", 50),
    ]
    
    for name, sort in prehistoric_cultures:
        node = create_knowledge_record(
            name=name,
            parent_id=prehistoric_id,
            subject_code="ARTS_HISTORY_FOUNDATION",
            exam_category_code="EDUCATION",
            joint_exam_group_code="EDUCATION_3",
            level=5,
            sort=sort
        )
        cursor.execute(
            """INSERT INTO knowledge (id, name, parentId, status, sort, createTime, updateTime, extJson)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (node["id"], node["name"], node["parentId"],
             node["status"], node["sort"], node["createTime"],
             node["updateTime"], node["extJson"])
        )
        print(f"  创建L5节点: {name[:30]}...")
    
    # 创建"中华文明起源"节点（L4）
    civilization_origin = create_knowledge_record(
        name="中华文明起源",
        parent_id=ancient_history_id,
        subject_code="ARTS_HISTORY_FOUNDATION",
        exam_category_code="EDUCATION",
        joint_exam_group_code="EDUCATION_3",
        level=4,
        sort=20
    )
    cursor.execute(
        """INSERT INTO knowledge (id, name, parentId, status, sort, createTime, updateTime, extJson)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (civilization_origin["id"], civilization_origin["name"], civilization_origin["parentId"],
         civilization_origin["status"], civilization_origin["sort"], civilization_origin["createTime"],
         civilization_origin["updateTime"], civilization_origin["extJson"])
    )
    civilization_origin_id = civilization_origin["id"]
    print(f"创建中华文明起源节点: {civilization_origin_id}")
    
    # 创建中华文明起源下的L5节点
    civilization_topics = [
        ("理解中华文明起源的'多元一体'格局，认识不同地区文化独立发展又相互交融的特点", 10),
        ("掌握中华文明起源的基本特征，理解其与世界上其他古代文明的区别", 20),
        ("了解中华文明探源工程的主要成果和意义", 30),
    ]
    
    for name, sort in civilization_topics:
        node = create_knowledge_record(
            name=name,
            parent_id=civilization_origin_id,
            subject_code="ARTS_HISTORY_FOUNDATION",
            exam_category_code="EDUCATION",
            joint_exam_group_code="EDUCATION_3",
            level=5,
            sort=sort
        )
        cursor.execute(
            """INSERT INTO knowledge (id, name, parentId, status, sort, createTime, updateTime, extJson)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (node["id"], node["name"], node["parentId"],
             node["status"], node["sort"], node["createTime"],
             node["updateTime"], node["extJson"])
        )
        print(f"  创建L5节点: {name[:30]}...")
    
    # 创建"古代史其他内容"节点（L4）
    other_ancient = create_knowledge_record(
        name="古代史其他内容",
        parent_id=ancient_history_id,
        subject_code="ARTS_HISTORY_FOUNDATION",
        exam_category_code="EDUCATION",
        joint_exam_group_code="EDUCATION_3",
        level=4,
        sort=30
    )
    cursor.execute(
        """INSERT INTO knowledge (id, name, parentId, status, sort, createTime, updateTime, extJson)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (other_ancient["id"], other_ancient["name"], other_ancient["parentId"],
         other_ancient["status"], other_ancient["sort"], other_ancient["createTime"],
         other_ancient["updateTime"], other_ancient["extJson"])
    )
    other_ancient_id = other_ancient["id"]
    print(f"创建古代史其他内容节点: {other_ancient_id}")
    
    # 创建古代史其他内容下的L5节点
    other_topics = [
        ("了解夏商周时期的基本历史概况和重大历史事件", 10),
        ("了解秦汉时期的基本历史概况和重大历史事件", 20),
        ("了解三国两晋南北朝时期的基本历史概况和重大历史事件", 30),
        ("了解隋唐时期的基本历史概况和重大历史事件", 40),
        ("了解宋元明清时期的基本历史概况和重大历史事件", 50),
        ("掌握考古发掘在研究古代史中的重要作用和方法", 60),
    ]
    
    for name, sort in other_topics:
        node = create_knowledge_record(
            name=name,
            parent_id=other_ancient_id,
            subject_code="ARTS_HISTORY_FOUNDATION",
            exam_category_code="EDUCATION",
            joint_exam_group_code="EDUCATION_3",
            level=5,
            sort=sort
        )
        cursor.execute(
            """INSERT INTO knowledge (id, name, parentId, status, sort, createTime, updateTime, extJson)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (node["id"], node["name"], node["parentId"],
             node["status"], node["sort"], node["createTime"],
             node["updateTime"], node["extJson"])
        )
        print(f"  创建L5节点: {name[:30]}...")
    
    conn.commit()
    conn.close()
    
    print("\n[成功] 中国古代史知识点分支添加成功！")
    print(f"根节点ID: {ancient_history_id}")
    print("包含以下分支：")
    print("  - 史前文化（含仰韶文化、河姆渡文化、大汶口文化等）")
    print("  - 中华文明起源")
    print("  - 古代史其他内容")

if __name__ == "__main__":
    main()
