"""
Конфигурация бота из переменных окружения
"""
import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Базовая директория проекта (корень)
BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем переменные из .env
load_dotenv()


@dataclass
class Config:
    """Конфигурация бота"""

    # Telegram
    bot_token: str
    admin_id: int
    channel_id: str  # Может быть @username или -100123456789
    channel_link: str

    # Контент
    article_link: str
    pdf_file_path: str

    # База данных
    database_path: str

    # Сообщения
    welcome_message: str
    success_message: str
    work_with_me_message: str

    @classmethod
    def from_env(cls) -> "Config":
        """Создает конфигурацию из переменных окружения"""

        # Проверяем обязательные переменные
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN не установлен в .env файле!")

        admin_id_str = os.getenv("ADMIN_ID")
        if not admin_id_str:
            raise ValueError("ADMIN_ID не установлен в .env файле!")

        try:
            admin_id = int(admin_id_str)
        except ValueError:
            raise ValueError("ADMIN_ID должен быть числом!")

        channel_id = os.getenv("CHANNEL_ID")
        if not channel_id:
            raise ValueError("CHANNEL_ID не установлен в .env файле!")

        # Преобразуем относительные пути в абсолютные
        pdf_path = os.getenv("PDF_FILE_PATH", "static/bonus.pdf")
        db_path = os.getenv("DATABASE_PATH", "data/bot.db")

        # Если путь относительный, делаем абсолютным от корня проекта
        if not os.path.isabs(pdf_path):
            pdf_path = str(BASE_DIR / pdf_path)
        if not os.path.isabs(db_path):
            db_path = str(BASE_DIR / db_path)

        return cls(
            bot_token=bot_token,
            admin_id=admin_id,
            channel_id=channel_id,
            channel_link=os.getenv("CHANNEL_LINK", "https://t.me/your_channel"),
            article_link=os.getenv("ARTICLE_LINK", "https://example.com/article"),
            pdf_file_path=pdf_path,
            database_path=db_path,
            welcome_message=os.getenv(
                "WELCOME_MESSAGE",
                "Привет! 👋\n\nДля получения полезной статьи подпишись на мой канал."
            ),
            success_message=os.getenv(
                "SUCCESS_MESSAGE",
                "Отлично! ✅\n\nВот твоя статья и бонусный материал."
            ),
            work_with_me_message=os.getenv(
                "WORK_WITH_ME_MESSAGE",
                "Хочешь работать со мной? Напиши мне прямо здесь, и я отвечу!"
            ),
        )


# Глобальный экземпляр конфигурации
config = Config.from_env()
