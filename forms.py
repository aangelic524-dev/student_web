from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FloatField, DateField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from database import User

class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[
        DataRequired(),
        Length(min=3, max=80, message='用户名长度必须在3-80个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=6, message='密码长度至少6位')
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('注册')
    
    def validate_username(self, username):
        """验证用户名是否唯一"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('该用户名已被使用')

class StudentForm(FlaskForm):
    """学生信息表单"""
    student_id = StringField('学号', validators=[
        DataRequired(),
        Length(min=3, max=50, message='学号长度必须在3-50个字符之间')
    ])
    name = StringField('姓名', validators=[
        DataRequired(),
        Length(min=2, max=100, message='姓名长度必须在2-100个字符之间')
    ])
    gender = SelectField('性别', choices=[
        ('', '请选择'),
        ('男', '男'),
        ('女', '女')
    ], validators=[Optional()])
    birth_date = DateField('出生日期', format='%Y-%m-%d', validators=[Optional()])
    grade_level = StringField('年级', validators=[Optional(), Length(max=50)])
    department = StringField('院系', validators=[Optional(), Length(max=100)])
    class_name = StringField('班级', validators=[Optional(), Length(max=50)])
    class_approved = BooleanField('班级分配批准', default=False)
    major = StringField('专业', validators=[Optional(), Length(max=100)])
    position = StringField('职位', validators=[Optional(), Length(max=50)])
    phone = StringField('电话', validators=[Optional(), Length(max=20)])
    email = StringField('邮箱', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('地址', validators=[Optional(), Length(max=500)])
    enrollment_date = DateField('入学日期', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('保存')

class CourseForm(FlaskForm):
    """课程表单"""
    course_id = StringField('课程ID', validators=[
        DataRequired(),
        Length(min=2, max=50, message='课程ID长度必须在2-50个字符之间')
    ])
    course_code = StringField('课程代码', validators=[
        DataRequired(),
        Length(min=2, max=50, message='课程代码长度必须在2-50个字符之间')
    ])
    course_name = StringField('课程名称', validators=[
        DataRequired(),
        Length(min=2, max=100, message='课程名称长度必须在2-100个字符之间')
    ])
    credit = FloatField('学分', validators=[
        DataRequired(),
        NumberRange(min=0.5, max=10, message='学分必须在0.5-10之间')
    ],default=2.0)
    semester = StringField('学期', validators=[Optional(), Length(max=50)])
    academic_year = StringField('学年', validators=[Optional(), Length(max=20)])
    description = TextAreaField('课程描述', validators=[Optional(), Length(max=500)])
    submit = SubmitField('保存')

class GradeForm(FlaskForm):
    """成绩表单"""
    student_id = SelectField('学生', coerce=int, validators=[DataRequired()])
    course_id = SelectField('课程', coerce=int, validators=[DataRequired()])
    score = FloatField('成绩', validators=[
        DataRequired(),
        NumberRange(min=0, max=100, message='成绩必须在0-100之间')
    ])
    exam_date = DateField('考试日期', format='%Y-%m-%d', validators=[Optional()])
    note = TextAreaField('备注', validators=[Optional(), Length(max=500)])
    submit = SubmitField('保存')

class QueryForm(FlaskForm):
    """查询表单"""
    query_type = SelectField('查询方式', choices=[
        ('student_id', '按学号'),
        ('name', '按姓名'),
        ('class', '按班级'),
        ('course', '按课程')
    ], validators=[DataRequired()])
    query_text = StringField('查询内容', validators=[DataRequired()])
    submit = SubmitField('查询')

class StatisticsForm(FlaskForm):
    """统计表单"""
    course_id = SelectField('课程', coerce=int, validators=[DataRequired()])
    semester = StringField('学期', validators=[Optional()])
    academic_year = StringField('学年', validators=[Optional()])
    submit = SubmitField('统计')

class AddUserForm(FlaskForm):
    """添加用户表单（管理员使用）"""
    username = StringField('用户名', validators=[
        DataRequired(),
        Length(min=3, max=80, message='用户名长度必须在3-80个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=6, message='密码长度至少6位')
    ])
    role_id = SelectField('角色', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('启用账户', default=True)
    is_approved = BooleanField('批准账户', default=True)
    submit = SubmitField('添加用户')
    
    def validate_username(self, username):
        """验证用户名是否唯一"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('该用户名已被使用')
            
    def validate_email(self, email):
        """验证邮箱是否唯一"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('该邮箱已被注册')

class EditUserForm(FlaskForm):
    """编辑用户表单"""
    username = StringField('用户名', validators=[
        DataRequired(),
        Length(min=3, max=80, message='用户名长度必须在3-80个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        Optional(),
        Length(min=6, message='密码长度至少6位')
    ])
    role_id = SelectField('角色', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('启用账户', default=True)
    is_approved = BooleanField('批准账户', default=True)
    submit = SubmitField('保存修改')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        """初始化表单，保存原始用户名和邮箱"""
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        """验证用户名是否唯一"""
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('该用户名已被使用')
            
    def validate_email(self, email):
        """验证邮箱是否唯一"""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('该邮箱已被注册')