"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""
from datetime import datetime
import random
from flask import Flask, render_template, request, redirect, url_for, session,flash
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import date
import os
from werkzeug.utils import secure_filename
from flask import current_app



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


class Vibe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=True)  # Текст (если есть)
    image_url = db.Column(db.String(500), nullable=True)  # Ссылка на картинку
    video_url = db.Column(db.String(500), nullable=True)  # Ссылка на видео (например, YouTube embed)
    category = db.Column(db.String(50), default='Интересное')  # Тег: Наука, История, Факты
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Таблица для сохранения понравившегося контента (Связь Юзер-Вайб)
class SavedVibe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vibe_id = db.Column(db.Integer, db.ForeignKey('vibe.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='saved_vibes')
    vibe = db.relationship('Vibe')

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
@app.route("/")
def l():
    if not current_user.is_authenticated:
        return render_template("begin.html")
    
    else:
        all_vibes = Vibe.query.all()
        day_seed = int(date.today().strftime("%Y%m%d"))
        rng = random.Random(day_seed)
        rng.shuffle(all_vibes)
        daily_vibes = all_vibes[:3]

        return render_template("index.html", vibes=daily_vibes)
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
    return render_template("begin.html")  # Возвращаем ответ

#@app.route("/post/<int:post_id>")
#def post_detail(post_id):
    #post = Post.query.get_or_404(post_id) # get_or_404 защищает от несуществующих id
    #return render_template('post_detail.html', post=post)

#@app.route("/post/<int:post_id>/delete", methods=['POST'])
#def delete_post(post_id):
    #post = Post.query.get_or_404(post_id)
    #db.session.delete(post)
    #db.session.commit()
    #flash('Пост удален', 'info')
    #return redirect(url_for('posts'))
@app.route("/index")
@login_required
def index():
    # 1. Получаем ВСЕ вайбы из базы
    all_vibes = Vibe.query.all()

    # 2. Создаем seed на основе сегодняшней даты (например, 20261103)
    day_seed = int(date.today().strftime("%Y%m%d"))

    # 3. Перемешиваем список с этим seed. 
    # random.Random(day_seed) гарантирует, что сегодня порядок будет один и тот же,
    # а завтра (когда дата изменится) — новый.
    rng = random.Random(day_seed)
    rng.shuffle(all_vibes)

    # 4. Берем первые 3 записи
    daily_vibes = all_vibes[:3]

    return render_template("index.html", vibes=daily_vibes)
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: # Если уже вошел, нечего тут делать
        return redirect(url_for('greet'))
        
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
        return redirect(url_for('greet'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user) # Вот она, магия входа!
            flash('Вы вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'danger')
            
    return render_template('login.html', form=form)


@app.route("/add_vibe", methods=["GET", "POST"])
@login_required
def add_vibe():
    if current_user.username != 'admin':
        flash('У вас нет прав на добавление контента', 'danger')
        return redirect(url_for('index'))

    if request.method == "POST":
        title = request.form.get("title")
        text = request.form.get("text")
        category = request.form.get("category")
        
        # Получаем текстовые ссылки (если админ вставил их вручную)
        image_url = request.form.get("image_url")
        video_url = request.form.get("video_url")

        # --- ОБРАБОТКА ЗАГРУЖЕННОГО ФАЙЛА КАРТИНКИ ---
        image_file = request.files.get("image_file")
        if image_file and image_file.filename != '':
            # secure_filename защищает от взлома (убирает опасные символы из имени файла)
            filename = secure_filename(image_file.filename)
            
            # Путь для сохранения файла на диске
            save_path = os.path.join(current_app.root_path, 'static', 'uploads', 'images', filename)
            image_file.save(save_path)
            
            # Записываем в базу путь для HTML
            image_url = f'/static/uploads/images/{filename}'

        # (Здесь можно добавить аналогичный код для видео, если нужно)

        new_vibe = Vibe(title=title, text=text, image_url=image_url, video_url=video_url, category=category)
        
        try:
            db.session.add(new_vibe)
            db.session.commit()
            flash('Вайб успешно добавлен!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Ошибка: {e}', 'danger')

    return render_template("add_vibe.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

#@app.route("/posts")
#@login_required  # <--- Добавляем защиту, чтобы анонимы не зашли
#def posts():
    # Фильтруем: только посты текущего пользователя
    #posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all() 
    #return render_template('posts.html', posts=posts)

#@app.route('/create', methods=['GET', 'POST'])
#@login_required  # <--- ВОТ ЭТА МАГИЯ. Без входа сюда не пустит
#def create():
    #if request.method == 'POST':
        #title = request.form['title']
        #text = request.form['text']
        # Привязываем пост к текущему пользователю:
        #post = Post(text=text, title=title, user_id=current_user.id) 
       
        #try:
            #db.session.add(post)
            #db.session.commit()
            #flash('Пост успешно создан!', 'success')
            #return redirect(url_for('posts'))
        #except Exception as e:
            #flash(f'Ошибка: {e}', 'danger')
            #return redirect(url_for('create'))
    #else:
        #return render_template('create.html')
@app.route("/favorites")
@login_required
def favorites():
    # Достаем все сохраненные вайбы текущего пользователя, сортируем по дате (новые сверху)
    # Благодаря relationship в модели SavedVibe, у нас есть доступ к объекту vibe
    saved_items = SavedVibe.query.filter_by(user_id=current_user.id).order_by(SavedVibe.saved_at.desc()).all()
    return render_template("favorites.html", saved_items=saved_items)

@app.route("/remove_favorite/<int:saved_id>", methods=["POST"])
@login_required
def remove_favorite(saved_id):
    # Ищем запись по ID и проверяем, что она принадлежит текущему пользователю
    item = SavedVibe.query.filter_by(id=saved_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('Удалено из избранного', 'info')
    return redirect(url_for('favorites'))

@app.route("/save/<int:vibe_id>", methods=["POST"])
@login_required
def save_vibe(vibe_id):
    # Проверяем, не сохранял ли уже этот пользователь этот вайб
    existing = SavedVibe.query.filter_by(user_id=current_user.id, vibe_id=vibe_id).first()
    
    if existing:
        flash('Ты уже сохранял это!', 'info')
    else:
        saved = SavedVibe(user_id=current_user.id, vibe_id=vibe_id)
        db.session.add(saved)
        db.session.commit()
        flash('Добавлено в избранное! ❤️', 'success')
        
    return redirect(url_for('index'))

@app.route("/delete_vibe/<int:vibe_id>", methods=["POST"])
@login_required
def delete_vibe(vibe_id):
    if current_user.username != 'admin':
        flash('У вас нет прав', 'danger')
        return redirect(url_for('index'))
        
    vibe = Vibe.query.get_or_404(vibe_id)
    db.session.delete(vibe)
    db.session.commit()
    flash('Вайб удален из базы', 'success')
    return redirect(url_for('index'))

@app.route("/vibe/<int:vibe_id>")
@login_required  # Чтобы незарегистрированные не могли смотреть статьи
def vibe_detail(vibe_id):
    # Ищем вайб по ID. Если не найден — выдаст ошибку 404
    vibe = Vibe.query.get_or_404(vibe_id)
    return render_template("vibe_detail.html", vibe=vibe)


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

