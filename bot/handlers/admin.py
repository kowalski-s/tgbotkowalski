"""
Обработчики команд администратора
"""
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import config
from bot.database import Database

logger = logging.getLogger(__name__)

# Создаем роутер для админских команд
router = Router()


class BroadcastStates(StatesGroup):
    """Состояния для рассылки"""
    waiting_for_message = State()


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == config.admin_id


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
    ])


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Главное меню администратора"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_stats")
async def callback_stats(callback: CallbackQuery, db: Database):
    """Статистика через callback"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    stats = await db.get_stats()

    stats_text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"✅ Подписались: <b>{stats['subscribed_users']}</b>\n"
        f"📎 Получили файл: <b>{stats['received_file']}</b>\n"
        f"💬 Всего сообщений: <b>{stats['total_messages']}</b>\n"
    )

    if stats['total_users'] > 0:
        subscription_rate = (stats['subscribed_users'] / stats['total_users']) * 100
        file_rate = (stats['received_file'] / stats['total_users']) * 100

        stats_text += (
            f"\n📈 <b>Конверсия:</b>\n"
            f"• В подписку: <b>{subscription_rate:.1f}%</b>\n"
            f"• Получили файл: <b>{file_rate:.1f}%</b>"
        )

    await callback.message.edit_text(
        stats_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def callback_users(callback: CallbackQuery, db: Database):
    """Список пользователей через callback"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    users = await db.get_all_users()

    if not users:
        await callback.message.edit_text(
            "👥 <b>Пользователи</b>\n\nПока нет пользователей.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
            ])
        )
        await callback.answer()
        return

    users_text = "👥 <b>Пользователи</b>\n\n"

    for i, user in enumerate(users[:20], 1):  # Показываем первых 20
        username = f"@{user['username']}" if user['username'] else "—"
        name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip() or "—"
        subscribed = "✅" if user['is_subscribed'] else "❌"
        file_received = "📎" if user['received_file'] else ""

        users_text += f"{i}. {name} ({username}) {subscribed}{file_received}\n"

    if len(users) > 20:
        users_text += f"\n<i>...и ещё {len(users) - 20} пользователей</i>"

    users_text += f"\n\n<b>Всего: {len(users)}</b>"

    await callback.message.edit_text(
        users_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
        ])
    )
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def callback_broadcast(callback: CallbackQuery, state: FSMContext):
    """Начало рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await state.set_state(BroadcastStates.waiting_for_message)

    await callback.message.edit_text(
        "📢 <b>Рассылка</b>\n\n"
        "Отправьте сообщение, которое хотите разослать всем пользователям.\n\n"
        "<i>Для отмены отправьте /cancel</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def callback_back(callback: CallbackQuery):
    """Возврат в главное меню"""
    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🔐 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    if not is_admin(message.from_user.id):
        return

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=get_admin_keyboard()
    )


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext, db: Database):
    """Обработка сообщения для рассылки"""
    if not is_admin(message.from_user.id):
        return

    await state.clear()

    user_ids = await db.get_all_user_ids()

    if not user_ids:
        await message.answer("❌ Нет пользователей для рассылки.")
        return

    await message.answer(f"📢 Начинаю рассылку для {len(user_ids)} пользователей...")

    success = 0
    failed = 0

    for user_id in user_ids:
        try:
            await message.bot.send_message(chat_id=user_id, text=message.text)
            success += 1
            await asyncio.sleep(0.05)  # Небольшая задержка для избежания лимитов
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            failed += 1

    await message.answer(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"Успешно: {success}\n"
        f"Ошибок: {failed}",
        parse_mode="HTML"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database):
    """Команда /stats - статистика по пользователям"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    stats = await db.get_stats()

    stats_text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"✅ Подписались: <b>{stats['subscribed_users']}</b>\n"
        f"📎 Получили файл: <b>{stats['received_file']}</b>\n"
        f"💬 Всего сообщений: <b>{stats['total_messages']}</b>\n"
    )

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


@router.message(Command("users"))
async def cmd_users(message: Message, db: Database):
    """Команда /users - список пользователей"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    users = await db.get_all_users()

    if not users:
        await message.answer("👥 Пока нет пользователей.")
        return

    users_text = "👥 <b>Пользователи</b>\n\n"

    for i, user in enumerate(users[:20], 1):
        username = f"@{user['username']}" if user['username'] else "—"
        name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip() or "—"
        subscribed = "✅" if user['is_subscribed'] else "❌"
        file_received = "📎" if user['received_file'] else ""

        users_text += f"{i}. {name} ({username}) {subscribed}{file_received}\n"

    if len(users) > 20:
        users_text += f"\n<i>...и ещё {len(users) - 20} пользователей</i>"

    users_text += f"\n\n<b>Всего: {len(users)}</b>"

    await message.answer(users_text, parse_mode="HTML")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    """Команда /broadcast - начать рассылку"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    await state.set_state(BroadcastStates.waiting_for_message)

    await message.answer(
        "📢 <b>Рассылка</b>\n\n"
        "Отправьте сообщение, которое хотите разослать всем пользователям.\n\n"
        "<i>Для отмены отправьте /cancel</i>",
        parse_mode="HTML"
    )


@router.message(F.reply_to_message)
async def reply_to_user(message: Message, db: Database):
    """Ответ администратора пользователю через reply"""
    if not is_admin(message.from_user.id):
        return

    replied_text = message.reply_to_message.text or message.reply_to_message.caption

    if not replied_text or "[ID:" not in replied_text:
        await message.answer(
            "⚠️ Не удалось определить пользователя. "
            "Отвечайте только на сообщения от пользователей."
        )
        return

    try:
        user_id_str = replied_text.split("[ID:")[1].split("]")[0].strip()
        user_id = int(user_id_str)
    except (IndexError, ValueError):
        await message.answer("⚠️ Ошибка парсинга ID пользователя.")
        return

    try:
        await message.bot.send_message(
            chat_id=user_id,
            text=message.text
        )

        await db.save_message(user_id, message.text, is_from_admin=True)

        await message.answer(f"✅ Сообщение отправлено пользователю {user_id}")

        logger.info(f"Администратор ответил пользователю {user_id}")

    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
        await message.answer(f"❌ Ошибка отправки сообщения: {e}")
