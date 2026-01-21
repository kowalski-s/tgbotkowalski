"""
Обработчик обычных сообщений от пользователей
"""
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import StateFilter

from bot.config import config
from bot.database import Database

logger = logging.getLogger(__name__)

# Создаем роутер для обработки сообщений
router = Router()


@router.message(StateFilter(None))
async def handle_user_message(message: Message, db: Database):
    """
    Обработка обычных сообщений от пользователей

    1. Сохраняем сообщение в БД
    2. Пересылаем администратору с информацией о пользователе
    3. Отправляем пользователю подтверждение
    """
    user = message.from_user
    user_id = user.id

    # Сохраняем сообщение в БД
    await db.save_message(user_id, message.text, is_from_admin=False)

    # Формируем информацию о пользователе
    user_info = f"@{user.username}" if user.username else "Нет username"
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

    # Получаем информацию о пользователе из БД
    user_data = await db.get_user(user_id)
    is_subscribed = user_data.get("is_subscribed", False) if user_data else False
    received_file = user_data.get("received_file", False) if user_data else False

    # Формируем сообщение для администратора
    admin_message = (
        f"📩 <b>Новое сообщение от пользователя</b>\n\n"
        f"👤 <b>Пользователь:</b> {full_name}\n"
        f"🔗 <b>Username:</b> {user_info}\n"
        f"🆔 <b>[ID: {user_id}]</b>\n"
        f"✅ <b>Подписан:</b> {'Да' if is_subscribed else 'Нет'}\n"
        f"📎 <b>Получил файл:</b> {'Да' if received_file else 'Нет'}\n\n"
        f"💬 <b>Сообщение:</b>\n{message.text}\n\n"
        f"<i>Чтобы ответить, используйте Reply на это сообщение</i>"
    )

    # Отправляем администратору
    try:
        await message.bot.send_message(
            chat_id=config.admin_id,
            text=admin_message,
            parse_mode="HTML"
        )
        logger.info(f"Сообщение от пользователя {user_id} отправлено администратору")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения администратору: {e}")

    # Подтверждение пользователю
    await message.answer(
        "✅ Ваше сообщение получено!\n\n"
        "Администратор ответит вам в ближайшее время."
    )

    logger.info(f"Обработано сообщение от пользователя {user_id}")
