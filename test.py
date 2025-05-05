import logging
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from pathlib import Path
import os
import socket

# Проверка доступности хоста перед запуском
def check_host(hostname):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False

# Загрузка переменных окружения
load_dotenv(Path(".env"))

# Проверка переменных
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле!")

API_KEY = os.getenv("STABLE_DIFFUSION_API_KEY")
if not API_KEY:
    raise ValueError("❌ STABLE_DIFFUSION_API_KEY не найден в .env файле!")

# Проверка доступности API хоста
API_HOST = "api.stablediffusionapi.com"
if not check_host(API_HOST):
    raise ConnectionError(f"❌ Не удалось разрешить имя хоста {API_HOST}")

API_URL = f"https://{API_HOST}/v1/text2img"

# Настройка бота с безопасным parse_mode
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Безопасный вывод ошибок
def safe_error_text(error: Exception) -> str:
    return str(error).replace("<", "&lt;").replace(">", "&gt;")

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 <b>Генератор изображений</b>\n"
        "Отправь /generate описание или просто текст"
    )

async def process_generation(message: Message, prompt: str):
    try:
        wait_msg = await message.answer("🔄 Генерация...")
        
        response = requests.post(
            API_URL,
            json={
                "key": API_KEY,
                "prompt": prompt,
                "width": 512,
                "height": 512,
                "samples": 1
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                await message.answer_photo(
                    photo=data["output"][0],
                    caption=f"🎨 <b>{prompt}</b>"
                )
            else:
                await message.answer(f"❌ API: {data.get('message', 'Unknown error')}")
        else:
            await message.answer(f"❌ HTTP {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        await message.answer("❌ Ошибка соединения с API")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await message.answer(f"❌ Ошибка: {safe_error_text(e)}")
    finally:
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id
            )
        except:
            pass

@dp.message(Command("generate"))
async def generate_cmd(message: Message):
    prompt = message.text.split("/generate", 1)[-1].strip()
    if prompt:
        await process_generation(message, prompt)
    else:
        await message.answer("❌ Укажите описание после /generate")

@dp.message(F.text & ~F.text.startswith("/"))
async def generate_text(message: Message):
    await process_generation(message, message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())