from flask import Flask, request, render_template, jsonify, redirect, url_for, session, flash
import subprocess
import os
from database import DB_Task, DB_User, DB_Create_Task
from functools import wraps
from file_proc import FileProcessor as fp
app = Flask(__name__)
app.secret_key = 'ваш_секретный_ключ'  # Замените на случайную строку

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = DB_Task()
db_user = DB_User()
db_create_task = DB_Create_Task()

@app.route('/')
def index():
    courses = db.get_all_courses()
    return render_template('main_theme.html', courses=courses)


@app.route('/course/<id_course>')
def course(id_course):
    task_data = db.get_lessons_by_course_id(id_course)
    courses = db.get_all_courses()
    return render_template('tasks_list.html', 
                         task_data=task_data, 
                         courses=courses,
                         course_id=id_course)


@app.route('/course/<course_id>/task/<task_id>')
def task(course_id, task_id):
    task_data = db.get_task_by_id(course_id, task_id)
    if task_data is None:
        return "Задача не найдена", 404

    course_tasks = db.get_lessons_by_course_id(course_id)  # Получаем все задачи курса
    return render_template('task.html', 
                         content=None, 
                         task=task_data, 
                         course_id=course_id,
                         course_tasks=course_tasks)  # Передаем список задач вместо списка курсов


@app.route('/upload/<num_task>', methods=['POST'])
def upload_file(num_task):
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    content = fp.process_file(file_path, num_task)

    return render_template(f'task.html', content=content)


@app.route('/submit_code/<num_task>', methods=['POST'])
def submit_code(num_task):
    try:
        code = request.json.get('code')
        if not code:
            return jsonify({'error': 'No code provided'}), 400

        # Создаем временный файл с кодом
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_solution.py')
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        # Обрабатываем код через существующую функцию
        content = fp.process_file(temp_file_path, num_task)
        print(content)

        # Удаляем временный файл
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # return jsonify({'content': content})
        return render_template(f'task.html', content=content)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = db_user.verify_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['email'] = user[1]
            session['role'] = user[2]
            return redirect(url_for('profile'))
        else:
            return render_template('login.html', error='Неверное имя пользователя или пароль')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html',
                         username=session.get('username'),
                         email=session.get('email'),
                         role=session.get('role'))


@app.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    if session.get('role') != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        inputs = request.form.getlist('inputs[]')
        outputs = request.form.getlist('outputs[]')
        
        test_cases = list(zip(inputs, outputs))
        
        # Создаем задачу в базе данных
        task_id = db_create_task.create_task(title, description, test_cases)
        
        if task_id:
            flash('Задача успешно создана')
            return redirect(url_for('profile'))
        else:
            flash('Ошибка при создании задачи')
    
    return render_template('create_task.html')


@app.route('/my_tasks')
@login_required
def my_tasks():
    if session.get('role') != 'teacher':
        flash('Доступ запрещен')
        return redirect(url_for('profile'))
        
    tasks = db_create_task.get_tasks_by_teacher(session.get('user_id'))
    return render_template('my_tasks.html', tasks=tasks)



if __name__ == '__main__':
    app.run(debug=True)
