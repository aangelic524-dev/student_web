import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

try:
    # 添加grade_level列
    cursor.execute('ALTER TABLE students ADD COLUMN grade_level VARCHAR(10)')
    print('Added grade_level column')
    
    # 添加department列
    cursor.execute('ALTER TABLE students ADD COLUMN department VARCHAR(50)')
    print('Added department column')
    
    # 添加position列
    cursor.execute('ALTER TABLE students ADD COLUMN position VARCHAR(50)')
    print('Added position column')
    
    # 提交更改
    conn.commit()
    print('Database updated successfully!')
except Exception as e:
    print(f'Error updating database: {e}')
    # 如果列已经存在，忽略错误
    conn.rollback()
finally:
    # 关闭连接
    cursor.close()
    conn.close()