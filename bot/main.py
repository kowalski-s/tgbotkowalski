"""
Главный файл для запуска Telegram бота
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import config
from bot.database import Database
from bot.handlers import main_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, db: Database):
    """
    Функция, которая выполняется при запуске бота
    """
    logger.info("🚀 Бот запускается...")

    # Подключаемся к базе данных
    await db.connect()

    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"✅ Бот запущен: @{bot_info.username}")
    logger.info(f"📊 База данных: {config.database_path}")

    # Уведомляем администратора о запуске
    try:
        await bot.send_message(
            chat_id=config.admin_id,
            text="🤖 <b>Бот успешно запущен!</b>\n\n"
                 f"ID бота: <code>{bot_info.id}</code>\n"
                 f"Username: @{bot_info.username}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление администратору: {e}")


async def on_shutdown(bot: Bot, db: Database):
    """
    Функция, которая выполняется при остановке бота
    """
    logger.info("🛑 Бот останавливается...")

    # Отключаемся от базы данных
    await db.disconnect()

    # Уведомляем администратора об остановке
    try:
        await bot.send_message(
            chat_id=config.admin_id,
            text="⚠️ <b>Бот остановлен</b>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление администратору: {e}")

    logger.info("✅ Бот остановлен")


async def main():
    """
    Главная функция для запуска бота
    """
    try:
        # Создаем экземпляр бота
        bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        # Создаем диспетчер
        dp = Dispatcher()

        # Подключаем роутеры
        dp.include_router(main_router)

        # Создаем экземпляр базы данных
        db = Database(config.database_path)

        # Регистрируем middleware для передачи db в обработчики
        @dp.update.outer_middleware()
        async def db_middleware(handler, event, data):
            """Middleware для передачи database в обработчики"""
            data["db"] = db
            return await handler(event, data)

        # Запускаем функцию при старте
        await on_startup(bot, db)

        # Запускаем polling (бесконечный опрос обновлений)
        try:
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True  # Пропускаем накопившиеся обновления
            )
        finally:
            # Выполняем при остановке
            await on_shutdown(bot, db)
            await bot.session.close()

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}", exc_info=True)
        sys.exit(1)
