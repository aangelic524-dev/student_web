from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import bcrypt

db = SQLAlchemy()

# 新增：角色模型
class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 角色名称
    description = db.Column(db.String(200))  # 角色描述
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关系
    users = db.relationship('User', backref='role', lazy=True)
    permissions = db.relationship('Permission', secondary='role_permissions', backref='roles', lazy=True)

# 新增：权限模型
class Permission(db.Model):
    """权限模型"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)  # 权限名称
    description = db.Column(db.String(200))  # 权限描述
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# 新增：角色-权限关联表
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=1)  # 默认角色ID
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)  # 用户审核状态，默认未审核
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
    
    @property
    def is_admin(self):
        """兼容性属性：检查用户是否为管理员角色"""
        return self.role.name == 'admin' if self.role else False
    
    def has_permission(self, permission_name):
        """检查用户是否具有特定权限"""
        return any(perm.name == permission_name for perm in self.role.permissions) if self.role else False
    
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
    class_approved = db.Column(db.Boolean, default=False)  # 班级分配审核状态
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
    
    # 创建默认权限
    default_permissions = [
        # 用户管理权限
        {'name': 'view_users', 'description': '查看用户列表'},
        {'name': 'edit_users', 'description': '编辑用户信息'},
        {'name': 'delete_users', 'description': '删除用户'},
        {'name': 'manage_roles', 'description': '管理角色'},
        
        # 学生管理权限
        {'name': 'view_students', 'description': '查看学生列表'},
        {'name': 'add_students', 'description': '添加学生'},
        {'name': 'edit_students', 'description': '编辑学生信息'},
        {'name': 'delete_students', 'description': '删除学生'},
        
        # 课程管理权限
        {'name': 'view_courses', 'description': '查看课程列表'},
        {'name': 'add_courses', 'description': '添加课程'},
        {'name': 'edit_courses', 'description': '编辑课程信息'},
        {'name': 'delete_courses', 'description': '删除课程'},
        
        # 成绩管理权限
        {'name': 'view_grades', 'description': '查看成绩'},
        {'name': 'add_grades', 'description': '添加成绩'},
        {'name': 'edit_grades', 'description': '编辑成绩'},
        {'name': 'delete_grades', 'description': '删除成绩'},
        
        # 日志管理权限
        {'name': 'view_logs', 'description': '查看日志'},
        {'name': 'download_logs', 'description': '下载日志'},
        
        # 系统管理权限
        {'name': 'system_settings', 'description': '系统设置'},
    ]
    
    permission_dict = {}
    for perm_data in default_permissions:
        perm = Permission.query.filter_by(name=perm_data['name']).first()
        if not perm:
            perm = Permission(**perm_data)
            db.session.add(perm)
        permission_dict[perm_data['name']] = perm
    
    # 创建默认角色
    default_roles = [
        {
            'name': 'admin',
            'description': '系统管理员，拥有所有权限',
            'permissions': list(permission_dict.values())
        },
        {
            'name': 'teacher',
            'description': '教师角色，可查看学生和课程，编辑学生信息，管理成绩',
            'permissions': [
                permission_dict['view_students'],
                permission_dict['edit_students'],
                permission_dict['view_courses'],
                permission_dict['view_grades'],
                permission_dict['add_grades'],
                permission_dict['edit_grades'],
            ]
        },
        {
            'name': 'user',
            'description': '普通用户角色，可查看和管理自己的学生',
            'permissions': [
                permission_dict['view_students'],
                permission_dict['add_students'],
                permission_dict['edit_students'],
                permission_dict['view_courses'],
                permission_dict['view_grades'],
            ]
        },
    ]
    
    role_dict = {}
    for role_data in default_roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(name=role_data['name'], description=role_data['description'])
            db.session.add(role)
        role.permissions = role_data['permissions']
        role_dict[role_data['name']] = role
    
    # 创建默认管理员用户
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            role=role_dict['admin'],
            is_approved=True  # 管理员账户默认通过审核
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