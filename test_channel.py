"""
Скрипт для проверки правильности настройки канала
Запуск: python test_channel.py
"""
import asyncio
import sys
import os
from aiogram import Bot
from dotenv import load_dotenv

# Для Windows - настройка вывода UTF-8
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Загружаем .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = os.getenv("ADMIN_ID")


async def test_channel():
    """Тестирование доступа к каналу"""

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не установлен в .env!")
        return False

    if not CHANNEL_ID:
        print("❌ CHANNEL_ID не установлен в .env!")
        return False

    if not ADMIN_ID:
        print("❌ ADMIN_ID не установлен в .env!")
        return False

    print("=" * 60)
    print("🔍 ТЕСТИРОВАНИЕ ДОСТУПА К КАНАЛУ")
    print("=" * 60)
    print()

    bot = Bot(token=BOT_TOKEN)

    try:
        # 1. Проверяем бота
        print("1️⃣ Проверка бота...")
        bot_info = await bot.get_me()
        print(f"✅ Бот найден: @{bot_info.username} (ID: {bot_info.id})")
        print()

        # 2. Получаем информацию о канале
        print("2️⃣ Проверка канала...")
        print(f"   CHANNEL_ID из .env: {CHANNEL_ID}")

        try:
            chat = await bot.get_chat(CHANNEL_ID)
            print(f"✅ Канал найден:")
            print(f"   Название: {chat.title}")
            print(f"   Тип: {chat.type}")
            if chat.username:
                print(f"   Username: @{chat.username}")
            print(f"   ID: {chat.id}")
            print()
        except Exception as e:
            print(f"❌ Ошибка получения информации о канале: {e}")
            print()
            print("🔧 Возможные причины:")
            print("   1. Неверный CHANNEL_ID в .env")
            print("   2. Бот не добавлен в канал")
            print()
            return False

        # 3. Проверяем, является ли бот администратором
        print("3️⃣ Проверка прав бота в канале...")
        try:
            bot_member = await bot.get_chat_member(CHANNEL_ID, bot_info.id)
            print(f"   Статус бота: {bot_member.status}")

            if bot_member.status in ["creator", "administrator"]:
                print("✅ Бот является администратором канала")

                # Проверяем права
                if hasattr(bot_member, "can_read_messages"):
                    if bot_member.can_read_messages:
                        print("✅ У бота есть право 'Просмотр сообщений'")
                    else:
                        print("⚠️  У бота НЕТ права 'Просмотр сообщений'")
            else:
                print("❌ Бот НЕ является администратором!")
                print()
                print("🔧 Что нужно сделать:")
                print("   1. Откройте канал в Telegram")
                print("   2. Перейдите в настройки канала → Администраторы")
                print("   3. Добавьте бота в администраторы")
                print("   4. Включите право 'Просмотр сообщений'")
                print()
                return False
            print()

        except Exception as e:
            print(f"❌ Ошибка проверки прав бота: {e}")
            print()
            return False

        # 4. Тестируем проверку подписки администратора
        print("4️⃣ Тестирование проверки подписки...")
        print(f"   Проверяю подписку для ADMIN_ID: {ADMIN_ID}")

        try:
            admin_member = await bot.get_chat_member(CHANNEL_ID, int(ADMIN_ID))
            print(f"   Статус администратора: {admin_member.status}")

            if admin_member.status in ["creator", "administrator", "member"]:
                print(f"✅ Пользователь {ADMIN_ID} подписан на канал")
            else:
                print(f"❌ Пользователь {ADMIN_ID} НЕ подписан на канал")
                print(f"   Статус: {admin_member.status}")

        except Exception as e:
            print(f"❌ Ошибка проверки подписки: {e}")
            print()
            return False

        print()
        print("=" * 60)
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("=" * 60)
        print()
        print("🚀 Бот готов к работе. Проверка подписки должна работать.")
        print()

        return True

    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await bot.session.close()


def main():
    """Главная функция"""
    result = asyncio.run(test_channel())

    if not result:
        print()
        print("❌ ТЕСТИРОВАНИЕ ПРОВАЛЕНО")
        print()
        print("📖 Инструкция по настройке канала:")
        print()
        print("1. Создайте канал в Telegram (если еще не создан)")
        print()
        print("2. Узнайте ID канала:")
        print("   a) Если у канала есть @username:")
        print("      CHANNEL_ID=@your_channel")
        print()
        print("   b) Если хотите использовать числовой ID:")
        print("      - Перешлите сообщение из канала в @username_to_id_bot")
        print("      - Скопируйте ID (формат: -1001234567890)")
        print("      CHANNEL_ID=-1001234567890")
        print()
        print("3. Добавьте бота в администраторы:")
        print("   - Откройте канал → Настройки → Администраторы")
        print("   - Нажмите 'Добавить администратора'")
        print("   - Найдите вашего бота")
        print("   - Включите минимум одно право (например, 'Удаление сообщений')")
        print("   - Сохраните")
        print()
        print("4. Проверьте .env файл:")
        print("   BOT_TOKEN=ваш_токен")
        print("   CHANNEL_ID=@your_channel  или  -1001234567890")
        print("   ADMIN_ID=ваш_telegram_id")
        print()
        sys.exit(1)
    else:
        print("🎉 Готово! Запускайте бота: python -m bot.main")


if __name__ == "__main__":
    main()
