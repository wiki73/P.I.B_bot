import sqlite3
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect('plans.db')
    conn.row_factory = sqlite3.Row  # Для доступа к полям по именам
    try:
        yield conn
    finally:
        conn.close()

def create_tables():
    """Создание всех таблиц при первом запуске"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Пользователи
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            registration_date TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Базовые планы
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS base_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            plan_text TEXT NOT NULL
        )''')
        
        # Пользовательские планы
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            plan_text TEXT NOT NULL,
            creation_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, name)
        )''')
        
        # Текущие планы
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_plans (
            user_id INTEGER PRIMARY KEY,
            plan_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # Добавляем демо-планы, если таблица пуста
        if not cursor.execute('SELECT 1 FROM base_plans LIMIT 1').fetchone():
            default_plans = [
                ("Стандартный день", "Утро:\n- Зарядка\n- Завтрак\n\nРабота:\n- Важные задачи\n- Встречи\n\nВечер:\n- Отдых\n- Подготовка к следующему дню"),
                ("Продуктивный день", "Утро:\n- Медитация\n- Планирование дня\n\nРабота:\n- Сложные задачи\n- Обучение\n\nВечер:\n- Анализ дня\n- Чтение"),
                ("Выходной день", "Утро:\n- Долгий завтрак\n- Прогулка\n\nДень:\n- Хобби\n- Встречи с друзьями\n\nВечер:\n- Кино\n- Ранний сон")
            ]
            cursor.executemany('INSERT INTO base_plans (name, plan_text) VALUES (?, ?)', default_plans)
        
        conn.commit()
# Пользователи
def get_user_name(user_id: int) -> Optional[str]:
    """Получить имя пользователя по ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result['name'] if result else None

def save_user_name(user_id: int, name: str):
    """Сохранить или обновить имя пользователя"""
    with get_db_connection() as conn:
        conn.execute('INSERT OR REPLACE INTO users (user_id, name) VALUES (?, ?)', (user_id, name))
        conn.commit()

# Базовые планы
def get_base_plan() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, plan_text FROM base_plans')
        return [dict(row) for row in cursor.fetchall()]

def get_plan_name_by_id(plan_id: int) -> Optional[str]:
    """Получить название плана по ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM base_plans WHERE id = ?', (plan_id,))
        result = cursor.fetchone()
        return result['name'] if result else None

# Пользовательские планы
def save_user_plan(user_id: int, plan_name: str, plan_text: str):
    """Сохранить пользовательский план"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO user_plans (user_id, name, plan_text) VALUES (?, ?, ?)',
                (user_id, plan_name, plan_text)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Если план с таким именем уже существует для пользователя
            raise ValueError("План с таким именем уже существует")

def get_user_plan(user_id: int) -> List[Dict[str, Any]]:
    """Получить все планы пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, plan_text FROM user_plans WHERE user_id = ?', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

# Текущие планы
def update_user_current_plan(user_id: int, plan_name: str):
    """Установить текущий план для пользователя"""
    with get_db_connection() as conn:
        conn.execute(
            'INSERT OR REPLACE INTO current_plans (user_id, plan_name) VALUES (?, ?)',
            (user_id, plan_name)
        )
        conn.commit()

def get_current_plan(user_id: int) -> Optional[str]:
    """Получить текущий план пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT plan_name FROM current_plans WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result['plan_name'] if result else None

# Поиск плана
def get_plan_text_by_name(plan_name: str) -> Optional[str]:
    """Получить текст плана по названию (ищет в базовых и пользовательских)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Сначала проверяем базовые планы
        cursor.execute('SELECT plan_text FROM base_plans WHERE name = ?', (plan_name,))
        result = cursor.fetchone()
        
        if not result:
            # Затем проверяем пользовательские планы
            cursor.execute('SELECT plan_text FROM user_plans WHERE name = ?', (plan_name,))
            result = cursor.fetchone()
        
        return result['plan_text'] if result else None