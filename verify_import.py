from app import app, db, Student

# 在应用上下文中运行
with app.app_context():
    # 查询测试学生记录
    students_to_check = ['JW250101', 'JW250104']
    
    print("验证批量导入结果：")
    
    for student_id in students_to_check:
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
    
    print("\n验证完成！")
