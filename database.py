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
            plan_name TEXT NOT NULL,
            plan_text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_public BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # Планы групп
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES user_plans(id),
            UNIQUE(group_id, plan_id)
        )''')
        
        # Текущие планы
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_plans (
            user_id INTEGER PRIMARY KEY,
            plan_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # Статистика выполнения планов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            group_id INTEGER,
            date TEXT NOT NULL,
            total_tasks INTEGER NOT NULL,
            completed_tasks INTEGER NOT NULL,
            plan_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )''')
        
        # Таблица статистики
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_tasks_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            group_id INTEGER,
            completed_tasks INTEGER NOT NULL,
            date TEXT DEFAULT CURRENT_DATE,
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
def save_user_plan(user_id: int, name: str, text: str):
    """Сохраняет пользовательский план"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO user_plans (user_id, plan_name, plan_text) VALUES (?, ?, ?)',
            (user_id, name, text)
        )
        conn.commit()

def get_user_plan(user_id: int) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, plan_name as name, plan_text 
            FROM user_plans 
            WHERE user_id = ?
        ''', (user_id,))
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
            cursor.execute('SELECT plan_text FROM user_plans WHERE plan_name = ?', (plan_name,))
            result = cursor.fetchone()
        
        return result['plan_text'] if result else None

def save_public_plan(group_id: int, user_id: int, name: str, text: str):
    """Сохраняет публичный план для группы"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO public_plans 
            (group_id, user_id, plan_name, plan_text) 
            VALUES (?, ?, ?, ?)''',
            (group_id, user_id, name, text)
        )
        conn.commit()

def get_active_group_plan(group_id: int) -> Optional[dict]:
    """Получает активный план группы"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.name as username 
            FROM public_plans p
            JOIN users u ON p.user_id = u.user_id
            WHERE group_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (group_id,))
        return cursor.fetchone()

def delete_user_plan(user_id: int, plan_id: int) -> bool:
    """Удаляет пользовательский план
    
    Args:
        user_id (int): ID пользователя
        plan_id (int): ID плана
        
    Returns:
        bool: True если план успешно удален, False если план не найден или не принадлежит пользователю
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Проверяем, существует ли план и принадлежит ли он пользователю
        cursor.execute(
            'SELECT 1 FROM user_plans WHERE id = ? AND user_id = ?',
            (plan_id, user_id)
        )
        if not cursor.fetchone():
            return False
            
        # Если это текущий план пользователя, удаляем его из current_plans
        cursor.execute(
            '''DELETE FROM current_plans 
               WHERE user_id = ? AND plan_name IN 
               (SELECT plan_name FROM user_plans WHERE id = ?)''',
            (user_id, plan_id)
        )
        
        # Удаляем сам план
        cursor.execute('DELETE FROM user_plans WHERE id = ?', (plan_id,))
        conn.commit()
        return True

# Функции для работы со статистикой
def save_plan_statistics(user_id: int, group_id: int | None, plan_name: str, total_tasks: int, completed_tasks: int):
    """Сохраняет статистику выполнения плана"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO plan_statistics 
            (user_id, group_id, date, total_tasks, completed_tasks, plan_name)
            VALUES (?, ?, date('now'), ?, ?, ?)''',
            (user_id, group_id, total_tasks, completed_tasks, plan_name)
        )
        conn.commit()

def get_user_statistics(user_id: int) -> List[Dict[str, Any]]:
    """Получает статистику пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, total_tasks, completed_tasks, plan_name
            FROM plan_statistics
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT 7
        ''', (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_group_statistics(group_id: int) -> List[Dict[str, Any]]:
    """Получает статистику группы"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                ps.date,
                SUM(ps.total_tasks) as total_tasks,
                SUM(ps.completed_tasks) as completed_tasks,
                COUNT(DISTINCT ps.user_id) as users_count,
                ROUND(AVG(CAST(ps.completed_tasks AS FLOAT) / ps.total_tasks * 100), 2) as avg_completion
            FROM plan_statistics ps
            WHERE ps.group_id = ?
            GROUP BY ps.date
            ORDER BY ps.date DESC
            LIMIT 7
        ''', (group_id,))
        return [dict(row) for row in cursor.fetchall()]

def save_completed_tasks(user_id: int | None, group_id: int | None, completed_tasks: int):
    """Сохраняет количество выполненных задач"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO completed_tasks_stats 
            (user_id, group_id, completed_tasks)
            VALUES (?, ?, ?)''',
            (user_id, group_id, completed_tasks)
        )
        conn.commit()

def get_user_completed_tasks(user_id: int) -> int:
    """Получает общее количество выполненных задач пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(completed_tasks) as total
            FROM completed_tasks_stats
            WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result['total'] if result['total'] is not None else 0

def get_group_completed_tasks(group_id: int) -> dict:
    """Получает статистику выполненных задач в группе"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Добавляем логирование для отладки
        print(f"Получаем статистику для группы {group_id}")
        cursor.execute('''
            SELECT 
                SUM(completed_tasks) as total_completed,
                COUNT(DISTINCT user_id) as unique_users,
                MAX(date) as last_update
            FROM completed_tasks_stats
            WHERE group_id = ?
            GROUP BY group_id
        ''', (group_id,))
        result = cursor.fetchone()
        
        # Добавляем логирование результата
        print(f"Результат запроса: {result}")
        
        if result is None:
            return {
                'total_completed': 0,
                'unique_users': 0,
                'last_update': None
            }
            
        return {
            'total_completed': result['total_completed'],
            'unique_users': result['unique_users'],
            'last_update': result['last_update']
        }