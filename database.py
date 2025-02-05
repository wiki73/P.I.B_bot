import sqlite3

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Функция для создания таблиц
def create_tables():
    conn = sqlite3.connect('user_plans.db')
    cursor = conn.cursor()



    # Создаем новую таблицу без ограничения уникальности на user_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan TEXT NOT NULL
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
    # Подключаемся к базе данных
    conn = sqlite3.connect('user_plans.db')
    cursor = conn.cursor()

    # Извлекаем план пользователя
    cursor.execute('SELECT plan FROM user_plans WHERE user_id = ?', (user_id,))
    result = cursor.fetchall()
    conn.close()

    if result:
        return result  # Возвращаем текст планов
    return None  # Если плана нет, возвращаем None

# Функция для сохранения плана пользователя
def save_user_plan(user_id, plan_text):
    # Подключаемся к базе данных
    conn = sqlite3.connect('user_plans.db')
    cursor = conn.cursor()

    # Сохраняем новый план в таблице
    cursor.execute('''INSERT INTO user_plans (user_id, plan) VALUES (?, ?)''', (user_id, plan_text))

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()
