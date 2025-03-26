import sqlite3
from typing import Optional, List, Tuple

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('bd.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создание таблиц при первом запуске
def create_tables():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            registration_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица базовых планов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS base_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            plan_text TEXT NOT NULL
        )
        ''')
        
        # Таблица пользовательских планов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            plan_text TEXT NOT NULL,
            creation_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Таблица текущих планов пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_plans (
            user_id INTEGER PRIMARY KEY,
            plan_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Добавляем базовые планы, если их нет
        cursor.execute('SELECT COUNT(*) FROM base_plans')
        if cursor.fetchone()[0] == 0:
            default_plans = [
                ("Стандартный день", "Утро:\n- Зарядка\n- Завтрак\n\nРабота:\n- Важные задачи\n- Встречи\n\nВечер:\n- Отдых\n- Подготовка к следующему дню"),
                ("Продуктивный день", "Утро:\n- Медитация\n- Планирование дня\n\nРабота:\n- Сложные задачи\n- Обучение\n\nВечер:\n- Анализ дня\n- Чтение"),
                ("Выходной день", "Утро:\n- Долгий завтрак\n- Прогулка\n\nДень:\n- Хобби\n- Встречи с друзьями\n\nВечер:\n- Кино\n- Ранний сон")
            ]
            cursor.executemany('INSERT INTO base_plans (name, plan_text) VALUES (?, ?)', default_plans)
        
        conn.commit()

# Работа с пользователями
def get_user_name(user_id: int) -> Optional[str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result['name'] if result else None

def save_user_name(user_id: int, name: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO users (user_id, name) VALUES (?, ?)',
            (user_id, name)
        )
        conn.commit()

# Работа с базовыми планами
def get_base_plan() -> List[Tuple]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, plan_text FROM base_plans')
        return cursor.fetchall()

def get_plan_name_by_id(plan_id: int) -> Optional[str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM base_plans WHERE id = ?', (plan_id,))
        result = cursor.fetchone()
        return result['name'] if result else None

# Работа с пользовательскими планами
def save_user_plan(user_id: int, plan_name: str, plan_text: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO user_plans (user_id, name, plan_text) VALUES (?, ?, ?)',
            (user_id, plan_name, plan_text)
        )
        conn.commit()

def get_user_plan(user_id: int) -> List[Tuple]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, plan_text FROM user_plans WHERE user_id = ?', (user_id,))
        return cursor.fetchall()

# Работа с текущими планами
def update_user_current_plan(user_id: int, plan_name: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO current_plans (user_id, plan_name) VALUES (?, ?)',
            (user_id, plan_name)
        )
        conn.commit()

def get_current_plan(user_id: int) -> Optional[str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT plan_name FROM current_plans WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result['plan_name'] if result else None

# Поиск плана по имени
def get_plan_text_by_name(plan_name: str) -> Optional[str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Сначала ищем в базовых планах
        cursor.execute('SELECT plan_text FROM base_plans WHERE name = ?', (plan_name,))
        result = cursor.fetchone()
        
        if not result:
            # Если не нашли в базовых, ищем в пользовательских
            cursor.execute('SELECT plan_text FROM user_plans WHERE name = ?', (plan_name,))
            result = cursor.fetchone()
        
        return result['plan_text'] if result else None