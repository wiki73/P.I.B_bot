import sqlite3

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Функция для создания таблиц
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        user_name TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plans (
        user_id INTEGER,
        plan_type TEXT,
        PRIMARY KEY (user_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    conn.commit()
    conn.close()

# Функция для получения имени пользователя из базы данных
def get_user_name(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_name FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Функция для сохранения имени пользователя в базе данных
def save_user_name(user_id, user_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users (user_id, user_name) VALUES (?, ?)', (user_id, user_name))
    conn.commit()
    conn.close()

# Функция для получения плана пользователя
def get_user_plan(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT plan_type FROM plans WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Функция для сохранения плана пользователя
def save_user_plan(user_id, plan_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO plans (user_id, plan_type) VALUES (?, ?)', (user_id, plan_type))
    conn.commit()
    conn.close() 