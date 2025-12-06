from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    
    # 关系
    students = db.relationship('Student', backref='creator', lazy=True)
    
    def set_password(self, password):
        """设置密码（哈希）"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_id(self):
        """获取用户ID（用于Flask-Login）"""
        return str(self.id)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
#    @property
#    def is_active(self):
#        return self.is_active
#    
#    def __repr__(self):
#        return f'<User {self.username}>'

class Student(db.Model):
    """学生模型"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    gender = db.Column(db.String(10))
    birth_date = db.Column(db.Date)
    grade_level = db.Column(db.String(50))  # 年级
    department = db.Column(db.String(100))  # 院系
    class_name = db.Column(db.String(50))
    major = db.Column(db.String(100))
    position = db.Column(db.String(50))  # 职位
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    enrollment_date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 关系
    grades = db.relationship('Grade', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.name}>'

class Course(db.Model):
    """课程模型"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 用户可自定义的课程ID
    course_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    course_name = db.Column(db.String(100), nullable=False, index=True)
    credit = db.Column(db.Float, default=1.0)
    semester = db.Column(db.String(50))
    academic_year = db.Column(db.String(20))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

     # 扩展字段（可选）
    is_required = db.Column(db.Boolean, default=True)  # 是否必修
    has_exam = db.Column(db.Boolean, default=True)     # 是否有期末考试
    has_coursework = db.Column(db.Boolean, default=True)  # 是否有平时作业
    hours_per_week = db.Column(db.Float, default=2.0)  # 每周学时
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 关系
    grades = db.relationship('Grade', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.course_code}: {self.course_name}>'

class Grade(db.Model):
    """成绩模型"""
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float, nullable=False)
    grade_point = db.Column(db.Float)
    exam_date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 外键
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # 唯一约束
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='_student_course_uc'),)
    
    @property
    def grade_level(self):
        """根据分数返回等级"""
        if self.score >= 90:
            return 'A'
        elif self.score >= 80:
            return 'B'
        elif self.score >= 70:
            return 'C'
        elif self.score >= 60:
            return 'D'
        else:
            return 'F'
    
    def __repr__(self):
        return f'<Grade {self.student_id}-{self.course_id}: {self.score}>'

def init_db():
    """初始化数据库"""
    db.create_all()
    
    # 创建默认管理员用户
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # 创建一些示例课程
        courses = [
            Course(course_id='MATH101', course_code='MATH101', course_name='高等数学', credit=4.0, semester='第一学期'),
            Course(course_id='PHYS101', course_code='PHYS101', course_name='大学物理', credit=3.5, semester='第一学期'),
            Course(course_id='ENG101', course_code='ENG101', course_name='大学英语', credit=3.0, semester='第一学期'),
            Course(course_id='CS101', course_code='CS101', course_name='计算机基础', credit=3.0, semester='第一学期'),
            Course(course_id='CHEM101', course_code='CHEM101', course_name='大学化学', credit=3.0, semester='第二学期'),
        ]
        
        for course in courses:
            db.session.add(course)
        
        db.session.commit()
        print("数据库已初始化，管理员账号: admin, 密码: admin123")