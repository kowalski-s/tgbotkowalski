"""
Скрипт для проверки конфигурации перед запуском бота
"""
import os
import sys
from pathlib import Path


def check_env_file():
    """Проверка наличия .env файла"""
    if not Path(".env").exists():
        print("❌ Файл .env не найден!")
        print("   Создайте его: copy .env.example .env")
        return False
    print("✅ Файл .env найден")
    return True


def check_env_variables():
    """Проверка переменных окружения"""
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = {
        "BOT_TOKEN": "Токен бота от @BotFather",
        "ADMIN_ID": "Ваш Telegram ID от @userinfobot",
        "CHANNEL_ID": "ID канала или @username",
        "CHANNEL_LINK": "Ссылка на канал",
    }

    all_ok = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            print(f"❌ {var} не установлен ({description})")
            all_ok = False
        else:
            # Маскируем чувствительные данные
            if var == "BOT_TOKEN":
                display_value = value[:10] + "..." + value[-5:]
            elif var == "ADMIN_ID":
                display_value = value
            else:
                display_value = value if len(value) < 30 else value[:27] + "..."
            print(f"✅ {var} = {display_value}")

    return all_ok


def check_pdf_file():
    """Проверка наличия PDF файла"""
    from dotenv import load_dotenv
    load_dotenv()

    pdf_path = os.getenv("PDF_FILE_PATH", "./data/bonus.pdf")

    if not Path(pdf_path).exists():
        print(f"❌ PDF файл не найден: {pdf_path}")
        print("   Поместите ваш PDF файл в папку data/")
        return False

    file_size = Path(pdf_path).stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    print(f"✅ PDF файл найден: {pdf_path} ({file_size_mb:.2f} MB)")

    # Telegram имеет лимит на размер файлов
    if file_size_mb > 50:
        print("⚠️  ВНИМАНИЕ: Размер файла больше 50 MB!")
        print("   Telegram Bot API поддерживает файлы до 50 MB")
        return False

    return True


def check_data_directory():
    """Проверка наличия папки data"""
    if not Path("data").exists():
        print("❌ Папка data не найдена")
        print("   Создайте её: mkdir data")
        return False
    print("✅ Папка data найдена")
    return True


def check_dependencies():
    """Проверка установки зависимостей"""
    try:
        import aiogram
        import aiosqlite
        from dotenv import load_dotenv
        print("✅ Все зависимости установлены")
        print(f"   aiogram: {aiogram.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Не установлены зависимости: {e}")
        print("   Установите их: pip install -r requirements.txt")
        return False


def main():
    """Главная функция проверки"""
    print("=" * 50)
    print("🔍 ПРОВЕРКА КОНФИГУРАЦИИ БОТА")
    print("=" * 50)
    print()

    checks = [
        ("Зависимости Python", check_dependencies),
        ("Файл .env", check_env_file),
        ("Переменные окружения", check_env_variables),
        ("Папка data", check_data_directory),
        ("PDF файл", check_pdf_file),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n📋 Проверка: {name}")
        print("-" * 50)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    if all(results):
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("\n🚀 Можно запускать бота: python -m bot.main")
    else:
        print("❌ ЕСТЬ ОШИБКИ!")
        print("\n⚠️  Исправьте ошибки перед запуском бота")
        sys.exit(1)
    print("=" * 50)


if __name__ == "__main__":
    main()
