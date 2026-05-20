from flask import render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    flash('Пожалуйста, авторизуйтесь для доступа к этой странице', 'warning')
    return redirect(url_for('login'))

def init_auth(app):
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Пожалуйста, авторизуйтесь для доступа к этой странице'
    login_manager.login_message_category = 'warning'

def role_required(role_name):
    """Декоратор для проверки роли"""
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Пожалуйста, авторизуйтесь', 'warning')
                return redirect(url_for('login'))
            if not current_user.has_role(role_name):
                flash(f'У вас нет прав для доступа к этой странице. Ваша роль: {current_user.role}', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def setup_routes(app):
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Пожалуйста, заполните все поля', 'danger')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password) and user.is_active:
                login_user(user)
                user.last_login = datetime.now()
                db.session.commit()
                
                flash(f'Добро пожаловать, {user.full_name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Неверное имя пользователя или пароль', 'danger')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы успешно вышли из системы', 'info')
        return redirect(url_for('login'))
    
    @app.route('/users')
    @login_required
    @role_required('admin')
    def users_list():
        users = User.query.all()
        return render_template('users.html', users=users)
    
    @app.route('/users/create', methods=['GET', 'POST'])
    @login_required
    @role_required('admin')
    def create_user():
        if request.method == 'POST':
            username = request.form['username']
            full_name = request.form['full_name']
            password = request.form['password']
            role = request.form['role']
            
            if User.query.filter_by(username=username).first():
                flash('Пользователь с таким логином уже существует', 'danger')
                return redirect(url_for('create_user'))
            
            user = User()
            user.username = username
            user.full_name = full_name
            user.role = role
            user.set_password(password)
            user.is_active = True
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'Пользователь {full_name} успешно создан', 'success')
            return redirect(url_for('users_list'))
        
        return render_template('user_form.html', title='Создание пользователя', user=None)
    
    @app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
    @login_required
    @role_required('admin')
    def edit_user(user_id):
        user = User.query.get_or_404(user_id)
        
        if request.method == 'POST':
            user.full_name = request.form['full_name']
            user.role = request.form['role']
            user.is_active = 'is_active' in request.form
            
            if request.form.get('password'):
                user.set_password(request.form['password'])
            
            db.session.commit()
            flash(f'Пользователь {user.full_name} обновлён', 'success')
            return redirect(url_for('users_list'))
        
        return render_template('user_form.html', title='Редактирование пользователя', user=user)
    
    @app.route('/users/delete/<int:user_id>')
    @login_required
    @role_required('admin')
    def delete_user(user_id):
        if user_id == current_user.id:
            flash('Нельзя удалить самого себя', 'danger')
            return redirect(url_for('users_list'))
        
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash(f'Пользователь {user.full_name} удалён', 'success')
        return redirect(url_for('users_list'))