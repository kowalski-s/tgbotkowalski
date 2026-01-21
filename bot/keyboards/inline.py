"""
Inline клавиатуры для бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_subscription_keyboard(channel_link: str) -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопками для подписки на канал

    Args:
        channel_link: Ссылка на канал

    Returns:
        InlineKeyboardMarkup: Клавиатура
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Подписаться на канал",
                    url=channel_link
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я подписался",
                    callback_data="check_subscription"
                )
            ],
        ]
    )
    return keyboard
