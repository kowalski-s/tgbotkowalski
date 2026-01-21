"""
Обработчик команды /start и проверки подписки
"""
import logging
import asyncio
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest

from bot.config import config
from bot.database import Database
from bot.keyboards import get_subscription_keyboard, get_article_keyboard
from bot.utils import check_user_subscription

logger = logging.getLogger(__name__)

# Создаем роутер для этого модуля
router = Router()

# Константы
ARTICLE_LINK = "https://teletype.in/@kowalski_inga/S3OpxEKn4Qh"
DELAY_BONUS = 5 * 60  # 5 минут в секундах
DELAY_CONTACT = 30  # 30 секунд


async def send_bonus_pdf(bot, user_id: int, db: Database):
    """Отправка бонусного PDF"""
    try:
        if os.path.exists(config.pdf_file_path):
            pdf_file = FSInputFile(config.pdf_file_path)
            await bot.send_document(
                chat_id=user_id,
                document=pdf_file,
                caption=(
                    "А это бонусный материал - чеклист с вопросами для ИИ.\n\n"
                    "Поможет подробно обсудить твой проект и заранее "
                    "разобраться во всех важных моментах."
                )
            )
            await db.mark_file_received(user_id)
            logger.info(f"PDF отправлен пользователю {user_id}")
        else:
            logger.error(f"PDF файл не найден: {config.pdf_file_path}")
    except Exception as e:
        logger.error(f"Ошибка отправки PDF пользователю {user_id}: {e}")


async def send_contact_message(bot, user_id: int):
    """Отправка контактного сообщения"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                "📩 Хочешь обсудить проект или заказать разработку?\n\n"
                "Напиши мне:\n"
                "- Здесь (в боте)\n"
                "- Напрямую: @kowalski_inga"
            )
        )
        logger.info(f"Контактное сообщение отправлено пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки контактного сообщения пользователю {user_id}: {e}")


async def send_delayed_messages(bot, user_id: int, db: Database):
    """Отложенная отправка бонуса и контактов"""
    # Ждём 5 минут
    await asyncio.sleep(DELAY_BONUS)
    await send_bonus_pdf(bot, user_id, db)

    # Ждём 30 секунд
    await asyncio.sleep(DELAY_CONTACT)
    await send_contact_message(bot, user_id)


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """
    Обработчик команды /start
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

    # Проверяем, получал ли уже материалы
    user_data = await db.get_user(user.id)
    already_received = user_data.get("received_file", False) if user_data else False

    if already_received:
        # Уже получал материалы - просто приветствуем
        logger.info(f"Пользователь {user.id} уже получал материалы")
        await message.answer(
            "Привет! 👋\n\n"
            "Ты уже получал материалы ранее.\n"
            "Если есть вопросы - просто напиши мне!"
        )
        return

    # Проверяем подписку
    is_subscribed = await check_user_subscription(
        bot=message.bot,
        user_id=user.id,
        channel_id=config.channel_id,
    )

    if is_subscribed:
        # Пользователь УЖЕ подписан - сразу выдаём материалы
        await db.update_user_subscription(user.id, is_subscribed=True)
        logger.info(f"Пользователь {user.id} уже подписан, выдаём материалы")

        # Сообщение 1: Приветствие + кнопка статьи
        await message.answer(
            "Привет!\n\n"
            "Вот обещанная статья, приятного прочтения 🖤",
            reply_markup=get_article_keyboard(ARTICLE_LINK)
        )

        # Запускаем отложенную отправку (5 мин + 30 сек)
        asyncio.create_task(send_delayed_messages(message.bot, user.id, db))

    else:
        # Пользователь НЕ подписан - показываем кнопки подписки
        logger.info(f"Пользователь {user.id} не подписан, показываем кнопки")

        await message.answer(
            "Привет!\n\n"
            'Для получения статьи "Твой первый проект за 6 шагов" - '
            "подпишись на мой канал.",
            reply_markup=get_subscription_keyboard(config.channel_link)
        )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, db: Database):
    """
    Обработчик нажатия на кнопку "Я подписался"
    """
    user_id = callback.from_user.id

    await callback.answer("Проверяю подписку... ⏳", show_alert=False)

    # Проверяем, получал ли уже материалы
    user_data = await db.get_user(user_id)
    already_received = user_data.get("received_file", False) if user_data else False

    if already_received:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await callback.message.answer(
            "Ты уже получал материалы ранее.\n"
            "Если есть вопросы - просто напиши мне!"
        )
        return

    # Проверяем подписку
    is_subscribed = await check_user_subscription(
        bot=callback.bot,
        user_id=user_id,
        channel_id=config.channel_id,
    )

    if is_subscribed:
        # Пользователь подписан
        await db.update_user_subscription(user_id, is_subscribed=True)

        # Удаляем кнопки
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass

        # Сообщение 2: Статья с кнопкой
        await callback.message.answer(
            "Супер! Вот твоя статья, приятного прочтения 🖤",
            reply_markup=get_article_keyboard(ARTICLE_LINK)
        )

        logger.info(f"Пользователь {user_id} подписался, выдаём материалы")

        # Запускаем отложенную отправку (5 мин + 30 сек)
        asyncio.create_task(send_delayed_messages(callback.bot, user_id, db))

    else:
        # Не подписан
        await callback.answer(
            "❌ Вы еще не подписались на канал!\n\n"
            "Подпишитесь и нажмите кнопку еще раз.",
            show_alert=True,
        )
        logger.info(f"Пользователь {user_id} не прошёл проверку подписки")
