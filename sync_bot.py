import os
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Загружаем токены из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

def ask_chatgpt(user_message: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты — добрый и поддерживающий психолог. Отвечай мягко, с сочувствием, без медицинских диагнозов."},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content.strip()

@dp.message_handler()
async def handle_message(message: types.Message):
    user_text = message.text
    await message.chat.do("typing")

    try:
        reply = ask_chatgpt(user_text)
        await message.reply(reply)
    except Exception as e:
        await message.reply("Извини, произошла ошибка при подключении к ИИ.")
        print("OpenAI error:", e)

if __name__ == '__main__':
    executor.start_polling(dp)
