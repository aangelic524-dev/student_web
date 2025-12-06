from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_file, Blueprint
from flask_login import LoginManager, current_user, login_required
from flask_bootstrap import Bootstrap
import os
from datetime import datetime, timezone
import json
import pandas as pd
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
import markupsafe
matplotlib.use('Agg')  # 使用非GUI后端

# 导入配置和模块
from config import Config
from database import db, User, Student, Course, Grade, init_db
from auth import auth_bp
from forms import *

# 初始化应用
app = Flask(__name__)
app.config.from_object(Config)

# ==== 新增：模板上下文处理器 ====
from datetime import datetime

@app.context_processor
def inject_now():
    """向所有模板注入当前时间 `now` 和配置 `config` 变量。"""
    return {
        'now': datetime.now(timezone.utc),  # 使用时区感知的UTC时间
        'config': app.config  # 同时注入config，确保页脚中的config.APP_NAME能访问
    }
# ==== 新增结束 ====

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)

# 初始化扩展
db.init_app(app)
bootstrap = Bootstrap(app)

# 登录管理
login_manager = LoginManager(app)  # 直接在初始化时传入app
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录以访问此页面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    return db.session.get(User, int(user_id))

# 注册蓝图
app.register_blueprint(auth_bp)

# 创建主应用蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='首页')

@main_bp.route('/en')
def index_en():
    """首页（英文）"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_en'))
    return render_template('index_en.html', title='Welcome')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """仪表板"""
    # 获取统计信息
    total_students = Student.query.filter_by(user_id=current_user.id).count()
    total_courses = Course.query.count()
    
    # 获取最近添加的学生
    recent_students = Student.query.filter_by(user_id=current_user.id).order_by(Student.created_at.desc()).limit(5).all()
    
    # 获取有成绩的课程
    graded_courses = db.session.query(Course.course_name, db.func.count(Grade.id).label('count')).join(Grade, Course.id == Grade.course_id).group_by(Course.id).order_by(db.func.count(Grade.id).desc()).limit(5).all()
    
    # 获取所有成绩数据用于生成图表
    all_grades = Grade.query.join(Student).filter(Student.user_id == current_user.id).all()
    chart_data = None
    
    if all_grades:
        scores = [g.score for g in all_grades]
        print(f"成绩数据: {scores}")  # 调试信息
        chart_data = generate_chart_data(scores)
        print(f"图表数据: {chart_data}")  # 调试信息
    else:
        print("没有找到成绩数据")  # 调试信息
    
    return render_template('dashboard.html',
                         title='仪表板',
                         total_students=total_students,
                         total_courses=total_courses,
                         recent_students=recent_students,
                         graded_courses=graded_courses,
                         chart_data=chart_data)

@main_bp.route('/dashboard_en')
@login_required
def dashboard_en():
    """仪表板（英文）"""
    # 获取统计信息
    total_students = Student.query.filter_by(user_id=current_user.id).count()
    total_courses = Course.query.count()
    
    # 获取最近添加的学生
    recent_students = Student.query.filter_by(user_id=current_user.id).order_by(Student.created_at.desc()).limit(5).all()
    
    # 获取有成绩的课程
    graded_courses = db.session.query(Course.course_name, db.func.count(Grade.id).label('count')).join(Grade, Course.id == Grade.course_id).group_by(Course.id).order_by(db.func.count(Grade.id).desc()).limit(5).all()
    
    # 获取所有成绩数据用于生成图表
    all_grades = Grade.query.join(Student).filter(Student.user_id == current_user.id).all()
    chart_data = None
    
    if all_grades:
        scores = [g.score for g in all_grades]
        chart_data = generate_chart_data(scores)
    
    return render_template('dashboard_en.html',
                         title='Dashboard',
                         total_students=total_students,
                         total_courses=total_courses,
                         recent_students=recent_students,
                         graded_courses=graded_courses,
                         chart_data=chart_data)

@main_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    """添加学生"""
    form = StudentForm()
    
    if form.validate_on_submit():
        # 检查学号是否已存在
        existing = Student.query.filter_by(student_id=form.student_id.data).first()
        if existing:
            flash('该学号已存在', 'danger')
            return redirect(url_for('main.add_student'))
        
        # 创建学生
        student = Student(
            student_id=form.student_id.data,
            name=form.name.data,
            gender=form.gender.data,
            birth_date=form.birth_date.data,
            grade_level=form.grade_level.data,
            department=form.department.data,
            class_name=form.class_name.data,
            major=form.major.data,
            position=form.position.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            enrollment_date=form.enrollment_date.data or datetime.now(timezone.utc),
            user_id=current_user.id
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash(f'学生 {student.name} 添加成功', 'success')
        return redirect(url_for('main.student_detail', student_id=student.id))
    
    return render_template('add_student.html', form=form, title='添加学生')

@main_bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    """修改学生信息"""
    student = Student.query.get_or_404(student_id)
    
    # 检查权限
    if student.user_id != current_user.id and not current_user.is_admin:
        flash('无权操作', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = StudentForm(obj=student)
    
    if form.validate_on_submit():
        # 检查学号是否已被其他学生使用
        existing = Student.query.filter_by(student_id=form.student_id.data).filter(Student.id != student_id).first()
        if existing:
            flash('该学号已被其他学生使用', 'danger')
            return redirect(url_for('main.edit_student', student_id=student_id))
        
        # 更新学生信息
        form.populate_obj(student)
        
        # 处理入学日期
        if not student.enrollment_date:
            student.enrollment_date = datetime.now(timezone.utc)
        
        db.session.commit()
        
        flash(f'学生 {student.name} 信息更新成功', 'success')
        return redirect(url_for('main.student_detail', student_id=student.id))
    
    return render_template('add_student.html', form=form, title='修改学生信息')

@main_bp.route('/students')
@login_required
def student_list():
    """学生列表"""
    page = request.args.get('page', 1, type=int)
    
    # 查询学生
    query = Student.query.filter_by(user_id=current_user.id)
    
    # 搜索功能
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            db.or_(
                Student.student_id.ilike(f'%{search}%'),
                Student.name.ilike(f'%{search}%'),
                Student.class_name.ilike(f'%{search}%')
            )
        )
    
    # 分页
    students = query.order_by(Student.created_at.desc()).paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
    
    return render_template('all_students.html',
                         title='学生列表',
                         students=students,
                         search=search)

@main_bp.route('/students_en')
@login_required
def student_list_en():
    """学生列表（英文）"""
    page = request.args.get('page', 1, type=int)
    
    # 查询学生
    query = Student.query.filter_by(user_id=current_user.id)
    
    # 搜索功能
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            db.or_(
                Student.student_id.ilike(f'%{search}%'),
                Student.name.ilike(f'%{search}%'),
                Student.class_name.ilike(f'%{search}%')
            )
        )
    
    # 分页
    students = query.order_by(Student.created_at.desc()).paginate(page=page, per_page=app.config['ITEMS_PER_PAGE'], error_out=False)
    
    return render_template('all_students_en.html',
                         title='Student List',
                         students=students,
                         search=search)

@main_bp.route('/student/<int:student_id>/delete', methods=['GET'])
@login_required
def delete_student(student_id):
    """删除学生"""
    try:
        student = Student.query.filter_by(id=student_id, user_id=current_user.id).first()
        
        if not student:
            flash('学生不存在或无权限操作', 'danger')
            return redirect(url_for('main.student_list'))
        
        # 删除学生的所有成绩记录
        Grade.query.filter_by(student_id=student.id).delete()
        
        # 删除学生
        db.session.delete(student)
        db.session.commit()
        
        flash(f'学生 {student.name} 及其所有成绩记录已成功删除', 'success')
        return redirect(url_for('main.student_list'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'删除学生失败：{str(e)}', 'danger')
        return redirect(url_for('main.student_list'))

@main_bp.route('/grades/<int:grade_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_grade(grade_id):
    """编辑成绩"""
    # 获取成绩记录
    grade = Grade.query.get_or_404(grade_id)
    student = Student.query.get_or_404(grade.student_id)
    
    # 检查权限
    if student.user_id != current_user.id and not current_user.is_admin:
        flash('无权操作', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # 更新成绩信息
        try:
            score = float(request.form.get('score', 0))
            exam_date = request.form.get('exam_date')
            note = request.form.get('note', '')
            
            # 验证分数范围
            if score < 0 or score > 100:
                flash('分数必须在0-100之间', 'danger')
                return redirect(url_for('main.edit_grade', grade_id=grade_id))
            
            # 计算绩点
            if score >= 90:
                grade_point = 4.0
            elif score >= 80:
                grade_point = 3.0
            elif score >= 70:
                grade_point = 2.0
            elif score >= 60:
                grade_point = 1.0
            else:
                grade_point = 0.0
            
            # 更新记录
            grade.score = score
            grade.grade_point = grade_point
            if exam_date:
                grade.exam_date = datetime.strptime(exam_date, '%Y-%m-%d')
            grade.note = note
            grade.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            flash('成绩更新成功', 'success')
            return redirect(url_for('main.student_detail', student_id=student.id))
            
        except ValueError:
            flash('请输入有效的分数', 'danger')
        except Exception as e:
            db.session.rollback()
            flash('更新失败: ' + str(e), 'danger')
    
    return render_template('edit_grade.html',
                         title='编辑成绩',
                         grade=grade,
                         student=student)

@main_bp.route('/grades/<int:grade_id>/delete', methods=['POST'])
@login_required
def delete_grade(grade_id):
    """删除成绩"""
    grade = Grade.query.get_or_404(grade_id)
    student = Student.query.get_or_404(grade.student_id)
    
    # 检查权限
    if student.user_id != current_user.id and not current_user.is_admin:
        flash('无权操作', 'danger')
        return redirect(url_for('main.dashboard'))
    
    try:
        db.session.delete(grade)
        db.session.commit()
        flash('成绩删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash('删除失败: ' + str(e), 'danger')
    
    return redirect(url_for('main.student_detail', student_id=student.id))

@main_bp.route('/bulk/operations')
@login_required
def bulk_operations():
    """批量操作页面"""
    # 获取班级和专业列表用于筛选
    classes = db.session.query(Student.class_name)\
        .filter(Student.user_id == current_user.id)\
        .filter(Student.class_name.isnot(None))\
        .distinct()\
        .all()
    classes = [c[0] for c in classes if c[0]]
    
    majors = db.session.query(Student.major)\
        .filter(Student.user_id == current_user.id)\
        .filter(Student.major.isnot(None))\
        .distinct()\
        .all()
    majors = [m[0] for m in majors if m[0]]
    
    return render_template('bulk_operations.html',
                         title='批量操作',
                         classes=classes,
                         majors=majors)

@main_bp.route('/bulk/update', methods=['POST'])
@login_required
def bulk_update():
    """批量更新"""
    if 'file' not in request.files:
        flash('请选择文件', 'danger')
        return redirect(url_for('main.bulk_operations'))
    
    file = request.files['file']
    if file.filename == '':
        flash('请选择文件', 'danger')
        return redirect(url_for('main.bulk_operations'))
    
    file_type = request.form.get('file_type', 'excel')
    update_content = request.form.get('update_content', 'students')
    match_by_id = request.form.get('match_by_id') == 'on'
    update_non_empty_only = request.form.get('update_non_empty_only') == 'on'
    auto_create = request.form.get('auto_create') == 'on'
    
    try:
        updated_count = 0
        created_count = 0
        error_count = 0
        
        # 根据文件类型解析数据
        if file.filename.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            import pandas as pd
            df = pd.read_excel(file)
        else:
            flash('不支持的文件类型', 'danger')
            return redirect(url_for('main.bulk_operations'))
        
        if update_content in ['students', 'both']:
            # 更新学生数据
            for _, row in df.iterrows():
                try:
                    # 获取并验证匹配字段
                    if match_by_id:
                        # 按ID匹配
                        student_id = row.get('学号', row.get('student_id', ''))
                        if pd.isna(student_id):
                            student_id = ''
                        student_id = str(student_id).strip()
                        
                        if not student_id:
                            continue
                        
                        # 查找学生
                        student = Student.query.filter_by(
                            student_id=student_id,
                            user_id=current_user.id
                        ).first()
                    else:
                        # 按姓名匹配
                        name = row.get('姓名', row.get('name', ''))
                        if pd.isna(name):
                            name = ''
                        name = str(name).strip()
                        
                        if not name:
                            continue
                        
                        # 查找学生
                        student = Student.query.filter_by(
                            name=name,
                            user_id=current_user.id
                        ).first()
                    
                    if not student:
                        if auto_create:
                            # 自动创建记录
                            if match_by_id:
                                student_id = row.get('学号', row.get('student_id', ''))
                                if pd.isna(student_id):
                                    student_id = ''
                                student_id = str(student_id).strip()
                            else:
                                student_id = row.get('学号', row.get('student_id', ''))
                                if pd.isna(student_id):
                                    student_id = ''
                                student_id = str(student_id).strip()
                            
                            name = row.get('姓名', row.get('name', ''))
                            if pd.isna(name):
                                name = ''
                            
                            student = Student(
                                student_id=student_id,
                                name=name,
                                user_id=current_user.id
                            )
                            db.session.add(student)
                            created_count += 1
                        else:
                            continue
                    
                    # 更新学生信息
                    fields_to_update = {
                        'gender': '性别',
                        'grade_level': '年级',
                        'department': '院系',
                        'class_name': '班级',
                        'major': '专业',
                        'position': '职位',
                        'phone': '电话',
                        'email': '邮箱'
                    }
                    
                    updated = False
                    for attr, column_name in fields_to_update.items():
                        value = row.get(column_name, row.get(attr, ''))
                        if pd.isna(value):
                            value = ''
                        value = str(value).strip()
                        
                        if update_non_empty_only and not value:
                            continue
                        
                        if hasattr(student, attr) and getattr(student, attr) != value:
                            setattr(student, attr, value)
                            updated = True
                    
                    if updated:
                        updated_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"更新学生失败: {e}")
        
        db.session.commit()
        flash(f'成功更新 {updated_count} 条记录，创建 {created_count} 条记录，失败 {error_count} 条', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('批量更新失败: ' + str(e), 'danger')
    
    return redirect(url_for('main.bulk_operations'))

@main_bp.route('/bulk/import', methods=['POST'])
@login_required
def bulk_import():
    """批量导入"""
    if 'file' not in request.files:
        flash('请选择文件', 'danger')
        return redirect(url_for('main.bulk_operations'))
    
    file = request.files['file']
    if file.filename == '':
        flash('请选择文件', 'danger')
        return redirect(url_for('main.bulk_operations'))
    
    file_type = request.form.get('file_type', 'excel')
    data_type = request.form.get('data_type', 'students')
    skip_duplicates = request.form.get('skip_duplicates') == 'on'
    
    try:
        import_count = 0
        error_count = 0
        
        # 根据文件类型解析数据
        if file.filename.endswith('.csv'):
            # CSV文件处理
            import pandas as pd
            df = pd.read_csv(file)
            
            if data_type in ['students', 'both']:
                # 导入学生数据
                for _, row in df.iterrows():
                    try:
                        # 获取并验证学生ID
                        student_id = row.get('学号', row.get('student_id', ''))
                        # 处理可能的nan值
                        if pd.isna(student_id):
                            student_id = ''
                        student_id = str(student_id).strip()
                        
                        # 跳过学生ID为空的记录
                        if not student_id:
                            continue

                        # 检查学号是否已存在
                        existing = Student.query.filter_by(
                            student_id=student_id,
                            user_id=current_user.id
                        ).first()
                        
                        if existing:
                            if skip_duplicates:
                                continue
                            # 如果不跳过重复记录，则更新现有学生信息
                            # 处理其他可能的nan值
                            name = row.get('姓名', row.get('name', ''))
                            if pd.isna(name):
                                name = ''
                            
                            gender = row.get('性别', row.get('gender', ''))
                            if pd.isna(gender):
                                gender = ''
                            
                            grade_level = row.get('年级', row.get('grade_level', ''))
                            if pd.isna(grade_level):
                                grade_level = ''
                            
                            department = row.get('院系', row.get('department', ''))
                            if pd.isna(department):
                                department = ''
                            
                            class_name = row.get('班级', row.get('class_name', ''))
                            if pd.isna(class_name):
                                class_name = ''
                            
                            major = row.get('专业', row.get('major', ''))
                            if pd.isna(major):
                                major = ''
                            
                            position = row.get('职位', row.get('position', ''))
                            if pd.isna(position):
                                position = ''
                            
                            phone = row.get('电话', row.get('phone', ''))
                            if pd.isna(phone):
                                phone = ''
                            
                            email = row.get('邮箱', row.get('email', ''))
                            if pd.isna(email):
                                email = ''
                            
                            # 更新学生信息
                            existing.name = name
                            existing.gender = gender
                            existing.grade_level = grade_level
                            existing.department = department
                            existing.class_name = class_name
                            existing.major = major
                            existing.position = position
                            existing.phone = phone
                            existing.email = email
                            existing.updated_at = datetime.now(timezone.utc)
                            
                            import_count += 1
                            continue
                        

                        
                        # 处理其他可能的nan值
                        name = row.get('姓名', row.get('name', ''))
                        if pd.isna(name):
                            name = ''
                            
                        gender = row.get('性别', row.get('gender', ''))
                        if pd.isna(gender):
                            gender = ''
                            
                        grade_level = row.get('年级', row.get('grade_level', ''))
                        if pd.isna(grade_level):
                            grade_level = ''
                            
                        department = row.get('院系', row.get('department', ''))
                        if pd.isna(department):
                            department = ''
                            
                        class_name = row.get('班级', row.get('class_name', ''))
                        if pd.isna(class_name):
                            class_name = ''
                            
                        major = row.get('专业', row.get('major', ''))
                        if pd.isna(major):
                            major = ''
                            
                        position = row.get('职位', row.get('position', ''))
                        if pd.isna(position):
                            position = ''
                            
                        phone = row.get('电话', row.get('phone', ''))
                        if pd.isna(phone):
                            phone = ''
                            
                        email = row.get('邮箱', row.get('email', ''))
                        if pd.isna(email):
                            email = ''
                        
                        student = Student(
                            student_id=student_id,
                            name=name,
                            gender=gender,
                            grade_level=grade_level,
                            department=department,
                            class_name=class_name,
                            major=major,
                            position=position,
                            phone=phone,
                            email=email,
                            user_id=current_user.id
                        )
                        db.session.add(student)
                        import_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"导入学生失败: {e}")
            
            # 检查是否需要导入成绩数据
            if data_type in ['grades', 'both']:
                # 导入成绩数据
                for _, row in df.iterrows():
                    try:
                        # 查找学生
                        student_id = row.get('学号', row.get('student_id', ''))
                        # 处理可能的nan值
                        if pd.isna(student_id):
                            student_id = ''
                        student_id = str(student_id).strip()
                        
                        # 跳过学生ID为空的记录
                        if not student_id:
                            continue
                        
                        student = Student.query.filter_by(
                            student_id=student_id,
                            user_id=current_user.id
                        ).first()
                        
                        if not student:
                            continue
                        
                        # 查找课程（这里假设CSV中有课程名称或代码）
                        course_name = row.get('课程名称', row.get('course_name', ''))
                        course_code = row.get('课程代码', row.get('course_code', ''))
                        
                        course = None
                        if course_code:
                            course = Course.query.filter_by(course_code=course_code).first()
                        elif course_name:
                            course = Course.query.filter_by(course_name=course_name).first()
                        
                        if not course:
                            continue
                        
                        # 检查成绩是否已存在
                        existing_grade = Grade.query.filter_by(
                            student_id=student.id,
                            course_id=course.id
                        ).first()
                        
                        if existing_grade:
                            if skip_duplicates:
                                continue
                            # 更新现有成绩
                            existing_grade.score = row.get('成绩', row.get('score', 0))
                            existing_grade.semester = row.get('学期', row.get('semester', ''))
                            existing_grade.academic_year = row.get('学年', row.get('academic_year', ''))
                        else:
                            # 创建新成绩
                            grade = Grade(
                                student_id=student.id,
                                course_id=course.id,
                                score=row.get('成绩', row.get('score', 0)),
                                semester=row.get('学期', row.get('semester', '')),
                                academic_year=row.get('学年', row.get('academic_year', ''))
                            )
                            db.session.add(grade)
                        
                        import_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"导入成绩失败: {e}")
            
            db.session.commit()
            flash(f'成功导入 {import_count} 条记录，失败 {error_count} 条', 'success')
            
        elif file.filename.endswith(('.xlsx', '.xls')):
            # Excel文件处理
            import pandas as pd
            df = pd.read_excel(file)
            
            if data_type in ['students', 'both']:
                # 导入学生数据
                for _, row in df.iterrows():
                    try:
                        # 获取并验证学生ID
                        student_id = row.get('学号', row.get('student_id', ''))
                        # 处理可能的nan值
                        if pd.isna(student_id):
                            student_id = ''
                        student_id = str(student_id).strip()
                        
                        # 跳过学生ID为空的记录
                        if not student_id:
                            continue
                        
                        # 检查学号是否已存在
                        existing = Student.query.filter_by(
                            student_id=student_id,
                            user_id=current_user.id
                        ).first()
                        
                        if existing:
                            if skip_duplicates:
                                continue
                            # 如果不跳过重复记录，则更新现有学生信息
                            # 处理其他可能的nan值
                            name = row.get('姓名', row.get('name', ''))
                            if pd.isna(name):
                                name = ''
                            
                            gender = row.get('性别', row.get('gender', ''))
                            if pd.isna(gender):
                                gender = ''
                            
                            grade_level = row.get('年级', row.get('grade_level', ''))
                            if pd.isna(grade_level):
                                grade_level = ''
                            
                            department = row.get('院系', row.get('department', ''))
                            if pd.isna(department):
                                department = ''
                            
                            class_name = row.get('班级', row.get('class_name', ''))
                            if pd.isna(class_name):
                                class_name = ''
                            
                            major = row.get('专业', row.get('major', ''))
                            if pd.isna(major):
                                major = ''
                            
                            position = row.get('职位', row.get('position', ''))
                            if pd.isna(position):
                                position = ''
                            
                            phone = row.get('电话', row.get('phone', ''))
                            if pd.isna(phone):
                                phone = ''
                            
                            email = row.get('邮箱', row.get('email', ''))
                            if pd.isna(email):
                                email = ''
                            
                            # 更新学生信息
                            existing.name = name
                            existing.gender = gender
                            existing.grade_level = grade_level
                            existing.department = department
                            existing.class_name = class_name
                            existing.major = major
                            existing.position = position
                            existing.phone = phone
                            existing.email = email
                            existing.updated_at = datetime.now(timezone.utc)
                            
                            import_count += 1
                            continue
                        
                        # 获取并验证学生ID
                        student_id = row.get('学号', row.get('student_id', ''))
                        # 处理可能的nan值
                        if pd.isna(student_id):
                            student_id = ''
                        student_id = str(student_id).strip()
                        
                        # 跳过学生ID为空的记录
                        if not student_id:
                            continue
                        
                        # 处理其他可能的nan值
                        name = row.get('姓名', row.get('name', ''))
                        if pd.isna(name):
                            name = ''
                            
                        gender = row.get('性别', row.get('gender', ''))
                        if pd.isna(gender):
                            gender = ''
                            
                        grade_level = row.get('年级', row.get('grade_level', ''))
                        if pd.isna(grade_level):
                            grade_level = ''
                            
                        department = row.get('院系', row.get('department', ''))
                        if pd.isna(department):
                            department = ''
                            
                        class_name = row.get('班级', row.get('class_name', ''))
                        if pd.isna(class_name):
                            class_name = ''
                            
                        major = row.get('专业', row.get('major', ''))
                        if pd.isna(major):
                            major = ''
                            
                        position = row.get('职位', row.get('position', ''))
                        if pd.isna(position):
                            position = ''
                            
                        phone = row.get('电话', row.get('phone', ''))
                        if pd.isna(phone):
                            phone = ''
                            
                        email = row.get('邮箱', row.get('email', ''))
                        if pd.isna(email):
                            email = ''
                        
                        student = Student(
                            student_id=student_id,
                            name=name,
                            gender=gender,
                            grade_level=grade_level,
                            department=department,
                            class_name=class_name,
                            major=major,
                            position=position,
                            phone=phone,
                            email=email,
                            user_id=current_user.id
                        )
                        db.session.add(student)
                        import_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"导入学生失败: {e}")
            
            # 检查是否需要导入成绩数据
            if data_type in ['grades', 'both']:
                # 导入成绩数据
                for _, row in df.iterrows():
                    try:
                        # 查找学生
                        student_id = row.get('学号', row.get('student_id', ''))
                        # 处理可能的nan值
                        if pd.isna(student_id):
                            student_id = ''
                        student_id = str(student_id).strip()
                        
                        # 跳过学生ID为空的记录
                        if not student_id:
                            continue
                        
                        student = Student.query.filter_by(
                            student_id=student_id,
                            user_id=current_user.id
                        ).first()
                        
                        if not student:
                            continue
                        
                        # 查找课程（这里假设Excel中有课程名称或代码）
                        course_name = row.get('课程名称', row.get('course_name', ''))
                        course_code = row.get('课程代码', row.get('course_code', ''))
                        
                        course = None
                        if course_code:
                            course = Course.query.filter_by(course_code=course_code).first()
                        elif course_name:
                            course = Course.query.filter_by(course_name=course_name).first()
                        
                        if not course:
                            continue
                        
                        # 检查成绩是否已存在
                        existing_grade = Grade.query.filter_by(
                            student_id=student.id,
                            course_id=course.id
                        ).first()
                        
                        if existing_grade:
                            if skip_duplicates:
                                continue
                            # 更新现有成绩
                            existing_grade.score = row.get('成绩', row.get('score', 0))
                            existing_grade.semester = row.get('学期', row.get('semester', ''))
                            existing_grade.academic_year = row.get('学年', row.get('academic_year', ''))
                        else:
                            # 创建新成绩
                            grade = Grade(
                                student_id=student.id,
                                course_id=course.id,
                                score=row.get('成绩', row.get('score', 0)),
                                semester=row.get('学期', row.get('semester', '')),
                                academic_year=row.get('学年', row.get('academic_year', ''))
                            )
                            db.session.add(grade)
                        
                        import_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"导入成绩失败: {e}")
            
            db.session.commit()
            flash(f'成功导入 {import_count} 条记录，失败 {error_count} 条', 'success')
            
        else:
            flash('不支持的文件格式', 'danger')
        
    except Exception as e:
        db.session.rollback()
        flash('导入失败: ' + str(e), 'danger')
    
    return redirect(url_for('main.bulk_operations'))

@main_bp.route('/bulk/estimate', methods=['POST'])
@login_required
def estimate_export_size():
    """估算导出数据量"""
    export_type = request.form.get('export_type', 'students')
    filter_class = request.form.get('filter_class', '')
    filter_major = request.form.get('filter_major', '')
    data_range = request.form.get('data_range', 'all')
    
    try:
        # 构建查询
        if export_type == 'students':
            query = Student.query.filter_by(user_id=current_user.id)
            
            if filter_class:
                query = query.filter_by(class_name=filter_class)
            if filter_major:
                query = query.filter_by(major=filter_major)
            
            count = query.count()
            description = '学生记录'
            
        elif export_type == 'grades':
            # 查询成绩
            query = Grade.query.join(Student).filter(Student.user_id == current_user.id).join(Course)
            
            if filter_class:
                query = query.filter(Student.class_name == filter_class)
            
            count = query.count()
            description = '成绩记录'
        
        elif export_type == 'both':
            # 计算学生和成绩总数
            students_query = Student.query.filter_by(user_id=current_user.id)
            if filter_class:
                students_query = students_query.filter_by(class_name=filter_class)
            if filter_major:
                students_query = students_query.filter_by(major=filter_major)
            students_count = students_query.count()
            
            grades_query = Grade.query.join(Student).filter(Student.user_id == current_user.id).join(Course)
            if filter_class:
                grades_query = grades_query.filter(Student.class_name == filter_class)
            grades_count = grades_query.count()
            
            count = students_count + grades_count
            description = '学生和成绩记录总数'
        
        else:
            return jsonify({'error': '暂不支持该导出类型'}), 400
        
        # 估算文件大小（基于记录数的大致估算）
        if export_type == 'students':
            # 每个学生记录大约150字节（JSON格式）
            estimated_size_bytes = count * 150
        elif export_type == 'grades':
            # 每个成绩记录大约200字节（JSON格式）
            estimated_size_bytes = count * 200
        else:
            # 综合估算
            estimated_size_bytes = count * 175
        
        # 转换为合适的单位
        if estimated_size_bytes < 1024:
            size_str = f"{estimated_size_bytes} B"
        elif estimated_size_bytes < 1024 * 1024:
            size_str = f"{round(estimated_size_bytes / 1024, 2)} KB"
        else:
            size_str = f"{round(estimated_size_bytes / (1024 * 1024), 2)} MB"
        
        return jsonify({
            'success': True,
            'count': count,
            'description': description,
            'estimated_size': size_str,
            'export_type': export_type
        })
        
    except Exception as e:
        return jsonify({'error': '估算失败: ' + str(e)}), 500


@main_bp.route('/bulk/export', methods=['POST'])
@login_required
def bulk_export():
    """批量导出"""
    export_format = request.form.get('export_format', 'excel')
    export_type = request.form.get('export_type', 'students')
    filter_class = request.form.get('filter_class', '')
    filter_major = request.form.get('filter_major', '')
    
    try:
        # 构建查询
        if export_type == 'students':
            query = Student.query.filter_by(user_id=current_user.id)
            
            if filter_class:
                query = query.filter_by(class_name=filter_class)
            if filter_major:
                query = query.filter_by(major=filter_major)
            
            students = query.all()
            
            # 创建DataFrame
            data = []
            for s in students:
                data.append({
                    '学号': s.student_id,
                    '姓名': s.name,
                    '性别': s.gender or '',
                    '班级': s.class_name or '',
                    '专业': s.major or '',
                    '电话': s.phone or '',
                    '邮箱': s.email or '',
                    '入学日期': s.enrollment_date.strftime('%Y-%m-%d') if s.enrollment_date else ''
                })
            
            df = pd.DataFrame(data)
            
        elif export_type == 'grades':
            # 查询成绩
            query = Grade.query.join(Student)\
                .filter(Student.user_id == current_user.id)\
                .join(Course)
            
            if filter_class:
                query = query.filter(Student.class_name == filter_class)
            
            grades = query.all()
            
            # 创建DataFrame
            data = []
            for g in grades:
                data.append({
                    '学号': g.student.student_id,
                    '姓名': g.student.name,
                    '课程代码': g.course.course_code,
                    '课程名称': g.course.course_name,
                    '成绩': g.score,
                    '等级': g.grade_level,
                    '绩点': g.grade_point,
                    '考试日期': g.exam_date.strftime('%Y-%m-%d') if g.exam_date else '',
                    '备注': g.note or ''
                })
            
            df = pd.DataFrame(data)
        
        else:
            flash('暂不支持该导出类型', 'warning')
            return redirect(url_for('main.bulk_operations'))
        
        # 导出文件
        from io import BytesIO
        output = BytesIO()
        
        if export_format == 'excel':
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='数据导出', index=False)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ext = 'xlsx'
        elif export_format == 'csv':
            output.write(df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'))
            mimetype = 'text/csv'
            ext = 'csv'
        elif export_format == 'json':
            output.write(df.to_json(orient='records', force_ascii=False).encode('utf-8'))
            mimetype = 'application/json'
            ext = 'json'
        else:
            flash('不支持的文件格式', 'danger')
            return redirect(url_for('main.bulk_operations'))
        
        output.seek(0)
        
        return send_file(output,
                        mimetype=mimetype,
                        as_attachment=True,
                        download_name=f'批量导出_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{ext}')
        
    except Exception as e:
        flash('导出失败: ' + str(e), 'danger')
        return redirect(url_for('main.bulk_operations'))

@main_bp.route('/bulk/delete', methods=['POST'])
@login_required
def bulk_delete():
    """批量删除"""
    delete_type = request.form.get('delete_type', 'grades')
    delete_condition = request.form.get('delete_condition', 'selected')
    confirm_phrase = request.form.get('confirm_phrase', '')
    admin_password = request.form.get('admin_password', '')
    
    # 验证确认信息
    if confirm_phrase != '确认删除':
        flash('确认短语错误', 'danger')
        return redirect(url_for('main.bulk_operations'))
    
    # 验证管理员密码（如果是管理员）
    if current_user.is_admin:
        if not current_user.check_password(admin_password):
            flash('管理员密码错误', 'danger')
            return redirect(url_for('main.bulk_operations'))
    
    try:
        deleted_count = 0
        
        if delete_type in ['students', 'both']:
            # 删除学生（会自动删除关联成绩）
            query = Student.query.filter_by(user_id=current_user.id)
            
            if delete_condition == 'selected':
                # 这里应该从前端接收选中的学生ID列表
                student_ids = request.form.getlist('student_ids')
                if student_ids:
                    query = query.filter(Student.id.in_(student_ids))
                else:
                    flash('请选择要删除的学生', 'warning')
                    return redirect(url_for('main.bulk_operations'))
            elif delete_condition == 'filtered':
                # 根据筛选条件删除
                delete_class = request.form.get('delete_class', '')
                delete_major = request.form.get('delete_major', '')
                
                if delete_class:
                    query = query.filter_by(class_name=delete_class)
                if delete_major:
                    query = query.filter_by(major=delete_major)
            # 如果delete_condition是'all'，则不添加额外条件，删除所有记录
            
            deleted_count = query.delete(synchronize_session=False)
            
        if delete_type in ['grades', 'both']:
            # 删除成绩
            query = Grade.query.join(Student)\
                .filter(Student.user_id == current_user.id)
            
            if delete_condition == 'selected':
                # 这里应该从前端接收选中的成绩ID列表
                grade_ids = request.form.getlist('grade_ids')
                if grade_ids:
                    query = query.filter(Grade.id.in_(grade_ids))
                else:
                    flash('请选择要删除的成绩', 'warning')
                    return redirect(url_for('main.bulk_operations'))
            elif delete_condition == 'filtered':
                # 根据筛选条件删除
                delete_class = request.form.get('delete_class', '')
                delete_major = request.form.get('delete_major', '')
                
                if delete_class:
                    query = query.join(Student).filter(Student.class_name == delete_class)
                if delete_major:
                    query = query.join(Student).filter(Student.major == delete_major)
            # 如果delete_condition是'all'，则不添加额外条件，删除所有记录
            
            deleted_count += query.delete(synchronize_session=False)
        
        db.session.commit()
        flash(f'成功删除 {deleted_count} 条记录', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('删除失败: ' + str(e), 'danger')
    
    return redirect(url_for('main.bulk_operations'))

# 批量操作API（用于前端动态获取数据）
@main_bp.route('/api/bulk/students', methods=['GET'])
@login_required
def api_bulk_students():
    """API：获取学生列表（用于批量操作）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    query = Student.query.filter_by(user_id=current_user.id)
    
    if search:
        query = query.filter(
            db.or_(
                Student.student_id.ilike(f'%{search}%'),
                Student.name.ilike(f'%{search}%'),
                Student.class_name.ilike(f'%{search}%')
            )
        )
    
    students = query.paginate(page=page, per_page=per_page, error_out=False)
    
    data = {
        'items': [{
            'id': s.id,
            'student_id': s.student_id,
            'name': s.name,
            'class_name': s.class_name or '',
            'major': s.major or '',
            'grade_count': len(s.grades)
        } for s in students.items],
        'total': students.total,
        'pages': students.pages,
        'page': students.page
    }
    
    return jsonify(data)

# 修改学生详情页面中的编辑和删除按钮URL
# 需要在 student_detail.html 中更新按钮的链接
@main_bp.route('/students/<int:student_id>')
@login_required
def student_detail(student_id):
    """学生详情"""
    student = Student.query.get_or_404(student_id)
    
    # 检查权限
    if student.user_id != current_user.id and not current_user.is_admin:
        flash('无权访问', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # 获取学生成绩
    grades = Grade.query.filter_by(student_id=student.id)\
        .join(Course)\
        .order_by(Course.course_name)\
        .all()
    
    # 计算平均分
    avg_score = None
    if grades:
        avg_score = sum(g.score for g in grades) / len(grades)
    
    return render_template('student_detail.html',
                         title=f'学生详情 - {student.name}',
                         student=student,
                         grades=grades,
                         avg_score=avg_score)

@main_bp.route('/students/<int:student_id>/add_grade', methods=['GET', 'POST'])
@login_required
def add_grade(student_id):
    """添加成绩"""
    student = Student.query.get_or_404(student_id)
    
    # 检查权限
    if student.user_id != current_user.id and not current_user.is_admin:
        flash('无权操作', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = GradeForm()
    
    # 动态填充下拉框
    form.student_id.choices = [(student.id, f"{student.student_id} - {student.name}")]
    form.course_id.choices = [(c.id, f"{c.course_code} - {c.course_name}") for c in Course.query.order_by(Course.course_code).all()]
    
    if form.validate_on_submit():
        # 检查是否已存在该课程成绩
        existing = Grade.query.filter_by(
            student_id=student.id,
            course_id=form.course_id.data
        ).first()
        
        if existing:
            flash('该学生此课程已有成绩，如需修改请编辑', 'warning')
            return redirect(url_for('main.student_detail', student_id=student.id))
        
        # 计算绩点（基于4.0制）
        score = form.score.data
        if score >= 90:
            grade_point = 4.0
        elif score >= 80:
            grade_point = 3.0
        elif score >= 70:
            grade_point = 2.0
        elif score >= 60:
            grade_point = 1.0
        else:
            grade_point = 0.0
        
        # 创建成绩记录
        grade = Grade(
            student_id=student.id,
            course_id=form.course_id.data,
            score=score,
            grade_point=grade_point,
            exam_date=form.exam_date.data,
            note=form.note.data
        )
        
        db.session.add(grade)
        db.session.commit()
        
        flash('成绩添加成功', 'success')
        return redirect(url_for('main.student_detail', student_id=student.id))
    
    return render_template('add_grade.html',
                         form=form,
                         student=student,
                         title=f'添加成绩 - {student.name}')

@main_bp.route('/query', methods=['GET', 'POST'])
@login_required
def query():
    """查询页面"""
    form = QueryForm()
    results = None
    
    if form.validate_on_submit():
        query_type = form.query_type.data
        query_text = form.query_text.data.strip()
        
        if query_type == 'student_id':
            # 按学号查询
            students = Student.query.filter(
                Student.user_id == current_user.id,
                Student.student_id.ilike(f'%{query_text}%')
            ).all()
            results = students
            
        elif query_type == 'name':
            # 按姓名查询
            students = Student.query.filter(
                Student.user_id == current_user.id,
                Student.name.ilike(f'%{query_text}%')
            ).all()
            results = students
            
        elif query_type == 'class':
            # 按班级查询
            students = Student.query.filter(
                Student.user_id == current_user.id,
                Student.class_name.ilike(f'%{query_text}%')
            ).all()
            results = students
            
        elif query_type == 'course':
            # 按课程查询
            course = Course.query.filter(
                db.or_(
                    Course.course_code.ilike(f'%{query_text}%'),
                    Course.course_name.ilike(f'%{query_text}%')
                )
            ).first()
            
            if course:
                # 获取该课程的所有成绩
                grades = Grade.query.filter_by(course_id=course.id)\
                    .join(Student)\
                    .filter(Student.user_id == current_user.id)\
                    .all()
                results = {
                    'course': course,
                    'grades': grades,
                    'type': 'course'
                }
    
    return render_template('query.html',
                         form=form,
                         results=results,
                         title='成绩查询')

@main_bp.route('/statistics', methods=['GET', 'POST'])
@login_required
def statistics():
    """成绩统计"""
    form = StatisticsForm()
    stats = None
    chart_data = None
    
    # 填充课程下拉框
    form.course_id.choices = [(c.id, f"{c.course_code} - {c.course_name}") 
                              for c in Course.query.order_by(Course.course_code).all()]
    
    if form.validate_on_submit():
        course_id = form.course_id.data
        course = Course.query.get(course_id)
        
        # 获取该课程的所有成绩
        grades = Grade.query.filter_by(course_id=course_id)\
            .join(Student)\
            .filter(Student.user_id == current_user.id)\
            .all()
        
        if grades:
            scores = [g.score for g in grades]
            
            # 计算统计信息
            stats = {
                'course': course,
                'count': len(grades),
                'avg_score': np.mean(scores),
                'max_score': max(scores),
                'min_score': min(scores),
                'std_dev': np.std(scores),
                'pass_rate': len([s for s in scores if s >= 60]) / len(scores) * 100
            }
            
            # 生成图表数据
            chart_data = generate_chart_data(scores)
    
    return render_template('statistics.html',
                         form=form,
                         stats=stats,
                         chart_data=chart_data,
                         title='成绩统计')

def generate_chart_data(scores):
    """生成图表数据"""
    # 成绩分布
    bins = [0, 60, 70, 80, 90, 100]
    labels = ['优秀', '良好', '中等', '及格', '不及格']
    
    hist, _ = np.histogram(scores, bins=bins)
    
    # 反转数据和颜色顺序，使其与标签顺序一致
    hist = hist.tolist()[::-1]
    colors = ['#4CAF50', '#2196F3', '#FFC107', '#FF9800', '#FF5252']
    
    return {
        'labels': labels,
        'data': hist,
        'colors': colors
    }

@main_bp.route('/courses')
@login_required
def course_list():
    """课程列表"""
    courses = Course.query.order_by(Course.course_code).all()
    return render_template('courses.html',
                         title='课程列表',
                         courses=courses)

@main_bp.route('/grades/chart/<int:course_id>')
@login_required
def grade_chart(course_id):
    """生成成绩分布图"""
    # 获取课程成绩
    grades = Grade.query.filter_by(course_id=course_id)\
        .join(Student)\
        .filter(Student.user_id == current_user.id)\
        .all()
    
    if not grades:
        return "无数据", 404
    
    scores = [g.score for g in grades]
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 柱状图：成绩分布
    bins = [0, 60, 70, 80, 90, 100]
    labels = ['不及格', '及格', '中等', '良好', '优秀']
    colors = ['#FF5252', '#FF9800', '#4CAF50', '#2196F3', '#9C27B0']
    
    hist, _ = np.histogram(scores, bins=bins)
    
    bars = ax1.bar(labels, hist, color=colors, edgecolor='black')
    ax1.set_title('成绩分布')
    ax1.set_xlabel('成绩等级')
    ax1.set_ylabel('人数')
    
    # 在柱子上显示数值
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')
    
    # 箱线图：成绩统计
    ax2.boxplot(scores, vert=True, patch_artist=True,
               boxprops=dict(facecolor='lightblue'))
    ax2.set_title('成绩箱线图')
    ax2.set_ylabel('分数')
    ax2.grid(True, alpha=0.3)
    
    # 添加统计信息
    stats_text = f"""
    平均分: {np.mean(scores):.2f}
    最高分: {max(scores)}
    最低分: {min(scores)}
    中位数: {np.median(scores):.2f}
    标准差: {np.std(scores):.2f}
    """
    ax2.text(1.1, 0.5, stats_text, transform=ax2.transAxes,
            verticalalignment='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # 保存图表到内存
    img = BytesIO()
    plt.savefig(img, format='png', dpi=100)
    img.seek(0)
    plt.close()
    
    return send_file(img, mimetype='image/png')
# 添加课程
@main_bp.route('/courses/add', methods=['GET', 'POST'])
@login_required
def add_course():
    """添加课程"""
    # 检查权限（只有管理员可以添加课程）
    if not current_user.is_admin:
        flash('只有管理员可以添加课程', 'danger')
        return redirect(url_for('main.course_list'))
    
    form = CourseForm()
    
    if form.validate_on_submit():
        # 检查课程ID是否已存在
        existing_id = Course.query.filter_by(course_id=form.course_id.data).first()
        if existing_id:
            flash('该课程ID已存在', 'danger')
            return redirect(url_for('main.add_course'))
        
        # 检查课程代码是否已存在
        existing_code = Course.query.filter_by(course_code=form.course_code.data).first()
        if existing_code:
            flash('该课程代码已存在', 'danger')
            return redirect(url_for('main.add_course'))
        
        # 创建课程
        course = Course(
            course_id=form.course_id.data,
            course_code=form.course_code.data,
            course_name=form.course_name.data,
            credit=form.credit.data,
            semester=form.semester.data,
            academic_year=form.academic_year.data,
            description=form.description.data
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash(f'课程 {course.course_name} 添加成功', 'success')
        return redirect(url_for('main.course_list'))
    
    return render_template('course_form.html',
                         title='添加课程',
                         form=form,
                         course=None)

# 编辑课程
@main_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    """编辑课程"""
    course = Course.query.get_or_404(course_id)
    
    # 检查权限
    if not current_user.is_admin:
        flash('只有管理员可以编辑课程', 'danger')
        return redirect(url_for('main.course_list'))
    
    form = CourseForm(obj=course)
    
    if form.validate_on_submit():
        # 检查课程ID是否被其他课程使用（如果是修改的话）
        if form.course_id.data != course.course_id:
            existing = Course.query.filter(
                Course.course_id == form.course_id.data,
                Course.id != course.id
            ).first()
            if existing:
                flash('该课程ID已被其他课程使用', 'danger')
                return redirect(url_for('main.edit_course', course_id=course.id))
        
        # 检查课程代码是否被其他课程使用（如果是修改的话）
        if form.course_code.data != course.course_code:
            existing = Course.query.filter(
                Course.course_code == form.course_code.data,
                Course.id != course.id
            ).first()
            if existing:
                flash('该课程代码已被其他课程使用', 'danger')
                return redirect(url_for('main.edit_course', course_id=course.id))
        
        # 更新课程信息
        course.course_id = form.course_id.data
        course.course_code = form.course_code.data
        course.course_name = form.course_name.data
        course.credit = form.credit.data
        course.semester = form.semester.data
        course.academic_year = form.academic_year.data
        course.description = form.description.data
        
        db.session.commit()
        
        flash(f'课程 {course.course_name} 更新成功', 'success')
        return redirect(url_for('main.course_list'))
    
    return render_template('course_form.html',
                         title='编辑课程',
                         form=form,
                         course=course)

# 删除课程
@main_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    """删除课程"""
    course = Course.query.get_or_404(course_id)
    
    # 检查权限
    if not current_user.is_admin:
        flash('只有管理员可以删除课程', 'danger')
        return redirect(url_for('main.course_list'))
    
    # 检查是否有成绩记录
    grade_count = Grade.query.filter_by(course_id=course.id).count()
    
    try:
        # 先删除相关的成绩记录
        if grade_count > 0:
            Grade.query.filter_by(course_id=course.id).delete()
        
        # 删除课程
        db.session.delete(course)
        db.session.commit()
        
        flash(f'课程 {course.course_name} 删除成功，同时删除了 {grade_count} 条成绩记录', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    
    return redirect(url_for('main.course_list'))

# 批量删除课程（可选）
@main_bp.route('/courses/bulk_delete', methods=['POST'])
@login_required
def bulk_delete_courses():
    """批量删除课程"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'})
    
    course_ids = request.form.getlist('course_ids[]')
    
    if not course_ids:
        return jsonify({'success': False, 'message': '请选择课程'})
    
    try:
        deleted_count = 0
        grade_deleted_count = 0
        
        for course_id in course_ids:
            course = Course.query.get(course_id)
            if course:
                # 统计要删除的成绩记录
                grade_count = Grade.query.filter_by(course_id=course.id).count()
                grade_deleted_count += grade_count
                
                # 删除成绩记录
                if grade_count > 0:
                    Grade.query.filter_by(course_id=course.id).delete()
                
                # 删除课程
                db.session.delete(course)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 门课程和 {grade_deleted_count} 条成绩记录'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# 批量导出课程（可选）
@main_bp.route('/courses/export', methods=['GET'])
@login_required
def export_courses():
    """导出课程数据为Excel"""
    courses = Course.query.order_by(Course.course_code).all()
    
    # 创建DataFrame
    data = []
    for c in courses:
        data.append({
            '课程代码': c.course_code,
            '课程名称': c.course_name,
            '学分': c.credit,
            '学期': c.semester or '',
            '学年': c.academic_year or '',
            '课程描述': c.description or '',
            '创建时间': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='课程信息', index=False)
    
    output.seek(0)
    
    return send_file(output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'课程信息_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

@main_bp.route('/export/students')
@login_required
def export_students():
    """导出学生数据为Excel"""
    # 获取当前用户的学生
    students = Student.query.filter_by(user_id=current_user.id).all()
    
    # 创建DataFrame
    data = []
    for s in students:
        data.append({
            '学号': s.student_id,
            '姓名': s.name,
            '性别': s.gender or '',
            '年级': s.grade_level or '',
            '院系': s.department or '',
            '班级': s.class_name or '',
            '专业': s.major or '',
            '职位': s.position or '',
            '电话': s.phone or '',
            '邮箱': s.email or '',
            '入学日期': s.enrollment_date.strftime('%Y-%m-%d') if s.enrollment_date else ''
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='学生信息', index=False)
    
    output.seek(0)
    
    return send_file(output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'学生信息_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

@main_bp.route('/export/grades')
@login_required
def export_grades():
    """导出成绩数据为Excel"""
    # 获取当前用户的学生的成绩
    grades = Grade.query.join(Student)\
        .filter(Student.user_id == current_user.id)\
        .join(Course)\
        .all()
    
    # 创建DataFrame
    data = []
    for g in grades:
        data.append({
            '学号': g.student.student_id,
            '姓名': g.student.name,
            '课程代码': g.course.course_code,
            '课程名称': g.course.course_name,
            '成绩': g.score,
            '等级': g.grade_level,
            '考试日期': g.exam_date.strftime('%Y-%m-%d') if g.exam_date else '',
            '备注': g.note or ''
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='成绩信息', index=False)
    
    output.seek(0)
    
    return send_file(output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'成绩信息_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

@main_bp.route('/admin')
@login_required
def admin():
    """管理页面"""
    if not current_user.is_admin:
        flash('无权访问管理页面', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # 获取系统统计
    total_users = User.query.count()
    total_students = Student.query.count()
    total_grades = Grade.query.count()
    
    # 获取最近活动
    recent_users = User.query.order_by(User.last_login.desc()).limit(10).all()
    
    return render_template('admin.html',
                         title='系统管理',
                         total_users=total_users,
                         total_students=total_students,
                         total_grades=total_grades,
                         recent_users=recent_users)

# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# 注册主蓝图
app.register_blueprint(main_bp)

if __name__ == '__main__':
    with app.app_context():
        # 初始化数据库
        init_db()
    
    # 运行应用
    app.run(debug=True, host='0.0.0.0', port=5000)