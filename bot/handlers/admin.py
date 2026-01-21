"""
Обработчики команд администратора
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.config import config
from bot.database import Database

logger = logging.getLogger(__name__)

# Создаем роутер для админских команд
router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == config.admin_id


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database):
    """
    Команда /stats - статистика по пользователям

    Доступна только администратору
    """
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    # Получаем статистику из БД
    stats = await db.get_stats()

    # Формируем сообщение
    stats_text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"✅ Подписались: <b>{stats['subscribed_users']}</b>\n"
        f"📎 Получили файл: <b>{stats['received_file']}</b>\n"
        f"💬 Всего сообщений: <b>{stats['total_messages']}</b>\n"
    )

    # Рассчитываем конверсию
    if stats['total_users'] > 0:
        subscription_rate = (stats['subscribed_users'] / stats['total_users']) * 100
        file_rate = (stats['received_file'] / stats['total_users']) * 100

        stats_text += (
            f"\n📈 <b>Конверсия:</b>\n"
            f"• В подписку: <b>{subscription_rate:.1f}%</b>\n"
            f"• Получили файл: <b>{file_rate:.1f}%</b>"
        )

    await message.answer(stats_text, parse_mode="HTML")
    logger.info(f"Администратор {message.from_user.id} запросил статистику")


@router.message(F.reply_to_message)
async def reply_to_user(message: Message, db: Database):
    """
    Ответ администратора пользователю через reply

    Администратор отвечает (reply) на сообщение пользователя,
    и бот пересылает ответ этому пользователю
    """
    if not is_admin(message.from_user.id):
        return  # Не админ - игнорируем

    # Получаем ID пользователя из текста пересланного сообщения
    # Формат: "Сообщение от пользователя [ID: 123456789]"
    replied_text = message.reply_to_message.text or message.reply_to_message.caption

    if not replied_text or "[ID:" not in replied_text:
        await message.answer(
            "⚠️ Не удалось определить пользователя. "
            "Отвечайте только на сообщения от пользователей."
        )
        return

    try:
        # Извлекаем user_id из текста
        user_id_str = replied_text.split("[ID:")[1].split("]")[0].strip()
        user_id = int(user_id_str)
    except (IndexError, ValueError):
        await message.answer("⚠️ Ошибка парсинга ID пользователя.")
        return

    # Отправляем сообщение пользователю
    try:
        await message.bot.send_message(
            chat_id=user_id,
            text=f"💬 <b>Ответ от администратора:</b>\n\n{message.text}",
            parse_mode="HTML"
        )

        # Сохраняем в БД
        await db.save_message(user_id, message.text, is_from_admin=True)

        # Подтверждение администратору
        await message.answer(f"✅ Сообщение отправлено пользователю {user_id}")

        logger.info(f"Администратор ответил пользователю {user_id}")

    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
        await message.answer(f"❌ Ошибка отправки сообщения: {e}")
