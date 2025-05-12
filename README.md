# 📋Проект: Telegram-бот для ежедневного планирования

## 🔍 Общее описание
Это Telegram-бот, созданный для ежедневного планирования задач, который работает как в личных чатах, так и в группах.

Цель: упрощенное создание, выбор, редактирование и публикация планов.

---

## 🔢 Структура проекта

- **bot.py** — основная логика бота.
- **database.py** — работа с базой данных SQLite.

---

## ⚡ Функции и привязка к коду

### 🔸 Регистрация имени пользователя
- `process_nickname` — ввод и сохранение имени.
- `save_user_name` — запись в базу.

### 🔸 Создание нового плана
- `create_plan_command` — запуск процесса.
- `process_plan_title` — ввод заголовка.
- `process_plan_tasks` — ввод списка задач.
- `confirm_plan` — подтверждение.
- `save_user_plan` — сохранение в БД.

### 🔸 Просмотр планов
- `view_plans_command` — меню выбора.
- `handle_show_base_plans`, `handle_show_user_plans` — показ планов.
- `get_base_plan`, `get_user_plan` — запрос в БД.

### 🔸 Установка текущего плана
- `handle_plan_action` — выбор плана.
- `update_user_current_plan` — запись в БД.

### 🔸 Публикация плана в группе
- `new_day_group` — старт дня.
- `start_command` — deep link в личку.
- `publish_plan` — отправка в группу.

### 🔸 Редактирование и отметка задач
- `edit_task`, `process_task_edit` — изменение текста.
- `start_marking_tasks`, `toggle_task_mark` — отметка задач.
- `task_comments_handler`, `process_comment` — добавление комментариев.

---

## 📂 Структура базы данных
- `users`
- `base_plans`
- `user_plans`
- `group_plans`
- `current_plans`

(Создание: `create_tables`)

---

## 🔧 Используемые библиотеки
- **aiogram** — Telegram бот API.
- **sqlite3** — локальная БД.
- **dotenv** — чтение .env.
- **logging** — логирование.

---

## 📅 Что можно улучшить
- Сделать категории задач.
- Сохранять прогресс завершения.
- Добавить ремайндеры (уведомления).

---

=======
# PlanItBot - Telegram бот для планирования

## Настройка окружения (Linux)

### 1. Установка необходимых пакетов
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Клонирование репозитория
```bash
git clone https://github.com/your-username/PlanItBot.git
cd PlanItBot
```

### 3. Создание и активация виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 5. Настройка конфигурации
Создайте файл `.env` в корневой директории проекта:
```bash
touch .env
```

Добавьте в файл `.env` следующие строки:
```
TOKEN=your_bot_token_here
LOG_LEVEL=INFO
```

### 6. Запуск бота
```bash
python3 bot.py
```

## Использование

1. Получите токен для вашего бота у [@BotFather](https://t.me/BotFather)
2. Вставьте полученный токен в файл `.env`
3. Запустите бота

## Основные команды бота

- `/start` - Начало работы с ботом
- `/help` - Показать справку
- `/info` - Информация о планировании
- `/create_plan` - Создать новый план
- `/view_plans` - Просмотр планов

## Групповые команды

- `/new_day` - Начать новый день
- `/static` - Просмотр статистики

## Требования

- Python 3.7+
- Все необходимые библиотеки указаны в `requirements.txt` 