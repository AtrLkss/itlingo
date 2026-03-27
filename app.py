from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
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
        except:
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
    
# @app.route("/one")
# @login_required
# def one():
#     return render_template("one.html", user=current_user)

# @app.route("/two")
# @login_required
# def two():
#     return render_template("two.html", user=current_user)

# @app.route("/three")
# @login_required
# def three():
#     return render_template("three.html", user=current_user)

# VKAD

class UserLessonProgress(db.Model):
    __tablename__ = "user_lesson_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lesson_slug = db.Column(db.String(100), nullable=False)
    unlocked_step = db.Column(db.Integer, default=1)
    completed = db.Column(db.Boolean, default=False)
    reward_claimed = db.Column(db.Boolean, default=False)


LESSONS = {
    "lesson-1": {
        "title": "Lesson 1",
        "description": "Description for Lesson 1",
        "reward_exp": 1000,
        "steps": 
        [
            {
                "order": 1,
                "type": "theory",
                "title": "Что такое Python?",
                "content": "Python - это высокоуровневый язык программирования общего назначения, который используется для разработки веб-приложений, анализа данных, искусственного интеллекта и многого другого.",
                "question": "Python - Это змея или Язык программирования?",
                "answer": "Да"
            },
            {
                "order": 2,
                "type": "test",
                "title": "PROVERKA PO TEORII",
                "task": "Kakoi yazik mi izuchaem?",
                "options": ["C++", "Python", "Java"],
                "correct": "Python"
            },
            {
                "order": 3,
                "type": "practice",
                "title": "Практическое задание",
                "task": "Напиши 'Hello, World!' на Python",
                "hint": "Используй print()"
            }
        ]
    }
}

def get_or_create_progress(user_id, lesson_slug):
    progress = UserLessonProgress.query.filter_by(
        user_id=user_id, lesson_slug=lesson_slug
    ).first()

    if progress is None:
        progress = UserLessonProgress(user_id=user_id, lesson_slug=lesson_slug)
        db.session.add(progress)
        db.session.commit()

    return progress


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

    step_number = request.args.get("step", progress.unlocked_step, type=int)
    step_number = min(step_number, progress.unlocked_step)

    current_step = next(
        (s for s in lesson["steps"] if s["order"] == step_number), 
        lesson["steps"][0]
    )
    return render_template(
        "lesson.html",
        lesson=lesson,
        lesson_slug=lesson_slug,
        current_step=current_step,
        progress=progress,
        user=current_user
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

    if is_correct:
        if step_order < len(lesson["steps"]):
            progress.unlocked_step = max(progress.unlocked_step, step_order + 1)
        else:
            progress.completed = True
            if not progress.reward_claimed:
                add_exp(current_user, lesson["reward_exp"])
                progress.reward_claimed = True

        db.session.commit()

    return redirect(url_for("lesson_page", lesson_slug=lesson_slug, step=progress.unlocked_step,))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
