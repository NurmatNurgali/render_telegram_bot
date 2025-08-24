import os
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command

# Загружаем токены из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Проверка на наличие токенов
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Настройка OpenAI
openai.api_key = OPENAI_API_KEY

# Функция общения с ChatGPT
def ask_chatgpt(message_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Можно заменить на "gpt-4", если у тебя есть доступ
        messages=[
            {"role": "system", "content": "Ты — добрый и поддерживающий психолог. Помогай мягко и с сочувствием. Не давай медицинских советов."},
            {"role": "user", "content": message_text}
        ]
    )
    return response.choices[0].message.content.strip()

# Обработка входящих сообщений
@dp.message_handler()
async def handle_message(message: types.Message):
    user_input = message.text
    await message.chat.do("typing")  # показывает, что бот "печатает"

    try:
        reply = ask_chatgpt(user_input)
        await message.reply(reply)
    except Exception as e:
        await message.reply("Произошла ошибка при обращении к ИИ.")
        print("OpenAI error:", e)

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp)
