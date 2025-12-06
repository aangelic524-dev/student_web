from app import app, db, Student
from datetime import datetime

# 在应用上下文中运行
with app.app_context():
    # 创建一个测试学生记录（与错误信息中相同的student_id）
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

    # 测试是否可以添加学生
    try:
        db.session.add(test_student)
        db.session.commit()
        print("学生记录添加成功！")
    except Exception as e:
        print(f"添加学生时出错: {e}")
        db.session.rollback()

    # 测试是否可以更新现有学生
    try:
        student = Student.query.filter_by(student_id='JW250101').first()
        if student:
            student.name = '苏琪彤（更新后）'
            db.session.commit()
            print("学生记录更新成功！")
        else:
            print("学生记录不存在")
    except Exception as e:
        print(f"更新学生时出错: {e}")
        db.session.rollback()

    # 显示学生记录
    try:
        student = Student.query.filter_by(student_id='JW250101').first()
        if student:
            print(f"\n学生记录信息:")
            print(f"学号: {student.student_id}")
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
            print("学生记录不存在")
    except Exception as e:
        print(f"查询学生时出错: {e}")
