"""
Утилиты для проверок
"""
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


async def check_user_subscription(bot: Bot, user_id: int, channel_id: str) -> bool:
    """
    Проверка подписки пользователя на канал

    Args:
        bot: Экземпляр бота
        user_id: ID пользователя в Telegram
        channel_id: ID или @username канала

    Returns:
        bool: True если подписан, False если нет
    """
    try:
        logger.info(f"🔍 Проверяю подписку: user_id={user_id}, channel_id={channel_id}")

        # Получаем информацию о пользователе в канале
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)

        # Логируем статус для отладки
        logger.info(f"📊 Статус пользователя {user_id} в канале: {member.status}")

        # Проверяем статус
        # creator - создатель, administrator - админ, member - участник
        # left - вышел, kicked - забанен, restricted - ограничен
        if member.status in ["creator", "administrator", "member"]:
            logger.info(f"✅ Пользователь {user_id} подписан на канал {channel_id} (статус: {member.status})")
            return True
        else:
            logger.info(f"❌ Пользователь {user_id} НЕ подписан на канал {channel_id} (статус: {member.status})")
            return False

    except TelegramBadRequest as e:
        logger.error(f"❌ Ошибка проверки подписки (Bad Request):")
        logger.error(f"   User ID: {user_id}")
        logger.error(f"   Channel ID: {channel_id}")
        logger.error(f"   Ошибка: {e}")
        logger.error(f"   Возможные причины:")
        logger.error(f"   1. Бот НЕ добавлен в администраторы канала")
        logger.error(f"   2. Неверный CHANNEL_ID в .env")
        logger.error(f"   3. У бота нет права 'Просмотр сообщений' в канале")
        return False
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка проверки подписки: {e}")
        logger.error(f"   User ID: {user_id}")
        logger.error(f"   Channel ID: {channel_id}")
        return False
