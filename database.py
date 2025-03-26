import sqlite3

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect('bd.db')
    conn.row_factory = sqlite3.Row
    return conn

# Функция для создания таблиц
def create_tables():
    """Создает таблицы в базе данных, если они не существуют."""
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()

    # Создаем таблицу user_plans
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        plan TEXT NOT NULL)''')

    # Создаем таблицу users
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        user_name TEXT NOT NULL,
        current_plan TEXT)''')

    # Создаем таблицу base_plans
    cursor.execute('''CREATE TABLE IF NOT EXISTS base_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_plan TEXT NOT NULL,
        text_plan TEXT NOT NULL)''')

    conn.commit()
    conn.close()

# Функция для получения имени пользователя из базы данных
def get_user_name(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT user_name FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.Error as e:
        return None
# Функция для сохранения имени пользователя в базе данных
def save_user_name(user_id, user_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users (user_id, user_name) VALUES (?, ?)', (user_id, user_name))
    conn.commit()
    conn.close()

# Функция для получения плана пользователя
def get_user_plan(user_id):
    # Подключаемся к базе данных
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()

    # Извлекаем план пользователя
    cursor.execute('SELECT plan, name_plan FROM user_plans WHERE user_id = ?', (user_id,))
    result = cursor.fetchall()
    conn.close()

    if result:
        return result  # Возвращаем текст планов
    return None  # Если плана нет, возвращаем None

def get_base_plan():
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()

    # Извлекаем план пользователя
    cursor.execute('SELECT text_plan, name_plan FROM base_plans ')
    result = cursor.fetchall()
    conn.close()
    if result:
        return result  # Возвращаем текст планов
    return None  # Если плана нет, возвращаем None

# Функция для сохранения плана пользователя
def save_user_plan(user_id,name_plan, plan_text):
    try:
        conn = sqlite3.connect('bd.db')
        cursor = conn.cursor()
        user_name = get_user_name(user_id)
        # Сохраняем новый план в таблице
        cursor.execute('''
            INSERT INTO user_plans (user_id, user_name, name_plan, plan) VALUES (?, ?, ?, ?)
        ''', (user_id, user_name, name_plan, plan_text))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении плана: {e}")
    finally:
        conn.close()

# Функция для получения name_plan по id
def get_plan_name_by_id(plan_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name_plan FROM base_plans WHERE id = ?', (plan_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Функция для обновления current_plan в таблице users
def update_user_current_plan(user_id, plan_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET current_user_plan = ? WHERE user_id = ?', (plan_name, user_id))
    conn.commit()
    conn.close()

# Функция для получения текущего плана пользователя
def get_current_plan(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT current_user_plan FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_plan_text_by_name(plan_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT text_plan FROM base_plans WHERE name_plan = ?', (plan_name,))
    result = cursor.fetchone()
    if not result:
        cursor.execute('SELECT plan FROM user_plans WHERE name_plan = ?', (plan_name,))
        result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

