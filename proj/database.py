import psycopg2
from psycopg2.extras import DictCursor
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_CONFIG = {
    'dbname': 'LLMMSS',
    'user': 'postgres',
    'password': 'q1w2e3r4t5!',
    'host': 'localhost',
    'port': '5432'
}

class DB():
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
    
    def get_db_connection(self):
        try:
            print("Подключение к базе данных успешно установлено")
            return self.conn
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return None

    def close_connection(self):
        if self.conn and not self.conn.closed:
            self.conn.close()


class DB_Task(DB):
    def get_task_by_id(self, id_course, id_task):
        conn = self.get_db_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT title, task, input_data, output_data 
                        FROM lessons
                        WHERE course_id = %s AND id = %s;
                    """, (id_course, id_task))
                    task = cur.fetchone()
                    return dict(task) if task else None
            except Exception as e:
                print(f"Ошибка при получении задачи: {e}")
                return None
        return None

    def get_all_courses(self):
        conn = self.get_db_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT id, title, description 
                        FROM courses
                    """)
                    courses = cur.fetchall()
                    return [dict(course) for course in courses] if courses else []
            except Exception as e:
                print(f"Ошибка при получении курсов: {e}")
                return []
            
    
    def get_lessons_by_course_id(self, course_id):
        conn = self.get_db_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT id, course_id, title
                        FROM lessons 
                        WHERE course_id = %s
                        ORDER BY id
                    """, (course_id,))
                    lessons = cur.fetchall()
                    return [dict(lesson) for lesson in lessons] if lessons else []
            except Exception as e:
                print(f"Ошибка при получении уроков курса: {e}")
                return []
        return []


class DB_User(DB):
    def get_user(self, username):
        conn = None
        try:
            conn = self.get_db_connection()
            if conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute('SELECT * FROM users WHERE email = %s;', (username,))
                    user = cur.fetchone()
                    return user
        except Exception as e:
            print(f"Ошибка при получении пользователя: {e}")
            return None

    def verify_user(self, username, password):
        try:
            user = self.get_user(username)
            if user and (user[3] == password):
                print(user)
                return user
            return None
        except Exception as e:
            print(f"Ошибка при верификации пользователя: {e}")
            return None

class DB_Create_Task(DB):
    def create_task(self, title, task, test_case):
        conn = None
        try:
            conn = self.get_db_connection()
            if conn:
                with conn.cursor() as cur:
                    # Создаем новую задачу
                    cur.execute("""
                        INSERT INTO tasks (title, task, input_data, output_data, test_case) 
                        VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """, (title, task, input_data, output_data, test_case))
                    
                    task_id = cur.fetchone()[0]
                    
                    # Добавляем тест-кейсы
                    for input_data, output_data in test_case:
                        cur.execute("""
                            INSERT INTO test_cases (task_id, input_data, output_data)
                            VALUES ($1, $2, $3
                                    )
                        """, (task_id, input_data, output_data))
                    
                    conn.commit()
                    return task_id
        except Exception as e:
            print(f"Ошибка при создании задачи: {e}")
            if conn:
                conn.rollback()
            return None
