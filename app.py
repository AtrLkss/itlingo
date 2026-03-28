from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Module(db.Model):
    __tablename__ = "modules"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer)


class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"))
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(name=name).first():
            return render_template("sign_up.html", error="Имя пользователя уже занято!")

        password_hash = generate_password_hash(password, method="pbkdf2:sha256")

        user = User(name=name, password=password_hash)

        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login"))
        except Exception:
            return render_template(
                "sign_up.html", error="При регистрации произошла ошибка!"
            )

    return render_template("sign_up.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(name=name).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template(
                "login.html", error="Неверное имя пользователя или пароль"
            )

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/personal_account")
@login_required
def personal_account():
    return render_template("personal_account.html", user=current_user)


@app.route("/learn")
@login_required
def learn():
    return render_template("learn.html", user=current_user)


class UserLessonProgress(db.Model):
    __tablename__ = "user_lesson_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lesson_slug = db.Column(db.String(100), nullable=False)
    unlocked_step = db.Column(db.Integer, default=2)
    test_passed = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    reward_claimed = db.Column(db.Boolean, default=False)


LESSONS = {
    "lesson-1": {
        "title": "Lesson 1",
        "description": "Description for Lesson 1",
        "reward_exp": 1000,
        "steps": [
            {
                "order": 1,
                "type": "theory",
                "title": "Вступление",
                "turtle-1": "Что такое Python?",
                "turtle-2": "Почему пайтон идеален для начинающих?",
                "turtle-3": "Первая программа",
                "turtle-4": "",
                "content-1": """"Представьте себе язык, на котором вы можете разговаривать с компьютером так же естественно, как с другом. Язык, который понимает ваши мысли и помогает воплощать идеи в жизнь без лишних преград. Это — Python.
                
                Python — это язык программирования, который появился в 1991 году благодаря голландскому разработчику Гвидо ван Россуму. Название было вдохновлено не змеей, как многие думают, а британским комедийным шоу «Летающий цирк Монти Пайтона». Создатель хотел, чтобы язык был таким же веселым, простым и доступным.
                
                Сегодня Python — один из самых популярных языков программирования в мире. Его любят за простоту, читаемость и мощь. На Python пишут всё: от простых скриптов до сложных систем искусственного интеллекта, веб-сайтов и научных исследований.""",
                "content-2": """Почему Python идеален для начинающих? Представьте, что вы учитесь кататься на велосипеде. Можно начать со сложного гоночного велосипеда с десятком передач, а можно с простого, устойчивого и надежного. Python — это тот самый надежный велосипед.

                Вот что делает Python особенным. Во-первых, читаемость. Код на Python похож на английский язык. Вместо запутанных скобок и сложных конструкций — понятные слова и логичные структуры. Во-вторых, простота. Чтобы написать первую программу, достаточно одной строчки. Вам не нужно изучать сотни правил перед тем, как увидеть результат. В-третьих, сообщество. Миллионы разработчиков по всему миру используют Python. Любой ваш вопрос уже задавали до вас, и ответ на него легко найти. И наконец, универсальность. Выучив Python, вы сможете работать в разных направлениях: веб-разработка, анализ данных, искусственный интеллект, автоматизация, создание игр и многое другое.
                """,
                "content-3": """В программировании есть традиция: первая программа на новом языке должна выводить фразу «Hello, World!». Это как первый шаг в большом путешествии.
                
                Python позволяет сделать это одной строчкой:

                print("Hello, World!")

                Разберем, что здесь происходит. print — это команда (функция), которая говорит компьютеру: «Выведи на экран то, что я укажу». В скобках помещается то, что мы хотим вывести. А кавычки показывают, что внутри находится текст — в программировании это называется «строка».
                """,
                "content-4": "",
                "question": "Python - Это змея или Язык программирования?",
                "answer": "Да",
            },
            {
                "order": 2,
                "type": "test",
                "title": "Тест",
                "task": "Какая функция позволяет вывести текст на экран в Python?",
                "options": ["print", "write", "pen"],
                "correct": "print",
            },
            {
                "order": 3,
                "type": "practice",
                "title": "Практическое задание",
                "task": "Напиши 'Hello, World!' на Python",
                "hint": "Используй print()",
            },
        ],
    },
    "lesson-2": {
        "title": "Lesson 2",
        "description": "Description for Lesson 2",
        "reward_exp": 1000,
        "steps": [
            {
                "order": 1,
                "type": "theory",
                "title": "Переменные и операторы",
                "turtle-1": "",
                "turtle-2": "",
                "turtle-3": "",
                "turtle-4": "",
                "content-1": "...",
                "content-2": "...",
                "content-3": "...",
                "content-4": "...",
                "question": "Python - Это змея или Язык программирования?",
                "answer": "Да",
            },
            {
                "order": 2,
                "type": "test",
                "title": "PROVERKA PO TEORII",
                "task": "Kakoi yazik mi izuchaem?",
                "options": ["C++", "Python", "Java"],
                "correct": "Python",
            },
            {
                "order": 3,
                "type": "practice",
                "title": "Практическое задание",
                "task": "Напиши 'Hello, World!' на Python",
                "hint": "Используй print()",
            },
        ],
    },
    "lesson-3": {
        "title": "Lesson 3",
        "description": "Description for Lesson 3",
        "reward_exp": 1000,
        "steps": [
            {
                "order": 1,
                "type": "theory",
                "title": "Условия и циклы",
                "turtle-1": "",
                "turtle-2": "",
                "turtle-3": "",
                "turtle-4": "",
                "content-1": "...",
                "content-2": "...",
                "content-3": "...",
                "content-4": "...",
                "question": "Python - Это змея или Язык программирования?",
                "answer": "Да",
            },
            {
                "order": 2,
                "type": "test",
                "title": "PROVERKA PO TEORII",
                "task": "Kakoi yazik mi izuchaem?",
                "options": ["C++", "Python", "Java"],
                "correct": "Python",
            },
            {
                "order": 3,
                "type": "practice",
                "title": "Практическое задание",
                "task": "Напиши 'Hello, World!' на Python",
                "hint": "Используй print()",
            },
        ],
    },
}


def get_or_create_progress(user_id, lesson_slug):
    progress = UserLessonProgress.query.filter_by(
        user_id=user_id, lesson_slug=lesson_slug
    ).first()

    if progress is None:
        progress = UserLessonProgress(
            user_id=user_id,
            lesson_slug=lesson_slug,
            unlocked_step=2,
        )
        db.session.add(progress)
        db.session.commit()
    elif progress.unlocked_step < 2:
        progress.unlocked_step = 2
        db.session.commit()

    return progress


def ensure_progress_columns():
    columns = {
        row[1]
        for row in db.session.execute(text("PRAGMA table_info(user_lesson_progress)"))
    }
    if "test_passed" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE user_lesson_progress "
                "ADD COLUMN test_passed BOOLEAN DEFAULT 0"
            )
        )
        db.session.commit()


def add_exp(user, amount):
    user.exp += amount
    user.level = user.exp // 1000 + 1


@app.route("/lessons/<lesson_slug>")
@login_required
def lesson_page(lesson_slug):
    lesson = LESSONS.get(lesson_slug)
    if lesson is None:
        return redirect(url_for("learn"))

    progress = get_or_create_progress(current_user.id, lesson_slug)
    incorrect_answer = request.args.get("incorrect", 0, type=int) == 1

    if not progress.test_passed and progress.unlocked_step > 2:
        progress.unlocked_step = 2
        db.session.commit()

    step_number = request.args.get("step", progress.unlocked_step, type=int)
    step_number = min(step_number, progress.unlocked_step)

    current_step = next(
        (s for s in lesson["steps"] if s["order"] == step_number),
        lesson["steps"][0],
    )
    return render_template(
        "lesson.html",
        lesson=lesson,
        lesson_slug=lesson_slug,
        current_step=current_step,
        progress=progress,
        incorrect_answer=incorrect_answer,
        user=current_user,
    )


@app.route("/lessons/<lesson_slug>/steps/<int:step_order>/complete", methods=["POST"])
@login_required
def complete_step(lesson_slug, step_order):
    lesson = LESSONS.get(lesson_slug)
    if lesson is None:
        return redirect(url_for("learn"))

    progress = get_or_create_progress(current_user.id, lesson_slug)
    current_step = next((s for s in lesson["steps"] if s["order"] == step_order), None)
    if current_step is None or step_order > progress.unlocked_step:
        return redirect(url_for("lesson_page", lesson_slug=lesson_slug))

    answer = request.form.get("answer", "").strip()
    is_correct = True

    if current_step["type"] == "theory":
        is_correct = answer.strip() != ""
    elif current_step["type"] == "test":
        is_correct = answer == current_step["correct"]
    elif current_step["type"] == "practice":
        is_correct = True

    if not is_correct and current_step["type"] == "test":
        progress.test_passed = False
        progress.unlocked_step = min(progress.unlocked_step, step_order)
        db.session.commit()
        return redirect(
            url_for("lesson_page", lesson_slug=lesson_slug, step=step_order, incorrect=1)
        )

    if is_correct:
        if current_step["type"] == "theory":
            progress.unlocked_step = max(progress.unlocked_step, 2)
        elif current_step["type"] == "test":
            progress.test_passed = True
            progress.unlocked_step = max(progress.unlocked_step, 3)
        elif step_order < len(lesson["steps"]):
            progress.unlocked_step = max(progress.unlocked_step, step_order + 1)
        else:
            progress.completed = True
            if not progress.reward_claimed:
                add_exp(current_user, lesson["reward_exp"])
                progress.reward_claimed = True

        db.session.commit()

    return redirect(
        url_for("lesson_page", lesson_slug=lesson_slug, step=progress.unlocked_step)
    )


with app.app_context():
    db.create_all()
    ensure_progress_columns()

if __name__ == "__main__":
    app.run(debug=True)
