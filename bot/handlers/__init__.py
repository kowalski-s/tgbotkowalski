"""
Модуль обработчиков команд и сообщений
"""
from aiogram import Router
from . import start, admin, messages

# Главный роутер для всех обработчиков
main_router = Router()

# Подключаем роутеры из модулей
main_router.include_router(start.router)
main_router.include_router(admin.router)
main_router.include_router(messages.router)

__all__ = ["main_router"]
