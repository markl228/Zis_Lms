import psycopg2
from psycopg2.extras import DictCursor

DB_CONFIG = {
    'dbname': 'LLMMSS',
    'user': 'postgres',
    'password': 'q1w2e3r4t5!',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Подключение к базе данных успешно установлено")
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

def get_task_by_id(task_id):
    conn = get_db_connection()
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