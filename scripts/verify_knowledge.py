#!/usr/bin/env python3
"""
验证中国古代史知识点是否添加成功
"""
import sqlite3

DB_PATH = "data/question_bank.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查询中国古代史相关知识点
    cursor.execute("""
        SELECT id, name, parentId, status 
        FROM knowledge 
        WHERE name LIKE '%中国古代史%' 
           OR name LIKE '%史前文化%' 
           OR name LIKE '%仰韶文化%'
           OR name LIKE '%河姆渡%'
           OR name LIKE '%大汶口%'
           OR name LIKE '%中华文明起源%'
        ORDER BY name
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("未找到中国古代史相关知识点")
        return
    
    print("找到以下知识点:")
    print("-" * 80)
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"名称: {row[1]}")
        print(f"父节点: {row[2]}")
        print(f"状态: {row[3]}")
        print("-" * 80)
    
    print(f"\n总共找到 {len(rows)} 个知识点")
    
    conn.close()

if __name__ == "__main__":
    main()
