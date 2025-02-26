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

    def get_teacher_groups(self, teacher_id):
        conn = None
        try:
            conn = self.get_db_connection()
            if conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT g.id_grouppa, g.name_gr,
                               COUNT(DISTINCT g.id_student) as student_count,
                               COUNT(DISTINCT c.id) as course_count
                        FROM grouppa g
                        LEFT JOIN courses_students cs ON g.id_grouppa = cs.id_grouppa
                        LEFT JOIN courses c ON cs.id_course = c.id
                        WHERE g.id_teacher = %s
                        GROUP BY g.id_grouppa, g.name_gr
                        ORDER BY g.name_gr
                    """, (teacher_id,))
                    groups = cur.fetchall()
                    return [dict(group) for group in groups] if groups else []
        except Exception as e:
            print(f"Ошибка при получении групп преподавателя: {e}")
            return []
        finally:
            if conn and not conn.closed:
                conn.commit()
        return []

    def get_student_progress(self, student_id):
        conn = None
        try:
            conn = self.get_db_connection()
            if conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT c.id as course_id,
                               COALESCE(
                                   (COUNT(DISTINCT cp.lesson_id) * 100.0 / 
                                    NULLIF(COUNT(DISTINCT l.id), 0)
                                   ), 0
                               ) as progress
                        FROM courses c
                        LEFT JOIN lessons l ON c.id = l.course_id
                        LEFT JOIN course_progress cp ON l.id = cp.lesson_id 
                            AND cp.student_id = %s
                        GROUP BY c.id
                    """, (student_id,))
                    progress = cur.fetchall()
                    return {row['course_id']: int(row['progress']) 
                            for row in progress} if progress else {}
        except Exception as e:
            print(f"Ошибка при получении прогресса студента: {e}")
            return {}
        finally:
            if conn and not conn.closed:
                conn.commit()
        return {}

    def get_student_notifications(self, student_id):
        conn = None
        try:
            conn = self.get_db_connection()
            if conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT n.id, n.message, n.created_at as date,
                               n.type, n.is_read
                        FROM notifications n
                        WHERE n.student_id = %s
                        ORDER BY n.created_at DESC
                        LIMIT 10
                    """, (student_id,))
                    notifications = cur.fetchall()
                    return [dict(notif) for notif in notifications] if notifications else []
        except Exception as e:
            print(f"Ошибка при получении уведомлений студента: {e}")
            return []
        finally:
            if conn and not conn.closed:
                conn.commit()
        return []

    def get_pending_assignments(self, teacher_id):
        conn = None
        try:
            conn = self.get_db_connection()
            if conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT l.id, l.task as description,
                               l.title,
                               u.email as student_name,
                               c.title as course_title
                        FROM lessons l
                        JOIN courses c ON l.course_id = c.id
                        JOIN users u ON c.teacher_id = u.id
                        WHERE c.teacher_id = %s
                        ORDER BY l.id ASC
                    """, (teacher_id,))
                    assignments = cur.fetchall()
                    return [dict(assignment) for assignment in assignments] if assignments else []
        except Exception as e:
            print(f"Ошибка при получении заданий на проверку: {e}")
            return []
        finally:
            if conn and not conn.closed:
                conn.commit()
        return []

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
