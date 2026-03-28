from flask import Flask, render_template, request, url_for, redirect, jsonify, flash
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
import docker
import os
import random
import subprocess
import shutil
from functools import wraps

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
    achievement_rows = (
        UserAchievement.query.filter_by(user_id=current_user.id)
        .order_by(UserAchievement.created_at.desc())
        .all()
    )

    user_achievements = []
    for row in achievement_rows:
        achievement = ACHIEVEMENTS.get(row.achievement_slug)
        if achievement:
            user_achievements.append(achievement)

    return render_template(
        "personal_account.html",
        user=current_user,
        user_achievements=user_achievements,
    )


@app.route("/learn")
@login_required
def learn():
    return render_template("learn.html", user=current_user)


class UserLessonProgress(db.Model):
    __tablename__ = "user_lesson_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lesson_slug = db.Column(db.String(100), nullable=False)
    unlocked_step = db.Column(db.Integer, default=1)
    test_passed = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    reward_claimed = db.Column(db.Boolean, default=False)


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    achievement_slug = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


LESSONS = {
    "lesson-1": {
        "title": "Урок 1. Знакомство с Python",
        "description": "Первые шаги в Python: что это за язык, как он выглядит и где применяется.",
        "steps": [
            {
                "order": 1,
                "type": "theory",
                "title": "Вступление",
                "turtle-1": "Что такое Python?",
                "turtle-2": "Почему Python удобен для новичков?",
                "turtle-3": "Первая программа",
                "turtle-4": "Где используют Python?",
                "content-1": """Python — это язык программирования, который помогает человеку общаться с компьютером с помощью понятных команд. Он был создан так, чтобы код было легко читать и писать. Благодаря этому Python часто выбирают как первый язык для изучения.""",
                "content-2": """Python удобен для новичков, потому что в нем меньше сложных конструкций, чем во многих других языках. Код выглядит аккуратно и напоминает обычный текст с командами. Это помогает сосредоточиться на логике задач, а не на запоминании большого количества правил.""",
                "content-3": """Традиционная первая программа на новом языке выводит фразу Hello, World!. В Python для этого используют функцию print. Например, команда print("Hello, World!") покажет эту строку на экране.""",
                "content-4": """Python применяют в веб-разработке, анализе данных, автоматизации, создании ботов и работе с искусственным интеллектом. Это универсальный язык, который подходит и для учебы, и для серьезных проектов. Поэтому изучение Python дает хорошую основу для роста в IT.""",
                "exp_reward": 50,
            },
            {
                "order": 2,
                "type": "test",
                "title": "Проверка по теме",
                "questions": [
                    {
                        "id": "q1",
                        "prompt": "Что такое Python?",
                        "options": [
                            {
                                "value": "programming_language",
                                "label": "Язык программирования",
                            },
                            {
                                "value": "graphic_editor",
                                "label": "Графический редактор",
                            },
                            {"value": "search_engine", "label": "Поисковая система"},
                        ],
                        "correct": "programming_language",
                    },
                    {
                        "id": "q2",
                        "prompt": "Какая команда выводит текст на экран?",
                        "options": [
                            {"value": "print", "label": "print"},
                            {"value": "input", "label": "input"},
                            {"value": "range", "label": "range"},
                        ],
                        "correct": "print",
                    },
                    {
                        "id": "q3",
                        "prompt": "Почему Python подходит новичкам?",
                        "options": [
                            {
                                "value": "clear_syntax",
                                "label": "У него понятный синтаксис",
                            },
                            {"value": "no_variables", "label": "В нем нет переменных"},
                            {
                                "value": "only_games",
                                "label": "Он работает только в играх",
                            },
                        ],
                        "correct": "clear_syntax",
                    },
                ],
                "exp_reward": 300,
            },
            {
                "order": 3,
                "type": "practice",
                "title": "Практическое задание",
                "task": "Напиши программу, которая выводит на экран строку Hello, World! с помощью функции print().",
                "hint": 'Используй print("Hello, World!")',
                "expected_output": "Hello, World!",
                "exp_reward": 250,
            },
        ],
    },
    "lesson-2": {
        "title": "Урок 2. Переменные и операторы",
        "description": "Разбираем, как хранить данные в переменных и выполнять вычисления.",
        "steps": [
            {
                "order": 1,
                "type": "theory",
                "title": "Переменные и операторы",
                "turtle-1": "Что такое переменная?",
                "turtle-2": "Как присваивать значения?",
                "turtle-3": "Основные операторы",
                "turtle-4": "Как использовать переменные в программе?",
                "content-1": """Переменная — это именованное место в памяти, где хранится какое-то значение. Можно представить ее как коробку с наклейкой: на наклейке написано имя, а внутри лежит нужная информация. Например, в переменной age можно сохранить возраст пользователя.""",
                "content-2": """Чтобы записать значение в переменную, используют знак равно. Например, name = "Alex" или count = 5. Слева пишут имя переменной, а справа — значение, которое должно в ней храниться.""",
                "content-3": """Операторы помогают выполнять действия с числами и значениями. Например, + складывает, - вычитает, * умножает, а / делит. С их помощью программа может считать и менять данные.""",
                "content-4": """Переменные удобно использовать вместе с print и вычислениями. Например, если a = 7 и b = 5, то команда print(a + b) выведет 12. Так программа работает не только с готовыми числами, но и с сохраненными значениями.""",
                "exp_reward": 50,
            },
            {
                "order": 2,
                "type": "test",
                "title": "Проверка по теме",
                "questions": [
                    {
                        "id": "q1",
                        "prompt": "Для чего нужна переменная?",
                        "options": [
                            {"value": "store_value", "label": "Чтобы хранить значение"},
                            {"value": "delete_code", "label": "Чтобы удалить код"},
                            {
                                "value": "close_program",
                                "label": "Чтобы закрыть программу",
                            },
                        ],
                        "correct": "store_value",
                    },
                    {
                        "id": "q2",
                        "prompt": "Как записать число 10 в переменную count?",
                        "options": [
                            {"value": "assign", "label": "count = 10"},
                            {"value": "reverse_assign", "label": "10 = count"},
                            {"value": "compare", "label": "count == 10"},
                        ],
                        "correct": "assign",
                    },
                    {
                        "id": "q3",
                        "prompt": "Какой оператор означает умножение?",
                        "options": [
                            {"value": "multiply", "label": "*"},
                            {"value": "plus", "label": "+"},
                            {"value": "divide", "label": "/"},
                        ],
                        "correct": "multiply",
                    },
                ],
                "exp_reward": 300,
            },
            {
                "order": 3,
                "type": "practice",
                "title": "Практическое задание",
                "task": "Создай две переменные a и b со значениями 7 и 5, а затем выведи их сумму на экран.",
                "hint": "Напиши a = 7, b = 5, а потом print(a + b).",
                "expected_output": "12",
                "exp_reward": 250,
            },
        ],
    },
    "lesson-3": {
        "title": "Урок 3. Условия и циклы",
        "description": "Учимся принимать решения в коде и повторять действия много раз.",
        "steps": [
            {
                "order": 1,
                "type": "theory",
                "title": "Условия и циклы",
                "turtle-1": "Что такое условие?",
                "turtle-2": "Как работает if?",
                "turtle-3": "Что такое цикл?",
                "turtle-4": "Где это применяют?",
                "content-1": """Условие помогает программе выбирать одно действие из нескольких. Например, если пароль введен правильно, программа пускает пользователя дальше. Если пароль неверный, она показывает сообщение об ошибке.""",
                "content-2": """В Python для условий используют команду if. После if пишут проверку, а ниже — действие, которое выполнится, если условие истинно. Можно также использовать else, чтобы задать поведение на случай, если условие не выполнено.""",
                "content-3": """Цикл нужен, когда требуется повторить действие несколько раз. Например, можно вывести числа от 1 до 5 без пяти отдельных команд print. В Python для этого часто используют цикл for.""",
                "content-4": """Условия и циклы встречаются почти в каждой программе. Условия помогают реагировать на действия пользователя, а циклы полезны при обработке списков, повторов и автоматизации однотипных задач. Это важные инструменты любого программиста.""",
                "exp_reward": 50,
            },
            {
                "order": 2,
                "type": "test",
                "title": "Проверка по теме",
                "questions": [
                    {
                        "id": "q1",
                        "prompt": "Какое слово используют для условия в Python?",
                        "options": [
                            {"value": "if", "label": "if"},
                            {"value": "for", "label": "for"},
                            {"value": "print", "label": "print"},
                        ],
                        "correct": "if",
                    },
                    {
                        "id": "q2",
                        "prompt": "Что делает цикл?",
                        "options": [
                            {
                                "value": "repeat_actions",
                                "label": "Повторяет действие несколько раз",
                            },
                            {
                                "value": "delete_variables",
                                "label": "Удаляет переменные",
                            },
                            {"value": "open_browser", "label": "Открывает браузер"},
                        ],
                        "correct": "repeat_actions",
                    },
                    {
                        "id": "q3",
                        "prompt": "Какое слово задает альтернативное действие?",
                        "options": [
                            {"value": "else", "label": "else"},
                            {"value": "input", "label": "input"},
                            {"value": "def", "label": "def"},
                        ],
                        "correct": "else",
                    },
                ],
                "exp_reward": 300,
            },
            {
                "order": 3,
                "type": "practice",
                "title": "Практическое задание",
                "task": "Напиши цикл for, который выводит числа от 1 до 5, каждое с новой строки.",
                "hint": "Используй for i in range(1, 6): и внутри print(i).",
                "expected_output": "1\n2\n3\n4\n5",
                "exp_reward": 250,
            },
        ],
    },
}

ACHIEVEMENTS = {
    "lesson-1-test": {
        "title": "Первые шаги",
        "description": "Вы успешно прошли тест 1 урока и получили это достижение!",
        "icon": "images/first_steps.jpg",
    },
    "lesson-2-test": {
        "title": "Переменные освоены",
        "description": "Вы успешно прошли тест 2 урока и получили это достижение!",
        "icon": "images/python_begginer.jpg",
    },
    "lesson-3-test": {
        "title": "Циклы покорены",
        "description": "Вы успешно прошли тест 3 урока и получили это достижение!",
        "icon": "images/csharp_expert.jpg",
    },
}


def get_or_create_progress(user_id, lesson_slug):
    progress = UserLessonProgress.query.filter_by(
        user_id=user_id,
        lesson_slug=lesson_slug,
    ).first()

    if progress is None:
        progress = UserLessonProgress(
            user_id=user_id,
            lesson_slug=lesson_slug,
            unlocked_step=1,
        )
        db.session.add(progress)
        db.session.commit()

    return progress


def give_achievement(user_id, achievement_slug):
    existing = UserAchievement.query.filter_by(
        user_id=user_id,
        achievement_slug=achievement_slug,
    ).first()

    if existing:
        return None

    achievement = ACHIEVEMENTS.get(achievement_slug)
    if achievement is None:
        return None

    db.session.add(
        UserAchievement(
            user_id=user_id,
            achievement_slug=achievement_slug,
        )
    )
    return achievement


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


error_list = [
    "ArithmeticError",
    "AssertionError",
    "AttributeError",
    "BaseException",
    "BlockingIOError",
    "BrokenPipeError",
    "BufferError",
    "BytesWarning",
    "ChildProcessError",
    "ConnectionAbortedError",
    "ConnectionError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "DeprecationWarning",
    "EOFError",
    "Ellipsis",
    "EnvironmentError",
    "Exception",
    "False",
    "FileExistsError",
    "FileNotFoundError",
    "FloatingPointError",
    "FutureWarning",
    "GeneratorExit",
    "IOError",
    "ImportError",
    "ImportWarning",
    "IndentationError",
    "IndexError",
    "InterruptedError",
    "IsADirectoryError",
    "KeyError",
    "KeyboardInterrupt",
    "LookupError",
    "MemoryError",
    "ModuleNotFoundError",
    "NameError",
    "None",
    "NotADirectoryError",
    "NotImplemented",
    "NotImplementedError",
    "OSError",
    "OverflowError",
    "PendingDeprecationWarning",
    "PermissionError",
    "ProcessLookupError",
    "RecursionError",
    "ReferenceError",
    "ResourceWarning",
    "RuntimeError",
    "RuntimeWarning",
    "StopAsyncIteration",
    "StopIteration",
    "SyntaxError",
    "SyntaxWarning",
    "SystemError",
    "SystemExit",
    "TabError",
    "TimeoutError",
    "True",
    "TypeError",
    "UnboundLocalError",
    "UnicodeDecodeError",
    "UnicodeEncodeError",
    "UnicodeError",
    "UnicodeTranslateError",
    "UnicodeWarning",
    "UserWarning",
    "ValueError",
    "Warning",
    "ZeroDivisionError",
]


@app.route("/lessons/<lesson_slug>")
@login_required
def lesson_page(lesson_slug):
    lesson = LESSONS.get(lesson_slug)
    if lesson is None:
        return redirect(url_for("learn"))

    progress = get_or_create_progress(current_user.id, lesson_slug)
    incorrect_answer = request.args.get("incorrect", 0, type=int) == 1

    if (
        not progress.test_passed
        and not progress.completed
        and progress.unlocked_step > 2
    ):
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
        is_correct = answer != ""
    elif current_step["type"] == "test":
        questions = current_step.get("questions", [])
        is_correct = all(
            request.form.get(question["id"], "").strip() == question["correct"]
            for question in questions
        )
    elif current_step["type"] == "practice":
        actual_output = request.form.get("actual_output", "")
        expected_output = current_step.get("expected_output", "")
        normalized_actual = actual_output.replace("\r\n", "\n").strip()
        normalized_expected = expected_output.replace("\r\n", "\n").strip()
        is_correct = (
            normalized_expected != "" and normalized_actual == normalized_expected
        )

    if not is_correct and current_step["type"] in {"test", "practice"}:
        return redirect(
            url_for(
                "lesson_page",
                lesson_slug=lesson_slug,
                step=step_order,
                incorrect=1,
            )
        )

    if is_correct:
        if current_step["type"] == "theory":
            if progress.unlocked_step < 2:
                add_exp(current_user, current_step.get("exp_reward", 50))
            progress.unlocked_step = max(progress.unlocked_step, 2)
        elif current_step["type"] == "test":
            if progress.unlocked_step < 3:
                add_exp(current_user, current_step.get("exp_reward", 100))
            progress.test_passed = True
            progress.unlocked_step = max(progress.unlocked_step, 3)

            achievement = give_achievement(current_user.id, f"{lesson_slug}-test")
            if achievement:
                flash(
                    f"Вы получили достижение: {achievement['title']}!",
                    "achievement",
                )
        elif step_order < len(lesson["steps"]):
            progress.unlocked_step = max(progress.unlocked_step, step_order + 1)
        else:
            if not progress.completed:
                add_exp(current_user, current_step.get("exp_reward", 250))
            progress.completed = True
            progress.reward_claimed = True

        db.session.commit()

    next_step = step_order
    if is_correct and step_order < len(lesson["steps"]):
        next_step = step_order + 1

    return redirect(url_for("lesson_page", lesson_slug=lesson_slug, step=next_step))


with app.app_context():
    db.create_all()
    ensure_progress_columns()


def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        data = request.get_json(silent=True) or {}
        if data.get("key") != "snILjFUkk_A":
            return jsonify({"error": "Invalid API key"}), 401
        return view_function(*args, **kwargs)

    return decorated_function


@login_required
def run_script(
    image,
    timeout,
    code,
    stdins="",
    expected_output=None,
):
    random_user_dir = f"{random.randint(1000, 2000)}"
    user_dir_url = os.path.join(
        os.path.dirname(__file__), "users_task_scripts", random_user_dir
    )
    os.makedirs(user_dir_url, exist_ok=True)

    file_url = os.path.join(user_dir_url, "task.py")
    input_data = "\\n".join(stdins)
    template_code = f'from io import StringIO;import sys;data = "{input_data}";sys.stdin = StringIO(data)\n'

    with open(file_url, "w") as file:
        file.write(template_code)
        file.write(code)

    result = {"stdout": "", "error": "None", "success": False}

    try:
        client = docker.from_env()
        container = client.containers.run(
            image,
            f"timeout {timeout} python task.py",
            network_disabled=True,
            detach=True,
            remove=False,
            working_dir="/task",
            volumes={user_dir_url: {"bind": "/task", "mode": "rw"}},
        )

        answer = container.logs(stream=True)
        container.wait(timeout=int(timeout))
        subprocess.Popen(f"docker rm -f {container.id}", shell=True)

        answer_list = [str(line, "utf-8") for line in answer]
        result["stdout"] = "".join(answer_list)

        for error_check in error_list:
            if any(error_check in ans for ans in answer_list):
                result["error"] = error_check
                break

        if expected_output and result["error"] == "None":
            actual_output = result["stdout"].replace("\r\n", "\n").strip()
            expected = expected_output.replace("\r\n", "\n").strip()

            if actual_output == expected:
                result["success"] = True
            else:
                result["success"] = False
                result["error"] = (
                    f"Wrong output. Expected: {expected}, Got: {actual_output}"
                )

    except Exception as e:
        result["error"] = f"Server error: {str(e)}"

    finally:
        shutil.rmtree(user_dir_url, ignore_errors=True)

    return result


@app.route("/python-ide", methods=["POST"])
@require_api_key
@login_required
def python_ide():
    try:
        data = request.json
        stdin_list = data.get("stdin", [])
        answer_list = []
        expected_output = data.get("expected_output", None)

        for stdins in stdin_list:
            answer = run_script(
                image=data["image"],
                timeout=data["timeout"],
                code=data["code"],
                stdins=stdins,
                expected_output=expected_output,
            )
            answer_list.append(answer)

        return jsonify(answer_list)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    os.makedirs(
        os.path.join(os.path.dirname(__file__), "users_task_scripts"), exist_ok=True
    )

    app.run(debug=True)
