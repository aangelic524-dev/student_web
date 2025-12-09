import sqlite3
import os

# 确保数据库文件存在
db_path = 'instance/database.db'
if not os.path.exists(db_path):
    print(f'Database file not found at {db_path}')
    exit(1)

# 连接到SQLite数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('开始更新数据库结构...')

try:
    # 1. 先查看当前表的索引信息，确认唯一约束的名称
    print('查看当前索引信息...')
    cursor.execute("PRAGMA index_list(students)")
    indexes = cursor.fetchall()
    print(f'当前索引: {indexes}')
    
    # 2. 查找student_id的唯一索引
    student_id_index = None
    for index in indexes:
        if index[2] == 1:  # unique == 1
            # 查看索引的列
            cursor.execute(f"PRAGMA index_info({index[1]})")
            index_cols = cursor.fetchall()
            if index_cols[0][2] == 'student_id':  # 确认索引是student_id上的
                student_id_index = index[1]
                print(f'找到student_id的唯一索引: {student_id_index}')
                break
    
    # 3. 如果找到唯一索引，删除它
    if student_id_index:
        print(f'删除student_id的唯一索引: {student_id_index}')
        cursor.execute(f"DROP INDEX {student_id_index}")
        print(f'成功删除索引: {student_id_index}')
    
    # 4. 添加student_id和user_id的组合唯一约束
    print('添加student_id和user_id的组合唯一约束...')
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS _student_user_uc 
    ON students(student_id, user_id)
    """)
    print('成功添加组合唯一约束')
    
    # 5. 验证约束是否正确添加
    print('验证新索引...')
    cursor.execute("PRAGMA index_list(students)")
    indexes = cursor.fetchall()
    print(f'更新后的索引: {indexes}')
    
    # 提交更改
    conn.commit()
    print('\n数据库更新成功！')
    print('student_id的唯一约束已从全局唯一改为按用户唯一')
    print('现在不同用户可以导入相同的学号了')
    
except Exception as e:
    print(f'\n错误更新数据库: {e}')
    conn.rollback()
finally:
    # 关闭连接
    cursor.close()
    conn.close()
