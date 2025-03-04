from flask import Flask, request, render_template, jsonify, redirect, url_for, session, flash
import subprocess
import os
from database import DB_Task, DB_User, DB_Create_Task
from file_proc import FileProcessor as fp
from auth import Auth

app = Flask(__name__)
app.secret_key = 'ваш_секретный_ключ'  # Замените на случайную строку

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = DB_Task()
db_user = DB_User()
db_create_task = DB_Create_Task()

login_required = Auth.login_required

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_role = session.get('role')
    courses = db.get_all_courses()
    
    if user_role == 'student':
        # Получаем прогресс студента
        student_progress = db_user.get_student_progress(session['user_id'])
        # Получаем уведомления студента
        notifications = db_user.get_student_notifications(session['user_id'])
        return render_template('dashboard.html',
                             courses=courses,
                             progress=student_progress,
                             notifications=notifications,
                             role='student')
    elif user_role in ['teacher', 'admin']:
        # Получаем группы преподавателя
        teacher_groups = db_user.get_teacher_groups(session['user_id'])
        # Получаем задания на проверку
        pending_assignments = db_user.get_pending_assignments(session['user_id'])
        return render_template('dashboard.html',
                             courses=courses,
                             groups=teacher_groups,
                             pending_assignments=pending_assignments,
                             role='teacher')
                             
    return redirect(url_for('login'))

class CourseRoute:
    @staticmethod
    @app.route('/course/<id_course>')
    def course(id_course):
        task_data_header = db.get_lessons_by_course_id(id_course)
        courses = db.get_all_courses()
        return render_template('tasks_list.html', 
                            task_data=task_data_header, 
                            courses=courses,
                            course_id=id_course)

    @staticmethod
    @app.route('/course/<course_id>/task/<task_id>')
    def task(course_id, task_id):
        task_data = db.get_task_by_id(course_id, task_id)
        if task_data is None:
            return "Задача не найдена", 404

        course_tasks = db.get_lessons_by_course_id(course_id)
        content = session.pop('task_content', None)

        print(course_tasks)
        
        return render_template('task.html', 
                            content=content, 
                            task=task_data,
                            course_id=course_id,
                            task_id = task_id,
                            course_tasks=course_tasks)

    @staticmethod
    @app.route('/upload/<id_course>/task/<id_task>', methods=['POST'])
    def upload_file(id_course, id_task):
        if 'file' not in request.files:
            return "No file part", 400

        file = request.files['file']

        if file.filename == '':
            return "No selected file", 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        fps = fp(file_path, id_task)
        content = fps.process_file()

        # Сохраняем content в сессию
        session['task_content'] = content
        
        # Исправляем url_for, убирая CourseRoute
        return redirect(url_for('task', course_id=id_course, task_id=id_task))

    @staticmethod
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

class AuthRouts:
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
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='Неверное имя пользователя или пароль')
        
        return render_template('login.html')


    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))

class ProfileRoutes():
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
                return redirect(url_for('.index'))
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
