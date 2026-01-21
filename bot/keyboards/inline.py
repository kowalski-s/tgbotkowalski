"""
Inline клавиатуры для бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_subscription_keyboard(channel_link: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопками для подписки на канал"""
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


def get_article_keyboard(article_link: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой для статьи"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Читать статью",
                    url=article_link
                )
            ],
        ]
    )
    return keyboard
