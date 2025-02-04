from flask import Flask, request, render_template, jsonify
import subprocess
import os
from database import get_task_by_id

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    return render_template('main_theme.html', content=None)


@app.route('/task/<num_task>')
def task(num_task):
    task_data = get_task_by_id(num_task)
    if task_data is None:
        return "Задача не найдена", 404

    return render_template(f'task{num_task}.html', content=None, task=task_data)


@app.route('/upload/<num_task>', methods=['POST'])
def upload_file(num_task):
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    content = process_file(file_path, num_task)

    return render_template(f'task{num_task}.html', content=content)


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
        content = process_file(temp_file_path, num_task)
        print(content)

        # Удаляем временный файл
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # return jsonify({'content': content})
        return render_template(f'task{num_task}.html', content=content)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def process_file(file_path, num_task):
    current_file = os.path.realpath(__file__)
    testcase_directory = os.path.dirname(current_file) + f'\\TestCases\\test{num_task}'
    with open(testcase_directory, 'r', encoding="utf-8") as f:
        file_content = f.read()
        file_mas = file_content.split()
    user_input = ""
    answer_correction = True
    content = ""
    # print(file_mas)
    for i in range(len(file_mas)):
        if file_mas[i][-1] == "Q":
            user_input = ""
        elif file_mas[i][-1] == "A":
            process = subprocess.Popen(['python', file_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(input=user_input.encode())
            output = stdout.decode()

            if output[:-2] != file_mas[i + 1]:
                answer_correction = False
                # print(output)
            if not output:
                content = stderr.decode()
                if not content:
                    content = file_mas[i + 1]
                # print(stderr.decode())
        else:
            user_input += file_mas[i] + "\n"
    if answer_correction:
        content = "Программа работает верно"
    else:
        a = content
        content = f"После прохождения тест-кейса №{a}, была обнаружена ошибка"
    return content


@app.route('/profile')
def profile():
    return render_template('profile.html')


if __name__ == '__main__':
    app.run(debug=True)
