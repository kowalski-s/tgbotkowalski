"""
Обработчик команды /start и проверки подписки
"""
import logging
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest

from bot.config import config
from bot.database import Database
from bot.keyboards import get_subscription_keyboard
from bot.utils import check_user_subscription

logger = logging.getLogger(__name__)

# Создаем роутер для этого модуля
router = Router()


async def send_materials(message: Message, db: Database, user_id: int):
    """
    Вспомогательная функция для отправки материалов пользователю

    Args:
        message: Сообщение для ответа
        db: База данных
        user_id: ID пользователя
    """
    # Отправляем ссылку на статью
    await message.answer(
        f"📄 Статья: {config.article_link}"
    )

    # Отправляем PDF файл
    try:
        if os.path.exists(config.pdf_file_path):
            pdf_file = FSInputFile(config.pdf_file_path)
            await message.answer_document(
                document=pdf_file,
                caption="📎 Бонусный материал в формате PDF"
            )
            # Отмечаем в БД, что файл отправлен
            await db.mark_file_received(user_id)
            logger.info(f"✅ PDF файл отправлен пользователю {user_id}")
        else:
            logger.error(f"❌ PDF файл не найден: {config.pdf_file_path}")
            await message.answer(
                "⚠️ К сожалению, файл временно недоступен. Обратитесь к администратору."
            )
    except Exception as e:
        logger.error(f"❌ Ошибка отправки PDF: {e}")
        await message.answer(
            "⚠️ Произошла ошибка при отправке файла. Попробуйте позже."
        )

    # Отправляем сообщение о работе
    await message.answer(config.work_with_me_message)


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """
    Обработчик команды /start

    1. Добавляем пользователя в БД
    2. Проверяем подписку
    3. Если подписан - сразу выдаем материалы
    4. Если нет - показываем кнопки подписки
    """
    user = message.from_user

    # Добавляем/обновляем пользователя в БД
    await db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")

    # Проверяем, подписан ли уже пользователь
    is_subscribed = await check_user_subscription(
        bot=message.bot,
        user_id=user.id,
        channel_id=config.channel_id,
    )

    if is_subscribed:
        # Пользователь УЖЕ подписан - сразу выдаем материалы
        logger.info(f"✅ Пользователь {user.id} уже подписан, выдаем материалы")

        # Обновляем БД
        await db.update_user_subscription(user.id, is_subscribed=True)

        # Отправляем приветствие
        await message.answer(
            "Привет! 👋\n\n"
            "Вижу, ты уже подписан на канал - отлично!\n"
            "Вот обещанные материалы:"
        )

        # Выдаем материалы
        await send_materials(message, db, user.id)

    else:
        # Пользователь НЕ подписан - показываем кнопки
        logger.info(f"❌ Пользователь {user.id} не подписан, показываем кнопки")

        keyboard = get_subscription_keyboard(config.channel_link)

        await message.answer(
            text=config.welcome_message,
            reply_markup=keyboard,
        )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, db: Database):
    """
    Обработчик нажатия на кнопку "Я подписался"

    1. Проверяем подписку через Bot API
    2. Если подписан - выдаем материалы
    3. Если нет - просим подписаться
    """
    user_id = callback.from_user.id

    # Показываем, что бот обрабатывает запрос
    await callback.answer("Проверяю подписку... ⏳", show_alert=False)

    # Проверяем подписку
    is_subscribed = await check_user_subscription(
        bot=callback.bot,
        user_id=user_id,
        channel_id=config.channel_id,
    )

    if is_subscribed:
        # Пользователь подписан - обновляем БД
        await db.update_user_subscription(user_id, is_subscribed=True)

        # Отправляем сообщение об успехе
        await callback.message.answer(config.success_message)

        # Выдаем материалы
        await send_materials(callback.message, db, user_id)

        # Удаляем кнопки из оригинального сообщения
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass  # Игнорируем ошибку если сообщение уже изменено

        logger.info(f"✅ Пользователь {user_id} успешно прошел воронку")

    else:
        # Пользователь не подписан
        await callback.answer(
            "❌ Вы еще не подписались на канал!\n\n"
            "Подпишитесь и нажмите кнопку еще раз.",
            show_alert=True,
        )
        logger.info(f"❌ Пользователь {user_id} не прошел проверку подписки")
