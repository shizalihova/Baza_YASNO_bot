# bot.py
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
import asyncio
import logging
from modules import dp, set_commands, get_from_env  # Импорты из пакета modules

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telegram_bot")

# Создание объектов бота и диспетчера
token = get_from_env("TG_BOT_TOKEN")
bot = Bot(token)

# Основная функция запуска бота
async def main():
    try:
        await set_commands(bot)
        logger.info("Бот запущен и готов к работе.")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())