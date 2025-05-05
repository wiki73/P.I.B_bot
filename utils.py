import aiohttp
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

async def get_forismatic_quote(lang: str = "ru") -> str:
    """Получает случайную цитату с Forismatic API"""
    url = "http://api.forismatic.com/api/1.0/"
    params = {
        "method": "getQuote",
        "format": "json",
        "lang": lang
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                quote_text = data.get("quoteText", "").strip()
                quote_author = data.get("quoteAuthor", "").strip()
                
                if quote_author:
                    return f"\n\n💬 «{quote_text}» — {quote_author}"
                return f"\n\n💬 «{quote_text}»"
    except Exception as e:
        print(f"Ошибка при запросе к Forismatic: {e}")
        return ""