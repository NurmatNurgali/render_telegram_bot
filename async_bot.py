import asyncio
import logging
import os

import openai
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    filters,
    MessageHandler,
)

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные окружения
URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 8000))
TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

openai.api_key = OPENAI_API_KEY

USE_WEBHOOK = URL is not None
logger.info("Running in %s mode", "webhook" if USE_WEBHOOK else "polling")


async def ask_chatgpt(user_message: str) -> str:
    try:
        response = await openai.chat.completions.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — добрый и поддерживающий психолог."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("OpenAI API error", exc_info=True)
        return "Извини, произошла ошибка при подключении к ИИ."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message.text if update.message else None

    if not message:
        logger.warning("Received update without text message")
        return

    logger.info("Received message from %s: %s", user.username or user.id, message)

    reply = await ask_chatgpt(message)
    await update.message.reply_text(reply)


async def main() -> None:
    if USE_WEBHOOK:
        logger.info("Starting webhook mode with URL: %s", URL)
        application = Application.builder().token(TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        await application.bot.set_webhook(url=f"{URL}/telegram")

        async def telegram(request: Request) -> Response:
            data = await request.json()
            await application.update_queue.put(Update.de_json(data, application.bot))
            return Response()

        async def health(_: Request) -> PlainTextResponse:
            return PlainTextResponse("Bot is running!")

        app = Starlette(
            routes=[
                Route("/telegram", telegram, methods=["POST"]),
                Route("/healthcheck", health, methods=["GET"]),
            ]
        )

        config = uvicorn.Config(app=app, port=PORT, host="0.0.0.0")
        server = uvicorn.Server(config)

        async with application:
            await application.start()
            await server.serve()
            await application.stop()
    else:
        logger.info("Starting polling mode for local development")
        application = Application.builder().token(TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        async with application:
            await application.start()
            await application.updater.start_polling()
            logger.info("Bot started! Send a message to test it.")

            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                pass
            finally:
                await application.updater.stop()
                await application.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Bot failed to start: %s", e)
        raise
