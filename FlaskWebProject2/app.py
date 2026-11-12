"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session,flash
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newflask.db'
app.secret_key = 'super_secret_key'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
db = SQLAlchemy(app)

# --- НАСТРОЙКА ВХОДА ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице нужно войти.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Методы для безопасного хранения пароля
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Post(db.Model):
    id = db.Column(db.Integer,primary_key = True) #будет создаваться для каждого поста спец.id
    title = db.Column(db.String(300),nullable = False)
    text = db.Column(db.Text,nullable = False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # <--- НОВАЯ СТРОКА
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

class RegisterForm(FlaskForm):
    username = StringField("Имя", validators=[DataRequired(), Length(3, 50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(6, 100)])
    confirm = PasswordField("Повтор пароля", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Зарегистрироваться")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app
@app.route("/", methods=["GET","POST"])  
def l():
    return render_template("base.html")
@app.route("/greet", methods=["GET","POST"])  
def greet():
    #username = request.form["name"]  # Получаем данные из формы
    #if request.method == "POST":
        # 1. Получаем данные из формы безопасно
        #name = request.form.get("name", "")
        # 2. Сохраняем имя в session, чтобы оно не потерялось при редиректе
        #session['username'] = name
        
        # 3. ВОТ ГЛАВНЫЙ ФИКС: делаем редирект вместо render_template
        #return redirect(url_for('greet'))

    # Этот код сработает только при GET-запросе (в том числе после редиректа)
    # Берем имя из session. Если там пусто, пишем "Гость"
    #username = session.get('username', 'Гость')
    habits = ["Зарядка", "Чтение 30 минут", "Стакан воды утром"]
    return render_template("index.html",habits = habits,app_name = 'Трекер')  # Возвращаем ответ

@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id) # get_or_404 защищает от несуществующих id
    return render_template('post_detail.html', post=post)

@app.route("/post/<int:post_id>/delete", methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Пост удален', 'info')
    return redirect(url_for('posts'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: # Если уже вошел, нечего тут делать
        return redirect(url_for('posts'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        # Проверяем, нет ли уже такого пользователя
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Этот email уже занят', 'danger')
            return redirect(url_for('register'))
            
        # Создаем нового
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь войдите.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('posts'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user) # Вот она, магия входа!
            flash('Вы вошли в систему!', 'success')
            return redirect(url_for('posts'))
        else:
            flash('Неверный email или пароль', 'danger')
            
    return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('posts'))

@app.route("/posts")
@login_required  # <--- Добавляем защиту, чтобы анонимы не зашли
def posts():
    # Фильтруем: только посты текущего пользователя
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all() 
    return render_template('posts.html', posts=posts)

@app.route('/create', methods=['GET', 'POST'])
@login_required  # <--- ВОТ ЭТА МАГИЯ. Без входа сюда не пустит
def create():
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        # Привязываем пост к текущему пользователю:
        post = Post(text=text, title=title, user_id=current_user.id) 
       
        try:
            db.session.add(post)
            db.session.commit()
            flash('Пост успешно создан!', 'success')
            return redirect(url_for('posts'))
        except Exception as e:
            flash(f'Ошибка: {e}', 'danger')
            return redirect(url_for('create'))
    else:
        return render_template('create.html')



with app.app_context():
    db.create_all()
if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=False)

