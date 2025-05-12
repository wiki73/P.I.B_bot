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