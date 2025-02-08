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


class DB_Task(DB):
    def get_task_by_id(self, task_id):
        conn = self.get_db_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT title, task, input_data, output_data 
                        FROM lessons
                    """, (task_id,))
                    task = cur.fetchone()
                    return dict(task) if task else None
            except Exception as e:
                print(f"Ошибка при получении задачи: {e}")
                return None
            finally:
                conn.close()
        return None


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
        finally:
            if conn and not conn.closed:
                conn.close()

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