from app import app, db, Student
from datetime import datetime
import pandas as pd
import tempfile
import os

# 在应用上下文中运行
with app.app_context():
    # 确保测试学生记录存在
    test_student = Student.query.filter_by(student_id='JW250101').first()
    if not test_student:
        test_student = Student(
            student_id='JW250101',
            name='苏琪彤',
            gender='女',
            grade_level=25,
            department='计算机与网络学院',
            class_name='计算机网络技术1班',
            major='计算机网络技术',
            enrollment_date=datetime.strptime('2025-12-06', '%Y-%m-%d'),
            user_id=1
        )
        db.session.add(test_student)
        db.session.commit()
        print("测试学生记录已创建")
    else:
        print("测试学生记录已存在")
    
    # 准备测试数据
    test_data = {
        '学号': ['JW250101', 'JW250103'],
        '姓名': ['苏琪彤（更新）', '李华'],
        '性别': ['女', '男'],
        '年级': [25, 26],
        '学院': ['计算机与网络学院', '电子工程学院'],
        '班级': ['计算机网络技术1班', '电子信息工程1班'],
        '专业': ['计算机网络技术', '电子信息工程'],
        '入学日期': ['2025-12-06', '2025-12-06']
    }
    
    # 创建DataFrame
    df = pd.DataFrame(test_data)
    
    # 创建临时CSV文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        df.to_csv(f, index=False)
        temp_file_path = f.name
    
    try:
        # 模拟修复后的批量导入学生数据逻辑（skip_duplicates=False）
        skip_duplicates = False
        
        # 读取CSV文件
        df = pd.read_csv(temp_file_path)
        
        # 统计变量
        added_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        # 处理每一行数据
        for index, row in df.iterrows():
            try:
                # 获取并验证学生ID
                student_id = row.get('学号', row.get('student_id', ''))
                # 处理可能的nan值
                if pd.isna(student_id):
                    student_id = ''
                student_id = str(student_id).strip()
                
                # 跳过学生ID为空的记录
                if not student_id:
                    skipped_count += 1
                    continue
                
                # 检查学号是否已存在
                existing_student = Student.query.filter_by(student_id=student_id).first()
                
                if existing_student:
                    if skip_duplicates:
                        # 跳过重复记录
                        skipped_count += 1
                    else:
                        # 更新现有学生信息
                        existing_student.name = row['姓名'] if pd.notna(row['姓名']) else existing_student.name
                        existing_student.gender = row['性别'] if pd.notna(row['性别']) else existing_student.gender
                        existing_student.grade_level = int(row['年级']) if pd.notna(row['年级']) else existing_student.grade_level
                        existing_student.department = row['学院'] if pd.notna(row['学院']) else existing_student.department
                        existing_student.class_name = row['班级'] if pd.notna(row['班级']) else existing_student.class_name
                        existing_student.major = row['专业'] if pd.notna(row['专业']) else existing_student.major
                        
                        if pd.notna(row['入学日期']):
                            existing_student.enrollment_date = datetime.strptime(row['入学日期'], '%Y-%m-%d')
                        
                        updated_count += 1
                else:
                    # 创建新学生记录
                    new_student = Student(
                        student_id=student_id,
                        name=row['姓名'] if pd.notna(row['姓名']) else '',
                        gender=row['性别'] if pd.notna(row['性别']) else '',
                        grade_level=int(row['年级']) if pd.notna(row['年级']) else 0,
                        department=row['学院'] if pd.notna(row['学院']) else '',
                        class_name=row['班级'] if pd.notna(row['班级']) else '',
                        major=row['专业'] if pd.notna(row['专业']) else '',
                        enrollment_date=datetime.strptime(row['入学日期'], '%Y-%m-%d') if pd.notna(row['入学日期']) else None,
                        user_id=1
                    )
                    db.session.add(new_student)
                    added_count += 1
            except Exception as e:
                error_count += 1
                print(f"处理第{index+1}行数据时出错: {e}")
                db.session.rollback()
        
        # 提交更改
        db.session.commit()
        
        print(f"\n批量导入测试完成！")
        print(f"- 新增学生数: {added_count}")
        print(f"- 更新学生数: {updated_count}")
        print(f"- 跳过学生数: {skipped_count}")
        print(f"- 错误学生数: {error_count}")
        
        # 显示学生记录
        print("\n学生记录信息:")
        for student_id in ['JW250101', 'JW250103']:
            student = Student.query.filter_by(student_id=student_id).first()
            if student:
                print(f"\n学号: {student.student_id}")
                print(f"姓名: {student.name}")
                print(f"性别: {student.gender}")
                print(f"年级: {student.grade_level}")
                print(f"学院: {student.department}")
                print(f"班级: {student.class_name}")
                print(f"专业: {student.major}")
                print(f"入学日期: {student.enrollment_date}")
                print(f"创建时间: {student.created_at}")
                print(f"更新时间: {student.updated_at}")
            else:
                print(f"\n学号 {student_id} 的学生记录不存在")
                
    except Exception as e:
        print(f"测试过程中出错: {e}")
        db.session.rollback()
    finally:
        # 删除临时文件
        os.unlink(temp_file_path)
