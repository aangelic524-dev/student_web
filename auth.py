from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse  # 修改这里：使用 Python 标准库的 urlparse
from database import db, User
from forms import LoginForm, RegistrationForm
from datetime import datetime, timezone  # 需要添加 datetime 和 timezone 导入

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('账户已被禁用，请联系管理员', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_approved:
            # 特殊处理：管理员角色的用户即使未审核也能登录
            if user.role and user.role.name == 'admin':
                flash('管理员账户自动通过审核', 'info')
            else:
                flash('账户尚未通过审核，请耐心等待或联系管理员', 'warning')
                return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        flash(f'欢迎回来，{user.username}!', 'success')
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':  # 修改这里：使用 urlparse
            next_page = url_for('main.dashboard')
        
        return redirect(next_page)
    
    return render_template('login.html', form=form, title='登录')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # 检查用户名是否已存在
        if User.query.filter_by(username=form.username.data).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('auth.register'))
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=form.email.data).first():
            flash('邮箱已被注册', 'danger')
            return redirect(url_for('auth.register'))
        
        # 创建新用户，默认未审核
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_approved=False  # 默认未审核
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！您的账户需要管理员审核后才能登录，请耐心等待。', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form, title='注册')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('main.index'))